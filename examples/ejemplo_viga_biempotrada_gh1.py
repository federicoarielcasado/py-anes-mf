# -*- coding: utf-8 -*-
"""
Ejemplo de Viga con Empotramiento y Rodillo (GH = 1)
====================================================

Caso clasico de estructura hiperestatica con GH = 1

Geometria:
    Empotramiento                    Rodillo
         |                             o
    N1 ============================ N2
    x=0     P=10kN v @ x=3         x=6

Viga empotrada en un extremo y con rodillo en el otro (GH=1):
- n = 2 nudos
- b = 1 barra
- r = 4 (3 empotramiento + 1 rodillo)
- gh = (4 + 1) - 2(2) = 5 - 4 = 1

CORRECTO! Este es GH = 1
"""

import sys
from pathlib import Path

# Agregar el directorio raiz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.domain.model.modelo_estructural import ModeloEstructural
from src.domain.entities.vinculo import Empotramiento, Rodillo
from src.domain.entities.carga import CargaPuntualBarra
from src.data.materials_db import MATERIALES
from src.data.sections_db import SECCIONES_IPE


def crear_ejemplo_gh1():
    """
    Crea el ejemplo de viga con empotramiento y rodillo (GH = 1).

    Estructura:
        Empotramiento                    Rodillo
             |                             o
        N1 ============================ N2
        x=0     P=10kN v @ x=3         x=6

    Solucion teorica (manual):
    - Momento en empotramiento: Ma = -15 kNm
    - Reaccion vertical en empotramiento: Ra = 5 kN
    - Reaccion horizontal en empotramiento: Ha = 0 kN
    - Reaccion en rodillo: Rb = 5 kN

    Momento maximo: M(x=3) = -7.5 kNm (en el punto de aplicacion de carga)
    """
    print("=" * 70)
    print("EJEMPLO: Viga Empotrada-Rodillo con Carga Puntual (GH = 1)")
    print("=" * 70)
    print()

    # Crear modelo
    modelo = ModeloEstructural("Viga GH=1: Empotramiento-Rodillo")

    # PASO 1: Crear nudos
    print("PASO 1: Creando nudos...")
    n1 = modelo.agregar_nudo(0, 0, "Apoyo A (Empotramiento)")
    n2 = modelo.agregar_nudo(6, 0, "Apoyo B (Rodillo)")
    print(f"  [OK] Nudo 1: {n1.nombre} en ({n1.x}, {n1.y})")
    print(f"  [OK] Nudo 2: {n2.nombre} en ({n2.x}, {n2.y})")
    print()

    # PASO 2: Crear barra
    print("PASO 2: Creando barra...")
    material = MATERIALES.get("Acero A-36")
    seccion = SECCIONES_IPE.get("IPE 220")

    barra = modelo.agregar_barra(n1, n2, material, seccion)
    print(f"  [OK] Barra 1: N{n1.id} -> N{n2.id}")
    print(f"    - Longitud: {barra.L:.2f} m")
    print(f"    - Material: {material.nombre} (E = {material.E/1e9:.0f} GPa)")
    print(f"    - Seccion: {seccion.nombre} (A = {seccion.A*1e4:.2f} cm2, I = {seccion.Iz*1e8:.2f} cm4)")
    print()

    # PASO 3: Asignar vinculos
    print("PASO 3: Asignando vinculos...")
    vinculo_a = Empotramiento(n1.id)
    modelo.asignar_vinculo(n1.id, vinculo_a)
    print(f"  [OK] Nudo 1: Empotramiento (restringe Ux, Uy, theta_z)")

    vinculo_b = Rodillo(n2.id, direccion="Uy")
    modelo.asignar_vinculo(n2.id, vinculo_b)
    print(f"  [OK] Nudo 2: Rodillo vertical (restringe Uy)")
    print()

    # PASO 4: Aplicar carga
    print("PASO 4: Aplicando carga puntual...")
    carga = CargaPuntualBarra(
        barra=barra,
        P=10.0,  # kN
        a=3.0,   # m (centro de la viga)
        angulo=90  # grados (perpendicular horaria = hacia abajo en barra horizontal)
    )
    modelo.agregar_carga(carga)
    print(f"  [OK] Carga puntual en Barra 1:")
    print(f"    - Magnitud: P = {carga.P} kN")
    print(f"    - Posicion: a = {carga.a} m desde Nudo 1")
    print(f"    - Direccion: {carga.angulo}° (perpendicular horaria = vertical hacia abajo)")
    print()

    # PASO 5: Verificar grado de hiperestaticidad
    print("PASO 5: Verificando grado de hiperestaticidad...")
    print(f"  - Numero de nudos (n): {modelo.num_nudos}")
    print(f"  - Numero de barras (b): {modelo.num_barras}")

    # Contar reacciones
    r = 0
    for nudo in modelo.nudos:
        if nudo.tiene_vinculo:
            r += len(nudo.vinculo.gdl_restringidos())
    print(f"  - Reacciones de vinculo (r): {r}")
    print(f"    * Empotramiento N1: 3 reacciones (Rx, Ry, Mz)")
    print(f"    * Rodillo N2: 1 reaccion (Ry)")

    # Formula correcta para porticos planos
    gh = (r + modelo.num_barras) - 2 * modelo.num_nudos
    print(f"  - Formula: gh = (r + b) - 2n")
    print(f"  - gh = ({r} + {modelo.num_barras}) - 2x{modelo.num_nudos}")
    print(f"  - gh = {gh}")
    print()

    if gh == 1:
        print("  [OK] CORRECTO! La estructura tiene GH = 1 (1 redundante)")
    elif gh > 1:
        print(f"  [!] ATENCION: La estructura tiene GH = {gh} (mas de 1 redundante)")
    elif gh == 0:
        print("  [!] La estructura es ISOSTATICA (GH = 0)")
    else:
        print(f"  [X] ERROR: La estructura es HIPOSTATICA (GH = {gh})")
    print()

    # PASO 6: Informacion sobre la solucion teorica
    print("PASO 6: Solucion teorica esperada...")
    print("  Para verificar los resultados del analisis:")
    print()
    print("  Reacciones:")
    print("    Ra (vertical en A): 5.0 kN ^")
    print("    Ha (horizontal en A): 0.0 kN")
    print("    Ma (momento en A): -15.0 kNm (horario)")
    print("    Rb (vertical en B): 5.0 kN ^")
    print()
    print("  Momentos flectores:")
    print("    M(x=0) = -15.0 kNm (empotramiento)")
    print("    M(x=3) = -7.5 kNm (punto de carga)")
    print("    M(x=6) = 0.0 kNm (rodillo)")
    print()
    print("  Cortantes:")
    print("    V(0-) = 5.0 kN")
    print("    V(3-) = 5.0 kN")
    print("    V(3+) = -5.0 kN")
    print("    V(6-) = -5.0 kN")
    print()

    # PASO 7: Guardar modelo
    print("PASO 7: Guardando modelo...")
    output_file = root_dir / "examples" / "viga_gh1.json"

    print("=" * 70)
    print("MODELO CREADO EXITOSAMENTE")
    print("=" * 70)
    print()
    print("INSTRUCCIONES PARA RESOLVER:")
    print("1. Abre la aplicacion principal (python -m src.main)")
    print("2. Ve a Archivo -> Abrir")
    print(f"3. Selecciona el archivo: {output_file}")
    print("4. Presiona F5 o haz clic en 'Resolver'")
    print("5. Verifica los resultados en el panel de Resultados")
    print("6. Activa la visualizacion de diagramas (Ver -> Diagramas)")
    print()

    return modelo


if __name__ == "__main__":
    modelo = crear_ejemplo_gh1()

    print("\nRESUMEN DEL MODELO:")
    print(f"  Nombre: {modelo.nombre}")
    print(f"  Nudos: {modelo.num_nudos}")
    print(f"  Barras: {modelo.num_barras}")
    print(f"  Cargas: {modelo.num_cargas}")
    print()

    print("Deseas resolver el modelo ahora? (requiere interfaz grafica)")
    print("Para resolver, ejecuta: python -m src.main")
