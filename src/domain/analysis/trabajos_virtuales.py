"""
Cálculo de coeficientes de flexibilidad mediante Trabajos Virtuales.

Implementa el Teorema de los Trabajos Virtuales (TTV) para calcular:
- Coeficientes de flexibilidad fij = ∫(M̄i × M̄j)/(EI) dx
- Términos independientes e0i = ∫(M̄i × M⁰)/(EI) dx

Utiliza la Tabla de Integrales de Mohr cuando es posible para
mayor eficiencia y precisión.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from src.utils.constants import (
    DEFAULT_INTEGRATION_POINTS,
    TOLERANCE,
)
from src.utils.integration import (
    integral_trabajo_virtual,
    integral_trabajo_virtual_completa,
    TipoDiagrama,
    integral_mohr,
)

if TYPE_CHECKING:
    from src.domain.entities.barra import Barra
    from src.domain.entities.carga import CargaTermica
    from src.domain.analysis.subestructuras import Subestructura


@dataclass
class CoeficientesFlexibilidad:
    """
    Resultado del cálculo de coeficientes de flexibilidad.

    Attributes:
        F: Matriz de flexibilidad [n×n]
        e0: Vector de términos independientes [n]
        n: Número de redundantes
        es_simetrica: True si F cumple simetría (Ley de Maxwell)
        condicionamiento: Número de condición de F
    """
    F: NDArray[np.float64]
    e0: NDArray[np.float64]
    n: int
    es_simetrica: bool = True
    condicionamiento: float = 1.0

    def fij(self, i: int, j: int) -> float:
        """
        Obtiene el coeficiente fij.

        Args:
            i: Índice del primer redundante (1-indexed)
            j: Índice del segundo redundante (1-indexed)

        Returns:
            Coeficiente de flexibilidad fij
        """
        return self.F[i-1, j-1]

    def e0i(self, i: int) -> float:
        """
        Obtiene el término independiente e0i.

        Args:
            i: Índice del redundante (1-indexed)

        Returns:
            Término independiente e0i
        """
        return self.e0[i-1]


class CalculadorFlexibilidad:
    """
    Calcula los coeficientes de flexibilidad para el SECE.

    Utiliza el Teorema de los Trabajos Virtuales:
    - fij = Σ∫(M̄i × M̄j)/(EI) dx + Σ∫(N̄i × N̄j)/(EA) dx
    - e0i = Σ∫(M̄i × M⁰)/(EI) dx + Σ∫(N̄i × N⁰)/(EA) dx + efectos térmicos

    La matriz F es simétrica por la Ley de Maxwell-Betti: fij = fji
    """

    def __init__(
        self,
        barras: List[Barra],
        fundamental: Subestructura,
        subestructuras_xi: List[Subestructura],
        incluir_axil: bool = False,
        incluir_cortante: bool = False,
        n_puntos_integracion: int = DEFAULT_INTEGRATION_POINTS,
        cargas_termicas: Optional[List[CargaTermica]] = None,
        redundantes: Optional[List] = None,
        nudos: Optional[List] = None,
        movimientos_impuestos: Optional[List] = None,
    ):
        """
        Inicializa el calculador.

        Args:
            barras: Lista de barras del modelo
            fundamental: Subestructura con cargas reales (M⁰, N⁰)
            subestructuras_xi: Lista de subestructuras Xi (M̄i, N̄i)
            incluir_axil: Si True, incluye deformación axial
            incluir_cortante: Si True, incluye deformación por cortante
            n_puntos_integracion: Puntos para integración numérica
            cargas_termicas: Lista de cargas térmicas (opcional)
            redundantes: Lista de redundantes (para identificar resortes)
            nudos: Lista de nudos (para acceder a vínculos elásticos)
            movimientos_impuestos: Lista de MovimientoImpuesto (opcional)
        """
        self.barras = barras
        self.fundamental = fundamental
        self.subestructuras_xi = subestructuras_xi
        self.incluir_axil = incluir_axil
        self.incluir_cortante = incluir_cortante
        self.n_puntos = n_puntos_integracion
        self.cargas_termicas = cargas_termicas or []
        self.redundantes = redundantes or []
        self.nudos = nudos or []
        self.movimientos_impuestos = movimientos_impuestos or []

        self.n = len(subestructuras_xi)
        self._F: Optional[NDArray] = None
        self._e0: Optional[NDArray] = None

    def calcular(self) -> CoeficientesFlexibilidad:
        """
        Calcula la matriz de flexibilidad F y el vector e0.

        Returns:
            CoeficientesFlexibilidad con F y e0 calculados
        """
        self._F = np.zeros((self.n, self.n), dtype=np.float64)
        self._e0 = np.zeros(self.n, dtype=np.float64)

        # Calcular coeficientes fij
        for i in range(self.n):
            for j in range(i, self.n):  # Solo triángulo superior (simetría)
                fij = self._calcular_fij(i, j)
                self._F[i, j] = fij
                self._F[j, i] = fij  # Simetría (Ley de Maxwell)

        # Agregar flexibilidad de resortes elásticos
        self._agregar_flexibilidad_resortes()

        # Calcular términos e0i
        for i in range(self.n):
            self._e0[i] = self._calcular_e0i(i)

        # Verificar simetría
        es_simetrica = np.allclose(self._F, self._F.T, atol=TOLERANCE)

        # Calcular condicionamiento
        try:
            condicionamiento = np.linalg.cond(self._F)
        except:
            condicionamiento = float('inf')

        return CoeficientesFlexibilidad(
            F=self._F,
            e0=self._e0,
            n=self.n,
            es_simetrica=es_simetrica,
            condicionamiento=condicionamiento,
        )

    def _calcular_fij(self, i: int, j: int) -> float:
        """
        Calcula el coeficiente de flexibilidad fij.

        fij = Σ∫(M̄i × M̄j)/(EI) dx + [términos axiales y cortante]

        Args:
            i: Índice del primer redundante (0-indexed)
            j: Índice del segundo redundante (0-indexed)

        Returns:
            Coeficiente fij
        """
        sub_i = self.subestructuras_xi[i]
        sub_j = self.subestructuras_xi[j]

        fij = 0.0

        for barra in self.barras:
            L = barra.L
            EI = barra.EI
            EA = barra.EA

            # Funciones de momento
            Mi = lambda x, b=barra, s=sub_i: s.M(b.id, x)
            Mj = lambda x, b=barra, s=sub_j: s.M(b.id, x)

            # Integrar ∫(Mi × Mj)/(EI) dx
            integral_M = integral_trabajo_virtual(
                Mi, Mj, L, EI,
                metodo="simpson",
                n_puntos=self.n_puntos
            )
            fij += integral_M

            # Término axial si se incluye
            if self.incluir_axil:
                Ni = lambda x, b=barra, s=sub_i: s.N(b.id, x)
                Nj = lambda x, b=barra, s=sub_j: s.N(b.id, x)

                integral_N = integral_trabajo_virtual(
                    Ni, Nj, L, EA,
                    metodo="simpson",
                    n_puntos=self.n_puntos
                )
                fij += integral_N

        return fij

    def _calcular_e0i_termico(self, i: int) -> float:
        """
        Calcula la contribución térmica al término independiente e0i.

        Para cada carga térmica en cada barra:
        - Efecto uniforme: δi = α·ΔT·∫(Ni dx)
        - Efecto gradiente: δi = (α·ΔT_grad/h)·∫(Mi dx)

        Args:
            i: Índice del redundante (0-indexed)

        Returns:
            Contribución térmica a e0i
        """
        if not self.cargas_termicas:
            return 0.0

        sub_i = self.subestructuras_xi[i]
        e0i_termico = 0.0

        for carga_termica in self.cargas_termicas:
            if not carga_termica.barra:
                continue

            barra = carga_termica.barra

            # Verificar que la barra esté en la lista de barras del modelo
            if barra not in self.barras:
                continue

            # Contribución uniforme: α·ΔT·∫(Ni dx)
            if abs(carga_termica.delta_T_uniforme) > TOLERANCE:
                # Obtener esfuerzo axial virtual en la barra
                # Para axil constante: ∫(Ni dx) = Ni·L
                try:
                    Ni_promedio = (sub_i.N(barra.id, 0) + sub_i.N(barra.id, barra.L)) / 2
                    trabajo_uniforme = carga_termica.trabajo_virtual_uniforme(Ni_promedio)
                    e0i_termico += trabajo_uniforme
                except (KeyError, AttributeError):
                    # La barra puede no tener esfuerzo axial en esta subestructura
                    pass

            # Contribución gradiente: κ·∫(Mi dx)
            if abs(carga_termica.delta_T_gradiente) > TOLERANCE:
                try:
                    # Crear función de momento virtual
                    def Mi_func(x):
                        return sub_i.M(barra.id, x)

                    trabajo_gradiente = carga_termica.trabajo_virtual_gradiente(Mi_func)
                    e0i_termico += trabajo_gradiente
                except (KeyError, AttributeError):
                    # La barra puede no tener momento en esta subestructura
                    pass

        return e0i_termico

    def _calcular_e0i(self, i: int) -> float:
        """
        Calcula el término independiente e0i.

        e0i = Σ∫(M̄i × M⁰)/(EI) dx + Σ∫(N̄i × N⁰)/(EA) dx + efectos térmicos

        Args:
            i: Índice del redundante (0-indexed)

        Returns:
            Término e0i
        """
        sub_i = self.subestructuras_xi[i]

        e0i = 0.0

        # Contribución mecánica (cargas convencionales)
        for barra in self.barras:
            L = barra.L
            EI = barra.EI
            EA = barra.EA

            # Funciones de momento
            Mi = lambda x, b=barra, s=sub_i: s.M(b.id, x)
            M0 = lambda x, b=barra, f=self.fundamental: f.M(b.id, x)

            # Integrar ∫(M̄i × M⁰)/(EI) dx
            integral_M = integral_trabajo_virtual(
                Mi, M0, L, EI,
                metodo="simpson",
                n_puntos=self.n_puntos
            )
            e0i += integral_M

            # Término axial
            if self.incluir_axil:
                Ni = lambda x, b=barra, s=sub_i: s.N(b.id, x)
                N0 = lambda x, b=barra, f=self.fundamental: f.N(b.id, x)

                integral_N = integral_trabajo_virtual(
                    Ni, N0, L, EA,
                    metodo="simpson",
                    n_puntos=self.n_puntos
                )
                e0i += integral_N

        # Contribución térmica
        e0i_termico = self._calcular_e0i_termico(i)
        e0i += e0i_termico

        # Contribución de resortes mantenidos (no eliminados)
        e0i_resortes = self._calcular_e0i_resortes(i)
        e0i += e0i_resortes

        # Contribución de movimientos impuestos (en nudos distintos al redundante)
        e0i_movimientos = self._calcular_e0i_movimientos_impuestos(i)
        e0i += e0i_movimientos

        return e0i

    def calcular_con_tabla_mohr(self) -> CoeficientesFlexibilidad:
        """
        Calcula usando la Tabla de Integrales de Mohr (más eficiente).

        Para fij (diagramas unitarios): usa fórmulas cerradas de Mohr
        Para e0i (diagrama fundamental): usa integración numérica
        porque el diagrama M0 puede ser no lineal.

        Returns:
            CoeficientesFlexibilidad calculado
        """
        self._F = np.zeros((self.n, self.n), dtype=np.float64)
        self._e0 = np.zeros(self.n, dtype=np.float64)

        for i in range(self.n):
            for j in range(i, self.n):
                fij = self._calcular_fij_mohr(i, j)
                self._F[i, j] = fij
                self._F[j, i] = fij

        # Usar integración numérica para e0i porque M0 puede ser no lineal
        for i in range(self.n):
            self._e0[i] = self._calcular_e0i(i)

        es_simetrica = np.allclose(self._F, self._F.T, atol=TOLERANCE)

        try:
            condicionamiento = np.linalg.cond(self._F)
        except:
            condicionamiento = float('inf')

        return CoeficientesFlexibilidad(
            F=self._F,
            e0=self._e0,
            n=self.n,
            es_simetrica=es_simetrica,
            condicionamiento=condicionamiento,
        )

    def _calcular_fij_mohr(self, i: int, j: int) -> float:
        """
        Calcula fij usando Tabla de Mohr para diagramas lineales.

        Para diagramas M̄i lineales (caso típico con cargas unitarias),
        usa las fórmulas cerradas de la tabla.
        """
        sub_i = self.subestructuras_xi[i]
        sub_j = self.subestructuras_xi[j]

        fij = 0.0

        for barra in self.barras:
            L = barra.L
            EI = barra.EI

            # Obtener valores en extremos
            diag_i = sub_i.diagramas.get(barra.id)
            diag_j = sub_j.diagramas.get(barra.id)

            if diag_i is None or diag_j is None:
                continue

            Mi_0 = diag_i.Mi
            Mi_L = diag_i.Mj
            Mj_0 = diag_j.Mi
            Mj_L = diag_j.Mj

            # Usar fórmula de trapecio × trapecio de la tabla de Mohr
            # ∫(Mi × Mj)dx = (L/6) × [Mi_0×(2×Mj_0 + Mj_L) + Mi_L×(Mj_0 + 2×Mj_L)]
            integral = (L / 6) * (
                Mi_0 * (2*Mj_0 + Mj_L) +
                Mi_L * (Mj_0 + 2*Mj_L)
            )

            fij += integral / EI

        return fij

    def _calcular_e0i_mohr(self, i: int) -> float:
        """
        Calcula e0i usando Tabla de Mohr.

        Para M̄i lineal y M⁰ que puede ser parabólico (carga distribuida),
        usa las fórmulas correspondientes.
        """
        sub_i = self.subestructuras_xi[i]

        e0i = 0.0

        for barra in self.barras:
            L = barra.L
            EI = barra.EI

            diag_i = sub_i.diagramas.get(barra.id)
            diag_0 = self.fundamental.diagramas.get(barra.id)

            if diag_i is None or diag_0 is None:
                continue

            Mi_0 = diag_i.Mi
            Mi_L = diag_i.Mj

            # Para M⁰, muestrear varios puntos y usar Simpson si es necesario
            # Simplificación: asumir M⁰ también lineal (aproximación)
            M0_0 = diag_0.Mi
            M0_L = diag_0.Mj

            # Fórmula trapecio × trapecio
            integral = (L / 6) * (
                Mi_0 * (2*M0_0 + M0_L) +
                Mi_L * (M0_0 + 2*M0_L)
            )

            e0i += integral / EI

        return e0i

    def _calcular_e0i_resortes(self, i: int) -> float:
        """
        Calcula la contribución de resortes MANTENIDOS (no eliminados) a e0i.

        REGLA: Solo contribuyen los resortes que NO son redundantes.
        Si el resorte fue eliminado como redundante, NO contribuye a e0i.

        Para un resorte mantenido con carga P₀:
        e0i += P̄ᵢ × P₀/k = 1 × P₀/k

        Args:
            i: Índice del redundante (0-indexed)

        Returns:
            Contribución de resortes mantenidos a e0i
        """
        if not self.nudos or not self.redundantes:
            return 0.0

        from src.domain.entities.vinculo import ResorteElastico
        from src.domain.analysis.redundantes import TipoRedundante

        e0i_resortes = 0.0

        # Identificar redundantes eliminados (sus nudos)
        nudos_redundantes_eliminados = {r.nudo_id for r in self.redundantes}

        # Procesar resortes en nudos NO eliminados
        for nudo in self.nudos:
            if not isinstance(nudo.vinculo, ResorteElastico):
                continue

            # Si este nudo es un redundante, el resorte fue eliminado → no contribuye a e0i
            if nudo.id in nudos_redundantes_eliminados:
                # Verificar si el tipo coincide (podría haber redundante en X pero resorte en Y)
                for redundante in self.redundantes:
                    if redundante.nudo_id != nudo.id:
                        continue

                    resorte = nudo.vinculo

                    # Si el redundante coincide con una rigidez del resorte, ese resorte fue eliminado
                    if (redundante.tipo == TipoRedundante.REACCION_RX and resorte.kx > 0) or \
                       (redundante.tipo == TipoRedundante.REACCION_RY and resorte.ky > 0) or \
                       (redundante.tipo == TipoRedundante.REACCION_MZ and resorte.ktheta > 0):
                        # Resorte eliminado, no contribuye
                        continue

            # Resorte mantenido → contribuye a e0i
            resorte = nudo.vinculo

            # Obtener la reacción del resorte en la estructura fundamental (carga real P₀)
            reaccion_fundamental = self.fundamental.obtener_reaccion(nudo.id)
            Rx0, Ry0, Mz0 = reaccion_fundamental

            # Obtener la fuerza virtual P̄ᵢ de la subestructura Xi
            reaccion_xi = self.subestructuras_xi[i].obtener_reaccion(nudo.id)
            Rxi, Ryi, Mzi = reaccion_xi

            # Contribución según tipo de rigidez
            if resorte.kx > 0 and abs(Rx0) > 1e-10:
                # e0i += P̄ᵢ × P₀/k
                e0i_resortes += Rxi * (Rx0 / resorte.kx)

            if resorte.ky > 0 and abs(Ry0) > 1e-10:
                e0i_resortes += Ryi * (Ry0 / resorte.ky)

            if resorte.ktheta > 0 and abs(Mz0) > 1e-10:
                e0i_resortes += Mzi * (Mz0 / resorte.ktheta)

        return e0i_resortes

    def _calcular_e0i_movimientos_impuestos(self, i: int) -> float:
        """
        Calcula la contribución de movimientos impuestos a e0i.

        REGLA FUNDAMENTAL:
        - Si el movimiento es en el mismo nudo que el redundante Xi:
          NO contribuye a e0i (va directamente a δₕ)
        - Si el movimiento es en otro nudo:
          Contribuye a e0i mediante trabajo virtual: e0i += P̄ᵢ × δₖ

        Donde:
        - P̄ᵢ: reacción virtual en el nudo k debido a Xi = 1
        - δₖ: movimiento impuesto en el nudo k

        Args:
            i: Índice del redundante (0-indexed)

        Returns:
            Contribución de movimientos impuestos a e0i
        """
        if not self.movimientos_impuestos or not self.redundantes:
            return 0.0

        e0i_mov = 0.0
        redundante_i = self.redundantes[i]
        sub_i = self.subestructuras_xi[i]

        for movimiento in self.movimientos_impuestos:
            if not movimiento.nudo:
                continue

            # CLAVE: Si el movimiento es en el mismo nudo que el redundante,
            # NO contribuye a e0i (va a δₕ)
            if movimiento.nudo.id == redundante_i.nudo_id:
                continue

            # Obtener reacción virtual P̄ᵢ en el nudo del movimiento
            try:
                Rxi, Ryi, Mzi = sub_i.obtener_reaccion(movimiento.nudo.id)
            except (KeyError, AttributeError):
                # El nudo puede no tener reacciones en esta subestructura
                continue

            # Contribución: P̄ᵢ × δ (trabajo virtual)
            e0i_mov += Rxi * movimiento.delta_x
            e0i_mov += Ryi * movimiento.delta_y
            e0i_mov += Mzi * movimiento.delta_theta

        return e0i_mov

    def _agregar_flexibilidad_resortes(self) -> None:
        """
        Agrega la contribución de resortes elásticos a la matriz de flexibilidad.

        Para cada resorte con rigidez k en la dirección de un redundante Xi:
        F[i,i] += 1/k

        Esto aumenta la flexibilidad del sistema en esa dirección.

        IMPORTANTE: Solo se modifica la diagonal de F, porque la flexibilidad
        de un resorte solo afecta al desplazamiento en su propia dirección.
        """
        if not self.redundantes or not self.nudos:
            # Sin redundantes o nudos, no hay resortes que procesar
            return

        from src.domain.entities.vinculo import ResorteElastico
        from src.domain.analysis.redundantes import TipoRedundante

        for i, redundante in enumerate(self.redundantes):
            # Buscar si este redundante corresponde a un resorte elástico
            nudo = next((n for n in self.nudos if n.id == redundante.nudo_id), None)

            if nudo is None or not isinstance(nudo.vinculo, ResorteElastico):
                # No es un resorte, continuar
                continue

            resorte = nudo.vinculo

            # Agregar flexibilidad 1/k según el tipo de redundante
            if redundante.tipo == TipoRedundante.REACCION_RX and resorte.kx > 0:
                # Redundante es Rx y el resorte tiene rigidez horizontal
                flexibilidad = 1.0 / resorte.kx
                self._F[i, i] += flexibilidad

            elif redundante.tipo == TipoRedundante.REACCION_RY and resorte.ky > 0:
                # Redundante es Ry y el resorte tiene rigidez vertical
                flexibilidad = 1.0 / resorte.ky
                self._F[i, i] += flexibilidad

            elif redundante.tipo == TipoRedundante.REACCION_MZ and resorte.ktheta > 0:
                # Redundante es Mz y el resorte tiene rigidez rotacional
                flexibilidad = 1.0 / resorte.ktheta
                self._F[i, i] += flexibilidad


def verificar_simetria_matriz(F: NDArray, tolerancia: float = TOLERANCE) -> Tuple[bool, float]:
    """
    Verifica la simetría de la matriz de flexibilidad (Ley de Maxwell).

    Args:
        F: Matriz de flexibilidad
        tolerancia: Tolerancia para comparación

    Returns:
        Tupla (es_simetrica, max_diferencia)
    """
    diferencia = np.abs(F - F.T)
    max_dif = np.max(diferencia)
    es_simetrica = max_dif < tolerancia

    return es_simetrica, max_dif


def verificar_diagonal_positiva(F: NDArray) -> Tuple[bool, List[int]]:
    """
    Verifica que los elementos diagonales de F sean positivos.

    Los coeficientes fii (flexibilidades directas) siempre deben ser
    positivos por definición física.

    Args:
        F: Matriz de flexibilidad

    Returns:
        Tupla (todos_positivos, indices_negativos)
    """
    diagonal = np.diag(F)
    indices_negativos = np.where(diagonal <= 0)[0].tolist()
    todos_positivos = len(indices_negativos) == 0

    return todos_positivos, indices_negativos
