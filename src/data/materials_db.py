"""
Base de datos de materiales estructurales predefinidos.

Proporciona materiales comunes con sus propiedades mecánicas
según normas y valores típicos de la práctica ingenieril.

Unidades:
    E: kN/m² (kPa)
    fy: kN/m² (kPa)
    rho: kg/m³
    alpha: 1/°C
"""

from typing import Dict, List, Optional

from src.domain.entities.material import Material


# =============================================================================
# ACEROS ESTRUCTURALES
# =============================================================================

ACERO_A36 = Material(
    nombre="Acero A-36",
    E=200e6,           # 200 GPa
    alpha=1.2e-5,      # 12 × 10⁻⁶ /°C
    rho=7850,          # kg/m³
    nu=0.3,
    fy=250e3,          # 250 MPa
)

ACERO_A572_GR50 = Material(
    nombre="Acero A-572 Gr.50",
    E=200e6,
    alpha=1.2e-5,
    rho=7850,
    nu=0.3,
    fy=345e3,          # 345 MPa
)

ACERO_A992 = Material(
    nombre="Acero A-992",
    E=200e6,
    alpha=1.2e-5,
    rho=7850,
    nu=0.3,
    fy=345e3,
)

ACERO_S235 = Material(
    nombre="Acero S235 (EN)",
    E=210e6,           # 210 GPa según Eurocódigo
    alpha=1.2e-5,
    rho=7850,
    nu=0.3,
    fy=235e3,
)

ACERO_S275 = Material(
    nombre="Acero S275 (EN)",
    E=210e6,
    alpha=1.2e-5,
    rho=7850,
    nu=0.3,
    fy=275e3,
)

ACERO_S355 = Material(
    nombre="Acero S355 (EN)",
    E=210e6,
    alpha=1.2e-5,
    rho=7850,
    nu=0.3,
    fy=355e3,
)

# =============================================================================
# HORMIGONES
# =============================================================================

def _crear_hormigon(fc_mpa: float) -> Material:
    """
    Crea un material de hormigón basado en la resistencia f'c.

    El módulo de elasticidad se calcula según ACI 318:
    E = 4700 * sqrt(f'c) [MPa]

    Args:
        fc_mpa: Resistencia a compresión f'c en MPa

    Returns:
        Material configurado para hormigón
    """
    import math
    E_mpa = 4700 * math.sqrt(fc_mpa)
    E_kn_m2 = E_mpa * 1000  # Convertir a kN/m²

    return Material(
        nombre=f"Hormigón H-{int(fc_mpa)}",
        E=E_kn_m2,
        alpha=1.0e-5,      # 10 × 10⁻⁶ /°C
        rho=2400,
        nu=0.2,
        fy=fc_mpa * 1000,  # f'c en kN/m²
    )


HORMIGON_H20 = _crear_hormigon(20)
HORMIGON_H25 = _crear_hormigon(25)
HORMIGON_H30 = _crear_hormigon(30)
HORMIGON_H35 = _crear_hormigon(35)
HORMIGON_H40 = _crear_hormigon(40)

# =============================================================================
# MADERAS
# =============================================================================

MADERA_PINO = Material(
    nombre="Madera Pino (C24)",
    E=11e6,            # 11 GPa
    alpha=5e-6,        # 5 × 10⁻⁶ /°C (paralelo a fibra)
    rho=420,
    nu=0.3,
    fy=24e3,           # fm,k = 24 MPa
)

MADERA_ROBLE = Material(
    nombre="Madera Roble (D40)",
    E=13e6,            # 13 GPa
    alpha=5e-6,
    rho=700,
    nu=0.3,
    fy=40e3,
)

MADERA_LAMINADA = Material(
    nombre="Madera Laminada GL28h",
    E=12.6e6,          # 12.6 GPa
    alpha=5e-6,
    rho=410,
    nu=0.3,
    fy=28e3,
)

# =============================================================================
# ALUMINIO
# =============================================================================

ALUMINIO_6061_T6 = Material(
    nombre="Aluminio 6061-T6",
    E=69e6,            # 69 GPa
    alpha=2.4e-5,      # 24 × 10⁻⁶ /°C
    rho=2700,
    nu=0.33,
    fy=276e3,          # 276 MPa
)

ALUMINIO_6063_T5 = Material(
    nombre="Aluminio 6063-T5",
    E=69e6,
    alpha=2.4e-5,
    rho=2700,
    nu=0.33,
    fy=145e3,
)

# =============================================================================
# DICCIONARIO PRINCIPAL DE MATERIALES
# =============================================================================

MATERIALES: Dict[str, Material] = {
    # Aceros ASTM
    "Acero A-36": ACERO_A36,
    "Acero A-572 Gr.50": ACERO_A572_GR50,
    "Acero A-992": ACERO_A992,
    # Aceros EN
    "Acero S235": ACERO_S235,
    "Acero S275": ACERO_S275,
    "Acero S355": ACERO_S355,
    # Hormigones
    "Hormigón H-20": HORMIGON_H20,
    "Hormigón H-25": HORMIGON_H25,
    "Hormigón H-30": HORMIGON_H30,
    "Hormigón H-35": HORMIGON_H35,
    "Hormigón H-40": HORMIGON_H40,
    # Maderas
    "Madera Pino": MADERA_PINO,
    "Madera Roble": MADERA_ROBLE,
    "Madera Laminada": MADERA_LAMINADA,
    # Aluminio
    "Aluminio 6061-T6": ALUMINIO_6061_T6,
    "Aluminio 6063-T5": ALUMINIO_6063_T5,
}

# Alias comunes
MATERIALES["Acero"] = ACERO_A36
MATERIALES["Hormigón"] = HORMIGON_H25
MATERIALES["Madera"] = MADERA_PINO


# =============================================================================
# FUNCIONES DE ACCESO
# =============================================================================

def obtener_material(nombre: str) -> Optional[Material]:
    """
    Obtiene un material predefinido por nombre.

    Args:
        nombre: Nombre del material (case-sensitive)

    Returns:
        Material si existe, None en caso contrario
    """
    return MATERIALES.get(nombre)


def listar_materiales() -> List[str]:
    """
    Lista los nombres de todos los materiales disponibles.

    Returns:
        Lista de nombres de materiales
    """
    return list(MATERIALES.keys())


def crear_acero(fy_mpa: float, nombre: Optional[str] = None) -> Material:
    """
    Crea un acero personalizado con la tensión de fluencia especificada.

    Args:
        fy_mpa: Tensión de fluencia en MPa
        nombre: Nombre opcional (se genera automáticamente si no se proporciona)

    Returns:
        Material de acero configurado
    """
    if nombre is None:
        nombre = f"Acero fy={int(fy_mpa)}"

    return Material(
        nombre=nombre,
        E=200e6,
        alpha=1.2e-5,
        rho=7850,
        nu=0.3,
        fy=fy_mpa * 1000,
    )


def crear_hormigon(fc_mpa: float, nombre: Optional[str] = None) -> Material:
    """
    Crea un hormigón personalizado con la resistencia especificada.

    El módulo E se calcula según ACI 318: E = 4700 * sqrt(f'c)

    Args:
        fc_mpa: Resistencia a compresión f'c en MPa
        nombre: Nombre opcional

    Returns:
        Material de hormigón configurado
    """
    import math

    if nombre is None:
        nombre = f"Hormigón f'c={int(fc_mpa)}"

    E_mpa = 4700 * math.sqrt(fc_mpa)
    E_kn_m2 = E_mpa * 1000

    return Material(
        nombre=nombre,
        E=E_kn_m2,
        alpha=1.0e-5,
        rho=2400,
        nu=0.2,
        fy=fc_mpa * 1000,
    )
