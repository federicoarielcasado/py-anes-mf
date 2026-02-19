# ARQUITECTURA DEL PROYECTO - py-anes-mf

## ESTRUCTURA DE DIRECTORIOS

```
py-anes-mf/
├── src/
│   ├── main.py                          # Punto de entrada de la aplicación
│   ├── domain/                          # Lógica de negocio
│   │   ├── entities/                    # Entidades del modelo
│   │   │   ├── nudo.py                  # Clase Nudo
│   │   │   ├── barra.py                 # Clase Barra
│   │   │   ├── material.py              # Clase Material
│   │   │   ├── seccion.py               # Clases Seccion (abstracta), SeccionRectangular, etc.
│   │   │   ├── vinculo.py               # Clases Vinculo (abstracta), Empotramiento, ApoyoFijo, Rodillo
│   │   │   └── carga.py                 # Clases Carga, CargaPuntualNudo, CargaPuntualBarra, CargaDistribuida
│   │   ├── mechanics/                   # Mecánica estructural
│   │   │   ├── equilibrio.py            # Cálculo de reacciones, equilibrio estático
│   │   │   └── esfuerzos.py             # Cálculo de esfuerzos internos (N, V, M)
│   │   ├── analysis/                    # Motor de análisis
│   │   │   ├── motor_fuerzas.py         # Motor principal del Método de las Fuerzas
│   │   │   ├── subestructuras.py        # Generación de subestructuras (fundamental, Xi)
│   │   │   ├── redundantes.py           # Selección de redundantes
│   │   │   ├── trabajos_virtuales.py    # Cálculo de coeficientes fij, e0i
│   │   │   └── sece_solver.py           # Resolución del SECE
│   │   └── model/                       # Modelo de datos
│   │       └── modelo_estructural.py    # Clase ModeloEstructural (contenedor)
│   ├── gui/                             # Interfaz gráfica (PyQt6)
│   │   ├── main_window.py               # Ventana principal
│   │   ├── canvas/
│   │   │   └── structure_canvas.py      # Canvas para dibujar estructura
│   │   ├── widgets/
│   │   │   ├── properties_panel.py      # Panel de propiedades
│   │   │   └── results_panel.py         # Panel de resultados
│   │   └── dialogs/
│   │       ├── carga_dialog.py          # Diálogo para crear cargas
│   │       └── redundantes_dialog.py    # Diálogo para seleccionar redundantes
│   ├── data/                            # Datos predefinidos
│   │   ├── materials_db.py              # Base de datos de materiales
│   │   └── sections_db.py               # Base de datos de secciones
│   └── utils/                           # Utilidades
│       ├── constants.py                 # Constantes del proyecto
│       └── integration.py               # Métodos de integración numérica
├── tests/                               # Tests
│   └── test_reacciones_simple.py        # Test de validación de reacciones
└── Informacion adicional/               # PDFs con teoría
```

---

## FLUJO DE EJECUCIÓN DE LA APLICACIÓN

### 1. INICIO DE LA APLICACIÓN
```
main.py → MainWindow.__init__()
```

**Archivos:**
- `src/main.py`: Crea QApplication y MainWindow
- `src/gui/main_window.py`: Ventana principal

**Elementos creados:**
- `self.modelo`: Instancia de `ModeloEstructural`
- `self.canvas`: Canvas para dibujar
- `self.properties_panel`: Panel de propiedades
- `self.results_panel`: Panel de resultados

---

### 2. CREACIÓN DEL MODELO

**Usuario crea nudos:**
```
MainWindow._on_crear_nudo()
  → modelo.agregar_nudo(x, y)
    → Nudo(id, x, y)
```

**Usuario crea barras:**
```
MainWindow._on_crear_barra()
  → modelo.agregar_barra(nudo_i, nudo_j, material, seccion)
    → Barra(nudo_i, nudo_j, material, seccion)
      → Calcula: L, angulo
```

**Usuario aplica vínculos:**
```
MainWindow._on_aplicar_vinculo()
  → nudo.vinculo = Empotramiento(nudo_id)  # o ApoyoFijo, Rodillo
```

**Usuario aplica cargas:**
```
MainWindow._on_crear_carga()
  → CargaDialog.exec()
    → modelo.agregar_carga(carga)
      → CargaPuntualBarra(barra, P, a, angulo)
```

---

### 3. RESOLUCIÓN (F5 o botón "Resolver")

```
MainWindow._on_resolver()
  ↓
  [Verificar GH]
  ↓
  [Si GH > 0: seleccionar redundantes]
    → RedundantesDialog.exec()
      → modelo.redundantes_seleccionados = [X1, X2, ...]
  ↓
  [Ejecutar análisis]
    → motor = MotorMetodoFuerzas(modelo)
      → motor.resolver()
  ↓
  [Mostrar resultados]
    → results_panel.mostrar_resultado(resultado)
```

**Detalle del motor.resolver():**
```python
MotorMetodoFuerzas.resolver()
  ↓
  1. calcular_grado_hiperestaticidad()
  ↓
  2. generar_subestructuras()
     ├─ generar_fundamental()
     │   └─ resolver_reacciones_isostatica()  # ← AQUÍ SE USA equilibrio.py
     ├─ generar_Xi(1)
     │   └─ resolver_reacciones_isostatica()
     └─ generar_Xi(2)
         └─ resolver_reacciones_isostatica()
  ↓
  3. calcular_esfuerzos()
     └─ calcular_esfuerzos_viga_isostatica()  # ← esfuerzos.py
  ↓
  4. calcular_coeficientes_flexibilidad()
     └─ CalculadorFlexibilidad.calcular()
         ├─ _calcular_fij(i, j)  # Integración numérica
         └─ _calcular_e0i(i)
  ↓
  5. resolver_sece()
     └─ np.linalg.solve([F], {e0})  # Obtiene {X}
  ↓
  6. calcular_resultados_finales()
     ├─ M_final = M0 + Σ Xi × Mi
     ├─ V_final = V0 + Σ Xi × Vi
     └─ N_final = N0 + Σ Xi × Ni
  ↓
  7. Retorna ResultadoAnalisis con:
     - reacciones_finales
     - diagramas_finales
     - redundantes_resueltos
```

---

## CLASES PRINCIPALES Y SUS RELACIONES

### ENTIDADES

```python
ModeloEstructural
  ├─ nudos: List[Nudo]
  ├─ barras: List[Barra]
  ├─ cargas: List[Carga]
  ├─ materiales: List[Material]
  └─ secciones: List[Seccion]

Nudo
  ├─ id: int
  ├─ x, y: float
  ├─ vinculo: Optional[Vinculo]
  └─ Propiedades: nombre, Ux, Uy, theta_z

Barra
  ├─ id: int
  ├─ nudo_i, nudo_j: Nudo
  ├─ material: Material
  ├─ seccion: Seccion
  ├─ L: float  # Calculado automáticamente
  ├─ angulo: float  # Calculado automáticamente
  └─ Métodos: local_a_global(), matriz_transformacion()

Vinculo (abstracta)
  ├─ Empotramiento: restringe [Ux, Uy, θz]
  ├─ ApoyoFijo: restringe [Ux, Uy]
  └─ Rodillo: restringe [Ux] o [Uy]

Carga (abstracta)
  ├─ CargaPuntualNudo: aplicada directamente en nudo
  ├─ CargaPuntualBarra: P, a, angulo
  └─ CargaDistribuida: q1, q2, tipo
```

### MOTOR DE ANÁLISIS

```python
MotorMetodoFuerzas
  ├─ modelo: ModeloEstructural
  ├─ fundamental: Subestructura
  ├─ subestructuras_xi: List[Subestructura]
  ├─ matriz_F: NDArray
  ├─ vector_e0: NDArray
  └─ solucion_X: NDArray

Subestructura
  ├─ nombre: str  # "Fundamental", "X1", "X2", ...
  ├─ nudos: List[Nudo]
  ├─ barras: List[Barra]
  ├─ cargas: List[Carga]
  ├─ reacciones: Dict[int, Tuple[Rx, Ry, Mz]]
  └─ diagramas: Dict[int, Diagrama]

CalculadorFlexibilidad
  ├─ fundamental: Subestructura
  ├─ subestructuras_xi: List[Subestructura]
  └─ calcular() → CoeficientesFlexibilidad
      ├─ F: matriz de flexibilidad
      └─ e0: vector de términos independientes
```

---

## FUNCIONES CLAVE

### src/domain/mechanics/equilibrio.py

```python
def momento_fuerza_respecto_punto(Fx, Fy, x_fuerza, y_fuerza, x_punto, y_punto) -> float
    """
    FÓRMULA: M = -Fy × (x_punto - x_fuerza) + Fx × (y_punto - y_fuerza)
    TERNA: X+ derecha, Y+ abajo, rotación horaria +
    """

def resolver_reacciones_isostatica(nudos, barras, cargas) -> Reacciones
    """
    Resuelve reacciones de estructura ISOSTÁTICA usando:
    - ΣFx = 0
    - ΣFy = 0
    - ΣMz = 0

    Construye sistema [A]{R} = {b} y resuelve con numpy.linalg.solve

    IMPORTANTE:
    - Calcula Fx_total, Fy_total, Mz_total DIRECTAMENTE de las cargas
    - No usa fuerzas nodales equivalentes
    - b = [-Fx_total, -Fy_total, -Mz_total]
    """

def verificar_equilibrio_global(nudos, cargas, reacciones, barras) -> (bool, Dict)
    """
    Verifica que reacciones + cargas cumplan equilibrio.
    Retorna (cumple, {ΣFx, ΣFy, ΣMz})
    """
```

### src/domain/mechanics/esfuerzos.py

```python
def calcular_esfuerzos_viga_isostatica(barra, cargas_barra, reacciones) -> Diagrama
    """
    Calcula N(x), V(x), M(x) usando MÉTODO DE SECCIONES.

    Regla para M(x):
    - Cortar en x
    - Mirar a la IZQUIERDA
    - Sumar momentos respecto al corte
    - Fuerza ARRIBA (Y-) a izq → momento HORARIO (+)
    - Fuerza ABAJO (Y+) a izq → momento ANTIHORARIO (-)
    """
```

### src/domain/analysis/trabajos_virtuales.py

```python
class CalculadorFlexibilidad:
    def _calcular_fij(i, j) -> float:
        """
        fij = ∫₀ᴸ [M̄i(x) × M̄j(x)] / (EI) dx
        Usa integración numérica (Simpson)
        """

    def _calcular_e0i(i) -> float:
        """
        e0i = ∫₀ᴸ [M̄i(x) × M₀(x)] / (EI) dx
        """
```

---

## CONVENCIÓN DE SIGNOS (TERNA)

**CRÍTICO - USADA EN TODO EL PROYECTO:**

```
TERNA GLOBAL:
- X+ → derecha
- Y+ → abajo
- Rotación+ → horaria (sentido agujas del reloj)

FUERZAS:
- Fx > 0: hacia derecha
- Fy > 0: hacia abajo
- Fy < 0: hacia arriba

MOMENTOS:
- M > 0: horario ⟳
- M < 0: antihorario ⟲

CARGAS EN BARRAS:
- angulo = 0°: en dirección de la barra (i→j)
- angulo = +90°: perpendicular HORARIO (abajo en barra horizontal)
- angulo = -90°: perpendicular ANTIHORARIO (arriba en barra horizontal)
```

---

## RESPUESTA A TU PREGUNTA

**"Si ahora abro la aplicación y cargo una estructura como la que estamos trabajando, ¿veré correctamente las reacciones?"**

**RESPUESTA:** **Probablemente SÍ**, porque:

1. ✅ La GUI llama a `motor.resolver()` cuando presionas F5
2. ✅ `motor.resolver()` usa `resolver_reacciones_isostatica()` que acabamos de corregir
3. ✅ Los resultados se guardan en `resultado.reacciones_finales`
4. ✅ `results_panel.mostrar_resultado()` lee `reacciones_finales` y los muestra en la tabla

**PERO hay que verificar:**
- Que el ángulo de las cargas se esté creando correctamente en el diálogo de cargas
- Que no haya código antiguo en el motor que esté usando funciones desactualizadas

**RECOMENDACIÓN:** Ejecutar la aplicación y probar con el caso simple para confirmar.

---

## ARCHIVOS QUE MODIFICAMOS HOY

1. **src/domain/mechanics/equilibrio.py**
   - ✅ Agregada función `momento_fuerza_respecto_punto()`
   - ✅ Corregido cálculo de Mz_total (usa posición REAL de cargas, no fuerzas nodales)
   - ✅ Corregida matriz A para usar NUESTRA terna

2. **src/domain/entities/carga.py**
   - ✅ Corregido comentario sobre ángulos (+90° = abajo, -90° = arriba)

3. **test_reacciones_simple.py**
   - ✅ Creado test que valida reacciones con ángulo correcto (+90°)

---

## PRÓXIMOS PASOS

1. Ejecutar la aplicación GUI y probar caso simple
2. Verificar que el diálogo de cargas permita crear ángulo +90°
3. Verificar que los diagramas M(x) se calculen correctamente
4. Implementar casos GH=1, GH=2, GH=3 completos
