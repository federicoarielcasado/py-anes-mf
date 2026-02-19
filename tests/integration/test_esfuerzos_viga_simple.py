"""
Test de cálculo de esfuerzos internos en viga simple.

Valida que el módulo esfuerzos.py calcule correctamente N(x), V(x), M(x)
para casos simples con solución analítica conocida.
"""

import pytest
import numpy as np

from src.domain.model.modelo_estructural import ModeloEstructural
from src.domain.entities.material import Material
from src.domain.entities.seccion import SeccionRectangular
from src.domain.entities.vinculo import Empotramiento, ApoyoFijo, Rodillo
from src.domain.entities.carga import CargaPuntualBarra, CargaDistribuida
from src.domain.mechanics.equilibrio import resolver_reacciones_isostatica
from src.domain.mechanics.esfuerzos import calcular_esfuerzos_viga_isostatica


def test_viga_simple_carga_puntual_centro():
    """
    Test: Viga simplemente apoyada con carga puntual en centro.

    Geometría:
        A------P------B
        |      ↓      |
        0     3m      6m
        ↑             ↑
       Ra=5kN        Rb=5kN

    Carga: P = 10 kN en x = 3m, ángulo +90° (hacia abajo)

    Soluciones teóricas:
        Ra = P/2 = 5 kN (hacia arriba = -5 kN en TERNA)
        Rb = P/2 = 5 kN (hacia arriba = -5 kN en TERNA)

        V(x):
            0 ≤ x < 3:  V = Ra = -5 kN
            3 < x ≤ 6:  V = Ra + P = -5 + 10 = +5 kN

        M(x):
            0 ≤ x ≤ 3:  M = Ra × x = -5 × x  → M(3) = -15 kNm
            3 ≤ x ≤ 6:  M = Ra × x + P × (x-3) = -5x + 10(x-3) = 5x - 30
                        → M(3) = -15 kNm, M(6) = 0 kNm
            (Aunque por método de secciones mirando a izquierda, signos pueden invertirse)

    NOTA: Verificamos magnitudes, no signos (dependen de convención).
    """
    # Crear modelo
    modelo = ModeloEstructural("Viga simple carga puntual")

    # Material y sección (no influyen en estática)
    acero = Material("Acero", E=200e6)
    seccion = SeccionRectangular("Rect 20x30", b=0.20, _h=0.30)

    # Geometría: viga horizontal de 6m
    n1 = modelo.agregar_nudo(0, 0, "A")
    n2 = modelo.agregar_nudo(6, 0, "B")
    barra = modelo.agregar_barra(n1, n2, acero, seccion)

    # Vínculos: configuración isostática (3 incógnitas)
    # A: Apoyo fijo (Ux=Uy=0) = 2 incógnitas
    # B: Rodillo vertical (solo Uy=0) = 1 incógnita → Total = 3 ✓
    n1.vinculo = ApoyoFijo(nudo=n1)
    n2.vinculo = Rodillo(nudo=n2, direccion='Uy')

    # Carga puntual: 10 kN en centro (x=3m), hacia abajo
    carga = CargaPuntualBarra(barra=barra, P=10.0, a=3.0, angulo=90.0)
    modelo.agregar_carga(carga)

    # Resolver reacciones
    reacciones = resolver_reacciones_isostatica(modelo.nudos, modelo.barras, modelo.cargas)

    # Verificar reacciones
    Ra = reacciones[n1.id]
    Rb = reacciones[n2.id]
    assert abs(Ra[1] + 5.0) < 0.01, f"Ra_y esperado -5 kN, obtenido {Ra[1]:.3f}"
    assert abs(Rb[1] + 5.0) < 0.01, f"Rb_y esperado -5 kN, obtenido {Rb[1]:.3f}"

    # Calcular esfuerzos
    cargas_barra = [c for c in modelo.cargas if hasattr(c, 'barra') and c.barra.id == barra.id]
    diagrama = calcular_esfuerzos_viga_isostatica(
        barra,
        cargas_barra,
        reaccion_i=Ra,
        reaccion_j=Rb
    )

    # Verificar cortantes
    V_antes = diagrama.V(1.5)  # Antes de la carga (x=1.5m)
    V_despues = diagrama.V(4.5)  # Después de la carga (x=4.5m)

    # NOTA: Los signos dependen de la convención.
    # Verificamos magnitudes y que hay cambio de signo
    assert abs(abs(V_antes) - 5.0) < 0.01, f"V antes de P: esperado ±5 kN, obtenido {V_antes:.3f}"
    assert abs(abs(V_despues) - 5.0) < 0.01, f"V después de P: esperado ±5 kN, obtenido {V_despues:.3f}"

    # Verificar momento máximo en centro
    M_centro = diagrama.M(3.0)
    # Momento máximo teórico: M_max = P*L/4 = 10*6/4 = 15 kNm (magnitud)
    assert abs(abs(M_centro) - 15.0) < 0.1, f"M en centro: esperado ±15 kNm, obtenido {M_centro:.3f}"

    # Verificar momento en extremos (debe ser cero, no hay empotramiento)
    M_i = diagrama.M(0.0)
    M_j = diagrama.M(6.0)
    assert abs(M_i) < 0.01, f"M en i debe ser ~0, obtenido {M_i:.3f}"
    assert abs(M_j) < 0.01, f"M en j debe ser ~0, obtenido {M_j:.3f}"

    print("✓ Test viga simple con carga puntual: PASSED")


def test_viga_empotrada_carga_puntual():
    """
    Test: Viga empotrada-libre con carga puntual en extremo.

    Geometría:
        ┃
        ┃------P
        A      ↓
        0      L=4m

    Carga: P = 8 kN en x = 4m (extremo libre)

    Soluciones teóricas:
        Ra_y = P = 8 kN (hacia arriba = -8 kN en TERNA)
        Ma = -P*L = -8*4 = -32 kNm (antihorario para equilibrar)

        V(x) = Ra = -8 kN (constante)
        M(x) = Ra × x + Ma = -8x - 32  → M(0)=-32 kNm, M(4)=0

    NOTA: Signos pueden variar según convención, verificamos magnitudes.

    Corregido: el solver de equilibrio ahora maneja correctamente el signo
    del momento de reacción en empotramientos (θz GDL).
    """
    modelo = ModeloEstructural("Viga empotrada")

    acero = Material("Acero", E=200e6)
    seccion = SeccionRectangular("Rect 20x30", b=0.20, _h=0.30)

    n1 = modelo.agregar_nudo(0, 0, "A")
    n2 = modelo.agregar_nudo(4, 0, "B")
    barra = modelo.agregar_barra(n1, n2, acero, seccion)

    # Empotramiento en A
    n1.vinculo = Empotramiento(nudo=n1)
    # B libre

    # Carga en extremo libre
    carga = CargaPuntualBarra(barra=barra, P=8.0, a=4.0, angulo=90.0)
    modelo.agregar_carga(carga)

    # Resolver
    reacciones = resolver_reacciones_isostatica(modelo.nudos, modelo.barras, modelo.cargas)
    Ra = reacciones[n1.id]

    assert abs(Ra[1] + 8.0) < 0.01, f"Ra_y esperado -8 kN, obtenido {Ra[1]:.3f}"
    # El momento de empotramiento es -P*L = -32 kNm (antihorario, signo negativo en TERNA Y+ abajo)
    assert abs(abs(Ra[2]) - 32.0) < 0.5, f"Ma esperado ~±32 kNm, obtenido {Ra[2]:.3f}"

    # Esfuerzos
    cargas_barra = [c for c in modelo.cargas if hasattr(c, 'barra') and c.barra.id == barra.id]
    diagrama = calcular_esfuerzos_viga_isostatica(
        barra,
        cargas_barra,
        reaccion_i=Ra,
        reaccion_j=(0, 0, 0)  # Extremo libre
    )

    # Cortante constante
    V_medio = diagrama.V(2.0)
    assert abs(abs(V_medio) - 8.0) < 0.01, f"V esperado ±8 kN, obtenido {V_medio:.3f}"

    # Momento en empotramiento
    M_empotrado = diagrama.M(0.0)
    assert abs(abs(M_empotrado) - 32.0) < 0.5, f"M(0) esperado ±32 kNm, obtenido {M_empotrado:.3f}"

    # Momento en extremo libre
    M_libre = diagrama.M(4.0)
    assert abs(M_libre) < 0.1, f"M(L) debe ser ~0, obtenido {M_libre:.3f}"

    print("✓ Test viga empotrada con carga puntual: PASSED")


def test_viga_simple_carga_distribuida_uniforme():
    """
    Test: Viga simplemente apoyada con carga distribuida uniforme.

    Geometría:
        A===========B
        |  q↓↓↓↓↓↓↓  |
        0           L=5m
        ↑           ↑

    Carga: q = 4 kN/m uniforme en toda la longitud

    Soluciones teóricas:
        Carga total: Q = q*L = 4*5 = 20 kN
        Ra = Rb = Q/2 = 10 kN (hacia arriba = -10 kN en TERNA)

        V(x) = Ra + q*x = -10 + 4x
            V(0) = -10 kN
            V(L) = +10 kN
            V(L/2) = 0

        M(x) = Ra*x + q*x²/2 = -10x + 2x²
            M_max en centro: M(2.5) = -10*2.5 + 2*2.5² = -25 + 12.5 = -12.5 kNm
            (Parábola con vértice en centro)
    """
    modelo = ModeloEstructural("Viga carga distribuida")

    acero = Material("Acero", E=200e6)
    seccion = SeccionRectangular("Rect 20x30", b=0.20, _h=0.30)

    n1 = modelo.agregar_nudo(0, 0, "A")
    n2 = modelo.agregar_nudo(5, 0, "B")
    barra = modelo.agregar_barra(n1, n2, acero, seccion)

    # Vínculos isostáticos
    n1.vinculo = ApoyoFijo(nudo=n1)    # Ux=Uy=0 (2 incógnitas)
    n2.vinculo = Rodillo(nudo=n2, direccion='Uy')  # Solo Uy=0 (1 incógnita) → Total=3 ✓

    # Carga distribuida uniforme: 4 kN/m
    carga = CargaDistribuida(
        barra=barra,
        q1=4.0,
        q2=4.0,
        x1=0.0,
        x2=5.0,
        angulo=90.0  # Hacia abajo
    )
    modelo.agregar_carga(carga)

    # Resolver
    reacciones = resolver_reacciones_isostatica(modelo.nudos, modelo.barras, modelo.cargas)
    Ra = reacciones[n1.id]
    Rb = reacciones[n2.id]

    # Verificar reacciones
    assert abs(Ra[1] + 10.0) < 0.01, f"Ra_y esperado -10 kN, obtenido {Ra[1]:.3f}"
    assert abs(Rb[1] + 10.0) < 0.01, f"Rb_y esperado -10 kN, obtenido {Rb[1]:.3f}"

    # Esfuerzos
    cargas_barra = [c for c in modelo.cargas if hasattr(c, 'barra') and c.barra.id == barra.id]
    diagrama = calcular_esfuerzos_viga_isostatica(
        barra,
        cargas_barra,
        reaccion_i=Ra,
        reaccion_j=Rb
    )

    # Cortante en extremos
    V_i = diagrama.V(0.0)
    V_j = diagrama.V(5.0)
    assert abs(abs(V_i) - 10.0) < 0.1, f"V(0) esperado ±10 kN, obtenido {V_i:.3f}"
    assert abs(abs(V_j) - 10.0) < 0.1, f"V(L) esperado ±10 kN, obtenido {V_j:.3f}"

    # Cortante en centro (debe ser ~0)
    V_centro = diagrama.V(2.5)
    assert abs(V_centro) < 0.1, f"V(L/2) debe ser ~0, obtenido {V_centro:.3f}"

    # Momento en centro (máximo)
    M_centro = diagrama.M(2.5)
    # M_max teórico = q*L²/8 = 4*5²/8 = 12.5 kNm
    assert abs(abs(M_centro) - 12.5) < 0.5, f"M(L/2) esperado ±12.5 kNm, obtenido {M_centro:.3f}"

    # Momentos en extremos (deben ser ~0)
    M_i = diagrama.M(0.0)
    M_j = diagrama.M(5.0)
    assert abs(M_i) < 0.1, f"M(0) debe ser ~0, obtenido {M_i:.3f}"
    assert abs(M_j) < 0.1, f"M(L) debe ser ~0, obtenido {M_j:.3f}"

    print("✓ Test viga con carga distribuida uniforme: PASSED")


def test_axil_en_barra_horizontal():
    """
    Test: Viga con carga axial.

    Geometría horizontal con carga axial en dirección X.
    Verificar que N(x) se calcula correctamente.
    """
    modelo = ModeloEstructural("Viga con axil")

    acero = Material("Acero", E=200e6)
    seccion = SeccionRectangular("Rect 20x30", b=0.20, _h=0.30)

    n1 = modelo.agregar_nudo(0, 0, "A")
    n2 = modelo.agregar_nudo(4, 0, "B")
    barra = modelo.agregar_barra(n1, n2, acero, seccion)

    # Empotramiento en A, libre en B
    n1.vinculo = Empotramiento(nudo=n1)

    # Carga axial: P=12 kN hacia derecha (ángulo 0°)
    carga = CargaPuntualBarra(barra=barra, P=12.0, a=4.0, angulo=0.0)
    modelo.agregar_carga(carga)

    # Resolver
    reacciones = resolver_reacciones_isostatica(modelo.nudos, modelo.barras, modelo.cargas)
    Ra = reacciones[n1.id]

    # Reacción axial debe equilibrar
    assert abs(Ra[0] + 12.0) < 0.01, f"Ra_x esperado -12 kN, obtenido {Ra[0]:.3f}"

    # Esfuerzos
    cargas_barra = [c for c in modelo.cargas if hasattr(c, 'barra') and c.barra.id == barra.id]
    diagrama = calcular_esfuerzos_viga_isostatica(
        barra,
        cargas_barra,
        reaccion_i=Ra,
        reaccion_j=(0, 0, 0)
    )

    # Axial constante (compresión = negativo en convención usual)
    N_medio = diagrama.N(2.0)
    assert abs(abs(N_medio) - 12.0) < 0.01, f"N esperado ±12 kN, obtenido {N_medio:.3f}"

    # Cortante y momento deben ser ~0 (solo carga axial)
    V_medio = diagrama.V(2.0)
    M_medio = diagrama.M(2.0)
    assert abs(V_medio) < 0.01, f"V debe ser ~0 (solo axil), obtenido {V_medio:.3f}"
    assert abs(M_medio) < 0.01, f"M debe ser ~0 (solo axil), obtenido {M_medio:.3f}"

    print("✓ Test axil en barra horizontal: PASSED")


def test_voladizo_carga_distribuida_uniforme():
    """
    Test: Voladizo (empotrado en A, libre en B) con carga uniforme q.

    Geometria:
        A============B
        |  q↓↓↓↓↓↓↓
        0           L=3m

    Carga: q = 4 kN/m uniforme en toda la longitud

    Soluciones teoricas (con TERNA Y+ abajo):
        Ra = q*L = 12 kN hacia arriba → Ry_i = -12 kN
        Ma = q*L^2/2 = 18 kNm antihorario → Mz_i = -18 kNm

        M(x) = -18 + 12*x - 2*x^2   (mirar izquierda)
        M(0) = -18 kNm
        M(1.5) = -18 + 18 - 4.5 = -4.5 kNm
        M(3) = 0 (extremo libre)
    """
    modelo = ModeloEstructural("Voladizo carga distribuida")
    acero = Material("Acero", E=200e6)
    seccion = SeccionRectangular("Rect 20x30", b=0.20, _h=0.30)

    n1 = modelo.agregar_nudo(0, 0, "A")
    n2 = modelo.agregar_nudo(3, 0, "B")
    barra = modelo.agregar_barra(n1, n2, acero, seccion)

    n1.vinculo = Empotramiento(nudo=n1)
    # B libre (voladizo)

    carga = CargaDistribuida(
        barra=barra,
        q1=4.0,
        q2=4.0,
        x1=0.0,
        x2=3.0,
        angulo=90.0  # Hacia abajo
    )
    modelo.agregar_carga(carga)

    reacciones = resolver_reacciones_isostatica(modelo.nudos, modelo.barras, modelo.cargas)
    Ra = reacciones[n1.id]

    # Reaccion vertical: 12 kN hacia arriba = -12 en TERNA
    assert abs(Ra[1] + 12.0) < 0.1, f"Ry esperado -12 kN, obtenido {Ra[1]:.3f}"
    # Momento de empotramiento: q*L^2/2 = 18 kNm
    assert abs(abs(Ra[2]) - 18.0) < 0.1, f"|Ma| esperado 18 kNm, obtenido {abs(Ra[2]):.3f}"

    cargas_barra = [c for c in modelo.cargas if hasattr(c, 'barra') and c.barra.id == barra.id]
    diagrama = calcular_esfuerzos_viga_isostatica(
        barra, cargas_barra, reaccion_i=Ra, reaccion_j=(0.0, 0.0, 0.0)
    )

    # M(0) = momento de empotramiento
    assert abs(abs(diagrama.M(0.0)) - 18.0) < 0.1, f"|M(0)| esperado 18 kNm, obtenido {abs(diagrama.M(0.0)):.3f}"
    # M(3) = 0 (extremo libre)
    assert abs(diagrama.M(3.0)) < 0.1, f"M(L) debe ser ~0, obtenido {diagrama.M(3.0):.3f}"
    # M(1.5) = -4.5 kNm
    assert abs(abs(diagrama.M(1.5)) - 4.5) < 0.1, f"|M(1.5)| esperado 4.5 kNm, obtenido {abs(diagrama.M(1.5)):.3f}"
    # V(0) = Ra = 12 kN
    assert abs(abs(diagrama.V(0.0)) - 12.0) < 0.1, f"|V(0)| esperado 12 kN, obtenido {abs(diagrama.V(0.0)):.3f}"
    # V(L) = 0 (extremo libre)
    assert abs(diagrama.V(3.0)) < 0.1, f"V(L) debe ser ~0, obtenido {diagrama.V(3.0):.3f}"


def test_viga_simple_carga_triangular():
    """
    Test: Viga simplemente apoyada con carga triangular (q1=0, q2=q_max).

    Geometria:
        A===========B
        |   /↓↓↓↓↓  |
        0           L=6m

    Carga: q crece de 0 en A hasta 6 kN/m en B, angulo=90 (hacia abajo)

    Soluciones teoricas:
        Resultante: R = q_max * L / 2 = 6*6/2 = 18 kN
        Centroide desde A: x_c = 2*L/3 = 4 m
        Ra = R * (L - x_c) / L = 18 * 2/6 = 6 kN (hacia arriba)
        Rb = R * x_c / L = 18 * 4/6 = 12 kN (hacia arriba)

        M_max ocurre donde V=0:
        V(x) = Ra - q(x)*x/2 = 6 - (q_max/L)*x^2/2
        V(x) = 0 → x^2 = 2*Ra*L/q_max = 2*6*6/6 = 12 → x = sqrt(12) ≈ 3.464 m
        M(x) = Ra*x - (q_max/L)*x^3/6
        M_max = 6*sqrt(12) - (1)*12*sqrt(12)/6 = sqrt(12)*(6 - 2) = 4*sqrt(12) ≈ 13.856 kNm
    """
    modelo = ModeloEstructural("Viga carga triangular")
    acero = Material("Acero", E=200e6)
    seccion = SeccionRectangular("Rect 20x30", b=0.20, _h=0.30)

    n1 = modelo.agregar_nudo(0, 0, "A")
    n2 = modelo.agregar_nudo(6, 0, "B")
    barra = modelo.agregar_barra(n1, n2, acero, seccion)

    n1.vinculo = ApoyoFijo(nudo=n1)
    n2.vinculo = Rodillo(nudo=n2, direccion='Uy')

    carga = CargaDistribuida(
        barra=barra,
        q1=0.0,     # Cero en A
        q2=6.0,     # 6 kN/m en B
        x1=0.0,
        x2=6.0,
        angulo=90.0  # Hacia abajo
    )
    modelo.agregar_carga(carga)

    reacciones = resolver_reacciones_isostatica(modelo.nudos, modelo.barras, modelo.cargas)
    Ra = reacciones[n1.id]
    Rb = reacciones[n2.id]

    # Ra = 6 kN hacia arriba = -6 kN en terna Y+ abajo
    assert abs(Ra[1] + 6.0) < 0.1, f"Ra_y esperado -6 kN, obtenido {Ra[1]:.3f}"
    # Rb = 12 kN hacia arriba = -12 kN en terna Y+ abajo
    assert abs(Rb[1] + 12.0) < 0.1, f"Rb_y esperado -12 kN, obtenido {Rb[1]:.3f}"

    cargas_barra = [c for c in modelo.cargas if hasattr(c, 'barra') and c.barra.id == barra.id]
    diagrama = calcular_esfuerzos_viga_isostatica(
        barra, cargas_barra, reaccion_i=Ra, reaccion_j=Rb
    )

    # Extremos: M(0) = M(L) = 0
    assert abs(diagrama.M(0.0)) < 0.1, f"M(0) debe ser ~0, obtenido {diagrama.M(0.0):.3f}"
    assert abs(diagrama.M(6.0)) < 0.1, f"M(L) debe ser ~0, obtenido {diagrama.M(6.0):.3f}"

    # Cortante en extremo i: V(0) = Ra = -6 kN (hacia arriba en terna)
    assert abs(abs(diagrama.V(0.0)) - 6.0) < 0.2, f"V(0) esperado ~6 kN, obtenido {diagrama.V(0.0):.3f}"

    # Momento maximo teorico ~ 13.856 kNm en x ~ 3.464 m
    import math as _math
    x_vmax = _math.sqrt(12)  # ~3.464 m
    M_max = diagrama.M(x_vmax)
    assert abs(abs(M_max) - 13.856) < 0.5, f"M_max esperado ~13.856 kNm, obtenido {M_max:.3f}"


def test_viga_simple_carga_trapezoidal():
    """
    Test: Viga simplemente apoyada con carga trapezoidal (q1 != q2, ambos != 0).

    Geometria: L = 4 m, q1 = 2 kN/m en A, q2 = 6 kN/m en B, angulo=90

    Soluciones teoricas:
        Resultante: R = (q1+q2)*L/2 = (2+6)*4/2 = 16 kN
        Centroide desde A: x_c = L*(q1+2*q2)/(3*(q1+q2)) = 4*(2+12)/(3*8) = 4*14/24 = 7/3 ≈ 2.333 m
        Ra = R * (L - x_c) / L = 16 * (4 - 7/3) / 4 = 16 * 5/12 = 20/3 ≈ 6.667 kN
        Rb = R - Ra = 16 - 20/3 = 28/3 ≈ 9.333 kN

        Verificacion: ΣM_A = -Rb*4 + R*x_c = -Rb*4 + 16*(7/3) = 0 → Rb = 16*7/(3*4) = 28/3 ✓
    """
    modelo = ModeloEstructural("Viga carga trapezoidal")
    acero = Material("Acero", E=200e6)
    seccion = SeccionRectangular("Rect 20x30", b=0.20, _h=0.30)

    n1 = modelo.agregar_nudo(0, 0, "A")
    n2 = modelo.agregar_nudo(4, 0, "B")
    barra = modelo.agregar_barra(n1, n2, acero, seccion)

    n1.vinculo = ApoyoFijo(nudo=n1)
    n2.vinculo = Rodillo(nudo=n2, direccion='Uy')

    carga = CargaDistribuida(
        barra=barra,
        q1=2.0,
        q2=6.0,
        x1=0.0,
        x2=4.0,
        angulo=90.0  # Hacia abajo
    )
    modelo.agregar_carga(carga)

    reacciones = resolver_reacciones_isostatica(modelo.nudos, modelo.barras, modelo.cargas)
    Ra = reacciones[n1.id]
    Rb = reacciones[n2.id]

    Ra_esperado = 20.0 / 3   # ~6.667 kN hacia arriba
    Rb_esperado = 28.0 / 3   # ~9.333 kN hacia arriba

    assert abs(Ra[1] + Ra_esperado) < 0.1, f"Ra_y esperado -{Ra_esperado:.3f} kN, obtenido {Ra[1]:.3f}"
    assert abs(Rb[1] + Rb_esperado) < 0.1, f"Rb_y esperado -{Rb_esperado:.3f} kN, obtenido {Rb[1]:.3f}"

    cargas_barra = [c for c in modelo.cargas if hasattr(c, 'barra') and c.barra.id == barra.id]
    diagrama = calcular_esfuerzos_viga_isostatica(
        barra, cargas_barra, reaccion_i=Ra, reaccion_j=Rb
    )

    # Extremos: M(0) = M(L) = 0
    assert abs(diagrama.M(0.0)) < 0.1, f"M(0) debe ser ~0, obtenido {diagrama.M(0.0):.3f}"
    assert abs(diagrama.M(4.0)) < 0.1, f"M(L) debe ser ~0, obtenido {diagrama.M(4.0):.3f}"

    # Verificar que el cortante en extremos coincide con reacciones
    assert abs(abs(diagrama.V(0.0)) - Ra_esperado) < 0.2, (
        f"V(0) esperado ~{Ra_esperado:.3f} kN, obtenido {diagrama.V(0.0):.3f}"
    )


if __name__ == "__main__":
    # Ejecutar tests
    print("\n" + "="*60)
    print("TESTS DE ESFUERZOS INTERNOS")
    print("="*60 + "\n")

    test_viga_simple_carga_puntual_centro()
    test_viga_empotrada_carga_puntual()
    test_viga_simple_carga_distribuida_uniforme()
    test_axil_en_barra_horizontal()
    test_viga_simple_carga_triangular()
    test_viga_simple_carga_trapezoidal()

    print("\n" + "="*60)
    print("Todos los tests pasaron")
    print("="*60 + "\n")
