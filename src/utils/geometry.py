"""
Funciones geométricas para análisis estructural.

Proporciona cálculos de distancias, ángulos y transformaciones
de coordenadas entre sistemas locales y globales.
"""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from .constants import LENGTH_TOLERANCE, TOLERANCE


def distancia(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calcula la distancia euclidiana entre dos puntos en 2D.

    Args:
        x1: Coordenada X del primer punto
        y1: Coordenada Y del primer punto
        x2: Coordenada X del segundo punto
        y2: Coordenada Y del segundo punto

    Returns:
        Distancia entre los dos puntos

    Example:
        >>> distancia(0, 0, 3, 4)
        5.0
    """
    return math.hypot(x2 - x1, y2 - y1)


def angulo_entre_puntos(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calcula el ángulo (en radianes) de la línea que une dos puntos
    respecto al eje X positivo.

    Args:
        x1: Coordenada X del punto inicial
        y1: Coordenada Y del punto inicial
        x2: Coordenada X del punto final
        y2: Coordenada Y del punto final

    Returns:
        Ángulo en radianes en el rango [-π, π]

    Example:
        >>> import math
        >>> angulo_entre_puntos(0, 0, 1, 1)  # doctest: +ELLIPSIS
        0.785...  # π/4
    """
    return math.atan2(y2 - y1, x2 - x1)


def angulo_grados(angulo_rad: float) -> float:
    """
    Convierte un ángulo de radianes a grados.

    Args:
        angulo_rad: Ángulo en radianes

    Returns:
        Ángulo en grados
    """
    return math.degrees(angulo_rad)


def angulo_radianes(angulo_deg: float) -> float:
    """
    Convierte un ángulo de grados a radianes.

    Args:
        angulo_deg: Ángulo en grados

    Returns:
        Ángulo en radianes
    """
    return math.radians(angulo_deg)


def matriz_rotacion_2d(angulo: float) -> NDArray[np.float64]:
    """
    Genera la matriz de rotación 2D para un ángulo dado.

    La matriz rota vectores del sistema local al sistema global.

    Args:
        angulo: Ángulo de rotación en radianes

    Returns:
        Matriz de rotación 2x2

    Example:
        >>> import numpy as np
        >>> R = matriz_rotacion_2d(np.pi/2)  # Rotación de 90°
        >>> np.allclose(R @ [1, 0], [0, 1])
        True
    """
    c = math.cos(angulo)
    s = math.sin(angulo)
    return np.array([
        [c, -s],
        [s, c]
    ], dtype=np.float64)


def matriz_transformacion_barra(angulo: float) -> NDArray[np.float64]:
    """
    Genera la matriz de transformación 3x3 para una barra.

    Transforma vectores [ux, uy, θz] del sistema local al global.

    Args:
        angulo: Ángulo de la barra respecto al eje X global (radianes)

    Returns:
        Matriz de transformación 3x3

    Note:
        La rotación θz no se ve afectada por la transformación
        (es la misma en ambos sistemas).
    """
    c = math.cos(angulo)
    s = math.sin(angulo)
    return np.array([
        [c, -s, 0],
        [s, c, 0],
        [0, 0, 1]
    ], dtype=np.float64)


def matriz_transformacion_barra_6x6(angulo: float) -> NDArray[np.float64]:
    """
    Genera la matriz de transformación 6x6 para los GDL de ambos extremos de una barra.

    Transforma el vector [uxi, uyi, θzi, uxj, uyj, θzj] del sistema local al global.

    Args:
        angulo: Ángulo de la barra respecto al eje X global (radianes)

    Returns:
        Matriz de transformación 6x6
    """
    T3 = matriz_transformacion_barra(angulo)
    T6 = np.zeros((6, 6), dtype=np.float64)
    T6[0:3, 0:3] = T3
    T6[3:6, 3:6] = T3
    return T6


def local_a_global(
    ux_local: float,
    uy_local: float,
    angulo: float
) -> Tuple[float, float]:
    """
    Transforma desplazamientos del sistema local al global.

    Args:
        ux_local: Desplazamiento en dirección x local
        uy_local: Desplazamiento en dirección y local
        angulo: Ángulo de la barra (radianes)

    Returns:
        Tupla (ux_global, uy_global)
    """
    c = math.cos(angulo)
    s = math.sin(angulo)
    ux_global = c * ux_local - s * uy_local
    uy_global = s * ux_local + c * uy_local
    return (ux_global, uy_global)


def global_a_local(
    ux_global: float,
    uy_global: float,
    angulo: float
) -> Tuple[float, float]:
    """
    Transforma desplazamientos del sistema global al local.

    Args:
        ux_global: Desplazamiento en dirección X global
        uy_global: Desplazamiento en dirección Y global
        angulo: Ángulo de la barra (radianes)

    Returns:
        Tupla (ux_local, uy_local)
    """
    c = math.cos(angulo)
    s = math.sin(angulo)
    ux_local = c * ux_global + s * uy_global
    uy_local = -s * ux_global + c * uy_global
    return (ux_local, uy_local)


def punto_sobre_barra(
    xi: float, yi: float,
    xj: float, yj: float,
    distancia_desde_i: float
) -> Tuple[float, float]:
    """
    Calcula las coordenadas globales de un punto sobre una barra.

    Args:
        xi: Coordenada X del nudo inicial
        yi: Coordenada Y del nudo inicial
        xj: Coordenada X del nudo final
        yj: Coordenada Y del nudo final
        distancia_desde_i: Distancia desde el nudo i a lo largo de la barra

    Returns:
        Tupla (x, y) con las coordenadas del punto

    Raises:
        ValueError: Si la distancia es negativa o mayor que la longitud
    """
    L = distancia(xi, yi, xj, yj)

    if distancia_desde_i < -LENGTH_TOLERANCE:
        raise ValueError("La distancia desde i no puede ser negativa")
    if distancia_desde_i > L + LENGTH_TOLERANCE:
        raise ValueError(f"La distancia desde i ({distancia_desde_i}) "
                        f"excede la longitud de la barra ({L})")

    # Normalizar la distancia al rango [0, L]
    distancia_desde_i = max(0, min(distancia_desde_i, L))

    if L < LENGTH_TOLERANCE:
        return (xi, yi)

    # Interpolación lineal
    t = distancia_desde_i / L
    x = xi + t * (xj - xi)
    y = yi + t * (yj - yi)

    return (x, y)


def perpendicular_a_barra(
    xi: float, yi: float,
    xj: float, yj: float,
    distancia_desde_i: float,
    offset: float
) -> Tuple[float, float]:
    """
    Calcula un punto desplazado perpendicularmente desde una barra.

    Útil para dibujar diagramas de esfuerzos con offset visual.

    Args:
        xi: Coordenada X del nudo inicial
        yi: Coordenada Y del nudo inicial
        xj: Coordenada X del nudo final
        yj: Coordenada Y del nudo final
        distancia_desde_i: Distancia desde el nudo i a lo largo de la barra
        offset: Distancia perpendicular (positivo = lado izquierdo según dirección i→j)

    Returns:
        Tupla (x, y) con las coordenadas del punto desplazado
    """
    # Punto base sobre la barra
    xp, yp = punto_sobre_barra(xi, yi, xj, yj, distancia_desde_i)

    # Ángulo de la barra
    theta = angulo_entre_puntos(xi, yi, xj, yj)

    # Vector perpendicular (90° en sentido antihorario)
    nx = -math.sin(theta)
    ny = math.cos(theta)

    # Punto desplazado
    x = xp + offset * nx
    y = yp + offset * ny

    return (x, y)


def son_colineales(
    x1: float, y1: float,
    x2: float, y2: float,
    x3: float, y3: float
) -> bool:
    """
    Determina si tres puntos son colineales.

    Args:
        x1, y1: Coordenadas del primer punto
        x2, y2: Coordenadas del segundo punto
        x3, y3: Coordenadas del tercer punto

    Returns:
        True si los puntos son colineales (dentro de tolerancia)
    """
    # Área del triángulo = 0.5 * |det([x2-x1, x3-x1; y2-y1, y3-y1])|
    area_doble = abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1))
    return area_doble < TOLERANCE


def son_coincidentes(
    x1: float, y1: float,
    x2: float, y2: float
) -> bool:
    """
    Determina si dos puntos son coincidentes (mismo punto).

    Args:
        x1, y1: Coordenadas del primer punto
        x2, y2: Coordenadas del segundo punto

    Returns:
        True si los puntos coinciden (dentro de tolerancia)
    """
    return distancia(x1, y1, x2, y2) < LENGTH_TOLERANCE


def normalizar_angulo(angulo: float) -> float:
    """
    Normaliza un ángulo al rango [-π, π].

    Args:
        angulo: Ángulo en radianes

    Returns:
        Ángulo normalizado en [-π, π]
    """
    while angulo > math.pi:
        angulo -= 2 * math.pi
    while angulo < -math.pi:
        angulo += 2 * math.pi
    return angulo


def interpolacion_lineal(
    x: float,
    x1: float, y1: float,
    x2: float, y2: float
) -> float:
    """
    Realiza interpolación lineal entre dos puntos.

    Args:
        x: Valor de x donde interpolar
        x1: Coordenada x del primer punto
        y1: Coordenada y del primer punto
        x2: Coordenada x del segundo punto
        y2: Coordenada y del segundo punto

    Returns:
        Valor interpolado de y en x

    Raises:
        ValueError: Si x1 == x2
    """
    if abs(x2 - x1) < LENGTH_TOLERANCE:
        raise ValueError("x1 y x2 no pueden ser iguales para interpolación")

    t = (x - x1) / (x2 - x1)
    return y1 + t * (y2 - y1)
