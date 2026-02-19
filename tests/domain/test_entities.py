"""
Tests unitarios para las entidades del dominio.

Verifica el comportamiento correcto de:
- Material
- Seccion (Rectangular, Circular, Perfil)
- Nudo
- Vinculo (Empotramiento, ApoyoFijo, Rodillo, etc.)
- Barra
- Carga (Puntual, Distribuida, Térmica, etc.)
"""

import math

import pytest

from src.domain.entities.material import Material, acero_estructural, hormigon
from src.domain.entities.seccion import (
    SeccionRectangular,
    SeccionCircular,
    SeccionPerfil,
    crear_seccion_rectangular,
)
from src.domain.entities.nudo import Nudo
from src.domain.entities.vinculo import (
    Empotramiento,
    ApoyoFijo,
    Rodillo,
    Guia,
    ResorteElastico,
)
from src.domain.entities.barra import Barra
from src.domain.entities.carga import (
    CargaPuntualNudo,
    CargaPuntualBarra,
    CargaDistribuida,
    CargaTermica,
    MovimientoImpuesto,
)


# =============================================================================
# TESTS DE MATERIAL
# =============================================================================

class TestMaterial:
    """Tests para la clase Material."""

    def test_crear_material_basico(self):
        """Debe crear un material con propiedades básicas."""
        mat = Material(nombre="Acero", E=200e6)
        assert mat.nombre == "Acero"
        assert mat.E == 200e6
        assert mat.nu == 0.3  # Valor por defecto

    def test_crear_material_completo(self):
        """Debe crear un material con todas las propiedades."""
        mat = Material(
            nombre="Acero A-36",
            E=200e6,
            alpha=1.2e-5,
            rho=7850,
            nu=0.3,
            fy=250e3,
        )
        assert mat.E == 200e6
        assert mat.alpha == 1.2e-5
        assert mat.rho == 7850
        assert mat.fy == 250e3

    def test_modulo_corte(self):
        """El módulo de corte debe calcularse correctamente."""
        mat = Material(nombre="Test", E=200e6, nu=0.3)
        G_esperado = 200e6 / (2 * (1 + 0.3))
        assert abs(mat.G - G_esperado) < 1e-6

    def test_material_E_invalido(self):
        """Debe rechazar E <= 0."""
        with pytest.raises(ValueError, match="módulo de elasticidad"):
            Material(nombre="Invalid", E=-100)

    def test_material_nombre_vacio(self):
        """Debe rechazar nombre vacío."""
        with pytest.raises(ValueError, match="nombre"):
            Material(nombre="", E=200e6)

    def test_crear_acero_estructural(self):
        """La función helper debe crear acero válido."""
        acero = acero_estructural("A-36")
        assert acero.E == 200e6
        assert acero.fy == 250e3

    def test_crear_hormigon(self):
        """La función helper debe crear hormigón con E calculado."""
        h25 = hormigon(25)
        E_esperado = 4700 * math.sqrt(25) * 1000  # kN/m²
        assert abs(h25.E - E_esperado) < 1


# =============================================================================
# TESTS DE SECCION
# =============================================================================

class TestSeccionRectangular:
    """Tests para SeccionRectangular."""

    def test_crear_seccion_rectangular(self):
        """Debe crear sección con dimensiones correctas."""
        sec = SeccionRectangular(nombre="30x50", b=0.30, _h=0.50)
        assert sec.b == 0.30
        assert sec.h == 0.50

    def test_area_rectangular(self):
        """El área debe ser b × h."""
        sec = SeccionRectangular(nombre="30x50", b=0.30, _h=0.50)
        assert abs(sec.A - 0.15) < 1e-10

    def test_inercia_rectangular(self):
        """El momento de inercia debe ser b×h³/12."""
        sec = SeccionRectangular(nombre="30x50", b=0.30, _h=0.50)
        Iz_esperado = 0.30 * 0.50**3 / 12
        assert abs(sec.Iz - Iz_esperado) < 1e-10

    def test_seccion_dimensiones_invalidas(self):
        """Debe rechazar dimensiones no positivas."""
        with pytest.raises(ValueError):
            SeccionRectangular(nombre="Invalid", b=0, _h=0.50)

    def test_crear_seccion_desde_cm(self):
        """La función helper debe convertir cm a m."""
        sec = crear_seccion_rectangular(30, 50)
        assert abs(sec.b - 0.30) < 1e-10
        assert abs(sec.h - 0.50) < 1e-10


class TestSeccionCircular:
    """Tests para SeccionCircular."""

    def test_crear_seccion_circular(self):
        """Debe crear sección con diámetro correcto."""
        sec = SeccionCircular(nombre="D30", diametro=0.30)
        assert sec.diametro == 0.30
        assert sec.h == 0.30

    def test_area_circular(self):
        """El área debe ser π×d²/4."""
        sec = SeccionCircular(nombre="D30", diametro=0.30)
        A_esperado = math.pi * 0.30**2 / 4
        assert abs(sec.A - A_esperado) < 1e-10

    def test_inercia_circular(self):
        """El momento de inercia debe ser π×d⁴/64."""
        sec = SeccionCircular(nombre="D30", diametro=0.30)
        Iz_esperado = math.pi * 0.30**4 / 64
        assert abs(sec.Iz - Iz_esperado) < 1e-12


class TestSeccionPerfil:
    """Tests para SeccionPerfil."""

    def test_crear_perfil(self):
        """Debe crear perfil con propiedades dadas."""
        sec = SeccionPerfil(
            nombre="IPE 220",
            _A=33.4e-4,
            _Iz=2772e-8,
            _h=0.220,
        )
        assert sec.nombre == "IPE 220"
        assert abs(sec.A - 33.4e-4) < 1e-10
        assert abs(sec.Iz - 2772e-8) < 1e-12


# =============================================================================
# TESTS DE NUDO
# =============================================================================

class TestNudo:
    """Tests para la clase Nudo."""

    def test_crear_nudo(self):
        """Debe crear nudo con coordenadas correctas."""
        n = Nudo(id=1, x=3.0, y=4.0, nombre="A")
        assert n.id == 1
        assert n.x == 3.0
        assert n.y == 4.0
        assert n.nombre == "A"

    def test_nudo_sin_vinculo(self):
        """Un nudo nuevo no debe tener vínculo."""
        n = Nudo(id=1, x=0, y=0)
        assert n.vinculo is None
        assert n.es_libre
        assert not n.tiene_vinculo

    def test_distancia_entre_nudos(self):
        """La distancia debe calcularse correctamente."""
        n1 = Nudo(id=1, x=0, y=0)
        n2 = Nudo(id=2, x=3, y=4)
        assert abs(n1.distancia_a(n2) - 5.0) < 1e-10

    def test_coordenadas_tupla(self):
        """Las coordenadas deben retornarse como tupla."""
        n = Nudo(id=1, x=3.0, y=4.0)
        assert n.coordenadas == (3.0, 4.0)

    def test_nudo_id_invalido(self):
        """Debe rechazar ID <= 0."""
        with pytest.raises(ValueError):
            Nudo(id=0, x=0, y=0)

    def test_mover_nudo(self):
        """Debe permitir mover el nudo."""
        n = Nudo(id=1, x=0, y=0)
        n.mover_a(5.0, 10.0)
        assert n.x == 5.0
        assert n.y == 10.0

    def test_desplazar_nudo(self):
        """Debe permitir desplazar relativamente."""
        n = Nudo(id=1, x=1.0, y=2.0)
        n.desplazar(3.0, 4.0)
        assert n.x == 4.0
        assert n.y == 6.0


# =============================================================================
# TESTS DE VINCULOS
# =============================================================================

class TestVinculos:
    """Tests para las clases de vínculos."""

    def test_empotramiento_gdl(self):
        """Empotramiento debe restringir 3 GDL."""
        emp = Empotramiento()
        gdl = emp.gdl_restringidos()
        assert len(gdl) == 3
        assert "Ux" in gdl
        assert "Uy" in gdl
        assert "θz" in gdl

    def test_apoyo_fijo_gdl(self):
        """Apoyo fijo debe restringir 2 GDL."""
        af = ApoyoFijo()
        gdl = af.gdl_restringidos()
        assert len(gdl) == 2
        assert "Ux" in gdl
        assert "Uy" in gdl
        assert "θz" not in gdl

    def test_rodillo_horizontal(self):
        """Rodillo horizontal debe restringir solo Uy."""
        rod = Rodillo(direccion="Uy")
        gdl = rod.gdl_restringidos()
        assert len(gdl) == 1
        assert "Uy" in gdl

    def test_rodillo_vertical(self):
        """Rodillo vertical debe restringir solo Ux."""
        rod = Rodillo(direccion="Ux")
        gdl = rod.gdl_restringidos()
        assert len(gdl) == 1
        assert "Ux" in gdl

    def test_guia_horizontal(self):
        """Guía horizontal permite Ux, restringe Uy y θz."""
        guia = Guia(direccion_libre="Ux")
        gdl = guia.gdl_restringidos()
        assert len(gdl) == 2
        assert "Ux" not in gdl
        assert "Uy" in gdl
        assert "θz" in gdl

    def test_resorte_elastico(self):
        """Resorte debe aceptar rigideces positivas."""
        resorte = ResorteElastico(kx=0, ky=1000, ktheta=0)
        assert resorte.ky == 1000
        assert resorte.es_resorte_traslacional

    def test_resorte_sin_rigidez(self):
        """Resorte sin rigidez debe fallar."""
        with pytest.raises(ValueError):
            ResorteElastico(kx=0, ky=0, ktheta=0)

    def test_asignar_vinculo_a_nudo(self, nudo_origen, empotramiento):
        """Debe poder asignar vínculo a nudo."""
        nudo_origen.asignar_vinculo(empotramiento)
        assert nudo_origen.tiene_vinculo
        assert nudo_origen.num_gdl_restringidos == 3


# =============================================================================
# TESTS DE BARRA
# =============================================================================

class TestBarra:
    """Tests para la clase Barra."""

    def test_crear_barra(self, barra_horizontal):
        """Debe crear barra con propiedades correctas."""
        assert barra_horizontal.id == 1
        assert barra_horizontal.nombre == "Viga"

    def test_longitud_barra(self, barra_horizontal):
        """La longitud debe calcularse correctamente."""
        assert abs(barra_horizontal.L - 6.0) < 1e-10

    def test_angulo_barra_horizontal(self, barra_horizontal):
        """Barra horizontal debe tener ángulo 0."""
        assert abs(barra_horizontal.angulo) < 1e-10
        assert barra_horizontal.es_horizontal

    def test_angulo_barra_vertical(self, barra_vertical):
        """Barra vertical debe tener ángulo π/2."""
        assert abs(barra_vertical.angulo - math.pi/2) < 1e-10
        assert barra_vertical.es_vertical

    def test_rigidez_flexion(self, barra_horizontal):
        """La rigidez EI debe calcularse correctamente."""
        E = barra_horizontal.material.E
        I = barra_horizontal.seccion.Iz
        assert abs(barra_horizontal.EI - E * I) < 1e-6

    def test_punto_medio(self, barra_horizontal):
        """El punto medio debe estar a L/2."""
        pm = barra_horizontal.punto_medio
        assert abs(pm[0] - 3.0) < 1e-10
        assert abs(pm[1] - 0.0) < 1e-10

    def test_barra_longitud_cero(self, nudo_origen, acero_a36, seccion_ipe220):
        """Barra de longitud cero debe fallar."""
        n2 = Nudo(id=2, x=0, y=0)  # Mismo punto que origen
        with pytest.raises(ValueError, match="longitud"):
            Barra(1, nudo_origen, n2, acero_a36, seccion_ipe220)

    def test_barra_mismo_nudo(self, nudo_origen, acero_a36, seccion_ipe220):
        """Barra con mismo nudo en ambos extremos debe fallar."""
        with pytest.raises(ValueError, match="mismo nudo"):
            Barra(1, nudo_origen, nudo_origen, acero_a36, seccion_ipe220)


# =============================================================================
# TESTS DE CARGAS
# =============================================================================

class TestCargas:
    """Tests para las clases de cargas."""

    def test_carga_puntual_nudo(self, nudo_origen):
        """Debe crear carga puntual en nudo."""
        carga = CargaPuntualNudo(nudo=nudo_origen, Fx=10, Fy=-20, Mz=5)
        assert carga.Fx == 10
        assert carga.Fy == -20
        assert carga.Mz == 5

    def test_carga_puntual_magnitud(self, nudo_origen):
        """La magnitud debe ser la hipotenusa."""
        carga = CargaPuntualNudo(nudo=nudo_origen, Fx=3, Fy=4, Mz=0)
        assert abs(carga.magnitud - 5.0) < 1e-10

    def test_carga_puntual_barra(self, barra_horizontal):
        """Debe crear carga puntual sobre barra."""
        carga = CargaPuntualBarra(barra=barra_horizontal, P=10, a=3.0, angulo=-90)
        assert carga.P == 10
        assert carga.a == 3.0
        assert abs(carga.b - 3.0) < 1e-10  # L - a

    def test_carga_puntual_barra_componentes(self):
        """Las componentes locales deben calcularse."""
        carga = CargaPuntualBarra(P=10, a=3.0, angulo=-90)
        Px, Py = carga.componentes_locales
        assert abs(Px - 0.0) < 1e-10
        assert abs(Py - (-10.0)) < 1e-10

    def test_carga_distribuida_uniforme(self, barra_horizontal):
        """Carga uniforme debe tener q1 == q2."""
        carga = CargaDistribuida(barra=barra_horizontal, q1=10, q2=10, x1=0, x2=6)
        assert carga.es_uniforme
        assert abs(carga.resultante - 60) < 1e-10  # q × L
        assert abs(carga.posicion_resultante - 3.0) < 1e-10  # L/2

    def test_carga_distribuida_triangular(self, barra_horizontal):
        """Carga triangular debe tener q1=0 o q2=0."""
        carga = CargaDistribuida(barra=barra_horizontal, q1=0, q2=10, x1=0, x2=6)
        assert carga.es_triangular
        assert abs(carga.resultante - 30) < 1e-10  # q × L / 2

    def test_carga_termica(self, barra_horizontal):
        """Debe crear carga térmica con componentes."""
        carga = CargaTermica(
            barra=barra_horizontal,
            delta_T_uniforme=20,
            delta_T_gradiente=10
        )
        assert carga.tiene_componente_uniforme
        assert carga.tiene_componente_gradiente

    def test_movimiento_impuesto(self, nudo_origen):
        """Debe crear hundimiento de apoyo."""
        mov = MovimientoImpuesto(
            nudo=nudo_origen,
            delta_x=0,
            delta_y=-0.010,  # 10 mm hundimiento
            delta_theta=0
        )
        assert mov.es_hundimiento
        assert abs(mov.delta_y - (-0.010)) < 1e-10
