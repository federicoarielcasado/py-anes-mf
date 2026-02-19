"""
Ejemplo de análisis con movimientos impuestos.

Demuestra 3 casos: hundimiento en viga continua, hundimiento en biempotrada,
y rotación prescrita.
"""

import matplotlib
matplotlib.use('Agg')

from src.domain.entities.material import Material
from src.domain.entities.seccion import SeccionPerfil
from src.domain.entities.vinculo import Empotramiento, ApoyoFijo
from src.domain.entities.carga import MovimientoImpuesto
from src.domain.model.modelo_estructural import ModeloEstructural
from src.domain.analysis.motor_fuerzas import MotorMetodoFuerzas

print("="*70)
print("EJEMPLOS DE MOVIMIENTOS IMPUESTOS")
print("="*70)

# Material y sección comunes
acero = Material(nombre="Acero", E=200e6)
ipe220 = SeccionPerfil(nombre="IPE 220", _A=33.4e-4, _Iz=2772e-8, _h=0.220)

# =============================================================================
# CASO 1: Viga continua con hundimiento del apoyo central
# =============================================================================
print("\n--- CASO 1: Viga continua - hundimiento apoyo B ---")

modelo1 = ModeloEstructural("Viga continua")
nA = modelo1.agregar_nudo(0.0, 0.0, "A")
nB = modelo1.agregar_nudo(6.0, 0.0, "B")
nC = modelo1.agregar_nudo(12.0, 0.0, "C")
modelo1.agregar_barra(nA, nB, acero, ipe220)
modelo1.agregar_barra(nB, nC, acero, ipe220)
modelo1.asignar_vinculo(nA.id, Empotramiento())
modelo1.asignar_vinculo(nB.id, ApoyoFijo())
modelo1.asignar_vinculo(nC.id, ApoyoFijo())

# Hundimiento de 10mm en B
mov1 = MovimientoImpuesto(nudo=nB, delta_y=-0.010)
modelo1.agregar_carga(mov1)

motor1 = MotorMetodoFuerzas(modelo1)
res1 = motor1.resolver()

print(f"  GH = {res1.grado_hiperestaticidad}")
print(f"  Hundimiento B: {mov1.delta_y*1000:.1f} mm")
print("  Reacciones:")
for nudo_id, (Rx, Ry, Mz) in res1.reacciones_finales.items():
    nudo = modelo1.obtener_nudo(nudo_id)
    print(f"    {nudo.nombre}: Ry={Ry:+8.2f} kN, Mz={Mz:+8.2f} kNm")

# =============================================================================
# CASO 2: Viga biempotrada con hundimiento en extremo
# =============================================================================
print("\n--- CASO 2: Viga biempotrada - hundimiento extremo B ---")

modelo2 = ModeloEstructural("Viga biempotrada")
nA2 = modelo2.agregar_nudo(0.0, 0.0, "A")
nB2 = modelo2.agregar_nudo(6.0, 0.0, "B")
modelo2.agregar_barra(nA2, nB2, acero, ipe220)
modelo2.asignar_vinculo(nA2.id, Empotramiento())
modelo2.asignar_vinculo(nB2.id, Empotramiento())

# Hundimiento de 8mm en B
mov2 = MovimientoImpuesto(nudo=nB2, delta_y=-0.008)
modelo2.agregar_carga(mov2)

motor2 = MotorMetodoFuerzas(modelo2)
res2 = motor2.resolver()

print(f"  GH = {res2.grado_hiperestaticidad}")
print(f"  Hundimiento B: {mov2.delta_y*1000:.1f} mm")
print("  Reacciones:")
for nudo_id, (Rx, Ry, Mz) in res2.reacciones_finales.items():
    nudo = modelo2.obtener_nudo(nudo_id)
    print(f"    {nudo.nombre}: Ry={Ry:+8.2f} kN, Mz={Mz:+8.2f} kNm")

# =============================================================================
# CASO 3: Viga biempotrada con rotación prescrita
# =============================================================================
print("\n--- CASO 3: Viga biempotrada - rotación extremo B ---")

modelo3 = ModeloEstructural("Rotación prescrita")
nA3 = modelo3.agregar_nudo(0.0, 0.0, "A")
nB3 = modelo3.agregar_nudo(6.0, 0.0, "B")
modelo3.agregar_barra(nA3, nB3, acero, ipe220)
modelo3.asignar_vinculo(nA3.id, Empotramiento())
modelo3.asignar_vinculo(nB3.id, Empotramiento())

# Rotación de 0.002 rad en B
mov3 = MovimientoImpuesto(nudo=nB3, delta_theta=0.002)
modelo3.agregar_carga(mov3)

motor3 = MotorMetodoFuerzas(modelo3)
res3 = motor3.resolver()

print(f"  GH = {res3.grado_hiperestaticidad}")
print(f"  Rotación B: {mov3.delta_theta:.4f} rad ({mov3.delta_theta*180/3.14159:.3f}°)")
print("  Reacciones:")
for nudo_id, (Rx, Ry, Mz) in res3.reacciones_finales.items():
    nudo = modelo3.obtener_nudo(nudo_id)
    print(f"    {nudo.nombre}: Ry={Ry:+8.2f} kN, Mz={Mz:+8.2f} kNm")

print("\n" + "="*70)
print("ANÁLISIS COMPLETADO")
print("="*70)
