"""
Tests unitarios para el Motor del Método de las Deformaciones (Rigidez).

Cubre:
- Función _k_local_barra(): valores numéricos y simetría
- CalculadorFuerzasEmpotramiento: FEF para carga distribuida y puntual
- NumeradorGDL: asignación correcta de índices
- MotorMetodoDeformaciones: casos canónicos con solución analítica conocida

Convención de signos (TERNA adoptada):
    Y+ hacia abajo, rotación CW positiva, M+ tracción fibra inferior
    angulo=+90° → carga perpendicular hacia abajo (Y_local+)
"""

import math
import pytest
import numpy as np

from src.domain.analysis.motor_deformaciones import (
    MotorMetodoDeformaciones,
    _k_local_barra,
    analizar_estructura_deformaciones,
)
from src.domain.analysis.fuerzas_empotramiento import (
    CalculadorFuerzasEmpotramiento,
    _fef_distribuida_transversal,
    _fef_puntual_transversal,
    _fef_distribuida_axial,
    _fef_puntual_axial,
)
from src.domain.analysis.numerador_gdl import NumeradorGDL
from src.domain.entities.barra import Barra
from src.domain.entities.carga import (
    CargaDistribuida,
    CargaPuntualBarra,
    CargaPuntualNudo,
)
from src.domain.entities.material import Material
from src.domain.entities.nudo import Nudo
from src.domain.entities.seccion import SeccionRectangular
from src.domain.entities.vinculo import Empotramiento, ApoyoFijo, Rodillo, ResorteElastico
from src.domain.model.modelo_estructural import ModeloEstructural


# ===========================================================================
# FIXTURES
# ===========================================================================

@pytest.fixture
def acero():
    """Acero estándar E=200 GPa."""
    return Material(nombre="Acero A-36", E=200e6)


@pytest.fixture
def ipe220():
    """Sección IPE 220."""
    return SeccionRectangular(nombre="IPE220", b=0.0334, _h=0.220)


@pytest.fixture
def seccion_rect():
    """Sección rectangular 30×50 cm."""
    return SeccionRectangular(nombre="30x50cm", b=0.30, _h=0.50)


@pytest.fixture
def barra_horizontal_6m(acero, seccion_rect):
    """Barra horizontal de 6m."""
    nA = Nudo(id=1, x=0.0, y=0.0)
    nB = Nudo(id=2, x=6.0, y=0.0)
    return Barra(id=1, nudo_i=nA, nudo_j=nB, material=acero, seccion=seccion_rect)


@pytest.fixture
def modelo_biempotrada(acero, seccion_rect):
    """
    Viga biempotrada horizontal de 6m.
    Nudo 1: empotramiento (0,0)
    Nudo 2: empotramiento (6,0)
    """
    modelo = ModeloEstructural("Biempotrada L=6m")
    nA = modelo.agregar_nudo(0.0, 0.0, "A")
    nB = modelo.agregar_nudo(6.0, 0.0, "B")
    modelo.agregar_barra(nA, nB, acero, seccion_rect)
    modelo.asignar_vinculo(nA.id, Empotramiento())
    modelo.asignar_vinculo(nB.id, Empotramiento())
    return modelo


# ===========================================================================
# TESTS: _k_local_barra
# ===========================================================================

class TestKLocalBarra:
    """Tests para la matriz de rigidez local 6×6."""

    def test_k_local_valores_axiales(self):
        """Verificar rigidez axial EA/L en posiciones (0,0), (0,3), (3,3)."""
        E, A, L = 200e6, 33.4e-4, 6.0
        EA = E * A
        k = _k_local_barra(EA, 1.0, L)  # EI=1 (no afecta axiales)

        assert k[0, 0] == pytest.approx(EA / L, rel=1e-10)
        assert k[0, 3] == pytest.approx(-EA / L, rel=1e-10)
        assert k[3, 3] == pytest.approx(EA / L, rel=1e-10)

    def test_k_local_valores_flexionales(self):
        """Verificar rigidez flexional 12EI/L³, 6EI/L², 4EI/L, 2EI/L."""
        EI = 200e6 * 2772e-8   # E*I para IPE220 estándar
        L = 6.0
        k = _k_local_barra(1.0, EI, L)  # EA=1 (no afecta flexionales)

        L2 = L * L
        L3 = L2 * L

        # k[1,1] = 12EI/L³
        assert k[1, 1] == pytest.approx(12 * EI / L3, rel=1e-10)
        # k[1,2] = 6EI/L²
        assert k[1, 2] == pytest.approx(6 * EI / L2, rel=1e-10)
        # k[2,2] = 4EI/L
        assert k[2, 2] == pytest.approx(4 * EI / L, rel=1e-10)
        # k[2,5] = 2EI/L
        assert k[2, 5] == pytest.approx(2 * EI / L, rel=1e-10)
        # k[5,5] = 4EI/L
        assert k[5, 5] == pytest.approx(4 * EI / L, rel=1e-10)
        # k[4,4] = 12EI/L³
        assert k[4, 4] == pytest.approx(12 * EI / L3, rel=1e-10)

    def test_k_local_simetria(self):
        """La matriz k_local debe ser exactamente simétrica."""
        EA = 200e6 * 33.4e-4
        EI = 200e6 * 2772e-8
        k = _k_local_barra(EA, EI, 6.0)
        np.testing.assert_array_almost_equal(k, k.T, decimal=10)

    def test_k_local_forma_shape(self):
        """La matriz debe tener forma 6×6."""
        k = _k_local_barra(100.0, 50.0, 5.0)
        assert k.shape == (6, 6)

    def test_k_local_longitud_nula_falla(self):
        """Longitud nula debe lanzar ValueError."""
        with pytest.raises(ValueError, match="[Ll]ongitud"):
            _k_local_barra(100.0, 50.0, 0.0)

    def test_k_local_positivo_definido(self):
        """K debe ser positiva semi-definida (autovalores >= 0)."""
        EA = 200e6 * 33.4e-4
        EI = 200e6 * 2772e-8
        k = _k_local_barra(EA, EI, 4.0)
        autovalores = np.linalg.eigvalsh(k)
        # Existen 3 modos de cuerpo rígido → 3 autovalores ~ 0
        assert np.all(autovalores >= -1e-6)


# ===========================================================================
# TESTS: CalculadorFuerzasEmpotramiento (FEF)
# ===========================================================================

class TestFEFDistribuidaTransversal:
    """Tests para FEF de carga distribuida transversal."""

    def test_fef_uniforme_formula_clasica(self):
        """
        Para q uniforme (q_a=q_b=q):
            FEF = [0, qL/2, qL²/12, 0, qL/2, -qL²/12]
        """
        q, L = 10.0, 6.0
        fef = _fef_distribuida_transversal(q, q, L)

        assert fef[0] == 0.0   # N_i
        assert fef[1] == pytest.approx(q * L / 2, rel=1e-10)    # V_i = 30
        assert fef[2] == pytest.approx(q * L**2 / 12, rel=1e-10)  # M_i = 30
        assert fef[3] == 0.0   # N_j
        assert fef[4] == pytest.approx(q * L / 2, rel=1e-10)    # V_j = 30
        assert fef[5] == pytest.approx(-q * L**2 / 12, rel=1e-10)  # M_j = -30

    def test_fef_triangular_cero_en_j(self):
        """
        Para q triangular (q_a=q, q_b=0):
            V_i = L(7q)/20 = 7qL/20
            M_i = L²(3q)/60 = qL²/20
            V_j = L(3q)/20 = 3qL/20
            M_j = -L²(2q)/60 = -qL²/30
        """
        q, L = 10.0, 6.0
        fef = _fef_distribuida_transversal(q, 0.0, L)

        assert fef[1] == pytest.approx(7 * q * L / 20, rel=1e-10)
        assert fef[2] == pytest.approx(q * L**2 / 20, rel=1e-10)
        assert fef[4] == pytest.approx(3 * q * L / 20, rel=1e-10)
        assert fef[5] == pytest.approx(-q * L**2 / 30, rel=1e-10)

    def test_fef_equilibrio_vertical(self):
        """La suma de V_i + V_j debe igualar la carga total qL."""
        q_a, q_b, L = 8.0, 12.0, 5.0
        fef = _fef_distribuida_transversal(q_a, q_b, L)
        carga_total = (q_a + q_b) / 2.0 * L
        assert fef[1] + fef[4] == pytest.approx(carga_total, rel=1e-10)


class TestFEFPuntualTransversal:
    """Tests para FEF de carga puntual transversal."""

    def test_fef_puntual_centro(self):
        """
        Para P en el centro (a=L/2, b=L/2):
            V_i = Pb²(3a+b)/L³ = P*(L/2)²*(2L)/L³ = P/2
            M_i = Pab²/L² = P*(L/2)³/L² = PL/8
            V_j = Pa²(a+3b)/L³ = P*(L/2)²*(2L)/L³ = P/2
            M_j = -Pa²b/L² = -PL/8
        """
        P, L = 12.0, 6.0
        a = L / 2
        fef = _fef_puntual_transversal(P, a, L)

        assert fef[1] == pytest.approx(P / 2, rel=1e-10)
        assert fef[2] == pytest.approx(P * L / 8, rel=1e-10)
        assert fef[4] == pytest.approx(P / 2, rel=1e-10)
        assert fef[5] == pytest.approx(-P * L / 8, rel=1e-10)

    def test_fef_puntual_equilibrio(self):
        """La suma de V_i + V_j debe igualar P."""
        P, L, a = 15.0, 4.0, 1.5
        fef = _fef_puntual_transversal(P, a, L)
        assert fef[1] + fef[4] == pytest.approx(P, rel=1e-10)

    def test_fef_puntual_extremo_coincide_estatica(self):
        """
        Para P en x=0 (en el nudo i):
            V_i = P, V_j = 0, M_i = 0, M_j = 0
        """
        P, L = 10.0, 4.0
        fef = _fef_puntual_transversal(P, 0.0, L)
        assert fef[1] == pytest.approx(P, rel=1e-10)
        assert fef[4] == pytest.approx(0.0, abs=1e-10)
        assert fef[2] == pytest.approx(0.0, abs=1e-10)

    def test_fef_puntual_barra_longitud_nula(self):
        """Para L=0 debe retornar vector cero sin error."""
        fef = _fef_puntual_transversal(10.0, 0.0, 0.0)
        np.testing.assert_array_equal(fef, np.zeros(6))


class TestFEFCalcCargaBarra:
    """Tests para CalculadorFuerzasEmpotramiento con objetos Barra reales."""

    def test_calcular_fef_distribuida_uniforme_90(self, barra_horizontal_6m, acero, seccion_rect):
        """
        Barra horizontal con q=10 kN/m a 90° (hacia abajo, Y_local+).
        FEF_V_i = qL/2 = 30, FEF_M_i = qL²/12 = 30
        """
        q = 10.0
        L = barra_horizontal_6m.L
        carga = CargaDistribuida(
            barra=barra_horizontal_6m,
            q1=q, q2=q,
            angulo=+90.0,    # +90° = dirección Y_local+ = hacia abajo
        )
        barra_horizontal_6m.cargas.append(carga)

        calc = CalculadorFuerzasEmpotramiento()
        fef = calc.calcular(barra_horizontal_6m)

        assert fef[1] == pytest.approx(q * L / 2, rel=1e-6)   # V_i = 30
        assert fef[2] == pytest.approx(q * L**2 / 12, rel=1e-6)  # M_i = 30

        barra_horizontal_6m.cargas.clear()

    def test_calcular_fef_puntual_centro_90(self, barra_horizontal_6m):
        """
        Carga puntual P=12 en L/2, angulo=+90°.
        FEF: V_i = V_j = P/2 = 6, M_i = PL/8 = 9, M_j = -PL/8 = -9
        """
        P = 12.0
        L = barra_horizontal_6m.L
        carga = CargaPuntualBarra(
            barra=barra_horizontal_6m,
            P=P, a=L / 2,
            angulo=+90.0,
        )
        barra_horizontal_6m.cargas.append(carga)

        calc = CalculadorFuerzasEmpotramiento()
        fef = calc.calcular(barra_horizontal_6m)

        assert fef[1] == pytest.approx(P / 2, rel=1e-6)
        assert fef[2] == pytest.approx(P * L / 8, rel=1e-6)
        assert fef[4] == pytest.approx(P / 2, rel=1e-6)
        assert fef[5] == pytest.approx(-P * L / 8, rel=1e-6)

        barra_horizontal_6m.cargas.clear()


# ===========================================================================
# TESTS: NumeradorGDL
# ===========================================================================

class TestNumeradorGDL:
    """Tests para la asignación de índices GDL globales."""

    def _modelo_3_nudos(self, acero, seccion_rect):
        """Modelo auxiliar con 3 nudos en línea."""
        m = ModeloEstructural("3 nudos")
        n1 = m.agregar_nudo(0.0, 0.0, "A")
        n2 = m.agregar_nudo(4.0, 0.0, "B")
        n3 = m.agregar_nudo(8.0, 0.0, "C")
        m.agregar_barra(n1, n2, acero, seccion_rect)
        m.agregar_barra(n2, n3, acero, seccion_rect)
        m.asignar_vinculo(n1.id, Empotramiento())
        m.asignar_vinculo(n3.id, ApoyoFijo())
        return m

    def test_indices_correctos_3_nudos(self, acero, seccion_rect):
        """Nudo con índice i (orden por id) → GDLs 3i, 3i+1, 3i+2."""
        modelo = self._modelo_3_nudos(acero, seccion_rect)
        num = NumeradorGDL(modelo)
        gdl_map = num.numerar()

        # Nudos están ordenados por id: 1, 2, 3 → índices 0, 1, 2
        nudo_ids = sorted(gdl_map.keys())
        assert nudo_ids == [1, 2, 3]

        gdl1 = gdl_map[1]   # primer nudo → índices 0, 1, 2
        gdl2 = gdl_map[2]   # segundo nudo → índices 3, 4, 5
        gdl3 = gdl_map[3]   # tercer nudo → índices 6, 7, 8

        assert gdl1 == (0, 1, 2)
        assert gdl2 == (3, 4, 5)
        assert gdl3 == (6, 7, 8)

    def test_n_total_3_nudos(self, acero, seccion_rect):
        """3 nudos → 9 GDL totales."""
        modelo = self._modelo_3_nudos(acero, seccion_rect)
        num = NumeradorGDL(modelo)
        num.numerar()
        assert num.n_total == 9

    def test_indices_restringidos_empotramiento(self, acero, seccion_rect):
        """Empotramiento en nudo 1 → GDLs 0, 1, 2 restringidos."""
        modelo = self._modelo_3_nudos(acero, seccion_rect)
        num = NumeradorGDL(modelo)
        num.numerar()

        restringidos = num.indices_restringidos
        # Empotramiento nudo 1: 0, 1, 2
        # ApoyoFijo nudo 3: 6, 7
        assert 0 in restringidos   # Ux nudo 1
        assert 1 in restringidos   # Uy nudo 1
        assert 2 in restringidos   # theta_z nudo 1
        assert 6 in restringidos   # Ux nudo 3
        assert 7 in restringidos   # Uy nudo 3
        assert 8 not in restringidos  # theta_z nudo 3 libre

    def test_indices_libres_correctos(self, acero, seccion_rect):
        """Los libres son el complemento de los restringidos."""
        modelo = self._modelo_3_nudos(acero, seccion_rect)
        num = NumeradorGDL(modelo)
        num.numerar()

        libres = set(num.indices_libres)
        restringidos = set(num.indices_restringidos)
        todos = set(range(num.n_total))

        assert libres | restringidos == todos
        assert libres & restringidos == set()

    def test_indices_elemento_6_valores(self, acero, seccion_rect):
        """indices_elemento debe retornar 6 valores para cualquier barra."""
        modelo = self._modelo_3_nudos(acero, seccion_rect)
        num = NumeradorGDL(modelo)
        num.numerar()

        idx = num.indices_elemento(modelo.barras[0].id)
        assert len(idx) == 6

    def test_gdl_de_nudo_invalido(self, acero, seccion_rect):
        """gdl_de_nudo con nudo inexistente debe lanzar KeyError."""
        modelo = self._modelo_3_nudos(acero, seccion_rect)
        num = NumeradorGDL(modelo)
        num.numerar()
        with pytest.raises(KeyError):
            num.gdl_de_nudo(999)


# ===========================================================================
# TESTS: MotorMetodoDeformaciones - Casos canónicos
# ===========================================================================

class TestVigaBiempotradaQUniforme:
    """
    Viga biempotrada de L=6m con q=10 kN/m (Y+ = hacia abajo).

    Solución analítica conocida:
        Reacciones: R_A = R_B = qL/2 = 30 kN
        M_extremos: M_A = M_B = -qL²/12 = -30 kNm (hogging = negativo)
        M_centro:   M(L/2) = qL²/24 = 15 kNm
        Todos los desplazamientos nodales = 0 (estructura biempotrada)
    """

    @pytest.fixture(autouse=True)
    def setup(self, modelo_biempotrada):
        """Agregar carga y resolver."""
        self.L = 6.0
        self.q = 10.0
        barra = modelo_biempotrada.barras[0]
        carga = CargaDistribuida(barra=barra, q1=self.q, q2=self.q, angulo=+90.0)
        modelo_biempotrada.agregar_carga(carga)

        self.resultado = analizar_estructura_deformaciones(modelo_biempotrada)
        self.nudo_A = modelo_biempotrada.nudos[0]
        self.nudo_B = modelo_biempotrada.nudos[1]
        self.barra = barra
        self.diag = self.resultado.diagramas_finales[barra.id]

    def test_exitoso(self):
        """El análisis debe completarse exitosamente."""
        assert self.resultado.exitoso
        assert not self.resultado.errores

    def test_desplazamientos_nulos(self):
        """En viga biempotrada todos los desplazamientos son cero."""
        tol = 1e-6
        assert abs(self.nudo_A.Ux) < tol
        assert abs(self.nudo_A.Uy) < tol
        assert abs(self.nudo_A.theta_z) < tol
        assert abs(self.nudo_B.Ux) < tol
        assert abs(self.nudo_B.Uy) < tol
        assert abs(self.nudo_B.theta_z) < tol

    def test_momento_en_extremo_i(self):
        """M(x=0) = -qL²/12."""
        M_esperado = -self.q * self.L**2 / 12
        assert self.diag.M(0.0) == pytest.approx(M_esperado, rel=1e-4)

    def test_momento_en_extremo_j(self):
        """M(x=L) = -qL²/12 (por simetría = mismo módulo que extremo i)."""
        M_esperado = -self.q * self.L**2 / 12
        # El momento en j tiene signo según convención: debe ser positivo (sagging negado → wait)
        # Para biempotrada simétrica: M_j también tiene módulo qL²/12 pero signo depende de convención
        # Con la convención de continuidad: M(L) = -qL²/12 también? Verifiquemos:
        # M(x) = -qL²/12 + qL/2*x - q*x²/2
        # M(L) = -qL²/12 + qL²/2 - qL²/2 = -qL²/12 ✓
        assert self.diag.M(self.L) == pytest.approx(M_esperado, rel=1e-4)

    def test_momento_en_centro(self):
        """M(L/2) = qL²/24 (máximo positivo en centro)."""
        M_esperado = self.q * self.L**2 / 24
        assert self.diag.M(self.L / 2) == pytest.approx(M_esperado, rel=1e-4)

    def test_cortante_en_centro(self):
        """V(L/2) = 0 (por simetría la viga simétrica tiene V=0 en el centro)."""
        assert self.diag.V(self.L / 2) == pytest.approx(0.0, abs=1e-3)

    def test_cortante_en_extremo_i(self):
        """V(0) = qL/2."""
        V_esperado = self.q * self.L / 2
        assert self.diag.V(0.0) == pytest.approx(V_esperado, rel=1e-4)

    def test_reaccion_vertical_A(self):
        """Reacción vertical en A = qL/2 (hacia arriba = negativo en TERNA Y+)."""
        nudo_id = self.nudo_A.id
        Rx, Ry, Mz = self.resultado.reacciones_finales[nudo_id]
        # R_A = qL/2 hacia arriba → en TERNA Y+: Ry negativo
        assert Ry == pytest.approx(-self.q * self.L / 2, rel=1e-4)

    def test_reaccion_momento_A(self):
        """Reacción de momento en A = qL²/12 (CCW = positivo opuesto al M_interno)."""
        nudo_id = self.nudo_A.id
        Rx, Ry, Mz = self.resultado.reacciones_finales[nudo_id]
        # La reacción de momento opone a M_interno = -qL²/12
        assert abs(Mz) == pytest.approx(self.q * self.L**2 / 12, rel=1e-4)

    def test_axil_nulo(self):
        """En carga vertical pura no hay axil."""
        assert self.diag.N(0.0) == pytest.approx(0.0, abs=1e-6)
        assert self.diag.N(self.L) == pytest.approx(0.0, abs=1e-6)


class TestVigaBiempotradaCargatPuntual:
    """
    Viga biempotrada L=6m con carga puntual P=12 kN en el centro.

    Solución analítica:
        M_extremos = -PL/8 = -9 kNm
        M_centro   = +PL/8 = +9 kNm
        V_izquierdo = P/2 = 6 kN
        R_A = R_B = P/2 = 6 kN (hacia arriba)
    """

    @pytest.fixture(autouse=True)
    def setup(self, modelo_biempotrada):
        self.L = 6.0
        self.P = 12.0
        barra = modelo_biempotrada.barras[0]
        carga = CargaPuntualBarra(barra=barra, P=self.P, a=self.L / 2, angulo=+90.0)
        modelo_biempotrada.agregar_carga(carga)

        self.resultado = analizar_estructura_deformaciones(modelo_biempotrada)
        self.barra = barra
        self.diag = self.resultado.diagramas_finales[barra.id]

    def test_exitoso(self):
        assert self.resultado.exitoso
        assert not self.resultado.errores

    def test_momento_extremo(self):
        """M(0) = -PL/8."""
        assert self.diag.M(0.0) == pytest.approx(-self.P * self.L / 8, rel=1e-4)

    def test_momento_extremo_j(self):
        """M(L) = -PL/8."""
        assert self.diag.M(self.L) == pytest.approx(-self.P * self.L / 8, rel=1e-4)

    def test_momento_centro(self):
        """M(L/2) = +PL/8."""
        assert self.diag.M(self.L / 2) == pytest.approx(self.P * self.L / 8, rel=1e-4)

    def test_cortante_izquierdo(self):
        """V justo antes del centro (x=L/2-) = P/2."""
        x_antes = self.L / 2 - 1e-4
        assert self.diag.V(x_antes) == pytest.approx(self.P / 2, rel=1e-3)

    def test_cortante_derecho(self):
        """V justo después del centro (x=L/2+) = -P/2."""
        x_despues = self.L / 2 + 1e-4
        assert self.diag.V(x_despues) == pytest.approx(-self.P / 2, rel=1e-3)

    def test_reaccion_vertical(self):
        """R_A = R_B = P/2 hacia arriba (negativo en TERNA Y+ abajo)."""
        for nudo in [1, 2]:
            Rx, Ry, Mz = self.resultado.reacciones_finales[nudo]
            assert Ry == pytest.approx(-self.P / 2, rel=1e-4)


class TestVigaSimpApoyada:
    """
    Viga simplemente apoyada (ApoyoFijo + Rodillo) con q uniforme.

    Estructura isostática (GH=0). La MD resuelve directamente.

    Solución analítica:
        M_max = qL²/8 en el centro
        M_extremos = 0 (sin restricción de rotación)
        R_A = R_B = qL/2
    """

    @pytest.fixture(autouse=True)
    def setup(self, acero, seccion_rect):
        self.L = 6.0
        self.q = 10.0
        modelo = ModeloEstructural("Simplemente apoyada")
        nA = modelo.agregar_nudo(0.0, 0.0, "A")
        nB = modelo.agregar_nudo(self.L, 0.0, "B")
        barra = modelo.agregar_barra(nA, nB, acero, seccion_rect)
        modelo.asignar_vinculo(nA.id, ApoyoFijo())
        modelo.asignar_vinculo(nB.id, Rodillo())

        carga = CargaDistribuida(barra=barra, q1=self.q, q2=self.q, angulo=+90.0)
        modelo.agregar_carga(carga)

        self.resultado = analizar_estructura_deformaciones(modelo)
        self.barra = barra
        self.diag = self.resultado.diagramas_finales[barra.id]
        self.nudos = {n.id: n for n in modelo.nudos}
        self.reacciones = self.resultado.reacciones_finales

    def test_exitoso(self):
        assert self.resultado.exitoso

    def test_momento_extremos_libres(self):
        """En apoyos simples los momentos extremos son cero."""
        assert self.diag.M(0.0) == pytest.approx(0.0, abs=1e-3)
        assert self.diag.M(self.L) == pytest.approx(0.0, abs=1e-3)

    def test_momento_maximo_centro(self):
        """M_max = qL²/8 en el centro."""
        M_esperado = self.q * self.L**2 / 8
        assert self.diag.M(self.L / 2) == pytest.approx(M_esperado, rel=1e-4)

    def test_reaccion_vertical(self):
        """R_A = R_B = qL/2 (hacia arriba = negativo en Y+)."""
        R_esperada = -self.q * self.L / 2
        for r in self.reacciones.values():
            Rx, Ry, Mz = r
            assert Ry == pytest.approx(R_esperada, rel=1e-4)

    def test_desplazamiento_vertical_nulo_apoyos(self):
        """Los desplazamientos verticales en los apoyos son cero."""
        for nudo in self.nudos.values():
            assert abs(nudo.Uy) < 1e-8


# ===========================================================================
# TESTS — Resortes elásticos en MD
# ===========================================================================

class TestResorteElasticoMD:
    """
    Viga voladizo con resorte vertical en el extremo libre.

    Geometría:
        A (empotramiento, x=0) ——— B (resorte ky, x=L)

    Carga: P vertical (hacia abajo) en B → CargaPuntualNudo(Fy=P).

    Solución analítica (submatriz rigidez libre [v_B, theta_B]):
        K_libre = [[12EI/L³ + ky,  -6EI/L²],
                   [-6EI/L²,         4EI/L ]]
        {P, 0} = K_libre · {d_By, theta_B}
        d_By    = P / (3EI/L³ + ky)
        R_spring = -ky · d_By          (resorte empuja hacia arriba)
        theta_B  = 3P / (2L·(3EI/L³ + ky))
    """

    E = 200e6       # kN/m²
    L = 6.0         # m
    P = 50.0        # kN
    k = 10_000.0    # kN/m  (resorte vertical)

    @pytest.fixture(autouse=True)
    def setup(self):
        from src.domain.entities.seccion import SeccionRectangular

        seccion = SeccionRectangular(nombre="30x50", b=0.30, _h=0.50)
        acero = Material(nombre="Acero", E=self.E)

        m = ModeloEstructural("VoladizoConResorte")
        nA = m.agregar_nudo(0.0, 0.0, "A")
        nB = m.agregar_nudo(self.L, 0.0, "B")
        m.agregar_barra(nA, nB, acero, seccion)
        m.asignar_vinculo(nA.id, Empotramiento())
        m.asignar_vinculo(nB.id, ResorteElastico(ky=self.k))
        m.agregar_carga(CargaPuntualNudo(nudo=nB, Fx=0.0, Fy=self.P, Mz=0.0))

        self.modelo = m
        self.nA = nA
        self.nB = nB
        self.EI = self.E * seccion.Iz
        self.resultado = analizar_estructura_deformaciones(m)

    # --- propiedades del resultado ------------------------------------------

    def test_exitoso(self):
        assert self.resultado.exitoso

    def test_b_en_reacciones(self):
        """El nudo B (resorte) debe aparecer en reacciones_finales."""
        assert self.nB.id in self.resultado.reacciones_finales

    # --- desplazamiento en B ------------------------------------------------

    def test_desplazamiento_vertical_B(self):
        """d_By = P / (3EI/L³ + k)."""
        d_esperado = self.P / (3 * self.EI / self.L**3 + self.k)
        assert self.nB.Uy == pytest.approx(d_esperado, rel=1e-4)

    def test_desplazamiento_A_nulo(self):
        """El empotramiento en A no desplaza."""
        assert abs(self.nA.Ux) < 1e-10
        assert abs(self.nA.Uy) < 1e-10
        assert abs(self.nA.theta_z) < 1e-10

    # --- rotación en B -------------------------------------------------------

    def test_rotacion_B(self):
        """theta_B = 3P / (2L · (3EI/L³ + k))."""
        theta_esperado = 3 * self.P / (2 * self.L * (3 * self.EI / self.L**3 + self.k))
        assert self.nB.theta_z == pytest.approx(theta_esperado, rel=1e-4)

    # --- reacción del resorte -----------------------------------------------

    def test_reaccion_resorte(self):
        """R_spring = -k · d_By (opuesta al desplazamiento, hacia arriba)."""
        d_By = self.nB.Uy
        Ry_esperado = -self.k * d_By
        _, Ry_B, _ = self.resultado.reacciones_finales[self.nB.id]
        assert Ry_B == pytest.approx(Ry_esperado, rel=1e-4)

    def test_reaccion_resorte_negativa(self):
        """El resorte empuja hacia arriba (Ry < 0 en TERNA Y+ abajo)."""
        _, Ry_B, _ = self.resultado.reacciones_finales[self.nB.id]
        assert Ry_B < 0.0

    # --- equilibrio global --------------------------------------------------

    def test_equilibrio_vertical(self):
        """ΣFy = P + R_spring + R_empotramiento = 0."""
        _, Ry_A, _ = self.resultado.reacciones_finales[self.nA.id]
        _, Ry_B, _ = self.resultado.reacciones_finales[self.nB.id]
        assert abs(self.P + Ry_A + Ry_B) < 1e-4

    # --- límites extremos ---------------------------------------------------

    def test_limite_resorte_infinito_voladizo_rigido(self):
        """Para k → ∞ el resorte actúa como rodillo; d_By → 0."""
        from src.domain.entities.seccion import SeccionRectangular

        seccion = SeccionRectangular(nombre="30x50", b=0.30, _h=0.50)
        acero = Material(nombre="Acero", E=self.E)
        k_rigido = 1e12  # Prácticamente infinito

        m = ModeloEstructural("VoladizoResorteRigido")
        nA = m.agregar_nudo(0.0, 0.0, "A")
        nB = m.agregar_nudo(self.L, 0.0, "B")
        m.agregar_barra(nA, nB, acero, seccion)
        m.asignar_vinculo(nA.id, Empotramiento())
        m.asignar_vinculo(nB.id, ResorteElastico(ky=k_rigido))
        m.agregar_carga(CargaPuntualNudo(nudo=nB, Fx=0.0, Fy=self.P, Mz=0.0))

        res = analizar_estructura_deformaciones(m)
        assert res.exitoso
        assert abs(nB.Uy) < 1e-4  # desplazamiento casi nulo

    def test_limite_sin_resorte_es_voladizo(self):
        """Para k → 0 (sin resorte) d_By = PL³/(3EI) (voladizo puro)."""
        from src.domain.entities.seccion import SeccionRectangular

        seccion = SeccionRectangular(nombre="30x50", b=0.30, _h=0.50)
        acero = Material(nombre="Acero", E=self.E)
        EI = self.E * seccion.Iz

        m = ModeloEstructural("VoladizoPuro")
        nA = m.agregar_nudo(0.0, 0.0, "A")
        nB = m.agregar_nudo(self.L, 0.0, "B")
        m.agregar_barra(nA, nB, acero, seccion)
        m.asignar_vinculo(nA.id, Empotramiento())
        # Sin vínculo en B: extremo libre
        m.agregar_carga(CargaPuntualNudo(nudo=nB, Fx=0.0, Fy=self.P, Mz=0.0))

        res = analizar_estructura_deformaciones(m)
        assert res.exitoso
        d_voladizo = self.P * self.L**3 / (3 * EI)
        assert nB.Uy == pytest.approx(d_voladizo, rel=1e-3)


class TestResorteElasticoNumeradorGDL:
    """Verifica que NumeradorGDL trate los resortes correctamente."""

    def test_resorte_no_en_restringidos(self):
        """Un GDL con resorte NO debe estar en indices_restringidos."""
        from src.domain.entities.seccion import SeccionRectangular

        acero = Material(nombre="Acero", E=200e6)
        seccion = SeccionRectangular(nombre="30x50", b=0.30, _h=0.50)

        m = ModeloEstructural("Test")
        nA = m.agregar_nudo(0.0, 0.0, "A")
        nB = m.agregar_nudo(6.0, 0.0, "B")
        m.agregar_barra(nA, nB, acero, seccion)
        m.asignar_vinculo(nA.id, Empotramiento())
        m.asignar_vinculo(nB.id, ResorteElastico(ky=1000.0))

        num = NumeradorGDL(m)
        num.numerar()

        gdl_B = num.gdl_map[nB.id]
        gdl_Uy_B = gdl_B[1]  # offset 1 = Uy

        assert gdl_Uy_B not in num.indices_restringidos

    def test_resorte_en_gdl_resorte_map(self):
        """El GDL con resorte debe estar en gdl_resorte_map con k correcto."""
        from src.domain.entities.seccion import SeccionRectangular

        k = 5000.0
        acero = Material(nombre="Acero", E=200e6)
        seccion = SeccionRectangular(nombre="30x50", b=0.30, _h=0.50)

        m = ModeloEstructural("Test")
        nA = m.agregar_nudo(0.0, 0.0, "A")
        nB = m.agregar_nudo(6.0, 0.0, "B")
        m.agregar_barra(nA, nB, acero, seccion)
        m.asignar_vinculo(nA.id, Empotramiento())
        m.asignar_vinculo(nB.id, ResorteElastico(ky=k))

        num = NumeradorGDL(m)
        num.numerar()

        gdl_B = num.gdl_map[nB.id]
        gdl_Uy_B = gdl_B[1]

        assert gdl_Uy_B in num.gdl_resorte_map
        assert num.gdl_resorte_map[gdl_Uy_B] == pytest.approx(k)

    def test_resorte_rotacional(self):
        """ResorteElastico con ktheta registra GDL de rotacion."""
        from src.domain.entities.seccion import SeccionRectangular

        ktheta = 8000.0
        acero = Material(nombre="Acero", E=200e6)
        seccion = SeccionRectangular(nombre="30x50", b=0.30, _h=0.50)

        m = ModeloEstructural("Test")
        nA = m.agregar_nudo(0.0, 0.0, "A")
        nB = m.agregar_nudo(6.0, 0.0, "B")
        m.agregar_barra(nA, nB, acero, seccion)
        m.asignar_vinculo(nA.id, Empotramiento())
        m.asignar_vinculo(nB.id, ResorteElastico(ktheta=ktheta))

        num = NumeradorGDL(m)
        num.numerar()

        gdl_B = num.gdl_map[nB.id]
        gdl_theta_B = gdl_B[2]

        assert gdl_theta_B not in num.indices_restringidos
        assert gdl_theta_B in num.gdl_resorte_map
        assert num.gdl_resorte_map[gdl_theta_B] == pytest.approx(ktheta)
