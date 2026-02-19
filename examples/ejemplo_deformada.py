"""
Ejemplo de visualización de deformada exagerada.

Resuelve una viga biempotrada y muestra la deformada.
"""

import matplotlib
matplotlib.use('Agg')  # Backend sin GUI para ejecución automática
import matplotlib.pyplot as plt

from src.domain.entities.material import Material
from src.domain.entities.seccion import SeccionPerfil
from src.domain.entities.vinculo import Empotramiento
from src.domain.entities.carga import CargaPuntualBarra
from src.domain.model.modelo_estructural import ModeloEstructural
from src.domain.analysis.motor_fuerzas import analizar_estructura
from src.ui.visualization.deformada import graficar_deformada, graficar_comparacion_deformadas

print("=" * 60)
print("EJEMPLO: Deformada de Viga Biempotrada")
print("=" * 60)

# Crear modelo
modelo = ModeloEstructural("Viga biempotrada")

# Material y sección
acero = Material(nombre="Acero A-36", E=200e6, alpha=1.2e-5, nu=0.3)
ipe220 = SeccionPerfil(nombre="IPE 220", _A=33.4e-4, _Iz=2772e-8, _h=0.220)

# Nudos y barra
nA = modelo.agregar_nudo(0.0, 0.0, "A")
nB = modelo.agregar_nudo(6.0, 0.0, "B")
barra = modelo.agregar_barra(nA, nB, acero, ipe220, "Viga")

# Empotramientos
modelo.asignar_vinculo(nA.id, Empotramiento())
modelo.asignar_vinculo(nB.id, Empotramiento())

# Carga puntual central
carga = CargaPuntualBarra(barra=barra, P=10.0, a=3.0, angulo=+90)
modelo.agregar_carga(carga)

print(f"\nModelo:")
print(f"  Longitud: {barra.L:.1f} m")
print(f"  Carga: {carga.P:.1f} kN en x = {carga.a:.1f} m")
print(f"  GH: {modelo.grado_hiperestaticidad}")

# Resolver
print(f"\nResolviendo...")
resultado = analizar_estructura(modelo)

if resultado.exitoso:
    print(f"OK - Analisis exitoso")

    # Graficar deformada única con escala automática
    print(f"\nGenerando deformada con escala automatica...")
    fig1, ax1 = graficar_deformada(modelo, resultado)
    fig1.savefig("ejemplo_deformada_auto.png", dpi=300, bbox_inches='tight')
    print(f"Guardado: ejemplo_deformada_auto.png")

    # Graficar comparación con diferentes escalas
    print(f"\nGenerando comparacion de escalas...")
    fig2, axes2 = graficar_comparacion_deformadas(
        modelo, resultado,
        factores=[100, 500, 1000],
        n_puntos=31
    )
    fig2.savefig("ejemplo_deformada_comparacion.png", dpi=300, bbox_inches='tight')
    print(f"Guardado: ejemplo_deformada_comparacion.png")

    print(f"\nOK - Graficos generados exitosamente")

else:
    print(f"ERROR - Analisis fallido:")
    for error in resultado.errores:
        print(f"  - {error}")
