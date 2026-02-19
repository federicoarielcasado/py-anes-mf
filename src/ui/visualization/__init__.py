"""
Módulo de visualización de resultados estructurales.

Proporciona funciones para:
- Diagramas de esfuerzos (N, V, M)
- Deformada exagerada
- Visualización de geometría y cargas
- Exportación a imágenes y PDF
"""

from .diagramas import (
    graficar_diagrama_momentos,
    graficar_diagrama_cortantes,
    graficar_diagrama_axiles,
    graficar_diagramas_combinados,
)

from .geometria import (
    graficar_estructura,
    graficar_estructura_con_cargas,
)

from .deformada import (
    graficar_deformada,
    graficar_comparacion_deformadas,
)

__all__ = [
    # Diagramas
    "graficar_diagrama_momentos",
    "graficar_diagrama_cortantes",
    "graficar_diagrama_axiles",
    "graficar_diagramas_combinados",
    # Geometría
    "graficar_estructura",
    "graficar_estructura_con_cargas",
    # Deformada
    "graficar_deformada",
    "graficar_comparacion_deformadas",
]
