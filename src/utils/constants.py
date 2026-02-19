"""
Constantes globales del sistema de análisis estructural.

Este módulo define tolerancias numéricas, constantes físicas y
parámetros de configuración usados en todo el sistema.
"""

from enum import Enum, auto
from typing import Final

# =============================================================================
# TOLERANCIAS NUMÉRICAS
# =============================================================================

# Tolerancia para comparación de números flotantes
TOLERANCE: Final[float] = 1e-10

# Tolerancia para verificación de equilibrio (fuerzas en kN)
EQUILIBRIUM_TOLERANCE: Final[float] = 1e-6

# Tolerancia para verificación de compatibilidad (desplazamientos)
COMPATIBILITY_TOLERANCE: Final[float] = 1e-8

# Tolerancia para detección de longitud cero
LENGTH_TOLERANCE: Final[float] = 1e-9

# Umbral de condicionamiento para advertencia de matriz mal condicionada
CONDITION_NUMBER_WARNING: Final[float] = 1e12

# =============================================================================
# PARÁMETROS DE INTEGRACIÓN NUMÉRICA
# =============================================================================

# Número de puntos por defecto para integración de Simpson
DEFAULT_INTEGRATION_POINTS: Final[int] = 21

# Subdivisiones mínimas para integración adaptativa
MIN_INTEGRATION_SUBDIVISIONS: Final[int] = 5

# Subdivisiones máximas para integración adaptativa
MAX_INTEGRATION_SUBDIVISIONS: Final[int] = 100

# =============================================================================
# UNIDADES (Sistema Internacional - kN, m, kNm)
# =============================================================================

class UnidadFuerza(Enum):
    """Unidades de fuerza soportadas."""
    KN = auto()   # Kilonewton (por defecto)
    N = auto()    # Newton
    KGF = auto()  # Kilogramo-fuerza
    TF = auto()   # Tonelada-fuerza


class UnidadLongitud(Enum):
    """Unidades de longitud soportadas."""
    M = auto()    # Metro (por defecto)
    CM = auto()   # Centímetro
    MM = auto()   # Milímetro


class UnidadMomento(Enum):
    """Unidades de momento soportadas."""
    KNM = auto()  # Kilonewton-metro (por defecto)
    NM = auto()   # Newton-metro
    KGF_M = auto() # Kilogramo-fuerza metro


# =============================================================================
# GRADOS DE LIBERTAD
# =============================================================================

class GDL(Enum):
    """Grados de libertad en análisis 2D de pórticos."""
    UX = "Ux"      # Desplazamiento horizontal
    UY = "Uy"      # Desplazamiento vertical
    THETA_Z = "θz"  # Rotación alrededor del eje Z (perpendicular al plano)


# Número de GDL por nudo en pórtico plano 2D
GDL_POR_NUDO: Final[int] = 3

# =============================================================================
# CONVENCIONES DE SIGNOS
# =============================================================================

class ConvencionSignos:
    """
    Convención de signos para esfuerzos internos.

    AXIL (N):
        Positivo = Tracción (alarga la barra)
        Negativo = Compresión (acorta la barra)

    CORTANTE (V):
        Positivo = Sentido horario en el elemento
        (siguiendo convención de viga: izquierda arriba, derecha abajo)

    MOMENTO (M):
        Positivo = Tracciona fibra inferior (curva hacia arriba, "sonrisa")
        Negativo = Tracciona fibra superior (curva hacia abajo, "ceño")

    REACCIONES:
        Positivas según ejes globales:
        - X: hacia la derecha
        - Y: hacia arriba
        - Mz: sentido antihorario
    """

    # Factores de signo (pueden modificarse para otras convenciones)
    AXIL_TRACCION_POSITIVO: Final[int] = 1
    CORTANTE_HORARIO_POSITIVO: Final[int] = 1
    MOMENTO_FIBRA_INFERIOR_POSITIVO: Final[int] = 1


# =============================================================================
# TIPOS DE VÍNCULO
# =============================================================================

class TipoVinculo(Enum):
    """Tipos de vínculos externos soportados."""
    EMPOTRAMIENTO = "empotramiento"      # 3 GDL restringidos
    APOYO_FIJO = "apoyo_fijo"            # 2 GDL restringidos (Ux, Uy)
    RODILLO_HORIZONTAL = "rodillo_h"      # 1 GDL (Uy)
    RODILLO_VERTICAL = "rodillo_v"        # 1 GDL (Ux)
    RODILLO_INCLINADO = "rodillo_inc"     # 1 GDL (dirección inclinada)
    GUIA_HORIZONTAL = "guia_h"            # 2 GDL (Uy, θz)
    GUIA_VERTICAL = "guia_v"              # 2 GDL (Ux, θz)
    RESORTE = "resorte"                   # Vínculo elástico


# =============================================================================
# TIPOS DE CARGA
# =============================================================================

class TipoCarga(Enum):
    """Tipos de cargas soportadas."""
    PUNTUAL_NUDO = "puntual_nudo"           # Carga en nudo
    PUNTUAL_BARRA = "puntual_barra"         # Carga sobre barra
    DISTRIBUIDA_UNIFORME = "dist_uniforme"   # q constante
    DISTRIBUIDA_TRIANGULAR = "dist_triang"   # q1=0 o q2=0
    DISTRIBUIDA_TRAPEZOIDAL = "dist_trapez"  # q1 ≠ q2
    TERMICA = "termica"                      # Carga térmica (uniforme o gradiente)
    MOVIMIENTO_IMPUESTO = "mov_impuesto"     # Hundimiento/rotación


# =============================================================================
# COLORES PARA VISUALIZACIÓN
# =============================================================================

class ColoresDiagramas:
    """Colores por defecto para diagramas de esfuerzos."""
    AXIL = "#2196F3"           # Azul
    CORTANTE = "#4CAF50"       # Verde
    MOMENTO = "#F44336"        # Rojo
    DEFORMADA = "#9C27B0"      # Púrpura
    ESTRUCTURA = "#424242"      # Gris oscuro
    NUDO = "#FF9800"           # Naranja
    VINCULO = "#795548"        # Marrón
    CARGA = "#E91E63"          # Rosa

    # Colores positivo/negativo
    POSITIVO = "#4CAF50"       # Verde
    NEGATIVO = "#F44336"       # Rojo


# =============================================================================
# PARÁMETROS DE VISUALIZACIÓN
# =============================================================================

# Factor de escala por defecto para diagramas
DEFAULT_DIAGRAM_SCALE: Final[float] = 1.0

# Factor de escala por defecto para deformada
DEFAULT_DEFORMED_SCALE: Final[float] = 100.0

# Tamaño de nudo en píxeles
NODE_SIZE: Final[int] = 8

# Grosor de línea de barra
MEMBER_LINE_WIDTH: Final[float] = 2.0

# Grosor de línea de diagrama
DIAGRAM_LINE_WIDTH: Final[float] = 1.5

# =============================================================================
# LÍMITES DEL SISTEMA
# =============================================================================

# Número máximo de barras recomendado (por rendimiento)
MAX_BARRAS_RECOMENDADO: Final[int] = 100

# Número máximo de redundantes recomendado
MAX_REDUNDANTES_RECOMENDADO: Final[int] = 30

# Tiempo máximo de resolución objetivo (segundos)
TIEMPO_RESOLUCION_OBJETIVO: Final[float] = 5.0
