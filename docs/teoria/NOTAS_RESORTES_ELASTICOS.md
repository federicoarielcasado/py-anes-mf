# Vínculos Elásticos (Resortes) - Guía Técnica

## Estado Actual

✅ **Implementado**:
- Clase `ResorteElastico` en `src/domain/entities/vinculo.py`
- Rigideces traslacionales: kx, ky [kN/m]
- Rigidez rotacional: kθ [kNm/rad]
- Funciones auxiliares: `crear_resorte_vertical/horizontal/rotacional()`
- 30 tests unitarios pasando (100%)
- Ejemplo demostrativo funcional

✅ **También implementado**:
- Integración en el motor de fuerzas: funciones `_agregar_flexibilidad_resortes()` y `_calcular_e0i_resortes()` en `trabajos_virtuales.py`
- Modificación de matriz de flexibilidad: término 1/k en diagonal F[i,i] para cada resorte redundante
- Validación con casos clásicos: `tests/unit/test_resorte_elastico.py` (35/35 tests)

## Fundamento Teórico

### 1. Concepto de Vínculo Elástico

Un vínculo elástico (resorte) es un apoyo con **rigidez finita** que permite desplazamiento proporcional a la carga aplicada:

```
F = -k × δ
```

Donde:
- F = fuerza de reacción [kN]
- k = rigidez del resorte [kN/m]
- δ = desplazamiento [m]

**Comparación con vínculos rígidos**:
- Vínculo rígido: k → ∞, δ = 0 (desplazamiento nulo)
- Vínculo elástico: k finito, δ ≠ 0 (desplazamiento permitido)
- Vínculo libre: k = 0, δ indeterminado

### 2. Tipos de Rigidez

#### a) Rigidez Traslacional Horizontal (kx)

```
Rx = -kx × Ux
```

**Aplicaciones**:
- Fricción suelo-fundación
- Amortiguadores horizontales
- Apoyos deslizantes con fricción

#### b) Rigidez Traslacional Vertical (ky)

```
Ry = -ky × Uy
```

**Aplicaciones**:
- Fundaciones sobre suelo elástico
- Módulo de balasto (Winkler): ky = k × A [kN/m]
- Apoyos elastoméricos (neopreno)

**Valores típicos**:
- Suelo blando: ky = 1,000 - 10,000 kN/m
- Suelo medio: ky = 10,000 - 50,000 kN/m
- Suelo rígido/roca: ky = 50,000 - 200,000 kN/m

#### c) Rigidez Rotacional (kθ)

```
Mz = -kθ × θz
```

**Aplicaciones**:
- Empotramientos parciales
- Conexiones semirrígidas
- Uniones atornilladas con rigidez limitada

**Relación con rigidez de conexión**:
- kθ = 0: articulación perfecta (libre rotación)
- kθ finito: conexión semirrígida
- kθ → ∞: empotramiento perfecto

### 3. Integración en Método de las Fuerzas

#### Modificación de la Matriz de Flexibilidad

Para un resorte en un nudo con rigidez k, la matriz de flexibilidad se modifica:

**Sistema sin resorte**:
```
[F] · {X} = -{e₀}
```

**Sistema con resorte**:
```
[F + Fₖ] · {X} = -{e₀}
```

Donde Fₖ es la contribución del resorte:
```
Fₖ[i,i] = 1/k
```

**Efecto**: Aumenta la flexibilidad del sistema (más deformable).

#### Trabajo Virtual con Resortes

El trabajo realizado por un resorte es:

```
W = ∫ F·dδ = ∫ k·δ·dδ = (1/2)·k·δ²
```

Para el método de las fuerzas:
```
δᵢ_resorte = (1/k) · Fᵢ
```

Donde Fᵢ es la fuerza virtual en el resorte.

## Implementación en Python

### Uso Básico

```python
from src.domain.entities.vinculo import ResorteElastico

# Resorte vertical (suelo elástico)
resorte_suelo = ResorteElastico(
    kx=0,        # Sin rigidez horizontal
    ky=50000,    # 50,000 kN/m (suelo rígido)
    ktheta=0     # Sin rigidez rotacional
)

# Resorte rotacional (empotramiento parcial)
resorte_rotacional = ResorteElastico(
    kx=0,
    ky=1e9,      # Muy rígido en Y (≈ infinito)
    ktheta=5000  # 5,000 kNm/rad
)

# Resorte combinado (fundación real)
resorte_combinado = ResorteElastico(
    kx=10000,    # Fricción horizontal
    ky=50000,    # Compresión vertical
    ktheta=2000  # Giro de fundación
)
```

### Funciones de Conveniencia

```python
from src.domain.entities.vinculo import (
    crear_resorte_vertical,
    crear_resorte_horizontal,
    crear_resorte_rotacional
)

# Creación rápida
r1 = crear_resorte_vertical(5000)      # ky = 5000 kN/m
r2 = crear_resorte_horizontal(3000)    # kx = 3000 kN/m
r3 = crear_resorte_rotacional(2000)    # kθ = 2000 kNm/rad
```

### Asignación a Nudos

```python
from src.domain.model.modelo_estructural import ModeloEstructural

modelo = ModeloEstructural("Viga sobre suelo elástico")

# Crear nudos
nA = modelo.agregar_nudo(0.0, 0.0, "A")
nB = modelo.agregar_nudo(6.0, 0.0, "B")

# Asignar resortes
resorte_A = ResorteElastico(kx=0, ky=10000, ktheta=0)
modelo.asignar_vinculo(nA.id, resorte_A)
```

### Cálculo de Reacciones

```python
# Después del análisis
resorte = modelo.nudos[0].vinculo

# Obtener desplazamiento calculado
Uy = modelo.nudos[0].Uy  # [m]

# Calcular reacción
Ry = -resorte.ky * Uy  # [kN]

print(f"Desplazamiento: {Uy*1000:.2f} mm")
print(f"Reacción: {Ry:.2f} kN")
```

## Casos de Validación

### Caso 1: Viga sobre Apoyo Elástico

**Configuración**:
- Viga simplemente apoyada: L = 6 m
- Apoyo A: empotramiento rígido
- Apoyo B: resorte elástico ky = 5,000 kN/m
- Carga: P = 10 kN en centro

**Solución teórica aproximada**:

Para viga con un apoyo elástico:
```
δB = RB / ky
```

Donde RB es la reacción en B (depende de la rigidez del resorte).

**Límites**:
- Si ky → ∞: comportamiento de viga biapoyada
- Si ky → 0: comportamiento de viga en voladizo

### Caso 2: Fundación sobre Suelo Elástico

**Datos**:
- Zapata cuadrada: 2m × 2m
- Módulo de reacción del suelo: k = 20,000 kN/m³
- Rigidez equivalente: ky = k × A = 20,000 × 4 = 80,000 kN/m

**Aplicación**:
```python
# Modelar zapata como resorte
resorte_zapata = ResorteElastico(
    kx=0,
    ky=80000,  # k × área
    ktheta=0
)
```

**Resultado esperado**:
```
Carga aplicada: P = 100 kN
Asentamiento: δ = P/ky = 100/80000 = 0.00125 m = 1.25 mm
```

### Caso 3: Conexión Semirrígida

**Parámetros**:
- Conexión atornillada con rigidez rotacional limitada
- kθ = 3,000 kNm/rad

**Comparación**:

| Tipo de conexión | kθ [kNm/rad] | Rotación bajo M=10 kNm |
|------------------|--------------|------------------------|
| Articulación | 0 | ∞ (libre) |
| Semirrígida | 3,000 | 0.0033 rad ≈ 0.19° |
| Empotramiento | ∞ | 0 (nula) |

## Integración en motor_fuerzas.py

### Modificaciones Necesarias

1. **Detectar resortes en vínculos**:

```python
def identificar_resortes(modelo: ModeloEstructural) -> List[ResorteElastico]:
    """
    Identifica todos los vínculos elásticos del modelo.
    """
    resortes = []
    for nudo in modelo.nudos:
        if isinstance(nudo.vinculo, ResorteElastico):
            resortes.append(nudo.vinculo)
    return resortes
```

2. **Modificar matriz de flexibilidad**:

```python
def agregar_flexibilidad_resortes(
    matriz_F: np.ndarray,
    resortes: List[ResorteElastico],
    subestructuras: List[Subestructura]
) -> np.ndarray:
    """
    Agrega la contribución de resortes a la matriz de flexibilidad.

    Para cada resorte con rigidez k en dirección i:
    F[i,i] += 1/k
    """
    F_modificada = matriz_F.copy()

    for resorte in resortes:
        if resorte.kx > 0:
            # Agregar flexibilidad horizontal: 1/kx
            idx_x = indice_redundante_x(resorte.nudo)
            F_modificada[idx_x, idx_x] += 1/resorte.kx

        if resorte.ky > 0:
            # Agregar flexibilidad vertical: 1/ky
            idx_y = indice_redundante_y(resorte.nudo)
            F_modificada[idx_y, idx_y] += 1/resorte.ky

        if resorte.ktheta > 0:
            # Agregar flexibilidad rotacional: 1/kθ
            idx_theta = indice_redundante_theta(resorte.nudo)
            F_modificada[idx_theta, idx_theta] += 1/resorte.ktheta

    return F_modificada
```

3. **Cálculo de reacciones en resortes**:

```python
def calcular_reacciones_resortes(
    modelo: ModeloEstructural,
    desplazamientos: np.ndarray
) -> None:
    """
    Calcula reacciones en resortes: R = -k × δ
    """
    for nudo in modelo.nudos:
        if isinstance(nudo.vinculo, ResorteElastico):
            resorte = nudo.vinculo

            # Reacción horizontal
            if resorte.kx > 0:
                resorte.Rx = -resorte.kx * nudo.Ux

            # Reacción vertical
            if resorte.ky > 0:
                resorte.Ry = -resorte.ky * nudo.Uy

            # Momento de reacción
            if resorte.ktheta > 0:
                resorte.Mz = -resorte.ktheta * nudo.theta_z
```

## Validación y Testing

### Tests Implementados (30/30 ✅)

1. **Creación y validación**:
   - Resortes vertical, horizontal, rotacional
   - Validación de rigideces negativas
   - Error si todas las rigideces son cero

2. **GDL restringidos**:
   - Identificación correcta de GDL con rigidez
   - Resortes combinados

3. **Propiedades**:
   - Flags `es_resorte_traslacional` y `es_resorte_rotacional`
   - Tupla de rigideces

4. **Cálculo de reacciones**:
   - R = -k × δ (validación conceptual)
   - Rigidez infinita → vínculo rígido

### Casos de Prueba Pendientes

- Viga sobre apoyo elástico (comparar con solución analítica)
- Pórtico con fundación elástica
- Conexión semirrígida (calibración con ensayos)

## Referencias

1. **Timoshenko & Gere** (1972). *Mechanics of Materials*. Cap. 2: "Stress and Strain"
   - Ley de Hooke para resortes lineales
   - Rigidez equivalente de sistemas

2. **Bowles, J.E.** (1996). *Foundation Analysis and Design*. 5th Ed.
   - Módulo de reacción del suelo (coeficiente de balasto)
   - Rigidez de fundaciones superficiales

3. **Chen, W.F. & Lui, E.M.** (1991). *Stability Design of Steel Frames*
   - Conexiones semirrígidas
   - Curvas momento-rotación

4. **ASCE 7-16**. *Minimum Design Loads for Buildings*
   - Modelado de interacción suelo-estructura
   - Coeficientes de rigidez recomendados

## Aplicaciones Prácticas

### 1. Análisis de Fundaciones

**Problema**: Diseñar fundación aislada sobre suelo compresible.

**Solución**:
```python
# Datos del suelo
k_suelo = 15000  # kN/m³ (módulo de balasto)
A_zapata = 2.0 * 2.0  # m²

# Rigidez equivalente
ky = k_suelo * A_zapata  # 60,000 kN/m

# Modelar como resorte
resorte_fundacion = ResorteElastico(kx=0, ky=ky, ktheta=0)
```

### 2. Conexiones Metálicas

**Problema**: Evaluar rigidez de conexión atornillada.

**Datos de ensayo**:
- Momento aplicado: M = 50 kNm
- Rotación medida: θ = 0.008 rad

**Rigidez**:
```
kθ = M/θ = 50/0.008 = 6,250 kNm/rad
```

**Modelado**:
```python
conexion = ResorteElastico(kx=0, ky=1e9, ktheta=6250)
```

### 3. Apoyos Elastoméricos

**Datos típicos** (Almohadilla de neopreno 300×300×50 mm):
- Módulo de corte: G = 1.0 MPa
- Rigidez horizontal: kx = G×A/e = 1000×0.09/0.05 = 1,800 kN/m
- Rigidez vertical: ky ≈ 200,000 kN/m (muy rígida)

```python
apoyo_neopreno = ResorteElastico(
    kx=1800,     # Corte horizontal
    ky=200000,   # Compresión vertical
    ktheta=0
)
```

## Próximos Pasos

1. ✅ Implementar clase `ResorteElastico` → **COMPLETADO**
2. ✅ Crear tests unitarios → **COMPLETADO** (30/30)
3. ✅ Crear ejemplo demostrativo → **COMPLETADO**
4. ✅ Integrar en motor de fuerzas → **COMPLETADO**
   - `_agregar_flexibilidad_resortes()`: agrega 1/k a F[i,i]
   - `_calcular_desplazamientos_resortes()`: δ = R/k post-análisis
5. ✅ Validar con casos de literatura → **COMPLETADO** (35/35 tests unitarios)
6. ⏳ Crear tests de integración end-to-end (análisis hiperestático completo con resorte)

## Notas de Implementación

- La clase `ResorteElastico` hereda de `Vinculo`
- El método `gdl_restringidos()` retorna GDL con rigidez > 0
- Permite combinar las tres rigideces (kx, ky, kθ) simultáneamente
- Validación: al menos una rigidez debe ser positiva
- Compatible con el sistema existente de vínculos
