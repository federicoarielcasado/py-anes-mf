"""
Módulos de mecánica estructural.

Proporciona funciones para:
- Cálculo de esfuerzos internos (N, V, M) en estructuras isostáticas
- Ecuaciones de equilibrio
- Cálculo de deformaciones y desplazamientos
"""

from .esfuerzos import (
    calcular_esfuerzos_viga_isostatica,
    EsfuerzosTramo,
    DiagramaEsfuerzos,
)
from .equilibrio import (
    resolver_reacciones_isostatica,
    verificar_equilibrio_global,
)

__all__ = [
    "calcular_esfuerzos_viga_isostatica",
    "EsfuerzosTramo",
    "DiagramaEsfuerzos",
    "resolver_reacciones_isostatica",
    "verificar_equilibrio_global",
]
