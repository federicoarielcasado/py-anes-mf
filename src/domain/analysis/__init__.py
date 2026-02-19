"""
Módulos de análisis estructural - Motor del Método de las Fuerzas.

Este paquete contiene la implementación del Método de las Fuerzas
(también conocido como Método de Flexibilidad) para el análisis
de estructuras hiperestáticas de pórticos planos 2D.

Flujo del análisis:
1. Calcular grado de hiperestaticidad (GH)
2. Seleccionar redundantes
3. Generar estructura fundamental y subestructuras Xi
4. Calcular esfuerzos en cada subestructura (isostática)
5. Calcular coeficientes de flexibilidad fij y términos e0i
6. Resolver SECE: [F]·{X} = -{e0}
7. Superponer resultados: Mh = M0 + Σ(Xi·Mi)
"""

from .redundantes import TipoRedundante, Redundante, SelectorRedundantes
from .motor_fuerzas import MotorMetodoFuerzas, ResultadoAnalisis

__all__ = [
    "TipoRedundante",
    "Redundante",
    "SelectorRedundantes",
    "MotorMetodoFuerzas",
    "ResultadoAnalisis",
]
