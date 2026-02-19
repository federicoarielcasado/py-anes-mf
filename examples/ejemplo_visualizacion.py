"""
Ejemplo de visualización de diagramas de esfuerzos.

Resuelve una viga biempotrada con carga puntual y muestra los diagramas.
"""

import matplotlib.pyplot as plt

from src.domain.entities.material import Material
from src.domain.entities.seccion import SeccionPerfil
from src.domain.entities.vinculo import Empotramiento
from src.domain.entities.carga import CargaPuntualBarra
from src.domain.model.modelo_estructural import ModeloEstructural
from src.domain.analysis.motor_fuerzas import analizar_estructura
from src.ui.visualization.diagramas import graficar_diagramas_combinados

# Crear modelo: viga biempotrada de 6m con carga central de 10 kN
print("=" * 60)
print("EJEMPLO: Viga Biempotrada con Carga Puntual Central")
print("=" * 60)

modelo = ModeloEstructural("Viga biempotrada")

# Material
acero = Material(nombre="Acero A-36", E=200e6, alpha=1.2e-5, nu=0.3)

# Sección
ipe220 = SeccionPerfil(nombre="IPE 220", _A=33.4e-4, _Iz=2772e-8, _h=0.220)

# Crear nudos
nA = modelo.agregar_nudo(0.0, 0.0, "A")
nB = modelo.agregar_nudo(6.0, 0.0, "B")

# Crear barra
barra = modelo.agregar_barra(nA, nB, acero, ipe220, "Viga principal")

# Aplicar empotramientos
modelo.asignar_vinculo(nA.id, Empotramiento())
modelo.asignar_vinculo(nB.id, Empotramiento())

# Aplicar carga puntual central: P = 10 kN hacia abajo
carga = CargaPuntualBarra(
    barra=barra,
    P=10.0,  # kN
    a=3.0,   # Centro (L/2)
    angulo=+90,  # Hacia abajo
)
modelo.agregar_carga(carga)

print(f"\nModelo creado:")
print(f"  - Longitud: {barra.L:.2f} m")
print(f"  - Grado de hiperestaticidad: {modelo.grado_hiperestaticidad}")
print(f"  - Carga: {carga.P:.1f} kN en x = {carga.a:.1f} m")

# Resolver
print(f"\nResolviendo...")
resultado = analizar_estructura(modelo)

if resultado.exitoso:
    print(f"OK - Analisis exitoso")
    print(f"\nRedundantes resueltos:")
    for i, red in enumerate(resultado.redundantes):
        print(f"  X{i+1} ({red.descripcion}): {resultado.valores_X[i]:.3f}")

    print(f"\nMomentos en puntos clave:")
    print(f"  M(0)   = {resultado.M(barra.id, 0.0):+.3f} kNm")
    print(f"  M(L/2) = {resultado.M(barra.id, 3.0):+.3f} kNm")
    print(f"  M(L)   = {resultado.M(barra.id, 6.0):+.3f} kNm")

    print(f"\nValores teoricos:")
    print(f"  M(0)   = +7.500 kNm")
    print(f"  M(L/2) = -7.500 kNm")
    print(f"  M(L)   = +7.500 kNm")

    # Visualizar
    print(f"\nGenerando graficos...")
    fig, axes = graficar_diagramas_combinados(
        modelo,
        resultado,
        n_puntos=51,
        mostrar_valores=True,
        titulo_general=f"Viga Biempotrada - L={barra.L:.0f}m, P={carga.P:.0f}kN"
    )

    print(f"Mostrando graficos (cierra la ventana para continuar)...")
    plt.show()

    # Guardar imagen
    output_file = "ejemplo_diagramas.png"
    fig.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nGrafico guardado en: {output_file}")

else:
    print(f"ERROR - Analisis fallido:")
    for error in resultado.errores:
        print(f"  - {error}")
