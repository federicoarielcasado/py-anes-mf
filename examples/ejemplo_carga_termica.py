"""
Ejemplo de análisis de carga térmica.

Resuelve una viga biempotrada con variación de temperatura uniforme
y gradiente térmico, mostrando esfuerzos inducidos.
"""

import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt

from src.domain.entities.material import Material
from src.domain.entities.seccion import SeccionRectangular
from src.domain.entities.vinculo import Empotramiento
from src.domain.entities.carga import CargaTermica
from src.domain.model.modelo_estructural import ModeloEstructural
from src.domain.analysis.motor_fuerzas import analizar_estructura

print("=" * 70)
print("EJEMPLO: Viga Biempotrada con Carga Termica")
print("=" * 70)

# =============================================================================
# CASO 1: Variación uniforme de temperatura (ΔT = +30°C)
# =============================================================================

print("\n" + "=" * 70)
print("CASO 1: Variacion uniforme de temperatura DT = +30 grados C")
print("=" * 70)

modelo1 = ModeloEstructural("Viga con DT uniforme")

# Material: Acero con coeficiente de dilatación térmica
acero = Material(
    nombre="Acero A-36",
    E=200e6,      # kN/m²
    alpha=1.2e-5  # 1/°C (coeficiente de dilatación térmica)
)

# Sección rectangular
seccion = SeccionRectangular(
    nombre="30x50cm",
    b=0.30,    # m (ancho)
    _h=0.50    # m (altura)
)

# Crear nudos (viga de 6m)
nA = modelo1.agregar_nudo(0.0, 0.0, "A")
nB = modelo1.agregar_nudo(6.0, 0.0, "B")

# Crear barra
barra1 = modelo1.agregar_barra(nA, nB, acero, seccion, "Viga principal")

# Aplicar empotramientos (impiden expansión libre)
modelo1.asignar_vinculo(nA.id, Empotramiento())
modelo1.asignar_vinculo(nB.id, Empotramiento())

# Aplicar carga térmica uniforme: +30°C
carga_termica = CargaTermica(
    barra=barra1,
    delta_T_uniforme=30.0,  # °C
    delta_T_gradiente=0.0
)
modelo1.agregar_carga(carga_termica)

print(f"\nModelo creado:")
print(f"  - Longitud: {barra1.L:.2f} m")
print(f"  - Grado de hiperestaticidad: {modelo1.grado_hiperestaticidad}")
print(f"  - Carga termica: DT = {carga_termica.delta_T_uniforme:+.1f} grados C")

# Calcular deformación libre (si no hubiera restricciones)
delta_libre = carga_termica.deformacion_axial_libre()
print(f"\nDeformacion axial libre (sin restricciones):")
print(f"  delta = alpha * DT * L = {acero.alpha:.2e} * {carga_termica.delta_T_uniforme} * {barra1.L}")
print(f"  delta = {delta_libre*1000:.3f} mm")

print(f"\nTeoria:")
print(f"  En una viga biempotrada, la expansion termica esta impedida.")
print(f"  Esto genera un esfuerzo axial de compresion:")
print(f"  N = -E * A * alpha * DT")
print(f"  N = -{acero.E/1e6:.0f}e6 * {seccion.A:.4f} * {acero.alpha:.2e} * {carga_termica.delta_T_uniforme}")
N_teorico = -acero.E * seccion.A * acero.alpha * carga_termica.delta_T_uniforme
print(f"  N = {N_teorico:.3f} kN (compresion)")

# NOTA: Para resolver esto correctamente, se necesita implementar la integración
# de cargas térmicas en el motor de fuerzas (cálculo de e₀ᵢ térmicos)
print(f"\n[NOTA] La resolucion numerica requiere implementar la integracion")
print(f"       de trabajos virtuales con efectos termicos en motor_fuerzas.py")


# =============================================================================
# CASO 2: Gradiente térmico (cara superior +20°C, cara inferior 0°C)
# =============================================================================

print("\n" + "=" * 70)
print("CASO 2: Gradiente termico DT_grad = +20 grados C")
print("=" * 70)

modelo2 = ModeloEstructural("Viga con gradiente termico")

# Crear estructura idéntica
nA2 = modelo2.agregar_nudo(0.0, 0.0, "A")
nB2 = modelo2.agregar_nudo(6.0, 0.0, "B")
barra2 = modelo2.agregar_barra(nA2, nB2, acero, seccion, "Viga principal")
modelo2.asignar_vinculo(nA2.id, Empotramiento())
modelo2.asignar_vinculo(nB2.id, Empotramiento())

# Aplicar carga térmica con gradiente
carga_gradiente = CargaTermica(
    barra=barra2,
    delta_T_uniforme=0.0,
    delta_T_gradiente=20.0  # Cara superior +20°C más caliente
)
modelo2.agregar_carga(carga_gradiente)

print(f"\nModelo creado:")
print(f"  - Carga termica: Gradiente = {carga_gradiente.delta_T_gradiente:+.1f} grados C")
print(f"  - Altura de seccion: h = {seccion.h:.2f} m")

# Calcular curvatura térmica libre
curvatura_libre = carga_gradiente.curvatura_termica()
print(f"\nCurvatura termica libre:")
print(f"  kappa = (alpha * DT_grad) / h")
print(f"  kappa = ({acero.alpha:.2e} * {carga_gradiente.delta_T_gradiente}) / {seccion.h}")
print(f"  kappa = {curvatura_libre:.6e} 1/m")

print(f"\nTeoria:")
print(f"  El gradiente termico induce curvatura en la viga.")
print(f"  En una viga biempotrada, esto genera momentos de empotramiento:")
print(f"  M = -E * Iz * kappa")
print(f"  M = -{acero.E/1e6:.0f}e6 * {seccion.Iz:.6e} * {curvatura_libre:.6e}")
M_teorico = -acero.E * seccion.Iz * curvatura_libre
print(f"  M_empotramientos = {M_teorico:.3f} kNm")

print(f"\n[NOTA] La resolucion numerica requiere implementar la integracion")
print(f"       de trabajos virtuales con gradientes termicos.")


# =============================================================================
# CASO 3: Combinación (ΔT uniforme + gradiente)
# =============================================================================

print("\n" + "=" * 70)
print("CASO 3: Combinacion DT_unif=+15 grados C + DT_grad=+10 grados C")
print("=" * 70)

modelo3 = ModeloEstructural("Viga con carga termica combinada")

nA3 = modelo3.agregar_nudo(0.0, 0.0, "A")
nB3 = modelo3.agregar_nudo(6.0, 0.0, "B")
barra3 = modelo3.agregar_barra(nA3, nB3, acero, seccion, "Viga principal")
modelo3.asignar_vinculo(nA3.id, Empotramiento())
modelo3.asignar_vinculo(nB3.id, Empotramiento())

carga_combinada = CargaTermica(
    barra=barra3,
    delta_T_uniforme=15.0,
    delta_T_gradiente=10.0
)
modelo3.agregar_carga(carga_combinada)

print(f"\nModelo creado:")
print(f"  - DT uniforme: {carga_combinada.delta_T_uniforme:+.1f} grados C")
print(f"  - DT gradiente: {carga_combinada.delta_T_gradiente:+.1f} grados C")

delta_axial = carga_combinada.deformacion_axial_libre()
curvatura = carga_combinada.curvatura_termica()

print(f"\nEfectos combinados:")
print(f"  1) Expansion axial libre: {delta_axial*1000:.3f} mm")
print(f"  2) Curvatura termica: {curvatura:.6e} 1/m")
print(f"\nEn estructura hiperestatica:")
print(f"  - La expansion genera axil de compresion")
print(f"  - El gradiente genera momentos de empotramiento")
print(f"  - Ambos efectos se superponen")

print("\n" + "=" * 70)
print("Resumen")
print("=" * 70)
print(f"\nLa clase CargaTermica ha sido implementada exitosamente.")
print(f"\nProximos pasos:")
print(f"  1. Implementar calculo de e0_i termicos en motor_fuerzas.py")
print(f"  2. Modificar trabajo_virtual() para incluir efectos termicos")
print(f"  3. Validar con casos de literatura (Timoshenko, Gere)")
print(f"  4. Crear tests unitarios e integracion")
print(f"\nFormulas implementadas:")
print(f"  - Deformacion axial: delta = alpha * DT * L")
print(f"  - Curvatura termica: kappa = (alpha * DT_grad) / h")
print(f"  - Trabajo virtual uniforme: delta_i = alpha * DT * integral(Ni dx)")
print(f"  - Trabajo virtual gradiente: delta_i = kappa * integral(Mi dx)")

print("\nEjemplo completado.")
