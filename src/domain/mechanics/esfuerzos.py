"""
Cálculo de esfuerzos internos (N, V, M) en barras.

Proporciona funciones para calcular los diagramas de esfuerzos
en estructuras isostáticas y para cada subestructura del método de fuerzas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple

import numpy as np

if TYPE_CHECKING:
    from src.domain.entities.barra import Barra
    from src.domain.entities.carga import Carga, CargaPuntualBarra, CargaDistribuida
    from src.domain.entities.nudo import Nudo
    from src.domain.mechanics.equilibrio import Reacciones


@dataclass
class EsfuerzosTramo:
    """
    Esfuerzos internos en un tramo de barra.

    Cada tramo tiene funciones que definen N(x), V(x), M(x)
    como funciones de la posición local x (desde el inicio del tramo).

    Attributes:
        x_inicio: Posición de inicio del tramo [m]
        x_fin: Posición de fin del tramo [m]
        N: Función N(x) de esfuerzo axil [kN]
        V: Función V(x) de esfuerzo cortante [kN]
        M: Función M(x) de momento flector [kNm]
    """
    x_inicio: float
    x_fin: float
    N: Callable[[float], float] = field(default=lambda x: 0.0)
    V: Callable[[float], float] = field(default=lambda x: 0.0)
    M: Callable[[float], float] = field(default=lambda x: 0.0)

    @property
    def longitud(self) -> float:
        """Longitud del tramo."""
        return self.x_fin - self.x_inicio


@dataclass
class DiagramaEsfuerzos:
    """
    Diagrama completo de esfuerzos para una barra.

    Contiene los esfuerzos como funciones continuas a lo largo de la barra.

    Attributes:
        barra_id: ID de la barra
        L: Longitud de la barra [m]
        tramos: Lista de tramos con sus funciones de esfuerzos
    """
    barra_id: int
    L: float
    tramos: List[EsfuerzosTramo] = field(default_factory=list)

    # Esfuerzos en extremos (para facilitar cálculos)
    Ni: float = 0.0  # N en x=0
    Nj: float = 0.0  # N en x=L
    Vi: float = 0.0  # V en x=0
    Vj: float = 0.0  # V en x=L
    Mi: float = 0.0  # M en x=0
    Mj: float = 0.0  # M en x=L

    # Funciones de esfuerzos personalizadas (para superposición)
    _N_func: Optional[Callable[[float], float]] = None
    _V_func: Optional[Callable[[float], float]] = None
    _M_func: Optional[Callable[[float], float]] = None

    def N(self, x: float) -> float:
        """
        Esfuerzo axil en la posición x.

        Args:
            x: Posición desde el nudo i [m]

        Returns:
            Esfuerzo axil N(x) [kN]
        """
        # Si hay función personalizada, usarla
        if self._N_func is not None:
            return self._N_func(x)

        # Buscar en tramos
        for tramo in self.tramos:
            if tramo.x_inicio <= x <= tramo.x_fin:
                return tramo.N(x)
        return 0.0

    def V(self, x: float) -> float:
        """
        Esfuerzo cortante en la posición x.

        Args:
            x: Posición desde el nudo i [m]

        Returns:
            Esfuerzo cortante V(x) [kN]
        """
        # Si hay función personalizada, usarla
        if self._V_func is not None:
            return self._V_func(x)

        # Buscar en tramos
        for tramo in self.tramos:
            if tramo.x_inicio <= x <= tramo.x_fin:
                return tramo.V(x)
        return 0.0

    def M(self, x: float) -> float:
        """
        Momento flector en la posición x.

        Args:
            x: Posición desde el nudo i [m]

        Returns:
            Momento flector M(x) [kNm]
        """
        # Si hay función personalizada, usarla
        if self._M_func is not None:
            return self._M_func(x)

        # Buscar en tramos
        for tramo in self.tramos:
            if tramo.x_inicio <= x <= tramo.x_fin:
                return tramo.M(x)
        return 0.0

    def valores_en_puntos(self, n_puntos: int = 21) -> Dict[str, np.ndarray]:
        """
        Calcula los esfuerzos en n_puntos a lo largo de la barra.

        Args:
            n_puntos: Número de puntos de muestreo

        Returns:
            Diccionario con arrays de x, N, V, M
        """
        x = np.linspace(0, self.L, n_puntos)
        N = np.array([self.N(xi) for xi in x])
        V = np.array([self.V(xi) for xi in x])
        M = np.array([self.M(xi) for xi in x])

        return {"x": x, "N": N, "V": V, "M": M}


def calcular_esfuerzos_viga_isostatica(
    barra: Barra,
    cargas_barra: List[Carga],
    reaccion_i: Tuple[float, float, float],
    reaccion_j: Tuple[float, float, float],
) -> DiagramaEsfuerzos:
    """
    Calcula esfuerzos internos usando método de secciones (mirar a izquierda).

    CONVENCIÓN:
    - Y+ hacia abajo
    - Reacción hacia arriba = negativa en Y
    - Momento positivo = tracciona fibra inferior

    MÉTODO DE SECCIONES:
    Para calcular M(x), me paro en x y miro a la IZQUIERDA:
    - Reacción hacia arriba (Y-) a distancia d → Momento = Ry × d (horario, positivo)
    - Carga hacia abajo (Y+) a distancia d → Momento = -P × d (antihorario, negativo)

    Args:
        barra: Barra a analizar
        cargas_barra: Cargas sobre la barra
        reaccion_i: (Rx, Ry, Mz) en nudo i (coordenadas globales)
        reaccion_j: (Rx, Ry, Mz) en nudo j (coordenadas globales)

    Returns:
        DiagramaEsfuerzos con N(x), V(x), M(x)
    """
    from src.domain.entities.carga import CargaPuntualBarra, CargaDistribuida

    L = barra.L
    Rx_i, Ry_i, Mz_i = reaccion_i
    Rx_j, Ry_j, Mz_j = reaccion_j

    # Identificar puntos de interés (extremos + cargas puntuales)
    puntos_interes = [0.0, L]
    for carga in cargas_barra:
        if isinstance(carga, CargaPuntualBarra):
            if 0 < carga.a < L:
                puntos_interes.append(carga.a)

    puntos_interes = sorted(set(puntos_interes))

    # Crear función de momento usando método de secciones
    def calcular_momento_en_x(x: float) -> float:
        """
        Calcula M(x) mirando a la IZQUIERDA desde posición x.

        REGLA: Determinar si cada fuerza produce giro HORARIO (+) o ANTIHORARIO (-)
        respecto al punto x.

        Con Y+ hacia abajo:
        - Fuerza hacia ARRIBA (Y-) a la izquierda → giro HORARIO → momento +
        - Fuerza hacia ABAJO (Y+) a la izquierda → giro ANTIHORARIO → momento -
        """
        momento = 0.0

        # 1. Reacción en i
        if x > 0 and abs(Ry_i) > 1e-10:
            distancia = x
            # Ry_i < 0 (hacia arriba) → giro horario
            # El momento es: M = -Ry_i × distancia
            # Si Ry_i = -10 (arriba), M = -(-10) × distancia = +10×d (positivo)
            momento -= Ry_i * distancia

        # 2. Momento aplicado en i
        momento += Mz_i

        # 3. Cargas puntuales a la izquierda de x
        for carga in cargas_barra:
            if isinstance(carga, CargaPuntualBarra):
                if carga.a < x:
                    Px_global, Py_global = carga.componentes_globales()
                    distancia = x - carga.a

                    # Py_global > 0 (hacia abajo) → giro antihorario → negativo
                    # Py_global < 0 (hacia arriba) → giro horario → positivo
                    if Py_global > 0:  # Hacia abajo
                        momento -= Py_global * distancia
                    else:  # Hacia arriba
                        momento += abs(Py_global) * distancia

        # 4. Cargas distribuidas a la izquierda de x
        for carga in cargas_barra:
            if isinstance(carga, CargaDistribuida):
                x1 = carga.x1
                x2 = min(carga.x2 or L, x)

                if x1 < x:
                    if carga.es_uniforme:
                        longitud_activa = x2 - x1
                        resultante = carga.q1 * longitud_activa
                        x_centroide = x1 + longitud_activa / 2
                    else:
                        longitud_activa = x2 - x1
                        resultante = (carga.q1 + carga.q2) / 2 * longitud_activa
                        x_centroide = x1 + longitud_activa / 2

                    ang_rad = math.radians(carga.angulo)
                    Py_dist = resultante * math.sin(ang_rad)
                    distancia = x - x_centroide

                    if Py_dist > 0:  # Hacia abajo
                        momento -= Py_dist * distancia
                    else:  # Hacia arriba
                        momento += abs(Py_dist) * distancia

        return momento

    def calcular_cortante_en_x(x: float) -> float:
        """Calcula V(x) mirando a la IZQUIERDA desde posición x."""
        cortante = Ry_i

        for carga in cargas_barra:
            if isinstance(carga, CargaPuntualBarra):
                if carga.a < x:
                    Px_global, Py_global = carga.componentes_globales()
                    cortante += Py_global

        for carga in cargas_barra:
            if isinstance(carga, CargaDistribuida):
                x1 = carga.x1
                x2 = min(carga.x2 or L, x)

                if x1 < x:
                    if carga.es_uniforme:
                        longitud_activa = x2 - x1
                        resultante = carga.q1 * longitud_activa
                    else:
                        longitud_activa = x2 - x1
                        resultante = (carga.q1 + carga.q2) / 2 * longitud_activa

                    ang_rad = math.radians(carga.angulo)
                    Py_dist = resultante * math.sin(ang_rad)
                    cortante += Py_dist

        return cortante

    def calcular_axial_en_x(x: float) -> float:
        """Calcula N(x) mirando a la IZQUIERDA desde posición x."""
        axial = Rx_i

        for carga in cargas_barra:
            if isinstance(carga, CargaPuntualBarra):
                if carga.a < x:
                    Px_global, Py_global = carga.componentes_globales()
                    axial += Px_global

        for carga in cargas_barra:
            if isinstance(carga, CargaDistribuida):
                x1 = carga.x1
                x2 = min(carga.x2 or L, x)

                if x1 < x:
                    if carga.es_uniforme:
                        longitud_activa = x2 - x1
                        resultante = carga.q1 * longitud_activa
                    else:
                        longitud_activa = x2 - x1
                        resultante = (carga.q1 + carga.q2) / 2 * longitud_activa

                    ang_rad = math.radians(carga.angulo)
                    Px_dist = resultante * math.cos(ang_rad)
                    axial += Px_dist

        return axial

    # Crear tramos
    tramos = []
    for i in range(len(puntos_interes) - 1):
        x_ini = puntos_interes[i]
        x_fin = puntos_interes[i + 1]

        tramo = EsfuerzosTramo(
            x_inicio=x_ini,
            x_fin=x_fin,
            N=calcular_axial_en_x,
            V=calcular_cortante_en_x,
            M=calcular_momento_en_x,
        )
        tramos.append(tramo)

    diagrama = DiagramaEsfuerzos(
        barra_id=barra.id,
        L=L,
        tramos=tramos,
        Ni=calcular_axial_en_x(0),
        Nj=calcular_axial_en_x(L),
        Vi=calcular_cortante_en_x(0),
        Vj=calcular_cortante_en_x(L),
        Mi=calcular_momento_en_x(0),
        Mj=calcular_momento_en_x(L),
    )

    return diagrama


def crear_diagrama_lineal(
    barra_id: int,
    L: float,
    valor_i: float,
    valor_j: float,
    tipo: str = "M"
) -> DiagramaEsfuerzos:
    """
    Crea un diagrama lineal (típico para momento con carga unitaria).

    Útil para generar diagramas de subestructuras Xi con carga unitaria.

    Args:
        barra_id: ID de la barra
        L: Longitud de la barra
        valor_i: Valor en el extremo i
        valor_j: Valor en el extremo j
        tipo: "N", "V" o "M"

    Returns:
        DiagramaEsfuerzos con variación lineal
    """
    pendiente = (valor_j - valor_i) / L if L > 0 else 0

    if tipo == "N":
        def N_func(x, v0=valor_i, m=pendiente):
            return v0 + m * x
        def V_func(x):
            return 0.0
        def M_func(x):
            return 0.0
    elif tipo == "V":
        def N_func(x):
            return 0.0
        def V_func(x, v0=valor_i, m=pendiente):
            return v0 + m * x
        def M_func(x):
            return 0.0
    else:  # M
        def N_func(x):
            return 0.0
        def V_func(x):
            return 0.0
        def M_func(x, v0=valor_i, m=pendiente):
            return v0 + m * x

    tramo = EsfuerzosTramo(
        x_inicio=0.0,
        x_fin=L,
        N=N_func,
        V=V_func,
        M=M_func,
    )

    return DiagramaEsfuerzos(
        barra_id=barra_id,
        L=L,
        tramos=[tramo],
        Mi=valor_i if tipo == "M" else 0.0,
        Mj=valor_j if tipo == "M" else 0.0,
        Ni=valor_i if tipo == "N" else 0.0,
        Nj=valor_j if tipo == "N" else 0.0,
        Vi=valor_i if tipo == "V" else 0.0,
        Vj=valor_j if tipo == "V" else 0.0,
    )


def crear_diagrama_constante(
    barra_id: int,
    L: float,
    valor: float,
    tipo: str = "N"
) -> DiagramaEsfuerzos:
    """
    Crea un diagrama constante (típico para axil).

    Args:
        barra_id: ID de la barra
        L: Longitud de la barra
        valor: Valor constante
        tipo: "N", "V" o "M"

    Returns:
        DiagramaEsfuerzos con valor constante
    """
    return crear_diagrama_lineal(barra_id, L, valor, valor, tipo)


def crear_diagrama_parabolico(
    barra_id: int,
    L: float,
    valor_i: float,
    valor_j: float,
    flecha: float,
    tipo: str = "M"
) -> DiagramaEsfuerzos:
    """
    Crea un diagrama parabólico (típico para momento con carga distribuida).

    La parábola tiene valores valor_i y valor_j en los extremos,
    con una flecha adicional en el centro.

    Args:
        barra_id: ID de la barra
        L: Longitud de la barra
        valor_i: Valor en el extremo i
        valor_j: Valor en el extremo j
        flecha: Valor adicional en el centro (curvatura de la parábola)
        tipo: "N", "V" o "M"

    Returns:
        DiagramaEsfuerzos con variación parabólica
    """
    # Parábola: y = a*x² + b*x + c
    # Condiciones: y(0) = valor_i, y(L) = valor_j, y(L/2) = (valor_i+valor_j)/2 + flecha

    # De y(0) = valor_i → c = valor_i
    c = valor_i

    # De y(L) = valor_j → a*L² + b*L + c = valor_j
    # De y(L/2) = (valor_i+valor_j)/2 + flecha
    #   → a*(L/2)² + b*(L/2) + c = (valor_i+valor_j)/2 + flecha
    #   → a*L²/4 + b*L/2 + valor_i = (valor_i+valor_j)/2 + flecha

    # Simplificando:
    # a*L² + b*L = valor_j - valor_i
    # a*L²/4 + b*L/2 = (valor_j - valor_i)/2 + flecha

    if L > 1e-10:
        # Sistema 2x2
        # [L²   L ] [a]   [valor_j - valor_i]
        # [L²/4 L/2] [b] = [(valor_j-valor_i)/2 + flecha]

        delta = valor_j - valor_i
        A = np.array([[L**2, L], [L**2/4, L/2]])
        B = np.array([delta, delta/2 + flecha])
        sol = np.linalg.solve(A, B)
        a, b = sol[0], sol[1]
    else:
        a, b = 0, 0

    if tipo == "M":
        def M_func(x, a=a, b=b, c=c):
            return a * x**2 + b * x + c
        def N_func(x):
            return 0.0
        def V_func(x):
            return 0.0
    else:
        def M_func(x):
            return 0.0
        def N_func(x):
            return 0.0
        def V_func(x):
            return 0.0

    tramo = EsfuerzosTramo(
        x_inicio=0.0,
        x_fin=L,
        N=N_func,
        V=V_func,
        M=M_func,
    )

    return DiagramaEsfuerzos(
        barra_id=barra_id,
        L=L,
        tramos=[tramo],
        Mi=valor_i,
        Mj=valor_j,
    )
