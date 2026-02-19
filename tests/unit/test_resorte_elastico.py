"""
Tests unitarios para la clase ResorteElastico (vínculos elásticos).
"""

import pytest
from src.domain.entities.vinculo import ResorteElastico
from src.domain.entities.nudo import Nudo
from src.utils.constants import GDL, TipoVinculo


class TestCreacionResorte:
    """Tests de creación de resortes elásticos."""

    def test_crear_resorte_vertical(self):
        """Test crear resorte vertical simple."""
        resorte = ResorteElastico(kx=0, ky=1000, ktheta=0)

        assert resorte.kx == 0
        assert resorte.ky == 1000
        assert resorte.ktheta == 0
        assert resorte.tipo == TipoVinculo.RESORTE

    def test_crear_resorte_horizontal(self):
        """Test crear resorte horizontal."""
        resorte = ResorteElastico(kx=500, ky=0, ktheta=0)

        assert resorte.kx == 500
        assert resorte.ky == 0
        assert resorte.ktheta == 0

    def test_crear_resorte_rotacional(self):
        """Test crear resorte rotacional (muelle de torsión)."""
        resorte = ResorteElastico(kx=0, ky=0, ktheta=100)

        assert resorte.kx == 0
        assert resorte.ky == 0
        assert resorte.ktheta == 100

    def test_crear_resorte_combinado(self):
        """Test crear resorte con rigidez traslacional y rotacional."""
        resorte = ResorteElastico(kx=300, ky=500, ktheta=50)

        assert resorte.kx == 300
        assert resorte.ky == 500
        assert resorte.ktheta == 50

    def test_error_rigidez_negativa_kx(self):
        """Test error al crear resorte con kx negativo."""
        with pytest.raises(ValueError, match="kx no puede ser negativo"):
            ResorteElastico(kx=-100, ky=0, ktheta=0)

    def test_error_rigidez_negativa_ky(self):
        """Test error al crear resorte con ky negativo."""
        with pytest.raises(ValueError, match="ky no puede ser negativo"):
            ResorteElastico(kx=0, ky=-50, ktheta=0)

    def test_error_rigidez_negativa_ktheta(self):
        """Test error al crear resorte con ktheta negativo."""
        with pytest.raises(ValueError, match="ktheta no puede ser negativo"):
            ResorteElastico(kx=0, ky=0, ktheta=-10)

    def test_error_todas_rigideces_cero(self):
        """Test error al crear resorte sin rigidez."""
        with pytest.raises(ValueError, match="Al menos una rigidez debe ser positiva"):
            ResorteElastico(kx=0, ky=0, ktheta=0)


class TestGDLRestringidos:
    """Tests de grados de libertad restringidos por resortes."""

    def test_gdl_resorte_vertical(self):
        """Test GDL restringidos por resorte vertical."""
        resorte = ResorteElastico(kx=0, ky=1000, ktheta=0)

        gdl = resorte.gdl_restringidos()
        assert GDL.UY.value in gdl
        assert GDL.UX.value not in gdl
        assert GDL.THETA_Z.value not in gdl

    def test_gdl_resorte_horizontal(self):
        """Test GDL restringidos por resorte horizontal."""
        resorte = ResorteElastico(kx=500, ky=0, ktheta=0)

        gdl = resorte.gdl_restringidos()
        assert GDL.UX.value in gdl
        assert GDL.UY.value not in gdl
        assert GDL.THETA_Z.value not in gdl

    def test_gdl_resorte_rotacional(self):
        """Test GDL restringidos por resorte rotacional."""
        resorte = ResorteElastico(kx=0, ky=0, ktheta=100)

        gdl = resorte.gdl_restringidos()
        assert GDL.THETA_Z.value in gdl
        assert GDL.UX.value not in gdl
        assert GDL.UY.value not in gdl

    def test_gdl_resorte_completo(self):
        """Test GDL restringidos por resorte con todas las rigideces."""
        resorte = ResorteElastico(kx=300, ky=500, ktheta=50)

        gdl = resorte.gdl_restringidos()
        assert GDL.UX.value in gdl
        assert GDL.UY.value in gdl
        assert GDL.THETA_Z.value in gdl
        assert len(gdl) == 3


class TestPropiedades:
    """Tests de propiedades de resortes."""

    def test_es_resorte_traslacional_solo_kx(self):
        """Test identificación de resorte traslacional (solo kx)."""
        resorte = ResorteElastico(kx=100, ky=0, ktheta=0)
        assert resorte.es_resorte_traslacional is True
        assert resorte.es_resorte_rotacional is False

    def test_es_resorte_traslacional_solo_ky(self):
        """Test identificación de resorte traslacional (solo ky)."""
        resorte = ResorteElastico(kx=0, ky=200, ktheta=0)
        assert resorte.es_resorte_traslacional is True
        assert resorte.es_resorte_rotacional is False

    def test_es_resorte_rotacional_puro(self):
        """Test identificación de resorte rotacional puro."""
        resorte = ResorteElastico(kx=0, ky=0, ktheta=50)
        assert resorte.es_resorte_traslacional is False
        assert resorte.es_resorte_rotacional is True

    def test_resorte_combinado_flags(self):
        """Test flags en resorte combinado."""
        resorte = ResorteElastico(kx=100, ky=200, ktheta=50)
        assert resorte.es_resorte_traslacional is True
        assert resorte.es_resorte_rotacional is True

    def test_rigideces_tupla(self):
        """Test obtener rigideces como tupla."""
        resorte = ResorteElastico(kx=300, ky=500, ktheta=75)
        rigideces = resorte.rigideces

        assert rigideces == (300, 500, 75)
        assert isinstance(rigideces, tuple)

    def test_num_reacciones(self):
        """Test número de reacciones del resorte."""
        resorte = ResorteElastico(kx=100, ky=200, ktheta=0)
        assert resorte.num_reacciones == 2

        resorte2 = ResorteElastico(kx=0, ky=0, ktheta=50)
        assert resorte2.num_reacciones == 1


class TestDescripcionYRepresentacion:
    """Tests de descripción textual y representación."""

    def test_tipo_str_resorte_vertical(self):
        """Test descripción de resorte vertical."""
        resorte = ResorteElastico(kx=0, ky=1000, ktheta=0)
        tipo_str = resorte.tipo_str

        assert "Resorte" in tipo_str
        assert "ky=1000" in tipo_str
        assert "kx" not in tipo_str

    def test_tipo_str_resorte_completo(self):
        """Test descripción de resorte completo."""
        resorte = ResorteElastico(kx=300, ky=500, ktheta=75)
        tipo_str = resorte.tipo_str

        assert "Resorte" in tipo_str
        assert "kx=300" in tipo_str
        assert "ky=500" in tipo_str
        # Nota: kθ puede aparecer como "ktheta" o "kθ" dependiendo de Unicode
        assert "75" in tipo_str

    def test_simbolo_grafico(self):
        """Test símbolo gráfico del resorte."""
        resorte = ResorteElastico(kx=100, ky=200, ktheta=0)
        assert resorte.simbolo_grafico == "SPRING"


class TestFuncionesConveniencia:
    """Tests de funciones auxiliares para crear resortes."""

    def test_crear_resorte_vertical_funcion(self):
        """Test función auxiliar crear_resorte_vertical."""
        from src.domain.entities.vinculo import crear_resorte_vertical

        resorte = crear_resorte_vertical(1500)

        assert resorte.kx == 0
        assert resorte.ky == 1500
        assert resorte.ktheta == 0

    def test_crear_resorte_horizontal_funcion(self):
        """Test función auxiliar crear_resorte_horizontal."""
        from src.domain.entities.vinculo import crear_resorte_horizontal

        resorte = crear_resorte_horizontal(800)

        assert resorte.kx == 800
        assert resorte.ky == 0
        assert resorte.ktheta == 0

    def test_crear_resorte_rotacional_funcion(self):
        """Test función auxiliar crear_resorte_rotacional."""
        from src.domain.entities.vinculo import crear_resorte_rotacional

        resorte = crear_resorte_rotacional(120)

        assert resorte.kx == 0
        assert resorte.ky == 0
        assert resorte.ktheta == 120


class TestReacciones:
    """Tests de cálculo de reacciones en resortes."""

    def test_reacciones_iniciales_cero(self):
        """Test reacciones iniciales son cero."""
        resorte = ResorteElastico(kx=100, ky=200, ktheta=50)

        assert resorte.Rx == 0
        assert resorte.Ry == 0
        assert resorte.Mz == 0

        reacciones = resorte.reacciones()
        assert reacciones == (0, 0, 0)

    def test_asignar_reacciones(self):
        """Test asignación de reacciones calculadas."""
        resorte = ResorteElastico(kx=100, ky=200, ktheta=0)

        # Simular cálculo de reacciones
        resorte.Rx = 50.0
        resorte.Ry = -30.0
        resorte.Mz = 0.0

        assert resorte.Rx == 50.0
        assert resorte.Ry == -30.0
        assert resorte.Mz == 0.0

    def test_reiniciar_reacciones(self):
        """Test reiniciar reacciones a cero."""
        resorte = ResorteElastico(kx=100, ky=200, ktheta=50)

        # Asignar reacciones
        resorte.Rx = 100.0
        resorte.Ry = 200.0
        resorte.Mz = 50.0

        # Reiniciar
        resorte.reiniciar_reacciones()

        assert resorte.Rx == 0.0
        assert resorte.Ry == 0.0
        assert resorte.Mz == 0.0


class TestIntegracionConNudo:
    """Tests de integración con nudos."""

    def test_asignar_resorte_a_nudo(self):
        """Test asignar resorte elástico a un nudo."""
        nudo = Nudo(id=1, x=0, y=0, nombre="A")
        resorte = ResorteElastico(kx=500, ky=1000, ktheta=100)

        resorte.nudo = nudo
        nudo.vinculo = resorte

        assert nudo.vinculo == resorte
        assert resorte.nudo == nudo

    def test_calcular_reaccion_proporcional_desplazamiento(self):
        """
        Test conceptual: reacción = -k * desplazamiento.

        En un resorte, la fuerza de reacción es proporcional al desplazamiento:
        R = -k * δ
        """
        resorte = ResorteElastico(kx=0, ky=1000, ktheta=0)

        # Ejemplo: si el nudo se desplaza 0.01 m hacia abajo (Uy = 0.01)
        # La reacción vertical debería ser: Ry = -ky * Uy = -1000 * 0.01 = -10 kN
        desplazamiento_y = 0.01  # m
        reaccion_esperada = -resorte.ky * desplazamiento_y

        assert reaccion_esperada == -10.0  # kN (hacia arriba)

    def test_rigidez_infinita_equivale_vinculo_rigido(self):
        """
        Test conceptual: rigidez muy alta (k → ∞) equivale a vínculo rígido.
        """
        # Resorte muy rígido (k = 1e9 kN/m ≈ infinito)
        resorte_rigido = ResorteElastico(kx=0, ky=1e9, ktheta=0)

        # Para desplazamiento pequeño (1e-6 m)
        delta = 1e-6
        reaccion = -resorte_rigido.ky * delta

        # Reacción = -1e9 * 1e-6 = -1000 kN (muy grande, impide movimiento)
        assert abs(reaccion) == 1000

        # Para comparación, resorte blando:
        resorte_blando = ResorteElastico(kx=0, ky=10, ktheta=0)
        reaccion_blando = -resorte_blando.ky * delta

        assert abs(reaccion_blando - (-1e-5)) < 1e-10  # Muy pequeña, casi no restringe
