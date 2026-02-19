"""
Ecuaciones de equilibrio para estructuras isostáticas.

Proporciona funciones para:
- Resolver reacciones de vínculo en estructuras isostáticas
- Verificar equilibrio global (ΣFx=0, ΣFy=0, ΣMz=0)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from src.utils.constants import EQUILIBRIUM_TOLERANCE

if TYPE_CHECKING:
    from src.domain.entities.barra import Barra
    from src.domain.entities.carga import Carga, CargaPuntualNudo, CargaDistribuida, CargaPuntualBarra
    from src.domain.entities.nudo import Nudo
    from src.domain.entities.vinculo import Vinculo


def momento_fuerza_respecto_punto(
    Fx: float,
    Fy: float,
    x_fuerza: float,
    y_fuerza: float,
    x_punto: float,
    y_punto: float,
) -> float:
    """
    Calcula el momento producido por una fuerza respecto a un punto.

    TERNA: X+ derecha, Y+ abajo, rotación horaria +

    La fórmula es: M = -Fy × (x_punto - x_fuerza) + Fx × (y_punto - y_fuerza)

    Interpretación física:
    - Para fuerza vertical Fy a la IZQUIERDA del punto (x_fuerza < x_punto):
        * Fy > 0 (abajo) → momento ANTIHORARIO (negativo)
        * Fy < 0 (arriba) → momento HORARIO (positivo)
    - Para fuerza vertical Fy a la DERECHA del punto (x_fuerza > x_punto):
        * Fy > 0 (abajo) → momento HORARIO (positivo)
        * Fy < 0 (arriba) → momento ANTIHORARIO (negativo)

    Args:
        Fx: Componente horizontal de la fuerza [kN]
        Fy: Componente vertical de la fuerza [kN]
        x_fuerza: Coordenada X donde se aplica la fuerza [m]
        y_fuerza: Coordenada Y donde se aplica la fuerza [m]
        x_punto: Coordenada X del punto de referencia [m]
        y_punto: Coordenada Y del punto de referencia [m]

    Returns:
        Momento respecto al punto [kNm]

    Examples:
        >>> # Fuerza 10kN hacia abajo en x=3, respecto al punto en x=6
        >>> momento_fuerza_respecto_punto(0, 10, 3, 0, 6, 0)
        -30.0  # antihorario

        >>> # Fuerza 10kN hacia arriba en x=0, respecto al punto en x=6
        >>> momento_fuerza_respecto_punto(0, -10, 0, 0, 6, 0)
        60.0  # horario
    """
    dx = x_punto - x_fuerza
    dy = y_punto - y_fuerza
    M = -Fy * dx + Fx * dy
    return M


@dataclass
class FuerzasNodales:
    """
    Fuerzas y momento resultantes en un nudo.

    Attributes:
        nudo_id: ID del nudo
        Fx: Fuerza en dirección X [kN]
        Fy: Fuerza en dirección Y [kN]
        Mz: Momento alrededor de Z [kNm]
    """
    nudo_id: int
    Fx: float = 0.0
    Fy: float = 0.0
    Mz: float = 0.0

    def __add__(self, other: "FuerzasNodales") -> "FuerzasNodales":
        """Suma de fuerzas nodales."""
        return FuerzasNodales(
            nudo_id=self.nudo_id,
            Fx=self.Fx + other.Fx,
            Fy=self.Fy + other.Fy,
            Mz=self.Mz + other.Mz,
        )


@dataclass
class Reacciones:
    """
    Reacciones de vínculo calculadas.

    Attributes:
        reacciones: Diccionario {nudo_id: (Rx, Ry, Mz)}
    """
    reacciones: Dict[int, Tuple[float, float, float]]

    def __getitem__(self, nudo_id: int) -> Tuple[float, float, float]:
        """Permite acceso directo: reacciones[nudo_id] → (Rx, Ry, Mz)"""
        return self.reacciones.get(nudo_id, (0.0, 0.0, 0.0))

    def obtener(self, nudo_id: int) -> Tuple[float, float, float]:
        """Obtiene las reacciones de un nudo."""
        return self.reacciones.get(nudo_id, (0.0, 0.0, 0.0))

    def Rx(self, nudo_id: int) -> float:
        """Reacción horizontal en un nudo."""
        return self.reacciones.get(nudo_id, (0.0, 0.0, 0.0))[0]

    def Ry(self, nudo_id: int) -> float:
        """Reacción vertical en un nudo."""
        return self.reacciones.get(nudo_id, (0.0, 0.0, 0.0))[1]

    def Mz(self, nudo_id: int) -> float:
        """Momento de reacción en un nudo."""
        return self.reacciones.get(nudo_id, (0.0, 0.0, 0.0))[2]


def calcular_fuerzas_equivalentes_nodales(
    barras: List[Barra],
    cargas: List[Carga],
) -> Dict[int, FuerzasNodales]:
    """
    Calcula las fuerzas equivalentes en los nudos debido a cargas sobre barras.

    Las cargas distribuidas y puntuales sobre barras se transforman en
    fuerzas equivalentes en los nudos extremos.

    Args:
        barras: Lista de barras
        cargas: Lista de cargas

    Returns:
        Diccionario {nudo_id: FuerzasNodales}
    """
    from src.domain.entities.carga import CargaPuntualNudo, CargaPuntualBarra, CargaDistribuida

    fuerzas: Dict[int, FuerzasNodales] = {}

    for carga in cargas:
        if isinstance(carga, CargaPuntualNudo):
            # Carga directa en nudo
            if carga.nudo is None:
                continue
            nudo_id = carga.nudo.id
            if nudo_id not in fuerzas:
                fuerzas[nudo_id] = FuerzasNodales(nudo_id)
            fuerzas[nudo_id].Fx += carga.Fx
            fuerzas[nudo_id].Fy += carga.Fy
            fuerzas[nudo_id].Mz += carga.Mz

        elif isinstance(carga, CargaPuntualBarra):
            # Carga puntual sobre barra - transformar a fuerzas nodales equivalentes
            if carga.barra is None:
                continue
            barra = carga.barra
            L = barra.L
            a = carga.a
            b = L - a

            # Componentes de la carga en coordenadas globales
            Px, Py = carga.componentes_globales()

            # IMPORTANTE: Para estructuras isostáticas, las cargas sobre barras
            # se distribuyen en los extremos como fuerzas concentradas, SIN momentos.
            # Los momentos de empotramiento solo existen si AMBOS extremos están empotrados.

            # Fuerzas equivalentes en los extremos (barra simplemente apoyada)
            # Reacciones: Ri = P * b/L, Rj = P * a/L
            Fxi = Px * b / L
            Fyi = Py * b / L
            Fxj = Px * a / L
            Fyj = Py * a / L

            # NO aplicar momentos de empotramiento para estructuras isostáticas
            # Esos momentos solo existen en el análisis de barras con extremos empotrados
            Mi = 0.0
            Mj = 0.0

            nudo_i_id = barra.nudo_i.id
            nudo_j_id = barra.nudo_j.id

            if nudo_i_id not in fuerzas:
                fuerzas[nudo_i_id] = FuerzasNodales(nudo_i_id)
            if nudo_j_id not in fuerzas:
                fuerzas[nudo_j_id] = FuerzasNodales(nudo_j_id)

            fuerzas[nudo_i_id].Fx += Fxi
            fuerzas[nudo_i_id].Fy += Fyi
            fuerzas[nudo_i_id].Mz += Mi
            fuerzas[nudo_j_id].Fx += Fxj
            fuerzas[nudo_j_id].Fy += Fyj
            fuerzas[nudo_j_id].Mz += Mj

        elif isinstance(carga, CargaDistribuida):
            # Carga distribuida sobre barra
            if carga.barra is None:
                continue
            barra = carga.barra
            L = barra.L

            # IMPORTANTE: Para una carga distribuida, tratarla como carga puntual
            # equivalente ubicada en el centroide de la distribución

            # Resultante total
            R = carga.resultante

            # Componentes en coordenadas globales
            import math
            ang_rad = math.radians(carga.angulo)
            Rx = R * math.cos(ang_rad)
            Ry = R * math.sin(ang_rad)

            # Posición del centroide respecto al nudo i (en coordenadas locales de la barra)
            # posicion_resultante_global ya incluye x1
            x_centroide = carga.posicion_resultante_global

            # Distancias desde el centroide a cada extremo
            a = x_centroide  # distancia desde nudo_i al centroide
            b = L - a        # distancia desde centroide al nudo_j

            # Reacciones en extremos como si fuera una carga puntual en el centroide
            # Ri = R * b/L,  Rj = R * a/L
            nudo_i_id = barra.nudo_i.id
            nudo_j_id = barra.nudo_j.id

            if nudo_i_id not in fuerzas:
                fuerzas[nudo_i_id] = FuerzasNodales(nudo_i_id)
            if nudo_j_id not in fuerzas:
                fuerzas[nudo_j_id] = FuerzasNodales(nudo_j_id)

            # Distribuir la carga equivalente
            if L > 1e-10:
                fuerzas[nudo_i_id].Fx += Rx * b / L
                fuerzas[nudo_i_id].Fy += Ry * b / L
                fuerzas[nudo_j_id].Fx += Rx * a / L
                fuerzas[nudo_j_id].Fy += Ry * a / L
            else:
                # Barra de longitud casi cero
                fuerzas[nudo_i_id].Fx += Rx * 0.5
                fuerzas[nudo_i_id].Fy += Ry * 0.5
                fuerzas[nudo_j_id].Fx += Rx * 0.5
                fuerzas[nudo_j_id].Fy += Ry * 0.5

    return fuerzas


def resolver_reacciones_isostatica(
    nudos: List[Nudo],
    barras: List[Barra],
    cargas: List[Carga],
) -> Reacciones:
    """
    Resuelve las reacciones de vínculo para una estructura isostática.

    Utiliza las 3 ecuaciones de equilibrio global:
    - ΣFx = 0
    - ΣFy = 0
    - ΣMz = 0 (respecto a un punto)

    Args:
        nudos: Lista de nudos
        barras: Lista de barras
        cargas: Lista de cargas aplicadas

    Returns:
        Reacciones calculadas

    Raises:
        ValueError: Si la estructura no es isostática o es inestable
    """
    # Identificar nudos con vínculos y sus GDL restringidos
    nudos_vinculados = [n for n in nudos if n.tiene_vinculo]

    # Contar incógnitas de reacción
    incognitas = []
    for nudo in nudos_vinculados:
        gdl = nudo.vinculo.gdl_restringidos()
        for gdl_name in gdl:
            incognitas.append((nudo.id, gdl_name))

    n_incognitas = len(incognitas)

    if n_incognitas < 3:
        raise ValueError(f"Estructura hipostática: solo {n_incognitas} incógnitas, se requieren al menos 3")

    if n_incognitas > 3:
        raise ValueError(f"Estructura hiperestática: {n_incognitas} incógnitas, máximo 3 para resolver por equilibrio")

    from src.domain.entities.carga import CargaPuntualNudo, CargaPuntualBarra, CargaDistribuida
    import math

    # Punto de referencia para momentos (usar primer nudo vinculado)
    x_ref = nudos_vinculados[0].x
    y_ref = nudos_vinculados[0].y

    # Calcular fuerzas y momentos totales DIRECTAMENTE de las cargas
    Fx_total = 0.0
    Fy_total = 0.0
    Mz_total = 0.0

    for carga in cargas:
        if isinstance(carga, CargaPuntualNudo):
            # Carga en nudo
            if carga.nudo is None:
                continue
            Fx_total += carga.Fx
            Fy_total += carga.Fy
            # Momento de la fuerza respecto al punto de referencia
            Mz_total += momento_fuerza_respecto_punto(
                carga.Fx, carga.Fy,
                carga.nudo.x, carga.nudo.y,
                x_ref, y_ref
            )
            # Más momento directo aplicado
            Mz_total += carga.Mz

        elif isinstance(carga, CargaPuntualBarra):
            # Carga puntual sobre barra - usar posición REAL de la carga
            if carga.barra is None:
                continue
            barra = carga.barra

            # Posición global de la carga
            ang_barra = math.atan2(
                barra.nudo_j.y - barra.nudo_i.y,
                barra.nudo_j.x - barra.nudo_i.x
            )
            x_carga = barra.nudo_i.x + carga.a * math.cos(ang_barra)
            y_carga = barra.nudo_i.y + carga.a * math.sin(ang_barra)

            # Componentes globales
            Px, Py = carga.componentes_globales()
            Fx_total += Px
            Fy_total += Py

            # Momento respecto al punto de referencia
            Mz_total += momento_fuerza_respecto_punto(
                Px, Py,
                x_carga, y_carga,
                x_ref, y_ref
            )

        elif isinstance(carga, CargaDistribuida):
            # Carga distribuida - usar centroide
            if carga.barra is None:
                continue
            barra = carga.barra

            # Resultante
            R = carga.resultante
            ang_rad = math.radians(carga.angulo)
            Rx = R * math.cos(ang_rad)
            Ry = R * math.sin(ang_rad)

            Fx_total += Rx
            Fy_total += Ry

            # Posición del centroide en coordenadas globales
            x_centroide = carga.posicion_resultante_global
            ang_barra = math.atan2(
                barra.nudo_j.y - barra.nudo_i.y,
                barra.nudo_j.x - barra.nudo_i.x
            )
            x_global = barra.nudo_i.x + x_centroide * math.cos(ang_barra)
            y_global = barra.nudo_i.y + x_centroide * math.sin(ang_barra)

            # Momento respecto al punto de referencia
            Mz_total += momento_fuerza_respecto_punto(
                Rx, Ry,
                x_global, y_global,
                x_ref, y_ref
            )

    # Construir sistema de ecuaciones [A]{R} = {b}
    # Las reacciones deben equilibrar las cargas: R + Cargas = 0 → R = -Cargas
    # Para momentos: ΣM = Momento_reacciones + Momento_cargas = 0
    # → Momento_reacciones = -Momento_cargas
    A = np.zeros((3, n_incognitas))
    b = np.array([-Fx_total, -Fy_total, +Mz_total])

    for j, (nudo_id, gdl) in enumerate(incognitas):
        nudo = next(n for n in nudos if n.id == nudo_id)

        if gdl == "Ux":
            A[0, j] = 1.0  # Contribuye a ΣFx
            # Fx en (x,y) respecto a (x_ref, y_ref): momento = +Fx × (y - y_ref)
            A[2, j] = (nudo.y - y_ref)  # Contribuye a ΣMz
        elif gdl == "Uy":
            A[1, j] = 1.0  # Contribuye a ΣFy
            # Fy en (x,y) respecto a (x_ref, y_ref): momento = -Fy × (x - x_ref)
            A[2, j] = -(nudo.x - x_ref)  # Contribuye a ΣMz
        elif gdl == "θz":
            # La convención de signos en A usa la negación del brazo de palanca
            # (consistente con A[2,Uy] = -(x-x_ref) en lugar de +(x-x_ref)).
            # Para el momento de reacción directo, se aplica la misma negación:
            # el coeficiente es -1 para que A[2,Mz]×Mz_react = b[2] = +Mz_cargas
            # dé Mz_react = -Mz_cargas, que es la condición de equilibrio correcta.
            A[2, j] = -1.0  # Momento directo (con negación por convención adoptada)

    # Resolver sistema
    try:
        R = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        raise ValueError("Sistema singular: estructura geométricamente inestable")

    # Organizar resultados
    reacciones_dict: Dict[int, Tuple[float, float, float]] = {}

    for j, (nudo_id, gdl) in enumerate(incognitas):
        if nudo_id not in reacciones_dict:
            reacciones_dict[nudo_id] = [0.0, 0.0, 0.0]

        if gdl == "Ux":
            reacciones_dict[nudo_id][0] = R[j]
        elif gdl == "Uy":
            reacciones_dict[nudo_id][1] = R[j]
        elif gdl == "θz":
            reacciones_dict[nudo_id][2] = R[j]

    # Convertir listas a tuplas
    reacciones_dict = {k: tuple(v) for k, v in reacciones_dict.items()}

    return Reacciones(reacciones_dict)


def verificar_equilibrio_global(
    nudos: List[Nudo],
    cargas: List[Carga],
    reacciones: Reacciones,
    barras: List[Barra],
    tolerancia: float = EQUILIBRIUM_TOLERANCE,
) -> Tuple[bool, Dict[str, float]]:
    """
    Verifica que se cumplan las ecuaciones de equilibrio global.

    Args:
        nudos: Lista de nudos
        cargas: Lista de cargas
        reacciones: Reacciones calculadas
        barras: Lista de barras
        tolerancia: Tolerancia para considerar equilibrio (por defecto 1e-6)

    Returns:
        Tupla (cumple_equilibrio, {ΣFx, ΣFy, ΣMz})
    """
    # Calcular fuerzas externas
    fuerzas_nodales = calcular_fuerzas_equivalentes_nodales(barras, cargas)

    Fx_ext = sum(f.Fx for f in fuerzas_nodales.values())
    Fy_ext = sum(f.Fy for f in fuerzas_nodales.values())
    Mz_ext = 0.0

    # Punto de referencia
    x_ref, y_ref = 0.0, 0.0

    for nudo_id, fuerza in fuerzas_nodales.items():
        nudo = next(n for n in nudos if n.id == nudo_id)
        # TERNA: M = -Fy × (x_punto - x_fuerza) + Fx × (y_punto - y_fuerza)
        Mz_ext += -fuerza.Fy * (x_ref - nudo.x) + fuerza.Fx * (y_ref - nudo.y) + fuerza.Mz

    # Sumar reacciones
    Rx_total = 0.0
    Ry_total = 0.0
    Mz_reac = 0.0

    for nudo_id, (Rx, Ry, Mz) in reacciones.reacciones.items():
        nudo = next(n for n in nudos if n.id == nudo_id)
        Rx_total += Rx
        Ry_total += Ry
        # TERNA: M = -Fy × (x_punto - x_fuerza) + Fx × (y_punto - y_fuerza)
        Mz_reac += -Ry * (x_ref - nudo.x) + Rx * (y_ref - nudo.y) + Mz

    # Calcular sumas
    sum_Fx = Fx_ext + Rx_total
    sum_Fy = Fy_ext + Ry_total
    sum_Mz = Mz_ext + Mz_reac

    residuos = {
        "ΣFx": sum_Fx,
        "ΣFy": sum_Fy,
        "ΣMz": sum_Mz,
    }

    cumple = (
        abs(sum_Fx) < tolerancia and
        abs(sum_Fy) < tolerancia and
        abs(sum_Mz) < tolerancia
    )

    return cumple, residuos
