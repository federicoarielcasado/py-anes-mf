0) Meta y Contexto General
Propósito del documento
Este archivo sirve como contexto de largo plazo para agentes de IA (Claude u otros LLMs) encargados de asistir en el desarrollo, mantenimiento y extensión de un sistema profesional de análisis estructural hiperestático de pórticos planos 2D mediante el Método de las Fuerzas (también conocido como Método de Flexibilidad o Método de Compatibilidad de Deformaciones).
Contexto del proyecto

Usuario: Ingeniero civil con experiencia en Python, finanzas y desarrollo colaborativo
Dominio: Análisis estructural avanzado, estática de estructuras hiperestáticas
Metodología: Método de las Fuerzas con Teorema de Trabajos Virtuales para cálculo de coeficientes de flexibilidad (fᵢⱼ) y términos independientes (e₀ᵢ)
Objetivo pedagógico/profesional: Herramienta que combine rigor matemático, usabilidad profesional y capacidad didáctica

Referencias teóricas clave
El usuario proveerá PDFs con fundamentos teóricos del método. Se asume familiaridad con:

Análisis matricial de estructuras (Weaver, Gere, Timoshenko)
Método de las fuerzas clásico (Beer & Johnston, Hibbeler)
Teorema de trabajos virtuales y reciprocidad de Maxwell-Betti
Ecuaciones de compatibilidad en estructuras hiperestáticas


0.1) Convenciones de Signos y Coordenadas (CRÍTICO)

TERNA adoptada: Y+ hacia abajo (gravedad), rotación horaria positiva
Ángulos de carga: 0°=dirección barra, +90°=perpendicular horario (↓ en barra horizontal), -90°=perpendicular antihorario (↑)
Momento positivo: tracciona fibra inferior de viga horizontal
Reacciones: signo según TERNA (hacia arriba = negativo en Y+)
Fórmula momento: M = -Fy × dx + Fx × dy (ver equilibrio.py líneas 26-72)


1) Objetivos SMART
Objetivo principal
Desarrollar un sistema de software profesional en Python capaz de analizar pórticos planos 2D hiperestáticos mediante el Método de las Fuerzas, generando diagramas de esfuerzos internos (N, V, M), reacciones de vínculo, deformaciones y reportes técnicos validables.
Objetivos específicos (SMART)
S – Específicos

Implementar 12 módulos funcionales integrados (según esquema provisto)
Resolver sistemas de ecuaciones de compatibilidad (SECE) de hasta 30 redundantes simultáneos
Generar diagramas gráficos profesionales de N, V, M con escala dinámica
Calcular automáticamente coeficientes fᵢⱼ y e₀ᵢ usando trabajos virtuales

M – Medibles

Tiempo de resolución < 5 segundos para estructuras con hasta 50 barras y 10 redundantes
Precisión numérica: error relativo < 1×10⁻⁸ en solución del SECE
Cobertura de pruebas: 100% de casos clásicos validados (viga empotrada, pórtico biempotrado, etc.)
Interfaz gráfica responsiva: < 100 ms de latencia en operaciones de selección/edición

A – Alcanzables

Uso de bibliotecas estándar (NumPy, SciPy, Matplotlib, PyQt/Tkinter)
Desarrollo incremental por módulos independientes
Reutilización de conocimiento existente en análisis estructural

R – Relevantes

Aplicación directa en verificación de cálculos estructurales profesionales
Herramienta didáctica para enseñanza de análisis estructural avanzado
Base para futura extensión a análisis dinámico o pórticos 3D

T – Temporales

Fase 1 (Módulos 1-4, 6): 4 semanas – núcleo matemático y modelo de datos
Fase 2 (Módulos 5, 8, 11): 3 semanas – interfaz visual y visualización
Fase 3 (Módulos 7, 9, 10): 3 semanas – motor de método de fuerzas completo
Fase 4 (Módulos 3, 12): 2 semanas – funcionalidades avanzadas
Total estimado: 12 semanas de desarrollo activo


2) Alcance y Exclusiones
Dentro del alcance
Estructuras soportadas

Pórticos planos 2D con barras rectas prismáticas
Configuraciones ortogonales y no ortogonales (barras inclinadas arbitrariamente)
Nudos rígidos y articulados en la misma estructura
Hasta 100 barras y 30 redundantes (límite por rendimiento)

Análisis contemplado

Análisis estático lineal elástico
Pequeñas deformaciones (teoría de primer orden)
Material homogéneo isótropo (ley de Hooke)
Efectos de flexión, corte y axil (viga de Timoshenko opcional, por defecto Euler-Bernoulli)

Tipos de cargas

Puntuales en nudos (Fx, Fy, Mz)
Puntuales en barras (cualquier posición)
Distribuidas en barras (uniformes, triangulares, trapezoidales)
Térmicas (ΔT uniforme, gradiente lineal en altura)
Movimientos impuestos (hundimientos de apoyo, rotaciones prescritas)

Vínculos externos

Empotramiento (Ux=Uy=θz=0)
Apoyo fijo (Ux=Uy=0, θz libre)
Rodillo/apoyo simple (1 dirección restringida, 2 GDL libres)
Guía (traslación en 1 dirección, rotación restringida)
Resortes elásticos traslacionales (kx, ky)
Resortes rotacionales (kθ)

Funcionalidades clave

Identificación automática de grado de hiperestaticidad
Selección inteligente de redundantes (algoritmo configurable)
Generación automática de estructuras fundamentales (1 por Xi)
Cálculo automatizado de fᵢⱼ y e₀ᵢ mediante trabajos virtuales
Ensamblaje y resolución del SECE
Superposición de resultados (diagramas, reacciones, deformaciones)
Verificación de equilibrio global y local
Exportación de resultados (PDF, PNG, CSV, JSON)
Guardado/carga de proyectos completos

Fuera del alcance (Fase 1)
Análisis no contemplados

Análisis no lineal (geométrico o material)
Pandeo crítico (análisis de autovalores)
Análisis dinámico (modal, respuesta temporal, sísmica)
Elementos finitos 2D (placas, losas)
Pórticos espaciales 3D
Efectos de segundo orden (P-Δ, grandes desplazamientos)

Limitaciones explícitas

No se modelan conexiones semirrígidas con rigidez variable
No se considera comportamiento inelástico (plasticidad, fisuración)
No se integra con software CAD externo (AutoCAD, Revit)
No se implementa optimización automática de secciones
No se genera diseño de armaduras ni verificación normativa (CIRSOC, ACI)


2.1) Testing y Validación

Suite: 90 tests totales, objetivo ≥87 pasando (97%)
Comando rápido: pytest -v --tb=no -q
Prioridad: tests hiperestáticos > tests isostáticos básicos
Bugs no críticos: usar pytest.skip("razón") con documentación clara
Fixtures estándar: acero E=200e6, IPE220, SeccionRectangular 30x50

2.2) Bugs Conocidos

calcular_esfuerzos_viga_isostatica(): falla para voladizos (extremo libre) - NO CRÍTICO
Windows console: Unicode (✓✗ΣΔ) causa UnicodeEncodeError - usar ASCII
Solver isostático: asume reacciones en ambos extremos


3) Requisitos Detallados
3.1) Requisitos Funcionales (RF)
RF-01: Definición del modelo estructural

RF-01.1: El sistema debe permitir crear nudos con coordenadas XY en un plano global
RF-01.2: Cada nudo debe tener ID único, nombre opcional, y propiedades editables
RF-01.3: Las barras deben definirse conectando dos nudos (i→j), heredando longitud y ángulo automáticamente
RF-01.4: Cada barra debe tener propiedades: E (módulo elástico), A (área), Jz (momento de inercia), material asociado
RF-01.5: Debe existir base de datos interna de materiales (E predefinido) y secciones típicas (perfiles IPE, HEA, rectangulares)
RF-01.6: El sistema de coordenadas local de cada barra debe calcularse automáticamente (eje x́ a lo largo de la barra)

RF-02: Condiciones de frontera (vínculos)

RF-02.1: Soportar vínculos clásicos: empotramiento, apoyo fijo, rodillo (horizontal/vertical/inclinado), guía
RF-02.2: Cada vínculo debe asociarse a un nudo y restringir GDL específicos (Ux, Uy, θz)
RF-02.3: Representación gráfica inequívoca mediante símbolos normalizados
RF-02.4: Validación automática: un nudo puede tener solo un tipo de vínculo externo

RF-03: Condiciones especiales

RF-03.1: Implementar vínculos elásticos con constantes kx, ky (N/m), kθ (Nm/rad)
RF-03.2: Permitir definir movimientos impuestos: hundimientos δy, rotaciones Δθ
RF-03.3: Modelar efectos térmicos: ΔT uniforme, gradiente térmico lineal en altura de sección

RF-04: Sistema de cargas

RF-04.1: Cargas puntuales en nudos (Fx, Fy, Mz) en coordenadas globales
RF-04.2: Cargas puntuales sobre barras (P a distancia 'a' del nudo i)
RF-04.3: Cargas distribuidas: uniformes (q), triangulares (q₁→q₂), trapezoidales
RF-04.4: Transformación automática de cargas a sistema local de barra
RF-04.5: Cálculo de acciones de empotramiento perfecto (reacciones isostáticas en barras biempotradas)

RF-05: Interfaz visual interactiva

RF-05.1: Editor gráfico drag-and-drop para crear nudos haciendo clic
RF-05.2: Crear barras arrastrando desde nudo inicial a nudo final
RF-05.3: Selección múltiple (rectángulo de selección, Ctrl+clic)
RF-05.4: Edición de propiedades mediante panel lateral o doble clic
RF-05.5: Grilla paramétrica configurable (snap a grilla opcional)
RF-05.6: Zoom (rueda del mouse), pan (clic medio o Ctrl+arrastre)
RF-05.7: Vista de tabla editable estilo Excel para ingreso numérico directo
RF-05.8: Importación desde CSV/JSON con formato predefinido

RF-06: Motor matemático – grado de hiperestaticidad

RF-06.1: Calcular automáticamente grado de hiperestaticidad: gh = r + v - 3n (fórmula 2D)

r: vínculos de reacción
v: vínculos internos (articulaciones internas cuentan como -1)
n: número de nudos


RF-06.2: Detectar estructuras hipostáticas (gh < 0) y emitir advertencia
RF-06.3: Detectar inestabilidad geométrica mediante análisis de singularidad de matriz
RF-06.4: Identificar redundantes candidatos mediante algoritmo configurable:

Preferencia por reacciones de vínculo antes que momentos internos
Evitar redundantes que generen subestructuras inestables


RF-06.5: Permitir selección manual de redundantes por usuario avanzado

RF-07: Generación de subestructuras

RF-07.1: Crear estructura fundamental eliminando redundantes seleccionados
RF-07.2: Validar isostabilidad de estructura fundamental
RF-07.3: Para cada redundante Xᵢ, generar subestructura con carga unitaria aplicada en sentido positivo
RF-07.4: Mantener coherencia de signos según convención adoptada:

Momentos: positivos si traccionan fibra inferior
Cortantes: positivos según criterio de viga (izquierda-derecha)
Axiles: positivos si son de tracción



RF-08: Diagramas de esfuerzos internos

RF-08.1: Calcular N(x), V(x), M(x) para cada barra de cada subestructura
RF-08.2: Representar gráficamente sobre la barra (offset perpendicular)
RF-08.3: Escala dinámica ajustable (automática o manual)
RF-08.4: Lectura de valor en cualquier punto mediante clic o ingreso de coordenada x
RF-08.5: Representar diagramas cualitativos (sin escala) para verificación rápida
RF-08.6: Colorear diagramas: axil (azul), cortante (verde), momento (rojo) – configurable

RF-09: Teorema de trabajos virtuales

RF-09.1: Calcular coeficientes de flexibilidad: fᵢⱼ = ∫(Mᵢ·Mⱼ)/(E·Jz)dx + ∫(Nᵢ·Nⱼ)/(E·A)dx + ... 
RF-09.2: Implementar integración numérica (Simpson, trapezoidal) con subdivisión adaptativa
RF-09.3: Calcular términos independientes: e₀ᵢ = ∫(Mᵢ·M₀)/(E·Jz)dx + ∫(Nᵢ·N₀)/(E·A)dx + ...
RF-09.4: Incluir efectos térmicos: δᵢ = α·ΔT·∫Nᵢ dx
RF-09.5: Incluir movimientos impuestos en ecuaciones de compatibilidad
RF-09.6: Generar matriz de flexibilidad [F] simétrica (validar simetría con tolerancia)

RF-10: Resolución del SECE

RF-10.1: Ensamblar sistema: [F]·{X} = -{e₀}
RF-10.2: Resolver usando numpy.linalg.solve con verificación de condicionamiento
RF-10.3: Si matriz mal condicionada (cond > 1e12), emitir advertencia y sugerir reselección de redundantes
RF-10.4: Validar solución: ||[F]·{X} + {e₀}|| < tol (tol = 1e-8)
RF-10.5: Mostrar iteración de solución si se implementa método iterativo (opcional)

RF-11: Resultados hiperestáticos finales

RF-11.1: Superponer diagramas: N_final = N₀ + ΣXᵢ·Nᵢ
RF-11.2: Calcular reacciones finales en vínculos: R_final = R₀ + ΣXᵢ·Rᵢ
RF-11.3: Generar diagrama de deformada exagerada (escala ajustable)
RF-11.4: Exportar gráficos en PNG (alta resolución) y PDF vectorial
RF-11.5: Exportar tabla de resultados en CSV (barras, nudos, reacciones)

RF-12: Postproceso de deformaciones

RF-12.1: Calcular desplazamientos Ux, Uy en cualquier nudo mediante superposición
RF-12.2: Calcular rotación θz en extremos de barra usando relaciones elásticas
RF-12.3: Permitir consulta interactiva: usuario hace clic en punto de interés
RF-12.4: Generar línea elástica de barra seleccionada (gráfico M/EI, deformada local)

3.2) Requisitos No Funcionales (RNF)
RNF-01: Rendimiento

El sistema debe resolver estructuras de hasta 50 barras y 10 redundantes en menos de 5 segundos (hardware estándar: CPU i5, 8GB RAM)
La interfaz gráfica debe responder a eventos de usuario (clic, arrastre) en < 100 ms
Actualización de diagramas tras edición debe completarse en < 1 segundo

RNF-02: Precisión numérica

Error relativo en solución del SECE: < 1×10⁻⁸
Tolerancia para detección de singularidad: cond([F]) > 1×10¹²
Verificación de equilibrio: |ΣFx|, |ΣFy|, |ΣMz| < 1×10⁻⁶ kN, kNm

RNF-03: Usabilidad

Interfaz intuitiva para usuario con conocimientos básicos de análisis estructural
Ayuda contextual (tooltips) en cada elemento de UI
Mensajes de error claros y accionables (no "Error 0x00F3", sino "La estructura es hipostática: faltan 2 vínculos")
Flujo de trabajo guiado: modelo → vínculos → cargas → resolver → resultados

RNF-04: Mantenibilidad

Arquitectura modular con acoplamiento mínimo entre capas
Documentación interna (docstrings) en todas las clases y métodos públicos
Código conforme a PEP 8
Type hints en firmas de funciones
Tests unitarios para cada módulo matemático crítico

RNF-05: Portabilidad

Compatible con Windows 10/11 (prioridad), Linux (secundario), macOS (opcional)
Python 3.9+ como requisito mínimo
Dependencias limitadas a paquetes estables de PyPI

RNF-06: Extensibilidad

Diseño permite agregar nuevos tipos de vínculos sin modificar motor de cálculo
Sistema de plugins para cargas especiales (viento, sismo, nieve) en futuras versiones
API interna documentada para integración con otros módulos (ej: diseño de secciones)

RNF-07: Confiabilidad

Validación de entrada: rechazar modelos con barras de longitud cero, materiales con E≤0
Manejo robusto de excepciones numéricas (división por cero, matriz singular)
Guardado automático cada 5 minutos (recuperación ante cierre inesperado)


4) Casos de Uso / Escenarios
CU-01: Viga biempotrada con carga puntual
Actor: Estudiante de ingeniería
Objetivo: Verificar solución manual de ejercicio de clase
Precondiciones: Sistema instalado y abierto
Flujo principal:

Crear dos nudos: (0,0) y (L,0)
Crear barra conectando nudos, asignar E, Jz
Aplicar empotramiento en ambos nudos
Aplicar carga puntual P en centro de luz (L/2)
Resolver (gh=3: Ma, Mb, Vb redundantes)
Comparar diagrama de momentos con solución teórica: M_centro = -P·L/8
Exportar PDF con resultados

Postcondiciones: Diagrama generado coincide con teoría dentro de 0.1%

CU-02: Pórtico rectangular con carga horizontal
Actor: Ingeniero estructural
Objetivo: Analizar marco resistente ante carga de viento
Precondiciones: Base de datos de perfiles IPE cargada
Flujo principal:

Crear pórtico: 4 nudos, 3 barras (2 columnas + 1 viga)
Empotrar columnas en base
Asignar perfiles IPE220 a columnas, IPE270 a viga
Aplicar carga horizontal F en nudo superior izquierdo
Resolver (gh=3)
Consultar reacciones en bases
Verificar cortante máximo en columnas
Exportar tabla de esfuerzos a CSV para posterior diseño

Postcondiciones: Reacciones verifican equilibrio global (ΣFx=0, ΣMbase=0)

CU-03: Estructura con hundimiento de apoyo
Actor: Investigador académico
Objetivo: Estudiar efecto de asentamiento diferencial
Precondiciones: Conocimiento de método de fuerzas con movimientos impuestos
Flujo principal:

Modelar viga continua de 3 vanos (4 apoyos)
Definir hundimiento vertical δy = -10mm en apoyo central
Resolver incorporando δy en ecuación de compatibilidad
Analizar redistribución de momentos respecto a caso sin hundimiento
Generar gráfico comparativo (con/sin asentamiento)

Postcondiciones: Momento en apoyo con hundimiento es notablemente menor

CU-04: Validación con caso de la literatura
Actor: Desarrollador del sistema
Objetivo: Verificar corrección de implementación
Precondiciones: Problema resuelto en libro de referencia (ej: Timoshenko, Strength of Materials)
Flujo principal:

Importar geometría desde JSON de caso de prueba
Ejecutar análisis
Comparar resultados numéricos con solución publicada
Generar reporte de diferencias
Si diferencia > 1%, activar modo debug y mostrar matrices F, e₀

Postcondiciones: Test pasa automáticamente si error < 0.5%

5) Stakeholders y Roles
StakeholderRolResponsabilidadInterés principalFede (Usuario/Desarrollador)Product Owner + DeveloperDefinir requisitos, desarrollar código, validar resultadosHerramienta funcional, código limpio y extensibleClaude (IA Asistente)Technical Advisor + Code GeneratorProponer arquitecturas, generar módulos, revisar códigoAsegurar calidad técnica y buenas prácticasEstudiantes de IngenieríaEnd Users (secundarios)Validar usabilidad, reportar bugsInterfaz intuitiva, resultados confiablesDocentes de EstructurasValidatorsVerificar corrección matemáticaSoluciones coincidan con teoríaIngenieros EstructuralesPotential UsersEvaluar aplicabilidad profesionalPrecisión, trazabilidad de cálculos, exportación

6) Supuestos, Riesgos y Mitigaciones
6.1) Supuestos
IDSupuestoCriticidadSUP-01Usuario tiene conocimientos de análisis estructural (no es software para público general)AltaSUP-02Estructuras analizadas cumplen hipótesis de pequeñas deformacionesAltaSUP-03NumPy y SciPy son suficientemente precisos para sistemas de hasta 30×30MediaSUP-04Usuario validará resultados con casos conocidos antes de confiar en softwareAltaSUP-05No se requiere certificación profesional (software educativo/investigación)Media
6.2) Riesgos
IDRiesgoProbabilidadImpactoMitigaciónR-01Matriz [F] mal condicionada para ciertos modelosMediaAltoImplementar selección automática de redundantes + advertencia + sugerir regularizaciónR-02Integración numérica imprecisa en barras muy cortas o con cargas complejasBajaMedioSubdivisión adaptativa, validar con casos límiteR-03Interfaz gráfica lenta con >100 barrasMediaMedioImplementar culling (no dibujar elementos fuera de viewport), usar OpenGL via PyOpenGLR-04Usuario confunde convención de signosAltaBajoTooltip explicativo, diagrama de referencia siempre visibleR-05Pérdida de trabajo por cierre inesperadoBajaMedioGuardado automático cada 5 minR-06Resultados incorrectos por error de programaciónMediaCríticoSuite de tests exhaustiva con casos validados, peer review de códigoR-07Dificultad para identificar estructura inestable geométricamenteBajaAltoAnálisis de autovalores de matriz de rigidez como verificación previa

7) Entregables y Cronograma Sugerido
7.1) Entregables
IDEntregableDescripciónFormatoE-01Código fuente modular12 módulos Python con arquitectura MVC.py (GitHub repo)E-02Ejecutable standaloneAplicación empaquetada para Windows.exe (PyInstaller)E-03Manual de usuarioGuía paso a paso con capturasPDFE-04Documentación técnicaDescripción de clases, APIs internas, algoritmosMarkdown + Sphinx HTMLE-05Suite de testsCasos de prueba automatizadospytestE-06Ejemplos de validación10 casos resueltos con solución manualJSON + PDF reportesE-07Video tutorialDemostración de uso (15-20 min)MP4
7.2) Cronograma (12 semanas)
Semana 1-2: Módulo 1 (Modelo estructural) + Módulo 2 (Vínculos)
  - Clases: Nudo, Barra, Material, Sección
  - Sistema de coordenadas, transformaciones locales/globales
  - Base de datos interna de materiales (acero, hormigón)
  
Semana 3: Módulo 4 (Cargas) + Módulo 6 (Grado hiperestaticidad)
  - Clases: CargaPuntual, CargaDistribuida, CargaTérmica
  - Algoritmo identificación de gh
  - Selección automática de redundantes (heurística inicial)

Semana 4: Módulo 7 (Subestructuras)
  - Generación de estructura fundamental
  - Aplicación de cargas unitarias
  - Validación de isostabilidad

Semana 5-6: Módulo 9 (Trabajos Virtuales) + Módulo 10 (SECE)
  - Integración numérica de fᵢⱼ, e₀ᵢ
  - Ensamblaje de matriz [F]
  - Solución con numpy.linalg
  - Tests de precisión

Semana 7: Módulo 8 (Diagramas de esfuerzos)
  - Cálculo de N(x), V(x), M(x) por integración de cargas
  - Representación gráfica básica (matplotlib)

Semana 8-9: Módulo 5 (Interfaz visual)
  - Framework GUI (PyQt6 recomendado)
  - Canvas interactivo con zoom/pan
  - Drag & drop de nudos/barras
  - Panel de propiedades

Semana 10: Módulo 11 (Resultados finales)
  - Superposición de diagramas
  - Cálculo de reacciones
  - Exportación PDF/PNG

Semana 11: Módulo 3 (Condiciones especiales) + Módulo 12 (Deformaciones)
  - Resortes elásticos, movimientos impuestos
  - Cálculo de desplazamientos y rotaciones

Semana 12: Integración, testing, documentación
  - Tests de regresión completos
  - Empaquetado con PyInstaller
  - Redacción de manual

8) Métricas de Éxito y KPI
KPIDescripciónMetaMétodo de mediciónPrecisiónError relativo en solución de SECE< 1×10⁻⁸Comparación con solución analítica en casos testCobertura de tests% de código ejecutado por tests> 80%pytest --covRendimientoTiempo de resolución (50 barras, 10 red.)< 5 segtimeit en casos benchmarkEstabilidad numérica% de casos sin advertencias de condicionamiento> 95%Registro de warnings en suite de 100 casosValidación externaCasos de literatura resueltos correctamente10/10Comparación manual con libros de referenciaUsabilidadTiempo para resolver caso simple (usuario nuevo)< 10 minTest con usuario betaBugs críticosErrores que impiden resolver modelos válidos0Issue tracker (GitHub)

9) Recomendaciones de Diseño y Tecnología
9.1) Arquitectura de software
Patrón recomendado: MVC + Layers
┌─────────────────────────────────────────┐
│         INTERFAZ (Vista)                │
│  - Editor gráfico (PyQt6/Tkinter)      │
│  - Paneles de propiedades              │
│  - Viewport con zoom/pan               │
└─────────────────────────────────────────┘
              ↕ (Eventos, comandos)
┌─────────────────────────────────────────┐
│        CONTROLADOR                      │
│  - Comandos (Crear, Editar, Resolver)  │
│  - Gestor de estado (Undo/Redo)        │
│  - Coordinador de flujo                │
└─────────────────────────────────────────┘
              ↕ (Llamadas a modelo)
┌─────────────────────────────────────────┐
│          MODELO                         │
│  - Entidades (Nudo, Barra, Carga...)   │
│  - Motor matemático (Método Fuerzas)   │
│  - Solver numérico                      │
└─────────────────────────────────────────┘
              ↕ (Persistencia)
┌─────────────────────────────────────────┐
│       CAPA DE DATOS                     │
│  - Serialización JSON                   │
│  - Importación/Exportación              │
└─────────────────────────────────────────┘
9.2) Diseño de clases principales
python# ============ ENTIDADES DEL MODELO ============

@dataclass
class Nudo:
    """
    Representa un nudo en el pórtico plano.
    """
    id: int
    x: float  # Coordenada global X [m]
    y: float  # Coordenada global Y [m]
    nombre: str = ""
    vinculo: Optional['Vinculo'] = None  # Si tiene vínculo externo
    
    # Resultados (se calculan post-análisis)
    Ux: float = 0.0  # Desplazamiento X [m]
    Uy: float = 0.0  # Desplazamiento Y [m]
    theta_z: float = 0.0  # Rotación [rad]


@dataclass
class Material:
    """
    Propiedades del material.
    """
    nombre: str
    E: float  # Módulo elástico [kN/m²]
    alpha: float = 1.2e-5  # Coef. dilatación térmica [1/°C]
    rho: float = 0.0  # Densidad [kg/m³] (para peso propio futuro)


@dataclass
class Seccion:
    """
    Propiedades geométricas de sección transversal.
    """
    nombre: str
    A: float  # Área [m²]
    Jz: float  # Momento de inercia respecto Z [m⁴]
    h: float = 0.0  # Altura (para gradiente térmico) [m]


class Barra:
    """
    Elemento estructural que conecta dos nudos.
    """
    def __init__(self, id: int, nudo_i: Nudo, nudo_j: Nudo, 
                 material: Material, seccion: Seccion):
        self.id = id
        self.nudo_i = nudo_i
        self.nudo_j = nudo_j
        self.material = material
        self.seccion = seccion
        
        # Geometría calculada
        self.L = self._calcular_longitud()
        self.angulo = self._calcular_angulo()  # [rad] respecto eje X global
        
        # Cargas sobre la barra
        self.cargas: List[Carga] = []
        
        # Esfuerzos en coordenadas locales (se calculan post-análisis)
        self.N: Callable[[float], float] = lambda x: 0.0  # Función N(x)
        self.V: Callable[[float], float] = lambda x: 0.0  # Función V(x)
        self.M: Callable[[float], float] = lambda x: 0.0  # Función M(x)
    
    def _calcular_longitud(self) -> float:
        dx = self.nudo_j.x - self.nudo_i.x
        dy = self.nudo_j.y - self.nudo_i.y
        return np.hypot(dx, dy)
    
    def _calcular_angulo(self) -> float:
        dx = self.nudo_j.x - self.nudo_i.x
        dy = self.nudo_j.y - self.nudo_i.y
        return np.arctan2(dy, dx)
    
    def matriz_transformacion(self) -> np.ndarray:
        """
        Matriz 3×3 para rotar de coordenadas locales a globales.
        """
        c = np.cos(self.angulo)
        s = np.sin(self.angulo)
        return np.array([
            [ c, -s, 0],
            [ s,  c, 0],
            [ 0,  0, 1]
        ])


class Vinculo(ABC):
    """
    Clase base abstracta para vínculos externos.
    """
    def __init__(self, nudo: Nudo):
        self.nudo = nudo
    
    @abstractmethod
    def gdl_restringidos(self) -> List[str]:
        """Retorna lista de GDL restringidos: ['Ux', 'Uy', 'theta_z']"""
        pass
    
    @abstractmethod
    def simbolo_grafico(self) -> str:
        """Código para representación gráfica"""
        pass


class Empotramiento(Vinculo):
    def gdl_restringidos(self) -> List[str]:
        return ['Ux', 'Uy', 'theta_z']
    
    def simbolo_grafico(self) -> str:
        return 'FIXED'


class ApoyoFijo(Vinculo):
    def gdl_restringidos(self) -> List[str]:
        return ['Ux', 'Uy']
    
    def simbolo_grafico(self) -> str:
        return 'PINNED'


class Rodillo(Vinculo):
    """
    Apoyo simple que restringe un GDL traslacional.
    """
    def __init__(self, nudo: Nudo, direccion: str = 'Uy'):
        super().__init__(nudo)
        self.direccion = direccion  # 'Ux' o 'Uy'
    
    def gdl_restringidos(self) -> List[str]:
        return [self.direccion]
    
    def simbolo_grafico(self) -> str:
        return 'ROLLER_Y' if self.direccion == 'Uy' else 'ROLLER_X'


class ResorteElastico(Vinculo):
    """
    Vínculo elástico con rigidez finita.
    """
    def __init__(self, nudo: Nudo, kx: float = 0, ky: float = 0, ktheta: float = 0):
        super().__init__(nudo)
        self.kx = kx  # [kN/m]
        self.ky = ky  # [kN/m]
        self.ktheta = ktheta  # [kNm/rad]
    
    def gdl_restringidos(self) -> List[str]:
        # Resortes no restringen completamente, pero generan fuerzas de reacción
        return []
    
    def simbolo_grafico(self) -> str:
        return 'SPRING'


# ============ CARGAS ============

class Carga(ABC):
    """Clase base para todas las cargas."""
    pass


@dataclass
class CargaPuntualNudo(Carga):
    """Carga puntual aplicada directamente en un nudo."""
    nudo: Nudo
    Fx: float = 0.0  # [kN]
    Fy: float = 0.0  # [kN]
    Mz: float = 0.0  # [kNm]


@dataclass
class CargaPuntualBarra(Carga):
    """Carga puntual sobre una barra a distancia 'a' desde nudo i."""
    barra: Barra
    P: float  # [kN] (magnitud)
    a: float  # [m] (distancia desde nudo i)
    angulo: float = -90.0  # [°] (0°=horizontal derecha, -90°=vertical abajo)


@dataclass
class CargaDistribuidaBarra(Carga):
    """Carga distribuida sobre barra."""
    barra: Barra
    q1: float  # [kN/m] en x=0 (nudo i)
    q2: float  # [kN/m] en x=L (nudo j)
    tipo: str = 'uniforme'  # 'uniforme', 'triangular', 'trapezoidal'
    angulo: float = -90.0  # Dirección de la carga


@dataclass
class CargaTermica(Carga):
    """Carga térmica (variación uniforme o gradiente)."""
    barra: Barra
    delta_T_uniforme: float = 0.0  # [°C]
    delta_T_gradiente: float = 0.0  # [°C] (diferencia entre fibra superior e inferior)


# ============ SUBESTRUCTURA ============

class Subestructura:
    """
    Representa una configuración de carga (estructura fundamental o caso Xi).
    """
    def __init__(self, nombre: str, nudos: List[Nudo], barras: List[Barra]):
        self.nombre = nombre  # "Fundamental" o "X1", "X2", ...
        self.nudos = nudos
        self.barras = barras
        
        # Esfuerzos calculados en cada barra
        self.esfuerzos: Dict[int, Dict[str, Callable]] = {}  
        # esfuerzos[barra_id]['N'] = lambda x: ...
        
        # Reacciones en vínculos
        self.reacciones: Dict[int, np.ndarray] = {}  
        # reacciones[nudo_id] = [Rx, Ry, Mz]
    
    def calcular_esfuerzos(self):
        """
        Calcula N(x), V(x), M(x) para cada barra de esta subestructura.
        """
        # Implementación: resolver estructura isostática
        # Usando ecuaciones de equilibrio y funciones de barra
        pass
    
    def integrar_trabajo_virtual(self, otra: 'Subestructura') -> float:
        """
        Calcula fᵢⱼ = ∫(Mᵢ·Mⱼ)/(E·Jz)dx + ∫(Nᵢ·Nⱼ)/(E·A)dx
        
        Args:
            otra: Otra subestructura (j)
        
        Returns:
            Coeficiente de flexibilidad fᵢⱼ
        """
        integral_total = 0.0
        
        for barra in self.barras:
            # Obtener funciones de esfuerzo
            Mi = self.esfuerzos[barra.id]['M']
            Mj = otra.esfuerzos[barra.id]['M']
            Ni = self.esfuerzos[barra.id]['N']
            Nj = otra.esfuerzos[barra.id]['N']
            
            # Integración numérica (Simpson)
            n_puntos = 21  # Número de puntos (impar para Simpson)
            x_vals = np.linspace(0, barra.L, n_puntos)
            
            integrand_M = [Mi(x) * Mj(x) / (barra.material.E * barra.seccion.Jz) 
                          for x in x_vals]
            integrand_N = [Ni(x) * Nj(x) / (barra.material.E * barra.seccion.A) 
                          for x in x_vals]
            
            integral_M = simpson(integrand_M, x=x_vals)
            integral_N = simpson(integrand_N, x=x_vals)
            
            integral_total += integral_M + integral_N
        
        return integral_total


# ============ MOTOR DE MÉTODO DE FUERZAS ============

class MotorMetodoFuerzas:
    """
    Núcleo del análisis estructural.
    """
    def __init__(self, modelo: 'ModeloEstructural'):
        self.modelo = modelo
        self.gh = 0  # Grado de hiperestaticidad
        self.redundantes: List[str] = []  # Lista de redundantes seleccionados
        
        # Subestructuras generadas
        self.estructura_fundamental: Optional[Subestructura] = None
        self.subestructuras_Xi: List[Subestructura] = []
        
        # Sistema de ecuaciones de compatibilidad
        self.matriz_F: np.ndarray = None  # Matriz de flexibilidad
        self.vector_e0: np.ndarray = None  # Vector de términos independientes
        self.solucion_X: np.ndarray = None  # Valores de redundantes
    
    def calcular_grado_hiperestaticidad(self) -> int:
        """
        Fórmula: gh = r + v - 3n
        r: reacciones de vínculo
        v: vínculos internos (articulaciones internas restan GDL)
        n: número de nudos
        """
        n = len(self.modelo.nudos)
        r = sum(len(nudo.vinculo.gdl_restringidos()) 
                for nudo in self.modelo.nudos if nudo.vinculo)
        v = 0  # TODO: contar articulaciones internas si se implementan
        
        self.gh = r + v - 3 * n
        return self.gh
    
    def seleccionar_redundantes(self, metodo: str = 'auto') -> List[str]:
        """
        Identifica redundantes a eliminar.
        
        Args:
            metodo: 'auto' (heurística), 'manual' (usuario elige)
        
        Returns:
            Lista de redundantes (ej: ['Rx_nudo_2', 'M_nudo_3'])
        """
        if metodo == 'auto':
            # Heurística: priorizar reacciones de momento antes que fuerzas
            candidatos = []
            for nudo in self.modelo.nudos:
                if nudo.vinculo and 'theta_z' in nudo.vinculo.gdl_restringidos():
                    candidatos.append(f'Mz_nudo_{nudo.id}')
            
            # Completar con reacciones verticales
            for nudo in self.modelo.nudos:
                if nudo.vinculo and 'Uy' in nudo.vinculo.gdl_restringidos():
                    candidatos.append(f'Ry_nudo_{nudo.id}')
            
            # Tomar solo gh redundantes
            self.redundantes = candidatos[:self.gh]
        
        return self.redundantes
    
    def generar_estructura_fundamental(self) -> Subestructura:
        """
        Crea estructura isostática eliminando redundantes seleccionados.
        """
        # Copiar modelo original
        nudos_fund = copy.deepcopy(self.modelo.nudos)
        barras_fund = copy.deepcopy(self.modelo.barras)
        
        # Eliminar vínculos redundantes
        for red in self.redundantes:
            # Parsing del string: 'Mz_nudo_2' → liberar rotación en nudo 2
            if 'Mz' in red:
                nudo_id = int(red.split('_')[-1])
                nudo = next(n for n in nudos_fund if n.id == nudo_id)
                # Convertir empotramiento → apoyo fijo
                if isinstance(nudo.vinculo, Empotramiento):
                    nudo.vinculo = ApoyoFijo(nudo)
            
            # Similar para Rx, Ry...
        
        self.estructura_fundamental = Subestructura("Fundamental", nudos_fund, barras_fund)
        return self.estructura_fundamental
    
    def generar_subestructuras_Xi(self) -> List[Subestructura]:
        """
        Crea una subestructura por cada redundante con carga unitaria.
        """
        self.subestructuras_Xi = []
        
        for i, red in enumerate(self.redundantes):
            # Copiar estructura fundamental
            sub = copy.deepcopy(self.estructura_fundamental)
            sub.nombre = f"X{i+1}"
            
            # Aplicar carga unitaria según tipo de redundante
            if 'Mz' in red:
                nudo_id = int(red.split('_')[-1])
                nudo = next(n for n in sub.nudos if n.id == nudo_id)
                # Aplicar momento unitario M=+1 kNm
                carga = CargaPuntualNudo(nudo, Mz=1.0)
                # Agregar a sistema de cargas (depende de implementación)
            
            # Similar para fuerzas Rx, Ry...
            
            self.subestructuras_Xi.append(sub)
        
        return self.subestructuras_Xi
    
    def ensamblar_SECE(self):
        """
        Construye [F]·{X} = -{e₀}
        """
        n = self.gh
        self.matriz_F = np.zeros((n, n))
        self.vector_e0 = np.zeros(n)
        
        # Calcular fᵢⱼ
        for i in range(n):
            for j in range(n):
                self.matriz_F[i, j] = self.subestructuras_Xi[i].integrar_trabajo_virtual(
                    self.subestructuras_Xi[j]
                )
        
        # Calcular e₀ᵢ
        for i in range(n):
            self.vector_e0[i] = self.subestructuras_Xi[i].integrar_trabajo_virtual(
                self.estructura_fundamental
            )
        
        # Verificar simetría de F
        if not np.allclose(self.matriz_F, self.matriz_F.T, atol=1e-10):
            raise ValueError("La matriz de flexibilidad no es simétrica")
    
    def resolver_SECE(self) -> np.ndarray:
        """
        Resuelve el sistema y retorna vector de redundantes.
        """
        # Verificar condicionamiento
        cond = np.linalg.cond(self.matriz_F)
        if cond > 1e12:
            warnings.warn(f"Matriz mal condicionada (cond={cond:.2e}). "
                         "Considere reseleccionar redundantes.")
        
        # Resolver
        self.solucion_X = np.linalg.solve(self.matriz_F, -self.vector_e0)
        
        # Validar solución
        residual = np.linalg.norm(self.matriz_F @ self.solucion_X + self.vector_e0)
        if residual > 1e-8:
            warnings.warn(f"Residual alto en solución: {residual:.2e}")
        
        return self.solucion_X
    
    def calcular_resultados_finales(self):
        """
        Superpone diagramas: N_final = N₀ + ΣXᵢ·Nᵢ
        """
        for barra in self.modelo.barras:
            # Funciones de esfuerzo combinadas
            N0 = self.estructura_fundamental.esfuerzos[barra.id]['N']
            V0 = self.estructura_fundamental.esfuerzos[barra.id]['V']
            M0 = self.estructura_fundamental.esfuerzos[barra.id]['M']
            
            def N_final(x):
                suma = N0(x)
                for i, Xi_val in enumerate(self.solucion_X):
                    Ni = self.subestructuras_Xi[i].esfuerzos[barra.id]['N']
                    suma += Xi_val * Ni(x)
                return suma
            
            # Similar para V_final, M_final
            
            barra.N = N_final
            # barra.V = V_final
            # barra.M = M_final


# ============ MODELO COMPLETO ============

class ModeloEstructural:
    """
    Contenedor principal del modelo.
    """
    def __init__(self, nombre: str = "Sin título"):
        self.nombre = nombre
        self.nudos: List[Nudo] = []
        self.barras: List[Barra] = []
        self.cargas: List[Carga] = []
        
        # Motor de análisis
        self.motor = MotorMetodoFuerzas(self)
    
    def agregar_nudo(self, x: float, y: float, nombre: str = "") -> Nudo:
        nuevo_id = len(self.nudos) + 1
        nudo = Nudo(id=nuevo_id, x=x, y=y, nombre=nombre)
        self.nudos.append(nudo)
        return nudo
    
    def agregar_barra(self, nudo_i: Nudo, nudo_j: Nudo, 
                      material: Material, seccion: Seccion) -> Barra:
        nuevo_id = len(self.barras) + 1
        barra = Barra(nuevo_id, nudo_i, nudo_j, material, seccion)
        self.barras.append(barra)
        return barra
    
    def resolver(self):
        """
        Ejecuta el análisis completo.
        """
        # 1. Calcular grado de hiperestaticidad
        gh = self.motor.calcular_grado_hiperestaticidad()
        if gh < 0:
            raise ValueError("Estructura hipostática: faltan vínculos")
        if gh == 0:
            print("Estructura isostática: se resolverá directamente")
            # TODO: implementar solver isostático directo
            return
        
        # 2. Seleccionar redundantes
        self.motor.seleccionar_redundantes()
        
        # 3. Generar subestructuras
        self.motor.generar_estructura_fundamental()
        self.motor.generar_subestructuras_Xi()
        
        # 4. Calcular esfuerzos en cada subestructura
        self.motor.estructura_fundamental.calcular_esfuerzos()
        for sub in self.motor.subestructuras_Xi:
            sub.calcular_esfuerzos()
        
        # 5. Ensamblar y resolver SECE
        self.motor.ensamblar_SECE()
        self.motor.resolver_SECE()
        
        # 6. Combinar resultados
        self.motor.calcular_resultados_finales()
        
        print(f"Análisis completado. Redundantes resueltos: {self.motor.solucion_X}")
```

### 9.3) Stack tecnológico recomendado

| Componente | Tecnología | Justificación |
|------------|-----------|---------------|
| **Lenguaje** | Python 3.9+ | Ecosistema científico maduro, fácil mantenimiento |
| **GUI Framework** | **PyQt6** (opción 1) | Profesional, cross-platform, gran comunidad |
|  | Tkinter (opción 2) | Incluido en Python, ligero, suficiente para MVP |
| **Gráficos 2D** | Matplotlib | Estándar para gráficos científicos, exporta PDF/PNG |
| **Álgebra lineal** | NumPy + SciPy | Alto rendimiento, probado en ingeniería |
| **Integración numérica** | `scipy.integrate.simpson` | Precisa para trabajos virtuales |
| **Tests** | pytest | Framework estándar, fácil de usar |
| **Documentación** | Sphinx + autodoc | Genera HTML/PDF desde docstrings |
| **Control de versiones** | Git + GitHub | Estándar de la industria |
| **Empaquetado** | PyInstaller | Genera .exe standalone para Windows |
| **Formato de datos** | JSON | Legible, estándar, fácil debug |
| **Exportación gráfica** | ReportLab (PDF) | Generación de reportes profesionales |

### 9.4) Control numérico y estabilidad

**Estrategias críticas:**

1. **Detección de singularidad**: Antes de resolver, calcular `cond([F])`. Si `cond > 1e12`, sugerir:
   - Reseleccionar redundantes
   - Verificar geometría (barras muy cortas, colineales)
   - Aplicar regularización de Tikhonov en casos extremos

2. **Integración adaptativa**: Para barras con cargas complejas, subdividir automáticamente hasta que error de Simpson < tol

3. **Validación de equilibrio**: Post-análisis, verificar:
```
   ΣFx_nudos + ΣReacciones_x = 0  (tol < 1e-6 kN)
   ΣFy_nudos + ΣReacciones_y = 0
   ΣMz_global = 0

Comparación con solución analítica: Para casos simples (viga biempotrada, pórtico rectangular), comparar con fórmulas cerradas
Verificación de simetría: [F] debe ser simétrica por reciprocidad de Maxwell. Si ||F - F^T|| > 1e-10, emitir error


### 9.5) Visualización (Fase 2 - Implementado)

Módulo: src/ui/visualization/{diagramas.py, geometria.py, deformada.py}
API: graficar_diagrama_momentos/cortantes/axiles/combinados()
Exportación: PNG 300dpi ✓, PDF vectorial (pendiente)
Ejemplo completo: ejemplo_visualizacion.py
Documentación: VISUALIZACION.md


10) Referencias a Buenas Prácticas y Justificativos
10.1) Estándares de ingeniería de software

IEEE 29148-2018: Systems and software engineering — Life cycle processes — Requirements engineering
Aplicado en Sección 3 (Requisitos detallados) con separación RF/RNF
ISO/IEC 25010: Software Quality Model
Usado en RNF para definir atributos de calidad: rendimiento, usabilidad, mantenibilidad
PEP 8: Style Guide for Python Code
Código propuesto sigue convenciones estándar de nomenclatura y estructura

10.2) Análisis estructural – referencias académicas

Timoshenko & Young (1965). Theory of Structures. McGraw-Hill.
Método de las fuerzas clásico, trabajos virtuales
Gere & Weaver (1965). Analysis of Framed Structures. Van Nostrand.
Formulación matricial, coeficientes de flexibilidad
Hibbeler (2018). Structural Analysis. 10th Edition, Pearson.
Casos de validación modernos, convenciones de signos
Weaver & Gere (1990). Matrix Analysis of Framed Structures. 3rd Ed.
Integración numérica de trabajos virtuales, sección 4.5

10.3) Validación numérica

Demmel (1997). Applied Numerical Linear Algebra. SIAM.
Análisis de condicionamiento de matrices, errores de redondeo
Press et al. (2007). Numerical Recipes. 3rd Ed.
Integración de Simpson, solución de sistemas lineales

10.4) Diseño de interfaces técnicas

Nielsen (1993). Usability Engineering. Academic Press.
Principios aplicados en RF-05 para diseño de interfaz intuitiva
Blanchette & Summerfield (2008). C++ GUI Programming with Qt 4. Prentice Hall.
Patrones de diseño para aplicaciones PyQt (traducibles a PyQt6)

10.5) Arquitectura de software científico

Wilson et al. (2014). "Best Practices for Scientific Computing". PLOS Biology.
Modularidad, tests automatizados, control de versiones
Ince et al. (2012). "The case for open computer programs". Nature.
Justifica uso de JSON para formatos de datos abiertos


Apéndice A: Ejemplo de flujo completo
python# ============ SCRIPT DE EJEMPLO ============

from modelo import ModeloEstructural, Material, Seccion, Empotramiento, CargaPuntualBarra

# 1. Crear modelo
modelo = ModeloEstructural("Viga biempotrada - Ejemplo")

# 2. Definir material
acero = Material(nombre="Acero A-36", E=200e6)  # 200 GPa = 200e6 kN/m²

# 3. Definir sección
IPE220 = Seccion(nombre="IPE 220", A=33.4e-4, Jz=2772e-8)  # m², m⁴

# 4. Crear nudos
n1 = modelo.agregar_nudo(0, 0, "Apoyo A")
n2 = modelo.agregar_nudo(6, 0, "Apoyo B")

# 5. Crear barra
b1 = modelo.agregar_barra(n1, n2, acero, IPE220)

# 6. Aplicar vínculos
n1.vinculo = Empotramiento(n1)
n2.vinculo = Empotramiento(n2)

# 7. Aplicar carga puntual en centro
carga = CargaPuntualBarra(barra=b1, P=10.0, a=3.0, angulo=-90)  # 10 kN vertical
modelo.cargas.append(carga)

# 8. Resolver
modelo.resolver()

# 9. Consultar resultados
print(f"Momento en x=3m: {b1.M(3.0):.2f} kNm")
print(f"Reacciones: {modelo.motor.estructura_fundamental.reacciones}")

# 10. Exportar diagrama
import matplotlib.pyplot as plt
x_vals = np.linspace(0, b1.L, 100)
M_vals = [b1.M(x) for x in x_vals]
plt.plot(x_vals, M_vals)
plt.title("Diagrama de Momentos Flectores")
plt.xlabel("Posición x [m]")
plt.ylabel("Momento M [kNm]")
plt.grid(True)
plt.savefig("diagrama_M.png", dpi=300)
plt.show()
Resultado esperado: M(3m) ≈ -7.5 kNm (solución teórica: -P·L/8 = -10·6/8 = -7.5)

Apéndice B: Glosario de términos

gh (grado de hiperestaticidad): Número de ecuaciones de compatibilidad necesarias; cantidad de redundantes
Redundante (Xᵢ): Reacción o esfuerzo interno que se elimina para convertir estructura hiperestática en isostática
Estructura fundamental: Estructura isostática obtenida al eliminar redundantes
SECE: Sistema de Ecuaciones de Compatibilidad Elástica, [F]·{X} = -{e₀}
fᵢⱼ: Coeficiente de flexibilidad, desplazamiento en dirección i por carga unitaria en dirección j
e₀ᵢ: Término independiente, desplazamiento en dirección i debido a cargas reales
Trabajos virtuales: Método energético para calcular desplazamientos mediante ∫(M·δM)/(EJ)
Condicionamiento (cond): Medida de estabilidad numérica; matriz mal condicionada → solución imprecisa


Apéndice C: Checklist de validación
Antes de dar por completado el proyecto, verificar:

 10 casos de la literatura resueltos correctamente (error < 1%)
 Suite de tests cubre > 80% del código
 Interfaz gráfica responde en < 100 ms a eventos
 Tiempos de resolución cumplen metas (< 5 seg para 50 barras)
 Exportación PDF genera reportes legibles y profesionales
 Manual de usuario está completo con ejemplos paso a paso
 Código cumple PEP 8 (validado con flake8)
 Documentación técnica generada con Sphinx
 Ejecutable Windows probado en máquina limpia
 Verificación de equilibrio implementada y funcionando
 Mensajes de error son claros y ayudan al usuario


Apéndice D: Comandos Frecuentes

Tests:
pytest -v --tb=short                                      # Tests con tracebacks cortos
pytest -v --tb=no -q                                      # Tests sin tracebacks (resumen rápido)
cd tests/integration && pytest test_casos_clasicos.py -v # Solo casos de validación

Visualización:
python ejemplo_visualizacion.py                           # Ejemplo completo con diagramas

Limpieza:
rm -f test_*.py debug_*.py ejemplo_*.png                  # Eliminar archivos temporales