"""
Base de datos de secciones estructurales predefinidas.

Incluye perfiles laminados europeos (IPE, HEA, HEB) y
funciones para crear secciones rectangulares y circulares.

Unidades:
    Dimensiones: m
    Área: m²
    Momento de inercia: m⁴
"""

from typing import Dict, List, Optional

from src.domain.entities.seccion import (
    Seccion,
    SeccionPerfil,
    SeccionRectangular,
    SeccionCircular,
)


# =============================================================================
# PERFILES IPE (EUROPEAN I-PROFILES)
# Datos según EN 10365
# =============================================================================

# Formato: (A [cm²], Iz [cm⁴], h [mm], Iy [cm⁴], b [mm], tf [mm], tw [mm])
_IPE_DATA = {
    "IPE 80":   (7.64,    80.1,    80,   8.49,   46,  5.2, 3.8),
    "IPE 100":  (10.3,    171,    100,   15.9,   55,  5.7, 4.1),
    "IPE 120":  (13.2,    318,    120,   27.7,   64,  6.3, 4.4),
    "IPE 140":  (16.4,    541,    140,   44.9,   73,  6.9, 4.7),
    "IPE 160":  (20.1,    869,    160,   68.3,   82,  7.4, 5.0),
    "IPE 180":  (23.9,   1317,    180,  100.9,   91,  8.0, 5.3),
    "IPE 200":  (28.5,   1943,    200,  142.4,  100,  8.5, 5.6),
    "IPE 220":  (33.4,   2772,    220,  204.9,  110,  9.2, 5.9),
    "IPE 240":  (39.1,   3892,    240,  283.6,  120,  9.8, 6.2),
    "IPE 270":  (45.9,   5790,    270,  419.9,  135, 10.2, 6.6),
    "IPE 300":  (53.8,   8356,    300,  603.8,  150, 10.7, 7.1),
    "IPE 330":  (62.6,  11770,    330,  788.1,  160, 11.5, 7.5),
    "IPE 360":  (72.7,  16270,    360, 1043.0,  170, 12.7, 8.0),
    "IPE 400":  (84.5,  23130,    400, 1318.0,  180, 13.5, 8.6),
    "IPE 450":  (98.8,  33740,    450, 1676.0,  190, 14.6, 9.4),
    "IPE 500": (116.0,  48200,    500, 2142.0,  200, 16.0, 10.2),
    "IPE 550": (134.0,  67120,    550, 2668.0,  210, 17.2, 11.1),
    "IPE 600": (156.0,  92080,    600, 3387.0,  220, 19.0, 12.0),
}


def _crear_seccion_ipe(nombre: str, datos: tuple) -> SeccionPerfil:
    """Crea un perfil IPE a partir de los datos tabulados."""
    A_cm2, Iz_cm4, h_mm, Iy_cm4, b_mm, tf_mm, tw_mm = datos
    return SeccionPerfil(
        nombre=nombre,
        _A=A_cm2 * 1e-4,      # cm² → m²
        _Iz=Iz_cm4 * 1e-8,    # cm⁴ → m⁴
        _h=h_mm * 1e-3,       # mm → m
        _Iy=Iy_cm4 * 1e-8,
        _b=b_mm * 1e-3,
        _tf=tf_mm * 1e-3,
        _tw=tw_mm * 1e-3,
    )


SECCIONES_IPE: Dict[str, SeccionPerfil] = {
    nombre: _crear_seccion_ipe(nombre, datos)
    for nombre, datos in _IPE_DATA.items()
}


# =============================================================================
# PERFILES HEA (EUROPEAN WIDE FLANGE - LIGHT SERIES)
# Datos según EN 10365
# =============================================================================

_HEA_DATA = {
    "HEA 100":  (21.2,    349,    96,  134,  100,  8.0, 5.0),
    "HEA 120":  (25.3,    606,   114,  231,  120,  8.0, 5.0),
    "HEA 140":  (31.4,   1033,   133,  389,  140,  8.5, 5.5),
    "HEA 160":  (38.8,   1673,   152,  616,  160,  9.0, 6.0),
    "HEA 180":  (45.3,   2510,   171,  925,  180,  9.5, 6.0),
    "HEA 200":  (53.8,   3692,   190, 1336,  200, 10.0, 6.5),
    "HEA 220":  (64.3,   5410,   210, 1955,  220, 11.0, 7.0),
    "HEA 240":  (76.8,   7763,   230, 2769,  240, 12.0, 7.5),
    "HEA 260":  (86.8,  10450,   250, 3668,  260, 12.5, 7.5),
    "HEA 280":  (97.3,  13670,   270, 4763,  280, 13.0, 8.0),
    "HEA 300": (112.5,  18260,   290, 6310,  300, 14.0, 8.5),
    "HEA 320": (124.4,  22930,   310, 6985,  300, 15.5, 9.0),
    "HEA 340": (133.5,  27690,   330, 7436,  300, 16.5, 9.5),
    "HEA 360": (142.8,  33090,   350, 7887,  300, 17.5, 10.0),
    "HEA 400": (159.0,  45070,   390, 8564,  300, 19.0, 11.0),
    "HEA 450": (178.0,  63720,   440, 9465,  300, 21.0, 11.5),
    "HEA 500": (197.5,  86970,   490, 10370, 300, 23.0, 12.0),
}


def _crear_seccion_hea(nombre: str, datos: tuple) -> SeccionPerfil:
    """Crea un perfil HEA a partir de los datos tabulados."""
    A_cm2, Iz_cm4, h_mm, Iy_cm4, b_mm, tf_mm, tw_mm = datos
    return SeccionPerfil(
        nombre=nombre,
        _A=A_cm2 * 1e-4,
        _Iz=Iz_cm4 * 1e-8,
        _h=h_mm * 1e-3,
        _Iy=Iy_cm4 * 1e-8,
        _b=b_mm * 1e-3,
        _tf=tf_mm * 1e-3,
        _tw=tw_mm * 1e-3,
    )


SECCIONES_HEA: Dict[str, SeccionPerfil] = {
    nombre: _crear_seccion_hea(nombre, datos)
    for nombre, datos in _HEA_DATA.items()
}


# =============================================================================
# PERFILES HEB (EUROPEAN WIDE FLANGE - STANDARD SERIES)
# =============================================================================

_HEB_DATA = {
    "HEB 100":  (26.0,    450,   100,  167,  100, 10.0, 6.0),
    "HEB 120":  (34.0,    864,   120,  318,  120, 11.0, 6.5),
    "HEB 140":  (43.0,   1509,   140,  550,  140, 12.0, 7.0),
    "HEB 160":  (54.3,   2492,   160,  889,  160, 13.0, 8.0),
    "HEB 180":  (65.3,   3831,   180, 1363,  180, 14.0, 8.5),
    "HEB 200":  (78.1,   5696,   200, 2003,  200, 15.0, 9.0),
    "HEB 220":  (91.0,   8091,   220, 2843,  220, 16.0, 9.5),
    "HEB 240": (106.0,  11260,   240, 3923,  240, 17.0, 10.0),
    "HEB 260": (118.4,  14920,   260, 5135,  260, 17.5, 10.0),
    "HEB 280": (131.4,  19270,   280, 6595,  280, 18.0, 10.5),
    "HEB 300": (149.1,  25170,   300, 8563,  300, 19.0, 11.0),
    "HEB 320": (161.3,  30820,   320, 9239,  300, 20.5, 11.5),
    "HEB 340": (170.9,  36660,   340, 9690,  300, 21.5, 12.0),
    "HEB 360": (180.6,  43190,   360, 10140, 300, 22.5, 12.5),
    "HEB 400": (197.8,  57680,   400, 10820, 300, 24.0, 13.5),
    "HEB 450": (218.0,  79890,   450, 11720, 300, 26.0, 14.0),
    "HEB 500": (238.6, 107200,   500, 12620, 300, 28.0, 14.5),
}

SECCIONES_HEB: Dict[str, SeccionPerfil] = {
    nombre: _crear_seccion_hea(nombre, datos)  # Mismo formato que HEA
    for nombre, datos in _HEB_DATA.items()
}


# =============================================================================
# FUNCIONES DE ACCESO
# =============================================================================

def obtener_seccion_ipe(nombre: str) -> Optional[SeccionPerfil]:
    """
    Obtiene un perfil IPE por nombre.

    Args:
        nombre: Nombre del perfil (ej: "IPE 220")

    Returns:
        SeccionPerfil si existe, None en caso contrario
    """
    return SECCIONES_IPE.get(nombre)


def obtener_seccion_hea(nombre: str) -> Optional[SeccionPerfil]:
    """
    Obtiene un perfil HEA por nombre.

    Args:
        nombre: Nombre del perfil (ej: "HEA 200")

    Returns:
        SeccionPerfil si existe, None en caso contrario
    """
    return SECCIONES_HEA.get(nombre)


def obtener_seccion_heb(nombre: str) -> Optional[SeccionPerfil]:
    """
    Obtiene un perfil HEB por nombre.

    Args:
        nombre: Nombre del perfil (ej: "HEB 200")

    Returns:
        SeccionPerfil si existe, None en caso contrario
    """
    return SECCIONES_HEB.get(nombre)


def listar_perfiles_ipe() -> List[str]:
    """Lista los nombres de todos los perfiles IPE disponibles."""
    return sorted(SECCIONES_IPE.keys(), key=lambda x: int(x.split()[1]))


def listar_perfiles_hea() -> List[str]:
    """Lista los nombres de todos los perfiles HEA disponibles."""
    return sorted(SECCIONES_HEA.keys(), key=lambda x: int(x.split()[1]))


def listar_perfiles_heb() -> List[str]:
    """Lista los nombres de todos los perfiles HEB disponibles."""
    return sorted(SECCIONES_HEB.keys(), key=lambda x: int(x.split()[1]))


# =============================================================================
# FUNCIONES PARA CREAR SECCIONES PERSONALIZADAS
# =============================================================================

def crear_seccion_rectangular_cm(
    ancho_cm: float,
    altura_cm: float,
    nombre: Optional[str] = None
) -> SeccionRectangular:
    """
    Crea una sección rectangular a partir de dimensiones en centímetros.

    Args:
        ancho_cm: Ancho en cm
        altura_cm: Altura en cm
        nombre: Nombre opcional

    Returns:
        SeccionRectangular configurada
    """
    if nombre is None:
        nombre = f"Rect {ancho_cm:.0f}x{altura_cm:.0f}"

    return SeccionRectangular(
        nombre=nombre,
        b=ancho_cm / 100,
        _h=altura_cm / 100,
    )


def crear_seccion_circular_cm(
    diametro_cm: float,
    nombre: Optional[str] = None
) -> SeccionCircular:
    """
    Crea una sección circular a partir del diámetro en centímetros.

    Args:
        diametro_cm: Diámetro en cm
        nombre: Nombre opcional

    Returns:
        SeccionCircular configurada
    """
    if nombre is None:
        nombre = f"Circ D{diametro_cm:.0f}"

    return SeccionCircular(
        nombre=nombre,
        diametro=diametro_cm / 100,
    )


def crear_seccion_personalizada(
    nombre: str,
    A_cm2: float,
    Iz_cm4: float,
    h_cm: float,
    Iy_cm4: Optional[float] = None,
    b_cm: Optional[float] = None
) -> SeccionPerfil:
    """
    Crea una sección con propiedades personalizadas.

    Útil para secciones compuestas o especiales que no están
    en los catálogos predefinidos.

    Args:
        nombre: Nombre de la sección
        A_cm2: Área en cm²
        Iz_cm4: Momento de inercia eje fuerte en cm⁴
        h_cm: Altura en cm
        Iy_cm4: Momento de inercia eje débil en cm⁴ (opcional)
        b_cm: Ancho en cm (opcional)

    Returns:
        SeccionPerfil configurada
    """
    return SeccionPerfil(
        nombre=nombre,
        _A=A_cm2 * 1e-4,
        _Iz=Iz_cm4 * 1e-8,
        _h=h_cm / 100,
        _Iy=Iy_cm4 * 1e-8 if Iy_cm4 else None,
        _b=b_cm / 100 if b_cm else None,
    )


# =============================================================================
# SECCIONES TÍPICAS DE HORMIGÓN
# =============================================================================

def seccion_viga_ha(ancho_cm: float, altura_cm: float) -> SeccionRectangular:
    """
    Crea una sección de viga de hormigón armado.

    Args:
        ancho_cm: Ancho en cm
        altura_cm: Altura en cm

    Returns:
        SeccionRectangular con nombre descriptivo
    """
    return crear_seccion_rectangular_cm(
        ancho_cm=ancho_cm,
        altura_cm=altura_cm,
        nombre=f"Viga HA {ancho_cm:.0f}x{altura_cm:.0f}",
    )


def seccion_columna_ha(lado_cm: float) -> SeccionRectangular:
    """
    Crea una sección de columna cuadrada de hormigón armado.

    Args:
        lado_cm: Lado de la sección en cm

    Returns:
        SeccionRectangular cuadrada
    """
    return crear_seccion_rectangular_cm(
        ancho_cm=lado_cm,
        altura_cm=lado_cm,
        nombre=f"Columna HA {lado_cm:.0f}x{lado_cm:.0f}",
    )
