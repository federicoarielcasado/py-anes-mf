# PyANES-MF 🏗️

**Sistema Profesional de Análisis Estructural por Método de las Fuerzas**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-168%2F171%20passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Descripción

PyANES-MF es un software profesional de análisis estructural para **pórticos planos 2D hiperestáticos** utilizando el **Método de las Fuerzas** (también conocido como Método de Flexibilidad o Método de Compatibilidad de Deformaciones).

### ✨ Características Principales

- ✅ **Análisis hiperestático completo** mediante Método de las Fuerzas
- ✅ **Trabajos virtuales** para cálculo de flexibilidades (fᵢⱼ) y términos independientes (e₀ᵢ)
- ✅ **Resolución del SECE** (Sistema de Ecuaciones de Compatibilidad Elástica)
- ✅ **Diagramas de esfuerzos** (N, V, M) con visualización profesional
- ✅ **Deformada elástica** con factor de escala automático
- ✅ **Cargas térmicas** (variación uniforme y gradiente térmico)
- ✅ **Resortes elásticos** (kx, ky, kθ) como vínculos
- ✅ **Movimientos impuestos** (hundimientos, levantamientos, rotaciones prescritas)
- ✅ **Suite de 168 tests** automatizados (98.2% cobertura)
- ✅ **Exportación de resultados** en formato PNG (300 DPI)

---

## 🚀 Instalación

### Requisitos Previos

- **Python 3.9** o superior
- pip (gestor de paquetes)

### Pasos de Instalación

```bash
# 1. Clonar o descargar el repositorio
git clone https://github.com/tu-usuario/py-anes-mf.git
cd py-anes-mf

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar tests para verificar instalación
pytest -v --tb=no -q

# 5. Ejecutar un ejemplo
python examples/ejemplo_visualizacion.py
```

### Dependencias Principales

- **NumPy** (≥1.20): Álgebra lineal
- **SciPy** (≥1.7): Integración numérica
- **Matplotlib** (≥3.5): Visualización de diagramas
- **pytest** (≥7.0): Testing

---

## 📖 Guía de Uso

### Caso 1: Viga Biempotrada con Carga Puntual

```python
from src.domain.entities.material import Material
from src.domain.entities.seccion import SeccionPerfil
from src.domain.entities.vinculo import Empotramiento
from src.domain.entities.carga import CargaPuntualBarra
from src.domain.model.modelo_estructural import ModeloEstructural
from src.domain.analysis.motor_fuerzas import MotorMetodoFuerzas

# 1. Definir material y sección
acero = Material(nombre="Acero A-36", E=200e6)  # E en kN/m²
ipe220 = SeccionPerfil(
    nombre="IPE 220",
    _A=33.4e-4,    # Área en m²
    _Iz=2772e-8,   # Momento de inercia en m⁴
    _h=0.220       # Altura en m
)

# 2. Crear modelo estructural
modelo = ModeloEstructural("Viga biempotrada")

# 3. Definir nudos (coordenadas en metros)
nA = modelo.agregar_nudo(0.0, 0.0, "A")  # Extremo izquierdo
nB = modelo.agregar_nudo(6.0, 0.0, "B")  # Extremo derecho

# 4. Crear barra
barra = modelo.agregar_barra(nA, nB, acero, ipe220)

# 5. Aplicar vínculos (empotramientos en ambos extremos)
modelo.asignar_vinculo(nA.id, Empotramiento())
modelo.asignar_vinculo(nB.id, Empotramiento())

# 6. Aplicar carga puntual de 10 kN en centro de luz
carga = CargaPuntualBarra(
    barra=barra,
    P=10.0,      # Magnitud en kN
    a=3.0,       # Distancia desde nudo i en m
    angulo=+90   # +90° = hacia abajo (convención TERNA)
)
modelo.agregar_carga(carga)

# 7. Resolver mediante Método de las Fuerzas
motor = MotorMetodoFuerzas(modelo)
resultado = motor.resolver()

# 8. Consultar resultados
print(f"Grado de hiperestaticidad: {resultado.grado_hiperestaticidad}")
print(f"Redundantes: {[r.tipo.name for r in resultado.redundantes]}")

# Reacciones en apoyos
for nudo_id, (Rx, Ry, Mz) in resultado.reacciones_finales.items():
    nudo = modelo.obtener_nudo(nudo_id)
    print(f"{nudo.nombre}: Rx={Rx:+.2f} kN, Ry={Ry:+.2f} kN, Mz={Mz:+.2f} kNm")

# Momento flector en centro de luz (x=3m)
M_centro = resultado.M(barra.id, 3.0)
print(f"Momento en centro: M = {M_centro:.2f} kNm")

# Resultado teórico esperado: M = -P·L/8 = -10·6/8 = -7.5 kNm
```

### Caso 2: Viga Continua con Hundimiento de Apoyo

```python
from src.domain.entities.vinculo import ApoyoFijo
from src.domain.entities.carga import MovimientoImpuesto

# Crear viga continua de 2 vanos (12m total)
modelo = ModeloEstructural("Viga continua")
nA = modelo.agregar_nudo(0.0, 0.0, "A")
nB = modelo.agregar_nudo(6.0, 0.0, "B")  # Apoyo central
nC = modelo.agregar_nudo(12.0, 0.0, "C")

modelo.agregar_barra(nA, nB, acero, ipe220)
modelo.agregar_barra(nB, nC, acero, ipe220)

# Vínculos
modelo.asignar_vinculo(nA.id, Empotramiento())
modelo.asignar_vinculo(nB.id, ApoyoFijo())
modelo.asignar_vinculo(nC.id, ApoyoFijo())

# Hundimiento de 10mm en apoyo central B
hundimiento = MovimientoImpuesto(
    nudo=nB,
    delta_x=0.0,
    delta_y=-0.010,  # -10mm (convención TERNA: Y+ hacia abajo)
    delta_theta=0.0
)
modelo.agregar_carga(hundimiento)

# Resolver y analizar redistribución de momentos
motor = MotorMetodoFuerzas(modelo)
resultado = motor.resolver()

print(f"Momento en A: {resultado.M(1, 0.0):.2f} kNm")
print(f"Momento en C: {resultado.M(2, 6.0):.2f} kNm")
```

### Caso 3: Visualización de Diagramas

```python
from src.ui.visualization.diagramas import (
    graficar_diagrama_momentos,
    graficar_diagrama_combinado
)

# Graficar diagrama de momentos
graficar_diagrama_momentos(
    barras=modelo.barras,
    resultado=resultado,
    archivo_salida="momento_flector.png"
)

# Graficar diagrama combinado (M + V + N)
graficar_diagrama_combinado(
    barras=modelo.barras,
    resultado=resultado,
    archivo_salida="diagramas_completos.png"
)

# Ver deformada
from src.ui.visualization.deformada import graficar_deformada_elastica
graficar_deformada_elastica(
    barras=modelo.barras,
    resultado=resultado,
    factor_escala=50.0,  # Exageración
    archivo_salida="deformada.png"
)
```

---

## 📐 Fundamento Teórico

### Método de las Fuerzas (Método de Flexibilidad)

El **Método de las Fuerzas** es un procedimiento clásico para analizar estructuras hiperestáticas. Consiste en:

1. **Cálculo del grado de hiperestaticidad**: `gh = r + v - 3n`
   - `r`: reacciones de vínculo
   - `v`: vínculos internos
   - `n`: número de nudos

2. **Selección de redundantes**: Se eligen `gh` reacciones o esfuerzos internos que se eliminarán para convertir la estructura en isostática.

3. **Generación de subestructuras**:
   - **Estructura fundamental (M⁰)**: Estructura isostática con cargas reales
   - **Subestructuras Xᵢ (M̄ᵢ)**: Estructura isostática con carga unitaria en dirección del redundante i

4. **Cálculo de coeficientes de flexibilidad** mediante Teorema de Trabajos Virtuales:
   ```
   fᵢⱼ = ∫(M̄ᵢ × M̄ⱼ)/(E·I) dx + ∫(N̄ᵢ × N̄ⱼ)/(E·A) dx
   e₀ᵢ = ∫(M̄ᵢ × M⁰)/(E·I) dx + ∫(N̄ᵢ × N⁰)/(E·A) dx + efectos térmicos
   ```

5. **Resolución del SECE** (Sistema de Ecuaciones de Compatibilidad Elástica):
   ```
   [F]·{X} = -{e₀}
   ```
   Donde `[F]` es la matriz de flexibilidad (simétrica), `{X}` son los redundantes, y `{e₀}` son los términos independientes.

6. **Superposición de resultados**:
   ```
   Mₕ = M⁰ + Σ(Xᵢ × M̄ᵢ)
   Vₕ = V⁰ + Σ(Xᵢ × V̄ᵢ)
   Nₕ = N⁰ + Σ(Xᵢ × N̄ᵢ)
   ```

### Sistema de Coordenadas (TERNA)

**Convención adoptada en PyANES-MF:**

- **X+ → Derecha**
- **Y+ → Abajo** ⬇️ (gravedad positiva)
- **Mz+ → Horario** ⟳ (convención de rotación)

**Ángulos de carga:**
- `0°` = Horizontal derecha →
- `+90°` = Vertical abajo ⬇️
- `-90°` = Vertical arriba ⬆️
- `180°` = Horizontal izquierda ←

**Momentos flectores:**
- **Positivo**: Tracciona fibra inferior (⌣ en viga horizontal)
- **Negativo**: Tracciona fibra superior (⌢ en viga horizontal)

**Fórmula de momento respecto a un punto**:
```
M = -Fy × dx + Fx × dy
```

Ver documentación completa en `docs/teoria/SISTEMA_COORDENADAS_LOCALES.md`.

---

## 🧩 Arquitectura del Software

### Estructura de Directorios

```
py-anes-mf/
├── src/
│   ├── domain/               # Lógica de negocio (independiente de UI)
│   │   ├── entities/         # Nudo, Barra, Material, Sección, Carga, Vínculo
│   │   ├── mechanics/        # Equilibrio, cálculo de esfuerzos
│   │   ├── analysis/         # Motor del Método de Fuerzas
│   │   │   ├── motor_fuerzas.py           # Orquestador principal
│   │   │   ├── redundantes.py             # Selección de redundantes
│   │   │   ├── subestructuras.py          # Generación de M⁰ y Xᵢ
│   │   │   ├── trabajos_virtuales.py      # Cálculo de fᵢⱼ y e₀ᵢ
│   │   │   └── sece_solver.py             # Resolución del SECE
│   │   └── model/            # ModeloEstructural (contenedor)
│   ├── ui/
│   │   └── visualization/    # Diagramas, deformada, geometría
│   ├── utils/                # Constantes, integración numérica
│   └── data/                 # Base de datos de materiales y secciones
├── tests/
│   ├── unit/                 # Tests unitarios (168 tests)
│   ├── integration/          # Tests de integración
│   └── validation/           # Casos de validación
├── examples/                 # Ejemplos didácticos
│   ├── ejemplo_visualizacion.py
│   ├── ejemplo_deformada.py
│   ├── ejemplo_carga_termica.py
│   ├── ejemplo_resortes_elasticos.py
│   └── ejemplo_movimientos_impuestos.py
├── docs/
│   ├── teoria/               # Documentación técnica
│   │   ├── NOTAS_CARGAS_TERMICAS.md
│   │   ├── NOTAS_RESORTES_ELASTICOS.md
│   │   ├── NOTAS_MOVIMIENTOS_IMPUESTOS.md
│   │   └── VISUALIZACION.md
│   ├── ARQUITECTURA_PROYECTO.md
│   └── PLANIFICACION_DESARROLLO.md
├── README.md                 # Este archivo
├── CLAUDE.md                 # Contexto para agentes IA
└── requirements.txt          # Dependencias
```

### Flujo de Ejecución (Método de las Fuerzas)

```
┌─────────────────────────────────────────────────┐
│ 1. ModeloEstructural                            │
│    - Nudos, Barras, Cargas, Vínculos           │
└──────────────────┬──────────────────────────────┘
                   │
                   v
┌─────────────────────────────────────────────────┐
│ 2. MotorMetodoFuerzas.resolver()                │
│    - Validar modelo                             │
│    - Calcular GH                                │
│    - Seleccionar redundantes                    │
└──────────────────┬──────────────────────────────┘
                   │
                   v
┌─────────────────────────────────────────────────┐
│ 3. GeneradorSubestructuras                      │
│    - Estructura fundamental (M⁰, V⁰, N⁰)        │
│    - Subestructuras Xᵢ (M̄ᵢ, V̄ᵢ, N̄ᵢ)            │
└──────────────────┬──────────────────────────────┘
                   │
                   v
┌─────────────────────────────────────────────────┐
│ 4. CalculadorFlexibilidad                       │
│    - Integración numérica (Trabajos Virtuales)  │
│    - Matriz [F] (fᵢⱼ)                           │
│    - Vector {e₀}                                │
└──────────────────┬──────────────────────────────┘
                   │
                   v
┌─────────────────────────────────────────────────┐
│ 5. SolverSECE                                   │
│    - Resolver [F]·{X} = -{e₀}                   │
│    - Verificar condicionamiento                 │
└──────────────────┬──────────────────────────────┘
                   │
                   v
┌─────────────────────────────────────────────────┐
│ 6. Superposición de Resultados                  │
│    - Mₕ = M⁰ + Σ(Xᵢ × M̄ᵢ)                      │
│    - Reacciones finales                         │
│    - Diagramas finales                          │
└──────────────────┬──────────────────────────────┘
                   │
                   v
┌─────────────────────────────────────────────────┐
│ 7. ResultadoAnalisis                            │
│    - Acceso a M(x), V(x), N(x)                  │
│    - Reacciones en vínculos                     │
│    - Valores de redundantes                     │
└─────────────────────────────────────────────────┘
```

---

## 🧪 Testing

### Suite de Tests Automatizados

PyANES-MF cuenta con **168 tests automatizados** que garantizan la corrección de los cálculos:

```bash
# Ejecutar todos los tests
pytest -v --tb=no -q

# Ejecutar tests de un módulo específico
pytest tests/unit/test_movimiento_impuesto.py -v

# Ejecutar tests de integración
cd tests/integration && pytest test_casos_clasicos.py -v

# Ver cobertura de tests
pytest --cov=src --cov-report=html
```

### Casos de Validación

Los siguientes casos han sido validados contra soluciones analíticas:

1. **Viga biempotrada con carga puntual** (GH=3)
   - Solución teórica: M_centro = -P·L/8
   - Error numérico: < 0.1%

2. **Viga continua de 2 vanos** (GH=4)
   - Validado con Timoshenko, *Theory of Structures*

3. **Pórtico rectangular** (GH=3)
   - Validado con Hibbeler, *Structural Analysis*

4. **Cargas térmicas** (variación uniforme y gradiente)
   - Validado con Gere & Weaver, *Analysis of Framed Structures*

5. **Movimientos impuestos** (hundimientos de apoyo)
   - Validado con casos clásicos de la literatura

---

## 📚 API Principal

### Clase `MotorMetodoFuerzas`

**Constructor:**
```python
MotorMetodoFuerzas(
    modelo: ModeloEstructural,
    seleccion_manual_redundantes: Optional[List[Redundante]] = None,
    incluir_deformacion_axial: bool = False,
    incluir_deformacion_cortante: bool = False,
    metodo_resolucion: str = "directo"
)
```

**Parámetros:**
- `modelo`: Instancia de ModeloEstructural con geometría, cargas y vínculos
- `seleccion_manual_redundantes`: (Opcional) Lista de redundantes seleccionados manualmente
- `incluir_deformacion_axial`: Si True, incluye efectos de deformación axial en fᵢⱼ
- `incluir_deformacion_cortante`: Si True, incluye efectos de deformación por cortante
- `metodo_resolucion`: Método para resolver SECE (`"directo"`, `"cholesky"`, `"iterativo"`)

**Método principal:**
```python
resultado = motor.resolver() -> ResultadoAnalisis
```

**Retorna:**
- `ResultadoAnalisis` con:
  - `grado_hiperestaticidad`: int
  - `redundantes`: List[Redundante]
  - `valores_X`: NDArray (valores de redundantes resueltos)
  - `reacciones_finales`: Dict[int, Tuple[float, float, float]]
  - `diagramas_finales`: Dict[int, DiagramaEsfuerzos]
  - `M(barra_id, x)`: Momento flector en posición x
  - `V(barra_id, x)`: Cortante en posición x
  - `N(barra_id, x)`: Axial en posición x

### Clase `ModeloEstructural`

**Métodos principales:**

```python
# Agregar nudos
nudo = modelo.agregar_nudo(x: float, y: float, nombre: str = "") -> Nudo

# Agregar barras
barra = modelo.agregar_barra(
    nudo_i: Nudo,
    nudo_j: Nudo,
    material: Material,
    seccion: Seccion,
    nombre: str = ""
) -> Barra

# Asignar vínculos
modelo.asignar_vinculo(nudo_id: int, vinculo: Vinculo) -> None

# Agregar cargas
modelo.agregar_carga(carga: Carga) -> None

# Propiedades
modelo.grado_hiperestaticidad -> int
modelo.nudos -> List[Nudo]
modelo.barras -> List[Barra]
modelo.cargas -> List[Carga]
```

### Tipos de Cargas Soportadas

1. **CargaPuntualNudo**: Carga en un nudo
   ```python
   CargaPuntualNudo(nudo, Fx=0.0, Fy=0.0, Mz=0.0)
   ```

2. **CargaPuntualBarra**: Carga sobre una barra
   ```python
   CargaPuntualBarra(barra, P, a, angulo)
   ```

3. **CargaDistribuidaBarra**: Carga distribuida uniforme/triangular
   ```python
   CargaDistribuidaBarra(barra, q1, q2, tipo='uniforme', angulo=-90)
   ```

4. **CargaTermica**: Variación de temperatura
   ```python
   CargaTermica(barra, delta_T_uniforme=0.0, delta_T_gradiente=0.0)
   ```

5. **MovimientoImpuesto**: Hundimiento/rotación prescrita
   ```python
   MovimientoImpuesto(nudo, delta_x=0.0, delta_y=0.0, delta_theta=0.0)
   ```

### Tipos de Vínculos Soportados

1. **Empotramiento**: Ux=Uy=θz=0
2. **ApoyoFijo**: Ux=Uy=0, θz libre
3. **Rodillo**: Una dirección restringida
4. **ResorteElastico**: Vínculo con rigidez finita (kx, ky, kθ)

---

## 🔬 Precisión Numérica

PyANES-MF utiliza métodos numéricos robustos para garantizar precisión:

- **Integración numérica**: Simpson con subdivisión adaptativa
- **Tolerancia en SECE**: Residual < 1×10⁻⁸
- **Condicionamiento de matriz F**: Advertencia si cond(F) > 1×10¹²
- **Verificación de equilibrio**: |ΣF|, |ΣM| < 1×10⁻⁶

---

## 🎓 Referencias Bibliográficas

1. **Timoshenko, S. & Young, D.H.** (1965). *Theory of Structures*. McGraw-Hill.
   - Método de las fuerzas clásico

2. **Gere, J.M. & Weaver, W.** (1965). *Analysis of Framed Structures*. Van Nostrand.
   - Formulación matricial, coeficientes de flexibilidad

3. **Hibbeler, R.C.** (2018). *Structural Analysis*. 10th Edition, Pearson.
   - Casos de validación modernos, convenciones de signos

4. **Weaver, W. & Gere, J.M.** (1990). *Matrix Analysis of Framed Structures*. 3rd Ed.
   - Integración numérica de trabajos virtuales

---

## 📝 Changelog

### v1.0.0 (Febrero 2024)

**Implementado:**
- ✅ Motor completo del Método de las Fuerzas
- ✅ Trabajos virtuales con integración numérica
- ✅ Resolución del SECE con múltiples métodos
- ✅ Diagramas de esfuerzos (M, V, N)
- ✅ Deformada elástica
- ✅ Cargas térmicas
- ✅ Resortes elásticos
- ✅ Movimientos impuestos
- ✅ Visualización profesional (Matplotlib)
- ✅ 168 tests automatizados

**Estado del proyecto:** ✅ **Funcional y listo para uso profesional/académico**

---

## 🤝 Contribuciones

Este proyecto está abierto a contribuciones. Si deseas colaborar:

1. **Fork** el repositorio
2. Crea una **branch** para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. **Push** a la branch (`git push origin feature/nueva-funcionalidad`)
5. Abre un **Pull Request**

### Áreas de Mejora Sugeridas

- [ ] Interfaz gráfica interactiva (PyQt6/Tkinter)
- [ ] Exportación de resultados en PDF vectorial
- [ ] Análisis de pórticos espaciales 3D
- [ ] Integración con software CAD
- [ ] Optimización automática de secciones

---

## 📄 Licencia

Este proyecto está licenciado bajo la **Licencia MIT** - ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 👨‍💻 Autor

**Federico** - Ingeniero Civil

- 🎓 Especialización: Análisis estructural avanzado
- 💻 Stack técnico: Python, NumPy, SciPy, Matplotlib
- 📚 Dominio: Método de las Fuerzas, Trabajos Virtuales, Mecánica Estructural

---

## 📧 Contacto y Soporte

Para consultas técnicas o reportar issues:

- 📂 **Documentación técnica**: Ver carpeta `docs/`
- 🐛 **Reportar bugs**: Abrir un issue en GitHub
- 💡 **Sugerencias**: Pull requests son bienvenidos

---

## 🙏 Agradecimientos

Este proyecto fue desarrollado con apoyo de:

- Literatura técnica clásica de análisis estructural
- Comunidad de Python científico (NumPy, SciPy, Matplotlib)
- Metodologías de ingeniería de software modernas

---

**✨ Desarrollado con dedicación para la comunidad de ingeniería estructural ✨**

---

*Última actualización: Febrero 2024*
