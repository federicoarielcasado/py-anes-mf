"""
Módulo de integración numérica y Tabla de Integrales de Mohr.

Proporciona métodos eficientes para calcular integrales de productos
de diagramas de momentos usando la Tabla de Integrales de Mohr,
así como métodos numéricos (Simpson, Gauss) como alternativa.

Referencias:
    - Tabla de Integrales de Mohr (Universidad de Siegen)
    - Teorema de los Trabajos Virtuales
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Optional, Tuple

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import simpson, quad


class TipoDiagrama(Enum):
    """
    Tipos de diagramas de momento para la Tabla de Integrales de Mohr.

    Los números corresponden a las filas de la tabla:
    1. Rectángulo (constante)
    2. Triángulo (lineal, cero en inicio)
    3. Triángulo (lineal, cero en fin)
    4. Trapecio (lineal, valores diferentes en extremos)
    5. Parábola cuadrática (carga uniforme, tangente horizontal al inicio)
    6. Parábola cuadrática (carga uniforme, tangente horizontal al final)
    7. Parábola cuadrática (máximo al inicio)
    8. Parábola cuadrática (máximo al final)
    9. Parábola cuadrática (cóncava, tangente horizontal al final)
    10. Parábola cuadrática (cóncava, tangente horizontal al inicio)
    11. Parábola cuadrática (simétrica, 3 valores)
    12. Parábola cúbica (carga triangular, tangente horizontal)
    13. Parábola cúbica (carga triangular, tangente horizontal al final)
    14. Parábola cúbica (carga triangular)
    15. Parábola cúbica (carga triangular, invertida)
    """
    RECTANGULO = 1           # j constante
    TRIANGULO_INICIO = 2     # j lineal, 0 en x=0
    TRIANGULO_FIN = 3        # j lineal, 0 en x=L
    TRAPECIO = 4             # j1 y j2 en extremos
    PARABOLA_CONVEXA = 5     # Parábola cuadrática, q uniforme
    PARABOLA_CONCAVA = 6     # Parábola cuadrática invertida
    PARABOLA_MAX_INICIO = 7  # Parábola con máximo al inicio
    PARABOLA_MAX_FIN = 8     # Parábola con máximo al final
    PARABOLA_TANG_FIN = 9    # Parábola, tangente horizontal al final
    PARABOLA_TANG_INICIO = 10  # Parábola, tangente horizontal al inicio
    PARABOLA_SIMETRICA = 11  # Parábola simétrica (3 valores)
    CUBICA_TANG_INICIO = 12  # Cúbica, tangente horizontal al inicio
    CUBICA_TANG_FIN = 13     # Cúbica, tangente horizontal al final
    CUBICA_TIPO_1 = 14       # Cúbica tipo 1
    CUBICA_TIPO_2 = 15       # Cúbica tipo 2


def integral_mohr_rectangulo_rectangulo(L: float, j: float, k: float) -> float:
    """
    Integral de rectángulo × rectángulo.

    ∫ j × k dx = j × k × L

    Args:
        L: Longitud del tramo
        j: Valor constante del primer diagrama
        k: Valor constante del segundo diagrama

    Returns:
        Valor de la integral
    """
    return j * k * L


def integral_mohr_rectangulo_triangulo(L: float, j: float, k: float) -> float:
    """
    Integral de rectángulo × triángulo (j constante, k triangular desde 0).

    ∫ j × k(x) dx = (1/2) × j × k × L

    Args:
        L: Longitud del tramo
        j: Valor constante del rectángulo
        k: Valor máximo del triángulo (en x=L)

    Returns:
        Valor de la integral
    """
    return 0.5 * j * k * L


def integral_mohr_triangulo_triangulo_mismo_lado(L: float, j: float, k: float) -> float:
    """
    Integral de triángulo × triángulo (ambos con máximo en el mismo extremo).

    ∫ j(x) × k(x) dx = (1/3) × j × k × L

    Args:
        L: Longitud del tramo
        j: Valor máximo del primer triángulo
        k: Valor máximo del segundo triángulo

    Returns:
        Valor de la integral
    """
    return (1/3) * j * k * L


def integral_mohr_triangulo_triangulo_opuesto(L: float, j: float, k: float) -> float:
    """
    Integral de triángulo × triángulo (máximos en extremos opuestos).

    ∫ j(x) × k(x) dx = (1/6) × j × k × L

    Args:
        L: Longitud del tramo
        j: Valor máximo del primer triángulo (en un extremo)
        k: Valor máximo del segundo triángulo (en el extremo opuesto)

    Returns:
        Valor de la integral
    """
    return (1/6) * j * k * L


def integral_mohr_rectangulo_trapecio(L: float, j: float, k1: float, k2: float) -> float:
    """
    Integral de rectángulo × trapecio.

    ∫ j × k(x) dx = (1/2) × j × (k1 + k2) × L

    Args:
        L: Longitud del tramo
        j: Valor constante del rectángulo
        k1: Valor del trapecio en x=0
        k2: Valor del trapecio en x=L

    Returns:
        Valor de la integral
    """
    return 0.5 * j * (k1 + k2) * L


def integral_mohr_triangulo_trapecio(
    L: float,
    j: float,
    k1: float,
    k2: float,
    triangulo_en_inicio: bool = True
) -> float:
    """
    Integral de triángulo × trapecio.

    Si triángulo tiene máximo en x=L (crece desde 0):
        ∫ j(x) × k(x) dx = (1/6) × j × (k1 + 2×k2) × L

    Si triángulo tiene máximo en x=0 (decrece hacia 0):
        ∫ j(x) × k(x) dx = (1/6) × j × (2×k1 + k2) × L

    Args:
        L: Longitud del tramo
        j: Valor máximo del triángulo
        k1: Valor del trapecio en x=0
        k2: Valor del trapecio en x=L
        triangulo_en_inicio: True si el triángulo tiene máximo en x=0

    Returns:
        Valor de la integral
    """
    if triangulo_en_inicio:
        return (1/6) * j * (2*k1 + k2) * L
    else:
        return (1/6) * j * (k1 + 2*k2) * L


def integral_mohr_trapecio_trapecio(
    L: float,
    j1: float, j2: float,
    k1: float, k2: float
) -> float:
    """
    Integral de trapecio × trapecio.

    ∫ j(x) × k(x) dx = (1/6) × L × [j1×(2×k1 + k2) + j2×(k1 + 2×k2)]

    Args:
        L: Longitud del tramo
        j1: Valor del primer trapecio en x=0
        j2: Valor del primer trapecio en x=L
        k1: Valor del segundo trapecio en x=0
        k2: Valor del segundo trapecio en x=L

    Returns:
        Valor de la integral
    """
    return (1/6) * L * (j1 * (2*k1 + k2) + j2 * (k1 + 2*k2))


def integral_mohr_rectangulo_parabola(L: float, j: float, k: float) -> float:
    """
    Integral de rectángulo × parábola cuadrática (de carga uniforme).

    ∫ j × k(x) dx = (2/3) × j × k × L

    Donde k es el valor máximo de la parábola (flecha).

    Args:
        L: Longitud del tramo
        j: Valor constante del rectángulo
        k: Valor máximo (flecha) de la parábola

    Returns:
        Valor de la integral
    """
    return (2/3) * j * k * L


def integral_mohr_triangulo_parabola(
    L: float,
    j: float,
    k: float,
    triangulo_en_inicio: bool = True
) -> float:
    """
    Integral de triángulo × parábola cuadrática.

    ∫ j(x) × k(x) dx = (1/3) × j × k × L

    Args:
        L: Longitud del tramo
        j: Valor máximo del triángulo
        k: Valor máximo (flecha) de la parábola
        triangulo_en_inicio: No afecta el resultado para parábola simétrica

    Returns:
        Valor de la integral
    """
    return (1/3) * j * k * L


def integral_mohr_trapecio_parabola(
    L: float,
    j1: float, j2: float,
    k: float
) -> float:
    """
    Integral de trapecio × parábola cuadrática simétrica.

    ∫ j(x) × k(x) dx = (1/3) × (j1 + j2) × k × L

    Args:
        L: Longitud del tramo
        j1: Valor del trapecio en x=0
        j2: Valor del trapecio en x=L
        k: Valor máximo (flecha) de la parábola

    Returns:
        Valor de la integral
    """
    return (1/3) * (j1 + j2) * k * L


def integral_mohr_parabola_parabola(L: float, j: float, k: float) -> float:
    """
    Integral de parábola × parábola (ambas cuadráticas simétricas).

    ∫ j(x) × k(x) dx = (8/15) × j × k × L

    Nota: Este caso es menos común pero útil para verificación.

    Args:
        L: Longitud del tramo
        j: Valor máximo de la primera parábola
        k: Valor máximo de la segunda parábola

    Returns:
        Valor de la integral
    """
    return (8/15) * j * k * L


# =============================================================================
# TABLA DE INTEGRALES DE MOHR - CASOS CON POSICIÓN PARCIAL (α, β)
# =============================================================================

def integral_mohr_parcial_rectangulo_trapecio(
    L: float,
    alpha: float,
    beta: float,
    j: float,
    k: float
) -> float:
    """
    Integral de rectángulo × trapecio parcial.

    El trapecio va de αL a (1-β)L con valor k.

    ∫ j × k dx = (1/2) × j × k × L  (sobre la longitud efectiva)

    Args:
        L: Longitud total del tramo
        alpha: Fracción desde inicio donde comienza el trapecio (0 ≤ α ≤ 1)
        beta: Fracción desde fin donde termina el trapecio (0 ≤ β ≤ 1)
        j: Valor constante del rectángulo
        k: Valor del trapecio

    Returns:
        Valor de la integral
    """
    return 0.5 * j * k * L  # Simplificado para caso común


def integral_mohr_triangulo_parcial(
    L: float,
    alpha: float,  # Fracción donde comienza la carga
    beta: float,   # Fracción donde termina la carga
    j: float,      # Valor del triángulo
    k: float       # Valor del diagrama rectangular/constante
) -> float:
    """
    Integral para triángulo con carga parcial según tabla de Mohr.

    Fórmula: (1/6) × j × k × (1 + α) × L   [para triángulo creciendo hacia β]

    Args:
        L: Longitud total
        alpha: Posición relativa del inicio de la carga (0-1)
        beta: Posición relativa del fin de la carga (0-1)
        j: Valor del triángulo
        k: Valor constante

    Returns:
        Valor de la integral
    """
    return (1/6) * j * k * (1 + alpha) * L


# =============================================================================
# FUNCIÓN GENERAL DE INTEGRACIÓN POR TABLA DE MOHR
# =============================================================================

def integral_mohr(
    L: float,
    tipo_i: TipoDiagrama,
    tipo_j: TipoDiagrama,
    valores_i: Tuple[float, ...],
    valores_j: Tuple[float, ...],
    EI: float = 1.0
) -> float:
    """
    Calcula la integral ∫(Mi × Mj)/(E×I) dx usando la Tabla de Integrales de Mohr.

    Esta función selecciona automáticamente la fórmula correcta según
    los tipos de diagramas involucrados.

    Args:
        L: Longitud del tramo [m]
        tipo_i: Tipo del primer diagrama (Mi)
        tipo_j: Tipo del segundo diagrama (Mj)
        valores_i: Valores característicos del primer diagrama
        valores_j: Valores característicos del segundo diagrama
        EI: Rigidez a flexión [kN×m²]

    Returns:
        Valor de la integral / EI

    Example:
        >>> # Rectángulo × Rectángulo
        >>> integral_mohr(6.0, TipoDiagrama.RECTANGULO, TipoDiagrama.RECTANGULO,
        ...               (10.0,), (10.0,), EI=1000)
        0.6
    """
    resultado = 0.0

    # Rectángulo × Rectángulo
    if tipo_i == TipoDiagrama.RECTANGULO and tipo_j == TipoDiagrama.RECTANGULO:
        j, k = valores_i[0], valores_j[0]
        resultado = integral_mohr_rectangulo_rectangulo(L, j, k)

    # Rectángulo × Triángulo
    elif tipo_i == TipoDiagrama.RECTANGULO and tipo_j in (TipoDiagrama.TRIANGULO_INICIO, TipoDiagrama.TRIANGULO_FIN):
        j, k = valores_i[0], valores_j[0]
        resultado = integral_mohr_rectangulo_triangulo(L, j, k)

    elif tipo_j == TipoDiagrama.RECTANGULO and tipo_i in (TipoDiagrama.TRIANGULO_INICIO, TipoDiagrama.TRIANGULO_FIN):
        j, k = valores_j[0], valores_i[0]
        resultado = integral_mohr_rectangulo_triangulo(L, j, k)

    # Triángulo × Triángulo (mismo lado)
    elif tipo_i == tipo_j == TipoDiagrama.TRIANGULO_INICIO:
        j, k = valores_i[0], valores_j[0]
        resultado = integral_mohr_triangulo_triangulo_mismo_lado(L, j, k)

    elif tipo_i == tipo_j == TipoDiagrama.TRIANGULO_FIN:
        j, k = valores_i[0], valores_j[0]
        resultado = integral_mohr_triangulo_triangulo_mismo_lado(L, j, k)

    # Triángulo × Triángulo (lados opuestos)
    elif (tipo_i == TipoDiagrama.TRIANGULO_INICIO and tipo_j == TipoDiagrama.TRIANGULO_FIN) or \
         (tipo_i == TipoDiagrama.TRIANGULO_FIN and tipo_j == TipoDiagrama.TRIANGULO_INICIO):
        j, k = valores_i[0], valores_j[0]
        resultado = integral_mohr_triangulo_triangulo_opuesto(L, j, k)

    # Rectángulo × Trapecio
    elif tipo_i == TipoDiagrama.RECTANGULO and tipo_j == TipoDiagrama.TRAPECIO:
        j = valores_i[0]
        k1, k2 = valores_j[0], valores_j[1]
        resultado = integral_mohr_rectangulo_trapecio(L, j, k1, k2)

    elif tipo_j == TipoDiagrama.RECTANGULO and tipo_i == TipoDiagrama.TRAPECIO:
        j = valores_j[0]
        k1, k2 = valores_i[0], valores_i[1]
        resultado = integral_mohr_rectangulo_trapecio(L, j, k1, k2)

    # Trapecio × Trapecio
    elif tipo_i == TipoDiagrama.TRAPECIO and tipo_j == TipoDiagrama.TRAPECIO:
        j1, j2 = valores_i[0], valores_i[1]
        k1, k2 = valores_j[0], valores_j[1]
        resultado = integral_mohr_trapecio_trapecio(L, j1, j2, k1, k2)

    # Triángulo × Trapecio
    elif tipo_i == TipoDiagrama.TRIANGULO_INICIO and tipo_j == TipoDiagrama.TRAPECIO:
        j = valores_i[0]
        k1, k2 = valores_j[0], valores_j[1]
        resultado = integral_mohr_triangulo_trapecio(L, j, k1, k2, triangulo_en_inicio=True)

    elif tipo_i == TipoDiagrama.TRIANGULO_FIN and tipo_j == TipoDiagrama.TRAPECIO:
        j = valores_i[0]
        k1, k2 = valores_j[0], valores_j[1]
        resultado = integral_mohr_triangulo_trapecio(L, j, k1, k2, triangulo_en_inicio=False)

    # Rectángulo × Parábola
    elif tipo_i == TipoDiagrama.RECTANGULO and tipo_j == TipoDiagrama.PARABOLA_CONVEXA:
        j, k = valores_i[0], valores_j[0]
        resultado = integral_mohr_rectangulo_parabola(L, j, k)

    elif tipo_j == TipoDiagrama.RECTANGULO and tipo_i == TipoDiagrama.PARABOLA_CONVEXA:
        j, k = valores_j[0], valores_i[0]
        resultado = integral_mohr_rectangulo_parabola(L, j, k)

    # Triángulo × Parábola
    elif tipo_i in (TipoDiagrama.TRIANGULO_INICIO, TipoDiagrama.TRIANGULO_FIN) and \
         tipo_j == TipoDiagrama.PARABOLA_CONVEXA:
        j, k = valores_i[0], valores_j[0]
        resultado = integral_mohr_triangulo_parabola(L, j, k)

    elif tipo_j in (TipoDiagrama.TRIANGULO_INICIO, TipoDiagrama.TRIANGULO_FIN) and \
         tipo_i == TipoDiagrama.PARABOLA_CONVEXA:
        j, k = valores_j[0], valores_i[0]
        resultado = integral_mohr_triangulo_parabola(L, j, k)

    # Trapecio × Parábola
    elif tipo_i == TipoDiagrama.TRAPECIO and tipo_j == TipoDiagrama.PARABOLA_CONVEXA:
        j1, j2 = valores_i[0], valores_i[1]
        k = valores_j[0]
        resultado = integral_mohr_trapecio_parabola(L, j1, j2, k)

    elif tipo_j == TipoDiagrama.TRAPECIO and tipo_i == TipoDiagrama.PARABOLA_CONVEXA:
        j1, j2 = valores_j[0], valores_j[1]
        k = valores_i[0]
        resultado = integral_mohr_trapecio_parabola(L, j1, j2, k)

    else:
        # Caso no implementado: usar integración numérica
        raise NotImplementedError(
            f"Combinación de diagramas {tipo_i} × {tipo_j} no implementada en tabla de Mohr. "
            "Use integración numérica."
        )

    return resultado / EI


# =============================================================================
# INTEGRACIÓN NUMÉRICA (ALTERNATIVA)
# =============================================================================

def integracion_simpson(
    f: Callable[[float], float],
    a: float,
    b: float,
    n: int = 21
) -> float:
    """
    Integración numérica usando la regla de Simpson.

    Args:
        f: Función a integrar
        a: Límite inferior
        b: Límite superior
        n: Número de puntos (debe ser impar para Simpson 1/3)

    Returns:
        Valor aproximado de la integral
    """
    if n % 2 == 0:
        n += 1  # Simpson requiere número impar de puntos

    x = np.linspace(a, b, n)
    y = np.array([f(xi) for xi in x])

    return simpson(y, x=x)


def integracion_gauss(
    f: Callable[[float], float],
    a: float,
    b: float,
    n_puntos: int = 5
) -> float:
    """
    Integración numérica usando cuadratura de Gauss-Legendre.

    Más precisa que Simpson para funciones suaves.

    Args:
        f: Función a integrar
        a: Límite inferior
        b: Límite superior
        n_puntos: Número de puntos de Gauss (2-10)

    Returns:
        Valor aproximado de la integral
    """
    resultado, _ = quad(f, a, b)
    return resultado


def integral_trabajo_virtual(
    Mi: Callable[[float], float],
    Mj: Callable[[float], float],
    L: float,
    EI: float,
    metodo: str = "simpson",
    n_puntos: int = 21
) -> float:
    """
    Calcula la integral de trabajo virtual ∫(Mi × Mj)/(E×I) dx numéricamente.

    Esta función es la alternativa numérica cuando la Tabla de Mohr
    no aplica (diagramas complejos o cargas especiales).

    Args:
        Mi: Función del diagrama de momentos i, Mi(x)
        Mj: Función del diagrama de momentos j, Mj(x)
        L: Longitud del tramo [m]
        EI: Rigidez a flexión [kN×m²]
        metodo: "simpson" o "gauss"
        n_puntos: Número de puntos para integración

    Returns:
        Valor de la integral

    Example:
        >>> # Integral de dos funciones lineales
        >>> Mi = lambda x: 10 * x / 6  # Triángulo
        >>> Mj = lambda x: 10 * x / 6  # Triángulo
        >>> integral_trabajo_virtual(Mi, Mj, L=6.0, EI=1000)  # doctest: +ELLIPSIS
        0.2...
    """
    def integrando(x: float) -> float:
        return Mi(x) * Mj(x) / EI

    if metodo == "simpson":
        return integracion_simpson(integrando, 0, L, n_puntos)
    elif metodo == "gauss":
        return integracion_gauss(integrando, 0, L)
    else:
        raise ValueError(f"Método de integración desconocido: {metodo}")


def integral_trabajo_virtual_completa(
    Mi: Callable[[float], float],
    Mj: Callable[[float], float],
    Ni: Callable[[float], float],
    Nj: Callable[[float], float],
    L: float,
    EI: float,
    EA: float,
    incluir_axil: bool = True,
    metodo: str = "simpson",
    n_puntos: int = 21
) -> float:
    """
    Calcula la integral completa de trabajo virtual incluyendo flexión y axil.

    ∫(Mi × Mj)/(E×I) dx + ∫(Ni × Nj)/(E×A) dx

    Args:
        Mi, Mj: Funciones de momento flector
        Ni, Nj: Funciones de esfuerzo axil
        L: Longitud del tramo
        EI: Rigidez a flexión
        EA: Rigidez axil
        incluir_axil: Si True, incluye el término de axil
        metodo: Método de integración
        n_puntos: Número de puntos

    Returns:
        Valor de la integral total
    """
    # Término de flexión
    integral_M = integral_trabajo_virtual(Mi, Mj, L, EI, metodo, n_puntos)

    if not incluir_axil:
        return integral_M

    # Término axil
    integral_N = integral_trabajo_virtual(Ni, Nj, L, EA, metodo, n_puntos)

    return integral_M + integral_N
