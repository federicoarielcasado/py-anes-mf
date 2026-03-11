"""
Módulos de análisis estructural.

Contiene dos motores de análisis independientes y complementarios:

**Método de las Fuerzas (MF)**:
    Resuelve por compatibilidad de deformaciones. Requiere identificar
    redundantes y generar subestructuras isostáticas.
    Flujo: GH → Redundantes → Subestructuras → SECE → Superposición

**Método de las Deformaciones (MD)**:
    Resuelve por equilibrio en coordenadas nodales (Método de Rigidez).
    Más programable y sistemático; da desplazamientos directamente.
    Flujo: Numerar GDL → K global → F global → BCs → Solve → Esfuerzos

Ambos métodos producen el mismo ``ResultadoAnalisis`` y pueden compararse
usando ``comparar_resultados()`` para validación cruzada.
"""

from .redundantes import TipoRedundante, Redundante, SelectorRedundantes
from .motor_fuerzas import MotorMetodoFuerzas, ResultadoAnalisis
from .motor_deformaciones import (
    MotorMetodoDeformaciones,
    analizar_estructura_deformaciones,
    comparar_resultados,
)
from .numerador_gdl import NumeradorGDL
from .fuerzas_empotramiento import CalculadorFuerzasEmpotramiento
from .solver_adaptativo import ResultadoAdaptativo, resolver_con_fallback

__all__ = [
    # Método de las Fuerzas
    "TipoRedundante",
    "Redundante",
    "SelectorRedundantes",
    "MotorMetodoFuerzas",
    "ResultadoAnalisis",
    # Método de las Deformaciones
    "MotorMetodoDeformaciones",
    "analizar_estructura_deformaciones",
    "comparar_resultados",
    # Solver Adaptativo (MD + búsqueda iterativa MF)
    "ResultadoAdaptativo",
    "resolver_con_fallback",
    # Soporte MD
    "NumeradorGDL",
    "CalculadorFuerzasEmpotramiento",
]
