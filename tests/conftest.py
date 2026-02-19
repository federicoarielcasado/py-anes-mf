"""
Configuración y fixtures de pytest para los tests del sistema.
"""

import sys
from pathlib import Path

import pytest

# Agregar el directorio src al path para importaciones
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.domain.entities.material import Material
from src.domain.entities.seccion import SeccionRectangular, SeccionPerfil
from src.domain.entities.nudo import Nudo
from src.domain.entities.barra import Barra
from src.domain.entities.vinculo import Empotramiento, ApoyoFijo, Rodillo
from src.domain.model.modelo_estructural import ModeloEstructural


# =============================================================================
# FIXTURES DE MATERIALES
# =============================================================================

@pytest.fixture
def acero_a36() -> Material:
    """Material de acero estructural A-36."""
    return Material(
        nombre="Acero A-36",
        E=200e6,  # 200 GPa en kN/m²
        alpha=1.2e-5,
        rho=7850,
        nu=0.3,
        fy=250e3,
    )


@pytest.fixture
def hormigon_h25() -> Material:
    """Material de hormigón H-25."""
    return Material(
        nombre="Hormigón H-25",
        E=23500e3,  # ~23.5 GPa
        alpha=1.0e-5,
        rho=2400,
        nu=0.2,
    )


# =============================================================================
# FIXTURES DE SECCIONES
# =============================================================================

@pytest.fixture
def seccion_rect_30x50() -> SeccionRectangular:
    """Sección rectangular 30x50 cm."""
    return SeccionRectangular(
        nombre="Rect 30x50",
        b=0.30,
        _h=0.50,
    )


@pytest.fixture
def seccion_ipe220() -> SeccionPerfil:
    """Perfil IPE 220."""
    return SeccionPerfil(
        nombre="IPE 220",
        _A=33.4e-4,  # m²
        _Iz=2772e-8,  # m⁴
        _h=0.220,  # m
    )


# =============================================================================
# FIXTURES DE NUDOS
# =============================================================================

@pytest.fixture
def nudo_origen() -> Nudo:
    """Nudo en el origen (0, 0)."""
    return Nudo(id=1, x=0.0, y=0.0, nombre="Origen")


@pytest.fixture
def nudo_6m() -> Nudo:
    """Nudo a 6 metros en X."""
    return Nudo(id=2, x=6.0, y=0.0, nombre="6m")


@pytest.fixture
def nudo_superior() -> Nudo:
    """Nudo superior a 3 metros de altura."""
    return Nudo(id=3, x=0.0, y=3.0, nombre="Superior")


# =============================================================================
# FIXTURES DE VÍNCULOS
# =============================================================================

@pytest.fixture
def empotramiento() -> Empotramiento:
    """Vínculo de empotramiento."""
    return Empotramiento()


@pytest.fixture
def apoyo_fijo() -> ApoyoFijo:
    """Vínculo de apoyo fijo (articulación)."""
    return ApoyoFijo()


@pytest.fixture
def rodillo_horizontal() -> Rodillo:
    """Vínculo de rodillo horizontal."""
    return Rodillo(direccion="Uy")


# =============================================================================
# FIXTURES DE BARRAS
# =============================================================================

@pytest.fixture
def barra_horizontal(nudo_origen, nudo_6m, acero_a36, seccion_ipe220) -> Barra:
    """Barra horizontal de 6 metros."""
    return Barra(
        id=1,
        nudo_i=nudo_origen,
        nudo_j=nudo_6m,
        material=acero_a36,
        seccion=seccion_ipe220,
        nombre="Viga",
    )


@pytest.fixture
def barra_vertical(nudo_origen, nudo_superior, acero_a36, seccion_ipe220) -> Barra:
    """Barra vertical de 3 metros."""
    return Barra(
        id=2,
        nudo_i=nudo_origen,
        nudo_j=nudo_superior,
        material=acero_a36,
        seccion=seccion_ipe220,
        nombre="Columna",
    )


# =============================================================================
# FIXTURES DE MODELOS COMPLETOS
# =============================================================================

@pytest.fixture
def modelo_vacio() -> ModeloEstructural:
    """Modelo estructural vacío."""
    return ModeloEstructural(nombre="Modelo vacío")


@pytest.fixture
def modelo_viga_biempotrada(acero_a36, seccion_ipe220) -> ModeloEstructural:
    """
    Modelo de viga biempotrada de 6 metros.

    Estructura clásica para validación:
    - Longitud: 6 m
    - Material: Acero A-36
    - Sección: IPE 220
    - Vínculos: Empotramiento en ambos extremos
    """
    modelo = ModeloEstructural(nombre="Viga biempotrada")

    # Crear nudos
    n1 = modelo.agregar_nudo(0.0, 0.0, "A")
    n2 = modelo.agregar_nudo(6.0, 0.0, "B")

    # Crear barra
    modelo.agregar_barra(n1, n2, acero_a36, seccion_ipe220, "Viga")

    # Aplicar empotramientos
    modelo.asignar_vinculo(n1.id, Empotramiento())
    modelo.asignar_vinculo(n2.id, Empotramiento())

    return modelo


@pytest.fixture
def modelo_viga_simplemente_apoyada(acero_a36, seccion_ipe220) -> ModeloEstructural:
    """
    Modelo de viga simplemente apoyada de 6 metros.

    - Longitud: 6 m
    - Vínculos: Apoyo fijo en A, Rodillo en B
    - Grado de hiperestaticidad: 0 (isostática)
    """
    modelo = ModeloEstructural(nombre="Viga simplemente apoyada")

    n1 = modelo.agregar_nudo(0.0, 0.0, "A")
    n2 = modelo.agregar_nudo(6.0, 0.0, "B")

    modelo.agregar_barra(n1, n2, acero_a36, seccion_ipe220, "Viga")

    modelo.asignar_vinculo(n1.id, ApoyoFijo())
    modelo.asignar_vinculo(n2.id, Rodillo(direccion="Uy"))

    return modelo


@pytest.fixture
def modelo_portico_simple(acero_a36, seccion_ipe220) -> ModeloEstructural:
    """
    Modelo de pórtico simple (2 columnas + 1 viga).

       C ━━━━━━━━━ D
       ┃           ┃
       ┃           ┃
       A           B

    - Altura columnas: 3 m
    - Luz viga: 6 m
    - Empotrado en bases
    """
    modelo = ModeloEstructural(nombre="Pórtico simple")

    # Nudos
    nA = modelo.agregar_nudo(0.0, 0.0, "A")
    nB = modelo.agregar_nudo(6.0, 0.0, "B")
    nC = modelo.agregar_nudo(0.0, 3.0, "C")
    nD = modelo.agregar_nudo(6.0, 3.0, "D")

    # Barras
    modelo.agregar_barra(nA, nC, acero_a36, seccion_ipe220, "Columna izq")
    modelo.agregar_barra(nB, nD, acero_a36, seccion_ipe220, "Columna der")
    modelo.agregar_barra(nC, nD, acero_a36, seccion_ipe220, "Viga")

    # Vínculos
    modelo.asignar_vinculo(nA.id, Empotramiento())
    modelo.asignar_vinculo(nB.id, Empotramiento())

    return modelo
