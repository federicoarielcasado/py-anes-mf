"""
Entidades del modelo estructural.

Este módulo exporta las clases fundamentales para modelar
estructuras de pórticos planos 2D.
"""

from .material import Material
from .seccion import Seccion, SeccionRectangular, SeccionCircular, SeccionPerfil
from .nudo import Nudo
from .vinculo import (
    Vinculo,
    Empotramiento,
    ApoyoFijo,
    Rodillo,
    Guia,
    ResorteElastico,
)
from .barra import Barra
from .carga import (
    Carga,
    CargaPuntualNudo,
    CargaPuntualBarra,
    CargaDistribuida,
    CargaTermica,
    MovimientoImpuesto,
)

__all__ = [
    # Material y Sección
    "Material",
    "Seccion",
    "SeccionRectangular",
    "SeccionCircular",
    "SeccionPerfil",
    # Nudo
    "Nudo",
    # Vínculos
    "Vinculo",
    "Empotramiento",
    "ApoyoFijo",
    "Rodillo",
    "Guia",
    "ResorteElastico",
    # Barra
    "Barra",
    # Cargas
    "Carga",
    "CargaPuntualNudo",
    "CargaPuntualBarra",
    "CargaDistribuida",
    "CargaTermica",
    "MovimientoImpuesto",
]
