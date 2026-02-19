"""
Datos predefinidos: materiales y secciones típicas.
"""

from .materials_db import MATERIALES, obtener_material, listar_materiales
from .sections_db import SECCIONES_IPE, SECCIONES_HEA, obtener_seccion_ipe, obtener_seccion_hea

__all__ = [
    "MATERIALES",
    "obtener_material",
    "listar_materiales",
    "SECCIONES_IPE",
    "SECCIONES_HEA",
    "obtener_seccion_ipe",
    "obtener_seccion_hea",
]
