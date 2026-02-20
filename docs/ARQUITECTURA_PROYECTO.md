# ARQUITECTURA DEL PROYECTO — py-anes-mf
**Versión:** 1.3.0 — **Última actualización:** 20 de febrero de 2026

---

## ESTRUCTURA DE DIRECTORIOS

```
py-anes-mf/
├── main.py                              # Punto de entrada (raíz)
├── src/
│   ├── main.py                          # Punto de entrada alternativo
│   ├── domain/                          # Lógica de negocio
│   │   ├── entities/                    # Entidades del modelo
│   │   │   ├── nudo.py                  # Clase Nudo (id, x, y, vinculo)
│   │   │   ├── barra.py                 # Clase Barra (L, angulo, cargas)
│   │   │   ├── material.py              # Clase Material (E, alpha, rho)
│   │   │   ├── seccion.py               # Seccion, SeccionRectangular, IPE, HEA
│   │   │   ├── vinculo.py               # Empotramiento, ApoyoFijo, Rodillo,
│   │   │   │                            #   Guia, ResorteElastico
│   │   │   └── carga.py                 # CargaPuntualNudo, CargaPuntualBarra,
│   │   │                                #   CargaDistribuida, CargaTermica,
│   │   │                                #   MovimientoImpuesto
│   │   ├── mechanics/                   # Mecánica estructural
│   │   │   ├── equilibrio.py            # Reacciones isostáticas, verificación
│   │   │   └── esfuerzos.py             # N(x), V(x), M(x) por barra
│   │   ├── analysis/                    # Motor de análisis
│   │   │   ├── motor_fuerzas.py         # Orquestador del Método de las Fuerzas
│   │   │   ├── subestructuras.py        # Estructura fundamental y Xi
│   │   │   ├── redundantes.py           # Selección automática de redundantes
│   │   │   ├── trabajos_virtuales.py    # fij, e0i (incl. térmicos y resortes)
│   │   │   └── sece_solver.py           # Resolución [F]{X}={e0}
│   │   └── model/                       # Modelo de datos
│   │       └── modelo_estructural.py    # Contenedor principal (nudos, barras,
│   │                                    #   cargas, materiales, secciones)
│   ├── gui/                             # Interfaz gráfica (PyQt6)
│   │   ├── main_window.py               # Ventana principal, menús, toolbar
│   │   ├── canvas/
│   │   │   └── structure_canvas.py      # Canvas interactivo zoom/pan/drag
│   │   ├── widgets/
│   │   │   ├── properties_panel.py      # Panel de propiedades de elementos
│   │   │   └── results_panel.py         # Panel de resultados numéricos
│   │   ├── dialogs/
│   │   │   ├── carga_dialog.py          # Diálogo creación de cargas
│   │   │   └── redundantes_dialog.py    # Diálogo selección de redundantes
│   │   └── history/
│   │       └── undo_redo_manager.py     # Undo/Redo (Ctrl+Z / Ctrl+Y)
│   ├── ui/                              # Visualización científica (matplotlib)
│   │   └── visualization/
│   │       ├── diagramas.py             # Diagramas M, V, N sobre barras
│   │       ├── geometria.py             # Geometría estructural con vínculos
│   │       └── deformada.py             # Deformada elástica (doble integración)
│   ├── data/                            # Catálogos predefinidos
│   │   ├── materials_db.py              # Base de datos de materiales
│   │   ├── sections_db.py               # Base de datos de secciones
│   │   └── proyecto_serializer.py       # Guardar/cargar proyectos JSON
│   └── utils/                           # Utilidades generales
│       ├── constants.py                 # Constantes del proyecto
│       ├── geometry.py                  # Funciones geométricas auxiliares
│       └── integration.py               # Integración numérica (Simpson)
├── tests/                               # Suite de tests (176/176)
│   ├── unit/                            # Tests unitarios por módulo
│   │   ├── test_carga_termica.py        # 20 tests — efectos térmicos
│   │   ├── test_resorte_elastico.py     # 35 tests — vínculos elásticos
│   │   └── test_movimiento_impuesto.py  # Tests — movimientos impuestos
│   ├── integration/                     # Tests de casos clásicos
│   │   ├── test_casos_clasicos.py       # GH=1, GH=2, GH=3 — validación numérica
│   │   └── test_esfuerzos_viga_simple.py
│   └── domain/                          # Tests del modelo de dominio
│       ├── test_entities.py
│       └── test_modelo.py
├── docs/                                # Documentación
│   ├── PLANIFICACION_DESARROLLO.md
│   ├── ARQUITECTURA_PROYECTO.md         # (este archivo)
│   ├── SISTEMA_COORDENADAS_LOCALES.md
│   ├── SELECCION_REDUNDANTES.md
│   └── teoria/
│       ├── NOTAS_CARGAS_TERMICAS.md
│       ├── NOTAS_RESORTES_ELASTICOS.md
│       ├── NOTAS_MOVIMIENTOS_IMPUESTOS.md
│       └── VISUALIZACION.md
├── ejemplo_viga_biempotrada_gh1.py      # Ejemplo ejecutable
├── ejemplo_visualizacion.py             # Ejemplo de diagramas
├── CLAUDE.md                            # Especificación del proyecto
└── requirements.txt
```

---

## FLUJO DE EJECUCIÓN DE LA APLICACIÓN

### 1. INICIO
```
main.py → QApplication → MainWindow.__init__()
  → ModeloEstructural()       # Contenedor vacío
  → StructureCanvas()         # Canvas interactivo
  → PropertiesPanel()         # Panel lateral izquierdo
  → ResultsPanel()            # Panel lateral derecho
  → UndoRedoManager()         # Historial de acciones
```

### 2. CREACIÓN DEL MODELO
```
Usuario crea nudos:
  StructureCanvas (clic) → MainWindow → modelo.agregar_nudo(x, y)

Usuario crea barras:
  StructureCanvas (drag i→j) → modelo.agregar_barra(nudo_i, nudo_j, mat, sec)
    → Barra.__init__(): calcula L, angulo automáticamente

Usuario aplica vínculos:
  PropertiesPanel → nudo.vinculo = Empotramiento() | ApoyoFijo() | Rodillo() | ...

Usuario aplica cargas:
  CargaDialog.exec() → modelo.agregar_carga(CargaPuntualBarra | CargaDistribuida | ...)
```

### 3. RESOLUCIÓN (F5 o botón "Resolver")
```
MainWindow._on_resolver()
  ↓
  motor = MotorMetodoFuerzas(modelo)
  ↓
  1. calcular_grado_hiperestaticidad()
     gh = r + v - 3n
  ↓
  2. [Si gh > 0] seleccionar_redundantes()
     → RedundantesDialog (si modo manual)
     → seleccion_automatica() (modo auto — ver SELECCION_REDUNDANTES.md)
  ↓
  3. generar_subestructuras()
     ├─ generar_fundamental()        → elimina redundantes, resuelve reacciones
     └─ generar_Xi(i)  ×gh           → carga unitaria en dirección de Xi
  ↓
  4. calcular_esfuerzos_todas_subestructuras()
     → calcular_esfuerzos_viga_isostatica() por cada barra
     → N(x), V(x), M(x) por método de secciones
  ↓
  5. calcular_coeficientes_flexibilidad()
     CalculadorFlexibilidad:
     ├─ _calcular_fij(i,j)            → ∫Mi·Mj/(EI) dx + ∫Ni·Nj/(EA) dx
     ├─ _calcular_e0i(i)              → ∫Mi·M0/(EI) dx (cargas mecánicas)
     ├─ _calcular_e0i_termico(i)      → α·ΔT·∫Ni dx + κ·∫Mi dx
     ├─ _calcular_e0i_resortes(i)     → P̄i·P0/k (resortes mantenidos)
     ├─ _agregar_flexibilidad_resortes() → F[i,i] += 1/k
     └─ Verificar simetría [F] (|F-F.T| < 1e-10)
  ↓
  6. resolver_sece()
     SolverSECE: np.linalg.solve([F], -{e0})
     → Verificar cond([F]) < 1e12
     → Verificar residual < 1e-8
  ↓
  7. calcular_resultados_finales()
     ├─ N_final(x) = N0(x) + Σ Xi·Ni(x)
     ├─ V_final(x) = V0(x) + Σ Xi·Vi(x)
     ├─ M_final(x) = M0(x) + Σ Xi·Mi(x)
     └─ Reacciones por equilibrio directo
  ↓
  8. verificar_equilibrio_global()
     |ΣFx|, |ΣFy|, |ΣMz| < 1e-6
  ↓
  ResultsPanel.mostrar_resultado(resultado)
```

### 4. VISUALIZACIÓN
```
Diagramas M/V/N:
  graficar_diagramas_combinados(modelo, resultado) → matplotlib figure

Geometría:
  graficar_geometria(modelo) → estructura con símbolos de vínculos y cargas

Deformada:
  graficar_deformada(modelo, resultado) → doble integración de M/EI → v(x)
```

### 5. PERSISTENCIA
```
Guardar: ProyectoSerializer.guardar(modelo, path)  → JSON
Cargar:  ProyectoSerializer.cargar(path) → ModeloEstructural

Undo: UndoRedoManager.deshacer()   (Ctrl+Z)
Redo: UndoRedoManager.rehacer()    (Ctrl+Y)
```

---

## CLASES PRINCIPALES Y SUS RELACIONES

### MODELO DE DOMINIO

```
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
  └─ Ux, Uy, theta_z: float  # Desplazamientos (post-análisis)

Barra
  ├─ id: int
  ├─ nudo_i, nudo_j: Nudo
  ├─ material: Material
  ├─ seccion: Seccion
  ├─ L: float            # Calculado: sqrt(dx²+dy²)
  ├─ angulo: float       # Calculado: arctan2(dy, dx) [rad]
  └─ cargas: List[Carga]

Vinculo (abstracta)
  ├─ Empotramiento    → restringe [Ux, Uy, theta_z]
  ├─ ApoyoFijo        → restringe [Ux, Uy]
  ├─ Rodillo          → restringe [Uy] o [Ux]
  ├─ Guia             → restringe [traslacion + rotacion]
  └─ ResorteElastico  → kx [kN/m], ky [kN/m], ktheta [kNm/rad]

Carga (abstracta)
  ├─ CargaPuntualNudo     → Fx, Fy, Mz en nudo
  ├─ CargaPuntualBarra    → P, a, angulo en barra
  ├─ CargaDistribuida     → q1, q2, tipo (uniforme/trapezoidal)
  ├─ CargaTermica         → delta_T_uniforme, delta_T_gradiente
  └─ MovimientoImpuesto   → delta_x, delta_y, delta_theta
```

### MOTOR DE ANÁLISIS

```
MotorMetodoFuerzas
  ├─ modelo: ModeloEstructural
  ├─ fundamental: Subestructura
  ├─ subestructuras_xi: List[Subestructura]
  ├─ matriz_F: NDArray[n×n]
  ├─ vector_e0: NDArray[n]
  └─ solucion_X: NDArray[n]     # Valores de redundantes Xi

Subestructura
  ├─ nombre: str                 # "Fundamental", "X1", "X2", ...
  ├─ nudos: List[Nudo]
  ├─ barras: List[Barra]
  ├─ cargas: List[Carga]
  ├─ reacciones: Dict[int, ndarray]   # {nudo_id: [Rx, Ry, Mz]}
  └─ diagramas: Dict[int, DiagramaEsfuerzos]  # {barra_id: diagrama}

CalculadorFlexibilidad
  ├─ _calcular_fij(i, j) → float
  ├─ _calcular_e0i(i) → float         # Mecánico
  ├─ _calcular_e0i_termico(i) → float # Térmico
  ├─ _calcular_e0i_resortes(i) → float
  └─ _agregar_flexibilidad_resortes(F) → NDArray

ResultadoAnalisis
  ├─ grado_hiperestaticidad: int
  ├─ redundantes: List[str]
  ├─ solucion_X: Dict[str, float]     # {nombre_redundante: valor}
  ├─ reacciones_finales: Dict[int, ndarray]
  └─ diagramas_finales: Dict[int, DiagramaEsfuerzos]
```

---

## FUNCIONES CLAVE

### src/domain/mechanics/equilibrio.py

```python
def momento_fuerza_respecto_punto(Fx, Fy, x_fuerza, y_fuerza, x_punto, y_punto) -> float:
    """
    M = -Fy × (x_punto - x_fuerza) + Fx × (y_punto - y_fuerza)
    TERNA: X+ derecha, Y+ abajo, rotacion horaria +
    """

def resolver_reacciones_isostatica(nudos, barras, cargas) -> Dict[int, ndarray]:
    """
    Construye [A]{R} = {b} y resuelve con numpy.linalg.solve.
    b = [-ΣFx, -ΣFy, -ΣMz] de cargas externas.
    """

def verificar_equilibrio_global(nudos, cargas, reacciones, barras) -> Tuple[bool, dict]:
    """Retorna (cumple, {SumFx, SumFy, SumMz}). Tolerancia: 1e-6."""
```

### src/domain/mechanics/esfuerzos.py

```python
def calcular_esfuerzos_viga_isostatica(barra, cargas_barra, reacciones) -> DiagramaEsfuerzos:
    """
    Calcula N(x), V(x), M(x) usando método de secciones.
    Convención: mirar a la izquierda del corte.
    """
```

### src/domain/analysis/trabajos_virtuales.py

```python
class CalculadorFlexibilidad:
    def _calcular_fij(self, i, j) -> float:
        """fij = integral(Mi·Mj/(E·Jz)) + integral(Ni·Nj/(E·A)) — Simpson 21 puntos"""

    def _calcular_e0i(self, i) -> float:
        """e0i = integral(Mi·M0/(E·Jz)) — trabajos virtuales mecanicos"""

    def _calcular_e0i_termico(self, i) -> float:
        """
        e0i_termico = alpha·dT·integral(Ni dx) + (alpha·dT_grad/h)·integral(Mi dx)
        Maneja ΔT uniforme y gradiente lineal.
        """

    def _agregar_flexibilidad_resortes(self, F) -> NDArray:
        """
        Para cada resorte con rigidez k que coincide con redundante i:
        F[i, i] += 1/k
        """
```

### src/ui/visualization/

```python
# diagramas.py
def graficar_diagrama_momentos(modelo, resultado, n_puntos=51, escala=None, ax=None)
def graficar_diagrama_cortantes(modelo, resultado, ...)
def graficar_diagrama_axiles(modelo, resultado, ...)
def graficar_diagramas_combinados(modelo, resultado, ...)  # M + V + N en subplots

# geometria.py
def graficar_geometria(modelo, ax=None)
    # Dibuja: barras, nudos, vínculos (empotramiento/rodillo/resorte), cargas

# deformada.py
def graficar_deformada(modelo, resultado, factor_escala=None, n_puntos=51)
    # Doble integración de kappa(x) = M(x)/(EI) → theta(x) → v(x)
    # Factor de escala automático: ~10% de dimensiones de la estructura

def graficar_comparacion_deformadas(modelo, resultado, factores=[1, 10, 100])
    # Subplots con distintos factores de escala
```

---

## CONVENCIÓN DE SIGNOS (TERNA) — CRÍTICO

```
TERNA GLOBAL:
  X+ → derecha
  Y+ → abajo (gravedad)
  Rotacion+ → horaria (sentido agujas del reloj)

FUERZAS EN BARRAS:
  angulo = 0°:   en dirección de la barra (i→j)
  angulo = +90°: perpendicular HORARIO (↓ en barra horizontal)
  angulo = -90°: perpendicular ANTIHORARIO (↑ en barra horizontal)

MOMENTOS:
  M > 0: horario, tracciona fibra inferior en viga horizontal
  M < 0: antihorario

FORMULA DE MOMENTO RESPECTO A UN PUNTO:
  M(punto) = -Fy × (x_punto - x_fuerza) + Fx × (y_punto - y_fuerza)
```

---

## PENDIENTE

| Funcionalidad | Módulo a crear | Observaciones |
|--------------|----------------|---------------|
| Exportación PDF | `src/ui/export/reporte_pdf.py` | Requiere ReportLab |
| Empaquetado .exe | — | PyInstaller, solo Windows |
| Manual de usuario | `docs/manual/` | Markdown + capturas |
| Tests resortes e2e | `tests/integration/test_resortes_sece.py` | Análisis completo |
| Tests deformada e2e | `tests/integration/test_deformada.py` | Verificar v(x) numérico |
