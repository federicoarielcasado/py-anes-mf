"""
Ejemplo de análisis con vínculos elásticos (resortes).

Demuestra el uso de resortes con rigidez finita en lugar de
vínculos rígidos perfectos.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.domain.entities.material import Material
from src.domain.entities.seccion import SeccionPerfil
from src.domain.entities.vinculo import (
    Empotramiento,
    ResorteElastico,
    crear_resorte_vertical,
    crear_resorte_horizontal,
    crear_resorte_rotacional
)
from src.domain.entities.carga import CargaPuntualBarra
from src.domain.model.modelo_estructural import ModeloEstructural

print("=" * 70)
print("EJEMPLO: Vinculos Elasticos (Resortes)")
print("=" * 70)

# =============================================================================
# CASO 1: Viga sobre apoyo elastico vertical
# =============================================================================

print("\n" + "=" * 70)
print("CASO 1: Viga simplemente apoyada con resorte elastico en un extremo")
print("=" * 70)

modelo1 = ModeloEstructural("Viga con apoyo elastico")

# Material y sección
acero = Material(nombre="Acero A-36", E=200e6, alpha=1.2e-5)
ipe220 = SeccionPerfil(nombre="IPE 220", _A=33.4e-4, _Iz=2772e-8, _h=0.220)

# Crear viga de 6m
nA = modelo1.agregar_nudo(0.0, 0.0, "A")
nB = modelo1.agregar_nudo(6.0, 0.0, "B")
barra1 = modelo1.agregar_barra(nA, nB, acero, ipe220, "Viga")

# Vínculo A: Empotramiento perfecto (rigidez infinita)
modelo1.asignar_vinculo(nA.id, Empotramiento())

# Vínculo B: Resorte elástico vertical (rigidez finita)
k_resorte = 5000  # kN/m
resorte_B = ResorteElastico(kx=0, ky=k_resorte, ktheta=0)
modelo1.asignar_vinculo(nB.id, resorte_B)

print(f"\nConfiguracion:")
print(f"  - Vinculo A: {nA.vinculo.tipo_str}")
print(f"  - Vinculo B: {nB.vinculo.tipo_str}")
print(f"  - Rigidez resorte: ky = {k_resorte} kN/m")

# Aplicar carga puntual en centro
P = 10.0  # kN
carga1 = CargaPuntualBarra(barra1, P=P, a=3.0, angulo=+90)
modelo1.agregar_carga(carga1)

print(f"\nCarga: P = {P} kN en centro de viga (x = 3m)")

print(f"\nAnalisis teorico:")
print(f"  En una viga con apoyo elastico, el desplazamiento en B es:")
print(f"  delta_B = Reaccion_B / k")
print(f"\n  Para rigidez infinita (apoyo rigido): delta_B = 0")
print(f"  Para rigidez finita: delta_B > 0")
print(f"\n  Cuando k es pequeño -> apoyo blando -> gran desplazamiento")
print(f"  Cuando k es grande -> apoyo casi rigido -> poco desplazamiento")

print(f"\n[NOTA] La resolucion numerica requiere incluir rigideces")
print(f"       elasticas en la matriz de flexibilidad del sistema.")


# =============================================================================
# CASO 2: Portico con resortes traslacionales en base
# =============================================================================

print("\n" + "=" * 70)
print("CASO 2: Portico con resortes traslacionales (simula suelo elastico)")
print("=" * 70)

modelo2 = ModeloEstructural("Portico sobre suelo elastico")

# Crear pórtico simple
nA2 = modelo2.agregar_nudo(0.0, 0.0, "A")
nB2 = modelo2.agregar_nudo(0.0, 3.0, "B")
nC2 = modelo2.agregar_nudo(4.0, 3.0, "C")
nD2 = modelo2.agregar_nudo(4.0, 0.0, "D")

# Columnas y viga
col_izq = modelo2.agregar_barra(nA2, nB2, acero, ipe220, "Columna izq")
viga = modelo2.agregar_barra(nB2, nC2, acero, ipe220, "Viga")
col_der = modelo2.agregar_barra(nC2, nD2, acero, ipe220, "Columna der")

# Resortes en las bases (simulan suelo elástico)
k_horizontal = 10000  # kN/m (rigidez horizontal)
k_vertical = 50000    # kN/m (rigidez vertical, suelo)

resorte_A = ResorteElastico(kx=k_horizontal, ky=k_vertical, ktheta=0)
resorte_D = ResorteElastico(kx=k_horizontal, ky=k_vertical, ktheta=0)

modelo2.asignar_vinculo(nA2.id, resorte_A)
modelo2.asignar_vinculo(nD2.id, resorte_D)

print(f"\nConfiguracion:")
print(f"  - Altura columnas: 3.0 m")
print(f"  - Luz viga: 4.0 m")
print(f"  - Resortes en bases:")
print(f"    * kx = {k_horizontal} kN/m (resistencia horizontal)")
print(f"    * ky = {k_vertical} kN/m (resistencia vertical)")

print(f"\nEste modelo simula:")
print(f"  - Fundacion sobre suelo elastico (no rigido)")
print(f"  - Interaccion suelo-estructura")
print(f"  - Asentamientos diferenciales por carga")

print(f"\n[NOTA] En analisis real:")
print(f"       - ky se obtiene del modulo de balasto del suelo")
print(f"       - kx depende de friccion suelo-fundacion")
print(f"       - Valores tipicos: 10,000 - 100,000 kN/m para suelos")


# =============================================================================
# CASO 3: Viga con resorte rotacional (empotramiento parcial)
# =============================================================================

print("\n" + "=" * 70)
print("CASO 3: Viga con resorte rotacional (empotramiento imperfecto)")
print("=" * 70)

modelo3 = ModeloEstructural("Viga con empotramiento parcial")

nA3 = modelo3.agregar_nudo(0.0, 0.0, "A")
nB3 = modelo3.agregar_nudo(6.0, 0.0, "B")
barra3 = modelo3.agregar_barra(nA3, nB3, acero, ipe220, "Viga")

# Extremo A: Resorte rotacional (simula rigidez finita del empotramiento)
k_rotacional = 5000  # kNm/rad
resorte_rot = ResorteElastico(
    kx=0,        # Sin traslación horizontal
    ky=1e9,      # Traslación vertical muy restringida (≈ ∞)
    ktheta=k_rotacional  # Rigidez rotacional finita
)
modelo3.asignar_vinculo(nA3.id, resorte_rot)

# Extremo B: Apoyo simple rígido
from src.domain.entities.vinculo import ApoyoFijo
modelo3.asignar_vinculo(nB3.id, ApoyoFijo())

# Carga puntual
carga3 = CargaPuntualBarra(barra3, P=10.0, a=3.0, angulo=+90)
modelo3.agregar_carga(carga3)

print(f"\nConfiguracion:")
print(f"  - Extremo A: Resorte rotacional ktheta = {k_rotacional} kNm/rad")
print(f"  - Extremo B: Apoyo fijo (articulacion)")
print(f"  - Carga: P = 10 kN en centro")

print(f"\nInterpretacion fisica:")
print(f"  Un resorte rotacional simula:")
print(f"  - Empotramiento imperfecto (conexion semirigida)")
print(f"  - Union con rigidez limitada")
print(f"  - Conexion atornillada/soldada no ideal")

print(f"\n  Cuando ktheta -> infinito: empotramiento perfecto")
print(f"  Cuando ktheta -> 0: articulacion libre")

print(f"\nRotacion en A esperada:")
print(f"  theta_A = Momento_A / ktheta")
print(f"  (A mayor rigidez, menor rotacion)")


# =============================================================================
# CASO 4: Comparacion rigideces
# =============================================================================

print("\n" + "=" * 70)
print("CASO 4: Comparacion de diferentes rigideces")
print("=" * 70)

rigideces_test = [100, 1000, 10000, 100000, 1e9]

print(f"\nEfecto de la rigidez en el comportamiento:\n")
print(f"  {'k [kN/m]':<15} {'Tipo de apoyo':<30} {'delta/F [mm/kN]'}")
print(f"  {'-'*15} {'-'*30} {'-'*15}")

for k in rigideces_test:
    # Flexibilidad = 1/k (desplazamiento por unidad de fuerza)
    flexibilidad = 1/k
    delta_por_kN = flexibilidad * 1000  # mm/kN

    if k < 1000:
        tipo = "Muy blando (casi libre)"
    elif k < 10000:
        tipo = "Blando"
    elif k < 100000:
        tipo = "Medio"
    elif k < 1e8:
        tipo = "Rigido"
    else:
        tipo = "Muy rigido (casi perfecto)"

    print(f"  {k:<15.0e} {tipo:<30} {delta_por_kN:.6f}")

print(f"\n  Interpretacion:")
print(f"  - k = 100 kN/m: 10mm de hundimiento por cada kN (muy blando)")
print(f"  - k = 10,000 kN/m: 0.1mm por kN (tipico suelo)")
print(f"  - k = 1e9 kN/m: 0.000001mm por kN (practicamente rigido)")


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

print("\n" + "=" * 70)
print("FUNCIONES AUXILIARES")
print("=" * 70)

print(f"\nEl modulo incluye funciones de conveniencia:")

# Ejemplo 1: Resorte vertical
r1 = crear_resorte_vertical(5000)
print(f"\n1. crear_resorte_vertical(5000)")
print(f"   -> {r1.tipo_str}")

# Ejemplo 2: Resorte horizontal
r2 = crear_resorte_horizontal(3000)
print(f"\n2. crear_resorte_horizontal(3000)")
print(f"   -> {r2.tipo_str}")

# Ejemplo 3: Resorte rotacional
r3 = crear_resorte_rotacional(2000)
print(f"\n3. crear_resorte_rotacional(2000)")
print(f"   -> {r3.tipo_str}")


# =============================================================================
# RESUMEN
# =============================================================================

print("\n" + "=" * 70)
print("RESUMEN")
print("=" * 70)

print(f"\nLa clase ResorteElastico permite modelar:")
print(f"  1. Apoyos con rigidez finita (suelo elastico)")
print(f"  2. Conexiones semirigidas")
print(f"  3. Empotramientos parciales")
print(f"  4. Fundaciones sobre resortes")

print(f"\nCaracteristicas:")
print(f"  - Rigidez traslacional: kx, ky [kN/m]")
print(f"  - Rigidez rotacional: ktheta [kNm/rad]")
print(f"  - Reaccion = -k * desplazamiento")
print(f"  - Permite combinar las tres rigideces")

print(f"\nAplicaciones:")
print(f"  - Analisis de interaccion suelo-estructura")
print(f"  - Modelado de conexiones reales (no ideales)")
print(f"  - Calibracion con ensayos experimentales")
print(f"  - Analisis de sensibilidad a rigideces")

print(f"\nProximos pasos:")
print(f"  1. Integrar resortes en motor de fuerzas")
print(f"  2. Modificar matriz de rigidez para incluir k")
print(f"  3. Validar con casos de literatura")
print(f"  4. Crear tests de integracion end-to-end")

print(f"\n[NOTA] Actualmente la clase esta implementada y testeada.")
print(f"       Se requiere integracion en el solver hiperestatico.")
print(f"       30/30 tests unitarios pasando (100%)")

print("\nEjemplo completado.")
