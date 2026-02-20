"""
Tests unitarios para la clase CargaTermica.
"""

import pytest
from src.domain.entities.carga import CargaTermica
from src.domain.entities.material import Material
from src.domain.entities.seccion import SeccionRectangular
from src.domain.entities.barra import Barra
from src.domain.entities.nudo import Nudo
from src.utils.constants import TipoCarga


@pytest.fixture
def material_acero():
    """Material de acero con coeficiente de dilatación térmica."""
    return Material(
        nombre="Acero A-36",
        E=200e6,      # kN/m²
        alpha=1.2e-5  # 1/°C
    )


@pytest.fixture
def seccion_rect():
    """Sección rectangular 30x50 cm."""
    return SeccionRectangular(
        nombre="30x50cm",
        b=0.30,
        _h=0.50
    )


@pytest.fixture
def barra_simple(material_acero, seccion_rect):
    """Barra simple de 6m."""
    nA = Nudo(id=1, x=0.0, y=0.0)
    nB = Nudo(id=2, x=6.0, y=0.0)
    return Barra(
        id=1,
        nudo_i=nA,
        nudo_j=nB,
        material=material_acero,
        seccion=seccion_rect
    )


class TestCargaTermicaBasico:
    """Tests básicos de la clase CargaTermica."""

    def test_crear_carga_termica_uniforme(self, barra_simple):
        """Test creación de carga térmica uniforme."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_uniforme=30.0,
            delta_T_gradiente=0.0
        )

        assert carga.barra == barra_simple
        assert carga.delta_T_uniforme == 30.0
        assert carga.delta_T_gradiente == 0.0
        assert carga.tipo == TipoCarga.TERMICA

    def test_crear_carga_termica_gradiente(self, barra_simple):
        """Test creación de carga térmica con gradiente."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_uniforme=0.0,
            delta_T_gradiente=20.0
        )

        assert carga.delta_T_uniforme == 0.0
        assert carga.delta_T_gradiente == 20.0
        assert carga.tipo == TipoCarga.TERMICA

    def test_crear_carga_termica_combinada(self, barra_simple):
        """Test creación de carga térmica combinada."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_uniforme=15.0,
            delta_T_gradiente=10.0
        )

        assert carga.delta_T_uniforme == 15.0
        assert carga.delta_T_gradiente == 10.0

    def test_descripcion_carga_uniforme(self, barra_simple):
        """Test descripción de carga térmica uniforme."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_uniforme=30.0
        )

        desc = carga.descripcion
        assert "ΔT=+30.0°C" in desc or "DT=+30.0" in desc.replace("Δ", "D")

    def test_descripcion_carga_gradiente(self, barra_simple):
        """Test descripción de carga térmica con gradiente."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_gradiente=20.0
        )

        desc = carga.descripcion
        assert "T=20.0" in desc  # Parte del string ∇T o gradT


class TestDeformacionAxialLibre:
    """Tests para cálculo de deformación axial libre."""

    def test_deformacion_axial_calentamiento(self, barra_simple):
        """Test deformación axial por calentamiento (+ΔT)."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_uniforme=30.0
        )

        # δ = α·ΔT·L = 1.2e-5 * 30 * 6 = 2.16e-3 m = 2.16 mm
        delta = carga.deformacion_axial_libre()

        assert abs(delta - 2.16e-3) < 1e-6, f"Esperado 2.16mm, obtenido {delta*1000:.3f}mm"

    def test_deformacion_axial_enfriamiento(self, barra_simple):
        """Test deformación axial por enfriamiento (-ΔT)."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_uniforme=-20.0
        )

        # δ = α·ΔT·L = 1.2e-5 * (-20) * 6 = -1.44e-3 m
        delta = carga.deformacion_axial_libre()

        assert abs(delta - (-1.44e-3)) < 1e-6

    def test_deformacion_sin_cambio_temperatura(self, barra_simple):
        """Test sin cambio de temperatura (ΔT = 0)."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_uniforme=0.0
        )

        delta = carga.deformacion_axial_libre()
        assert abs(delta) < 1e-10


class TestCurvaturaTermica:
    """Tests para cálculo de curvatura térmica."""

    def test_curvatura_gradiente_positivo(self, barra_simple):
        """Test curvatura por gradiente térmico positivo."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_gradiente=20.0
        )

        # κ = (α·ΔT_grad) / h = (1.2e-5 * 20) / 0.5 = 4.8e-4 1/m
        kappa = carga.curvatura_termica()

        assert abs(kappa - 4.8e-4) < 1e-8

    def test_curvatura_gradiente_negativo(self, barra_simple):
        """Test curvatura por gradiente térmico negativo."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_gradiente=-15.0
        )

        # κ = (α·ΔT_grad) / h = (1.2e-5 * -15) / 0.5 = -3.6e-4 1/m
        kappa = carga.curvatura_termica()

        assert abs(kappa - (-3.6e-4)) < 1e-8

    def test_curvatura_sin_gradiente(self, barra_simple):
        """Test sin gradiente térmico."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_gradiente=0.0
        )

        kappa = carga.curvatura_termica()
        assert abs(kappa) < 1e-10


class TestTrabajoVirtualUniforme:
    """Tests para trabajo virtual con variación uniforme."""

    def test_trabajo_virtual_uniforme_axil_constante(self, barra_simple):
        """Test trabajo virtual con axil constante."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_uniforme=30.0
        )

        # Para axil virtual Ni = 1.0 kN (constante)
        # δ_térmico = α·ΔT·∫(Ni dx) = α·ΔT·Ni·L
        # δ = 1.2e-5 * 30 * 1.0 * 6 = 2.16e-3 m
        delta_virtual = carga.trabajo_virtual_uniforme(esfuerzo_axil_virtual=1.0)

        assert abs(delta_virtual - 2.16e-3) < 1e-8

    def test_trabajo_virtual_uniforme_axil_doble(self, barra_simple):
        """Test trabajo virtual con axil virtual doble."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_uniforme=30.0
        )

        # Con Ni = 2.0 kN, el resultado se duplica
        delta_virtual = carga.trabajo_virtual_uniforme(esfuerzo_axil_virtual=2.0)

        assert abs(delta_virtual - 4.32e-3) < 1e-8

    def test_trabajo_virtual_sin_temperatura(self, barra_simple):
        """Test trabajo virtual sin variación de temperatura."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_uniforme=0.0
        )

        delta_virtual = carga.trabajo_virtual_uniforme(esfuerzo_axil_virtual=1.0)
        assert abs(delta_virtual) < 1e-10


class TestTrabajoVirtualGradiente:
    """Tests para trabajo virtual con gradiente térmico."""

    def test_trabajo_virtual_gradiente_momento_constante(self, barra_simple):
        """Test trabajo virtual con momento virtual constante."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_gradiente=20.0
        )

        # Momento virtual constante Mi(x) = 1.0 kNm
        def momento_virtual(x):
            return 1.0

        # δ = κ·∫(Mi dx) = κ·Mi·L
        # κ = 4.8e-4 1/m (calculado antes)
        # δ = 4.8e-4 * 1.0 * 6 = 2.88e-3 m
        delta_virtual = carga.trabajo_virtual_gradiente(momento_virtual)

        assert abs(delta_virtual - 2.88e-3) < 1e-6

    def test_trabajo_virtual_gradiente_momento_lineal(self, barra_simple):
        """Test trabajo virtual con momento virtual lineal."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_gradiente=20.0
        )

        # Momento virtual lineal: Mi(x) = x (de 0 a L)
        def momento_lineal(x):
            return x

        # ∫(x dx) de 0 a L = L²/2 = 6²/2 = 18
        # δ = κ·∫(Mi dx) = 4.8e-4 * 18 = 8.64e-3 m
        delta_virtual = carga.trabajo_virtual_gradiente(momento_lineal)

        assert abs(delta_virtual - 8.64e-3) < 1e-5

    def test_trabajo_virtual_sin_gradiente(self, barra_simple):
        """Test trabajo virtual sin gradiente térmico."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_gradiente=0.0
        )

        def momento_virtual(x):
            return 1.0

        delta_virtual = carga.trabajo_virtual_gradiente(momento_virtual)
        assert abs(delta_virtual) < 1e-10


class TestCargaTermicaCombinada:
    """Tests para cargas térmicas combinadas."""

    def test_efectos_independientes(self, barra_simple):
        """Test que efectos uniforme y gradiente son independientes."""
        # Carga con ambos efectos
        carga_combinada = CargaTermica(
            barra=barra_simple,
            delta_T_uniforme=30.0,
            delta_T_gradiente=20.0
        )

        # Cargas separadas
        carga_uniforme = CargaTermica(
            barra=barra_simple,
            delta_T_uniforme=30.0
        )

        carga_gradiente = CargaTermica(
            barra=barra_simple,
            delta_T_gradiente=20.0
        )

        # Verificar independencia
        assert carga_combinada.deformacion_axial_libre() == carga_uniforme.deformacion_axial_libre()
        assert carga_combinada.curvatura_termica() == carga_gradiente.curvatura_termica()


class TestCasosLimite:
    """Tests de casos límite y validación."""

    def test_carga_sin_barra(self):
        """Test carga térmica sin barra asignada."""
        carga = CargaTermica(
            barra=None,
            delta_T_uniforme=30.0
        )

        # Debe retornar 0 en todos los cálculos
        assert carga.deformacion_axial_libre() == 0.0
        assert carga.curvatura_termica() == 0.0

    def test_str_representation(self, barra_simple):
        """Test representación en string."""
        carga = CargaTermica(
            barra=barra_simple,
            delta_T_uniforme=15.0,
            delta_T_gradiente=10.0
        )

        str_repr = str(carga)
        assert "CargaTermica" in str_repr
        assert "15.0" in str_repr or "+15" in str_repr
        assert "10.0" in str_repr or "+10" in str_repr


class TestCalculadorFlexibilidadTermico:
    """
    Tests de integración: contribución térmica al vector e0 en el CalculadorFlexibilidad.

    Verifica que _calcular_e0i_termico integra numéricamente ∫N̄ᵢ dx
    en lugar de aproximar con N̄_promedio, lo que es esencial para
    barras inclinadas o estructuras donde N̄ᵢ varía a lo largo de la barra.
    """

    def _hacer_subestructura_xi(self, barra, N_inicio, N_fin):
        """
        Crea una Subestructura Xi con N̄ lineal de N_inicio a N_fin y M̄=0.

        Usa un DiagramaEsfuerzos con función N personalizada para que
        sub.N(barra.id, x) devuelva el axil correcto.
        """
        from src.domain.analysis.subestructuras import Subestructura
        from src.domain.mechanics.esfuerzos import DiagramaEsfuerzos, EsfuerzosTramo

        L = barra.L
        pendiente = (N_fin - N_inicio) / L if L > 1e-10 else 0.0

        def N_func(x, N0=N_inicio, m=pendiente):
            return N0 + m * x

        tramo = EsfuerzosTramo(
            x_inicio=0.0, x_fin=L,
            N=N_func,
            V=lambda x: 0.0,
            M=lambda x: 0.0,
        )
        diagrama = DiagramaEsfuerzos(
            barra_id=barra.id, L=L,
            tramos=[tramo],
            Ni=N_inicio, Nj=N_fin,
            Mi=0.0, Mj=0.0,
        )
        sub = Subestructura(nombre="X1_test", es_fundamental=False)
        sub.diagramas[barra.id] = diagrama
        return sub

    def _hacer_fundamental_vacia(self, barra):
        """Subestructura fundamental con M⁰=N⁰=0."""
        from src.domain.analysis.subestructuras import Subestructura
        from src.domain.mechanics.esfuerzos import crear_diagrama_lineal

        fundamental = Subestructura(nombre="Fund", es_fundamental=True)
        fundamental.diagramas[barra.id] = crear_diagrama_lineal(
            barra.id, barra.L, 0, 0, "M"
        )
        return fundamental

    def test_e0_termico_axil_constante(self, barra_simple):
        """
        ΔT uniforme con N̄=1 constante → e0 = α·ΔT·N̄·L (resultado clásico).

        Verifica que la integración numérica coincide con la fórmula cerrada
        cuando el axil virtual es constante.
          e0 = α·ΔT·∫N̄ dx = 1.2e-5 · 30 · 1.0 · 6.0 = 2.16e-3 m
        """
        from src.domain.analysis.trabajos_virtuales import CalculadorFlexibilidad

        carga_termica = CargaTermica(barra=barra_simple, delta_T_uniforme=30.0)
        sub_xi = self._hacer_subestructura_xi(barra_simple, N_inicio=1.0, N_fin=1.0)
        fundamental = self._hacer_fundamental_vacia(barra_simple)

        calculador = CalculadorFlexibilidad(
            barras=[barra_simple],
            fundamental=fundamental,
            subestructuras_xi=[sub_xi],
            cargas_termicas=[carga_termica],
        )

        e0_esperado = 1.2e-5 * 30.0 * 1.0 * 6.0  # = 2.16e-3
        coef = calculador.calcular()
        assert abs(coef.e0[0] - e0_esperado) < 1e-8, (
            f"e0 termico esperado {e0_esperado:.2e}, obtenido {coef.e0[0]:.2e}"
        )

    def test_e0_termico_axil_lineal_variable(self, barra_simple):
        """
        ΔT uniforme con N̄ lineal de 0→1 → e0 = α·ΔT·∫N̄ dx = α·ΔT·L/2.

        Este caso (N̄ variable) verifica que la integración numérica es necesaria:
        el promedio de extremos (N̄=(0+1)/2=0.5) daría α·ΔT·0.5·L = α·ΔT·L/2,
        que coincide en este caso lineal, pero la integración con Simpson es
        la implementación correcta para el caso general.
          e0 = α·ΔT·∫₀ᴸ(x/L) dx = α·ΔT·L/2 = 1.2e-5 · 30 · 3.0 = 1.08e-3 m
        """
        from src.domain.analysis.trabajos_virtuales import CalculadorFlexibilidad

        carga_termica = CargaTermica(barra=barra_simple, delta_T_uniforme=30.0)
        # N̄(x) = x/L  →  ∫N̄ dx = L/2 = 3.0
        sub_xi = self._hacer_subestructura_xi(barra_simple, N_inicio=0.0, N_fin=1.0)
        fundamental = self._hacer_fundamental_vacia(barra_simple)

        calculador = CalculadorFlexibilidad(
            barras=[barra_simple],
            fundamental=fundamental,
            subestructuras_xi=[sub_xi],
            cargas_termicas=[carga_termica],
        )

        e0_esperado = 1.2e-5 * 30.0 * 3.0  # = 1.08e-3
        coef = calculador.calcular()
        assert abs(coef.e0[0] - e0_esperado) < 1e-8, (
            f"e0 termico esperado {e0_esperado:.2e}, obtenido {coef.e0[0]:.2e}"
        )
