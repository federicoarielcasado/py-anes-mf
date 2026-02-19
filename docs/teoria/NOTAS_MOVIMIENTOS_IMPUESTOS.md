# Movimientos Impuestos - Guía Técnica

## Estado Actual

✅ **COMPLETADO**:
- Clase `MovimientoImpuesto` en `src/domain/entities/carga.py` (pre-existente)
- Integración completa en motor de fuerzas
- 31 tests unitarios pasando (100%)
- Ejemplo demostrativo funcional (3 casos)

## Fundamento Teórico

### 1. Concepto de Movimiento Impuesto

Un movimiento impuesto es un **desplazamiento prescrito** en un nudo de la estructura:
- **Hundimiento**: δy < 0 (asentamiento de fundación)
- **Levantamiento**: δy > 0 (expansión del suelo)
- **Desplazamiento horizontal**: δx ≠ 0
- **Rotación prescrita**: δθ ≠ 0

### 2. Método de las Fuerzas con Movimientos Impuestos

En el método de fuerzas, los movimientos impuestos modifican el **lado derecho del SECE**:

**Sin movimientos impuestos**:
```
[F]·{X} = -{e₀}
```

**Con movimientos impuestos**:
```
[F]·{X} = {eₕ} - {e₀}
```

Donde:
- `{eₕ}`: vector de movimientos impuestos en direcciones de redundantes
- Los movimientos que coinciden con redundantes → van a eₕ
- Los movimientos en otros nudos → contribuyen a e₀ᵢ vía trabajo virtual

### 3. Contribuciones de Movimientos Impuestos

**Caso A: Movimiento en el mismo nudo que redundante Xᵢ**
```
eₕᵢ = δₖ    (va directo al lado derecho)
```

**Caso B: Movimiento en otro nudo**
```
e₀ᵢ += P̄ᵢₖ × δₖ    (trabajo virtual)
```

Donde `P̄ᵢₖ` es la reacción virtual en el nudo k debido a la carga unitaria Xᵢ.

## Implementación en Python

### Uso Básico

```python
from src.domain.entities.carga import MovimientoImpuesto
from src.domain.model.modelo_estructural import ModeloEstructural
from src.domain.analysis.motor_fuerzas import MotorMetodoFuerzas

# Crear modelo (nudos, barras, vínculos)
modelo = ModeloEstructural("Viga con hundimiento")
nA = modelo.agregar_nudo(0.0, 0.0, "A")
nB = modelo.agregar_nudo(6.0, 0.0, "B")
# ... (definir barra y vínculos)

# Hundimiento de 10mm en nudo B
hundimiento = MovimientoImpuesto(
    nudo=nB,
    delta_x=0.0,
    delta_y=-0.010,  # -10mm (convención TERNA: Y+ hacia abajo)
    delta_theta=0.0
)
modelo.agregar_carga(hundimiento)

# Resolver
motor = MotorMetodoFuerzas(modelo)
resultado = motor.resolver()

# Consultar resultados
print(f"Momento en A: {resultado.M(1, 0.0):.2f} kNm")
```

### Propiedades de MovimientoImpuesto

- `es_hundimiento`: True si δy < 0 (con tolerancia)
- `es_levantamiento`: True si δy > 0
- `componentes()`: Retorna tupla (δx, δy, δθ)
- `descripcion`: Descripción textual del movimiento

## Casos de Validación

### Caso 1: Viga Continua con Hundimiento de Apoyo Central

**Configuración**:
- Viga continua de 2 vanos (12m total)
- Apoyos: A (empotramiento), B (apoyo fijo), C (apoyo fijo)
- Hundimiento: δy = -10mm en B

**Comportamiento esperado**:
- Momentos negativos en A y C (fibra superior traccionada)
- Redistribución de reacciones
- Sin cargas externas, reacciones suman cero (equilibrio)

### Caso 2: Viga Biempotrada con Hundimiento en Extremo

**Configuración**:
- Viga de 6m biempotrada
- Hundimiento: δy = -8mm en extremo B

**Resultado teórico**:
- Momentos de empotramiento en ambos extremos
- Reacciones verticales para compensar el hundimiento
- Deformada de doble flexión

### Caso 3: Viga Biempotrada con Rotación Prescrita

**Configuración**:
- Viga de 6m biempotrada
- Rotación: δθ = 0.002 rad (≈0.115°) en extremo B

**Resultado teórico**:
- Momento resistente en A
- Reacciones verticales para compatibilidad
- Sin cargas externas, momentos puros de compatibilidad

## Integración en motor_fuerzas.py

### Archivos Modificados

1. **`trabajos_virtuales.py`**:
   - Agregado parámetro `movimientos_impuestos`
   - Método `_calcular_e0i_movimientos_impuestos(i)`: calcula contribución a e₀ᵢ
   - Modificado `_calcular_e0i()` para incluir movimientos

2. **`motor_fuerzas.py`**:
   - Método `_calcular_movimientos_impuestos_en_redundantes()`: construye vector eₕ
   - Modificado `_calcular_coeficientes_flexibilidad()` para pasar movimientos
   - Modificado `_resolver_sece()` para usar vector eₕ

3. **`sece_solver.py`** (ya compatible):
   - Clase `SolverSECE` ya soporta parámetro `eh`
   - Ecuación: `b = eh - e0`

## Validación y Testing

### Tests Implementados (31/31 ✅)

**`tests/unit/test_movimiento_impuesto.py`**:
- Creación de movimientos (vertical, horizontal, rotacional, combinado)
- Propiedades (`es_hundimiento`, `es_levantamiento`, `componentes`)
- Descripción textual
- Casos límite (movimiento nulo, muy grande, muy pequeño)
- Integración con nudos
- Tipos de carga

### Suite Completa

```bash
# Tests específicos
pytest tests/unit/test_movimiento_impuesto.py -v    # 31 tests

# Suite completa
pytest -v --tb=no -q                                # 168 tests
```

## Referencias

1. **Timoshenko & Young** (1965). *Theory of Structures*. Cap. 9: "Influence Lines"
   - Movimientos impuestos en estructuras hiperestáticas

2. **Hibbeler** (2018). *Structural Analysis*. 10th Ed. Sección 11-4
   - Ejemplo clásico: viga continua con hundimiento de apoyo

3. **Gere & Weaver** (1965). *Analysis of Framed Structures*. Sección 5.7
   - Método de fuerzas con desplazamientos prescritos
   - Formulación matricial del término eₕ

## Aplicaciones Prácticas

### 1. Asentamientos Diferenciales

**Problema**: Fundación de edificio sobre suelo compresible.

**Datos típicos**:
- Asentamiento diferencial: 5-20mm (normal)
- Asentamiento excesivo: >25mm (puede causar daños)

**Modelado**:
```python
hundimiento_central = MovimientoImpuesto(
    nudo=nudo_fundacion,
    delta_y=-0.015  # -15mm
)
```

### 2. Expansión Térmica de Apoyos

**Problema**: Puente con apoyo deslizante bloqueado temporalmente.

**Modelado**:
```python
desplazamiento_termico = MovimientoImpuesto(
    nudo=apoyo_bloqueado,
    delta_x=0.008  # 8mm expansión horizontal
)
```

### 3. Conexiones Semirrígidas

**Problema**: Conexión con rotación prescrita por detalle constructivo.

**Modelado**:
```python
rotacion_conexion = MovimientoImpuesto(
    nudo=conexion,
    delta_theta=0.001  # 0.001 rad ≈ 0.057°
)
```

## Próximos Pasos

✅ Implementación completa
✅ Tests comprehensivos
✅ Ejemplo demostrativo
✅ Documentación

## Notas de Implementación

- La clase `MovimientoImpuesto` hereda de `Carga` (`TipoCarga.MOVIMIENTO_IMPUESTO`)
- Compatible con el sistema existente de cargas del modelo
- Los movimientos se filtran automáticamente del modelo en el motor
- El vector eₕ se calcula automáticamente en `_resolver_sece()`
- Los movimientos en nudos no redundantes contribuyen a e₀ᵢ vía trabajo virtual
- **Convención de signos (TERNA)**: Y+ hacia abajo, rotación horaria positiva
