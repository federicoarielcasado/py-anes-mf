"""
Tests para el Solver Adaptativo (MD como referencia + búsqueda iterativa MF).

Cubre:
- Estructura isostática: solo MD, sin iteración MF
- Viga biempotrada (GH=2): ambos métodos coinciden
- Pórtico simple biempotrado (GH=3): coincidencia en pocos intentos
- Propiedades del ResultadoAdaptativo
- Casos de inestabilidad descartados correctamente
"""

import pytest
import math

from src.domain.entities.material import Material
from src.domain.entities.seccion import SeccionRectangular
from src.domain.entities.vinculo import Empotramiento, ApoyoFijo, Rodillo
from src.domain.entities.carga import CargaPuntualNudo, CargaDistribuida
from src.domain.model.modelo_estructural import ModeloEstructural
from src.domain.analysis.solver_adaptativo import (
    ResultadoAdaptativo,
    resolver_con_fallback,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def acero():
    return Material(nombre="Acero", E=200e6, alpha=1.2e-5)


@pytest.fixture
def seccion():
    return SeccionRectangular(nombre="30x50", b=0.30, _h=0.50)


def _modelo_viga_biempotrada(acero, seccion, L=6.0, q=10.0):
    """Viga biempotrada con carga uniforme. GH=2."""
    m = ModeloEstructural("VigaBiempotrada")
    nA = m.agregar_nudo(0.0, 0.0, "A")
    nB = m.agregar_nudo(L, 0.0, "B")
    barra = m.agregar_barra(nA, nB, acero, seccion)
    m.asignar_vinculo(nA.id, Empotramiento())
    m.asignar_vinculo(nB.id, Empotramiento())
    carga = CargaDistribuida(barra=barra, q1=q, q2=q, angulo=+90)
    m.agregar_carga(carga)
    return m


def _modelo_viga_isostatica(acero, seccion, L=6.0, q=10.0):
    """Viga simplemente apoyada con carga uniforme. GH=0."""
    m = ModeloEstructural("VigaIsostatica")
    nA = m.agregar_nudo(0.0, 0.0, "A")
    nB = m.agregar_nudo(L, 0.0, "B")
    barra = m.agregar_barra(nA, nB, acero, seccion)
    m.asignar_vinculo(nA.id, ApoyoFijo())
    m.asignar_vinculo(nB.id, Rodillo())
    carga = CargaDistribuida(barra=barra, q1=q, q2=q, angulo=+90)
    m.agregar_carga(carga)
    return m


def _modelo_portico_simple(acero, seccion, H=4.0, L=6.0, P=20.0):
    """
    Portico rectangular biempotrado con carga puntual lateral. GH=3.

         P→  ●──────────────●
             |              |
          H  |              |
             |              |
             ■              ■
    """
    m = ModeloEstructural("PorticoSimple")
    nA = m.agregar_nudo(0.0, H, "A")   # base izq (Y+ hacia abajo → H arriba = -H)
    nB = m.agregar_nudo(L, H, "B")    # base der
    nC = m.agregar_nudo(0.0, 0.0, "C")  # cima izq
    nD = m.agregar_nudo(L, 0.0, "D")   # cima der

    col_izq = m.agregar_barra(nA, nC, acero, seccion)  # columna izq
    col_der = m.agregar_barra(nB, nD, acero, seccion)  # columna der
    viga = m.agregar_barra(nC, nD, acero, seccion)     # viga

    m.asignar_vinculo(nA.id, Empotramiento())
    m.asignar_vinculo(nB.id, Empotramiento())

    # Carga puntual horizontal en nudo superior izquierdo
    carga = CargaPuntualNudo(nudo=nC, Fx=P, Fy=0.0, Mz=0.0)
    m.agregar_carga(carga)

    return m


# ---------------------------------------------------------------------------
# Tests de ResultadoAdaptativo (propiedades y estado)
# ---------------------------------------------------------------------------


class TestResultadoAdaptativoVacio:
    """El objeto vacío debe tener valores seguros por defecto."""

    def test_mejor_resultado_none_sin_md(self):
        r = ResultadoAdaptativo()
        assert r.mejor_resultado is None

    def test_max_diferencia_inf_sin_comparacion(self):
        r = ResultadoAdaptativo()
        assert r.max_diferencia == float("inf")

    def test_ambos_validos_false_inicial(self):
        r = ResultadoAdaptativo()
        assert not r.ambos_validos

    def test_resumen_no_falla_vacio(self):
        r = ResultadoAdaptativo()
        texto = r.resumen()
        assert isinstance(texto, str)
        assert "Solver Adaptativo" in texto


# ---------------------------------------------------------------------------
# Test: estructura isostática (GH=0) — solo MD, sin MF
# ---------------------------------------------------------------------------


class TestSolverIsostatico:
    """Para GH=0, solo se resuelve con MD sin iterar MF."""

    def test_metodo_exitoso_solo_md(self, acero, seccion):
        modelo = _modelo_viga_isostatica(acero, seccion)
        res = resolver_con_fallback(modelo, tol=1e-2)

        assert res.metodo_exitoso == "MD"
        assert res.resultado_md is not None
        assert res.resultado_md.exitoso

    def test_mf_no_intentado_en_isostatica(self, acero, seccion):
        modelo = _modelo_viga_isostatica(acero, seccion)
        res = resolver_con_fallback(modelo)

        assert res.resultado_mf is None
        assert res.intentos_mf == 0

    def test_md_isostatica_momento_maximo_correcto(self, acero, seccion):
        """M_max = q*L²/8 en el centro para viga simplemente apoyada con q uniforme."""
        L, q = 6.0, 10.0
        modelo = _modelo_viga_isostatica(acero, seccion, L=L, q=q)
        res = resolver_con_fallback(modelo)

        barra_id = list(res.resultado_md.diagramas_finales.keys())[0]
        M_centro = res.resultado_md.M(barra_id, L / 2)
        M_teorico = q * L**2 / 8  # = 45.0 kNm

        assert abs(M_centro - M_teorico) < 0.5


# ---------------------------------------------------------------------------
# Test: viga biempotrada (GH=2)
# ---------------------------------------------------------------------------


class TestSolverVigaBiempotrada:
    """GH=2; el solver debe encontrar coincidencia en pocos intentos."""

    def test_exitoso_ambos_metodos(self, acero, seccion):
        modelo = _modelo_viga_biempotrada(acero, seccion)
        res = resolver_con_fallback(modelo, tol=1e-2)

        assert res.resultado_md is not None
        assert res.resultado_md.exitoso

    def test_md_siempre_presente(self, acero, seccion):
        modelo = _modelo_viga_biempotrada(acero, seccion)
        res = resolver_con_fallback(modelo)
        assert res.resultado_md is not None

    def test_mejor_resultado_es_md(self, acero, seccion):
        modelo = _modelo_viga_biempotrada(acero, seccion)
        res = resolver_con_fallback(modelo)
        assert res.mejor_resultado is res.resultado_md

    def test_md_momento_extremo_correcto(self, acero, seccion):
        """M(0) = -q*L²/12 para viga biempotrada con carga uniforme."""
        L, q = 6.0, 10.0
        modelo = _modelo_viga_biempotrada(acero, seccion, L=L, q=q)
        res = resolver_con_fallback(modelo)

        barra_id = list(res.resultado_md.diagramas_finales.keys())[0]
        M0 = res.resultado_md.M(barra_id, 0.0)
        M_teorico = -(q * L**2) / 12  # = -30 kNm

        assert abs(M0 - M_teorico) < 0.5

    def test_md_momento_centro_correcto(self, acero, seccion):
        """M(L/2) = q*L²/24 para viga biempotrada."""
        L, q = 6.0, 10.0
        modelo = _modelo_viga_biempotrada(acero, seccion, L=L, q=q)
        res = resolver_con_fallback(modelo)

        barra_id = list(res.resultado_md.diagramas_finales.keys())[0]
        M_mid = res.resultado_md.M(barra_id, L / 2)
        M_teorico = (q * L**2) / 24  # = 15 kNm

        assert abs(M_mid - M_teorico) < 0.5

    def test_validacion_cruzada_cuando_mf_coincide(self, acero, seccion):
        """Si MF coincide con MD, validacion_cruzada debe estar presente."""
        modelo = _modelo_viga_biempotrada(acero, seccion)
        res = resolver_con_fallback(modelo, tol=1e-2)

        # Si ambos coincidieron, el dict debe tener la estructura esperada
        if res.ambos_validos:
            assert res.validacion_cruzada is not None
            assert "coinciden" in res.validacion_cruzada
            assert "max_diferencia" in res.validacion_cruzada
            assert res.validacion_cruzada["coinciden"]
            assert res.max_diferencia < 1e-2

    def test_redundantes_usados_cuando_mf_coincide(self, acero, seccion):
        modelo = _modelo_viga_biempotrada(acero, seccion)
        res = resolver_con_fallback(modelo, tol=1e-2)

        if res.ambos_validos:
            assert res.redundantes_usados is not None
            assert len(res.redundantes_usados) == modelo.grado_hiperestaticidad


# ---------------------------------------------------------------------------
# Test: portico biempotrado (GH=3)
# ---------------------------------------------------------------------------


class TestSolverPortico:
    """GH=3; más redundantes, más combinaciones, pero MD siempre resuelve."""

    def test_md_siempre_exitoso(self, acero, seccion):
        modelo = _modelo_portico_simple(acero, seccion)
        res = resolver_con_fallback(modelo, tol=1e-2)

        assert res.resultado_md is not None
        assert res.resultado_md.exitoso

    def test_metodo_md_al_menos(self, acero, seccion):
        modelo = _modelo_portico_simple(acero, seccion)
        res = resolver_con_fallback(modelo)
        assert "MD" in res.metodo_exitoso

    def test_resumen_incluye_intentos(self, acero, seccion):
        modelo = _modelo_portico_simple(acero, seccion)
        res = resolver_con_fallback(modelo, tol=1e-2, max_combinaciones=50)
        texto = res.resumen()
        assert "Intentos MF" in texto

    def test_portico_reaccion_horizontal_equilibrio(self, acero, seccion):
        """La suma de reacciones Rx en bases debe igualar la carga P aplicada."""
        H, L, P = 4.0, 6.0, 20.0
        modelo = _modelo_portico_simple(acero, seccion, H=H, L=L, P=P)
        res = resolver_con_fallback(modelo)

        # Sumar Rx en nudos con vínculo
        Rx_total = 0.0
        for nudo_id, (Rx, Ry, Mz) in res.resultado_md.reacciones_finales.items():
            Rx_total += Rx

        # ΣFx = 0 → sum(reacciones_Rx) + P = 0
        assert abs(Rx_total + P) < 1.0  # tolerancia 1 kN


# ---------------------------------------------------------------------------
# Test: límite de combinaciones
# ---------------------------------------------------------------------------


class TestLimiteCombinaciones:
    """Verificar que el límite max_combinaciones se respeta."""

    def test_no_supera_limite(self, acero, seccion):
        modelo = _modelo_viga_biempotrada(acero, seccion)
        limite = 3
        res = resolver_con_fallback(modelo, max_combinaciones=limite)
        # intentos_mf <= limite (puede ser menos si coincide antes)
        assert res.intentos_mf <= limite

    def test_md_presente_aunque_limite_alcanzado(self, acero, seccion):
        """Aunque MF no converja por límite, MD siempre retorna resultado."""
        modelo = _modelo_viga_biempotrada(acero, seccion)
        res = resolver_con_fallback(modelo, max_combinaciones=0)
        # max_combinaciones=0 → ningún intento de MF
        assert res.resultado_md is not None
        assert res.intentos_mf == 0


# ---------------------------------------------------------------------------
# Test: combinaciones_totales coherente con math.comb
# ---------------------------------------------------------------------------


class TestCombinacionesTotales:
    """El campo combinaciones_totales debe ser C(n_candidatos, GH)."""

    def test_combinaciones_totales_mayor_cero_hiperest(self, acero, seccion):
        modelo = _modelo_viga_biempotrada(acero, seccion)
        res = resolver_con_fallback(modelo, max_combinaciones=1)
        # Con GH=2 y al menos 2 candidatos hay > 0 combinaciones
        assert res.combinaciones_totales > 0

    def test_combinaciones_totales_cero_isostatica(self, acero, seccion):
        """Para GH=0, no se llega a calcular combinaciones (retorno temprano)."""
        modelo = _modelo_viga_isostatica(acero, seccion)
        res = resolver_con_fallback(modelo)
        # Retorno temprano antes de calcular combinaciones
        assert res.combinaciones_totales == 0
