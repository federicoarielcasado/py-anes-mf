# Integración de Cargas Térmicas en el Método de las Fuerzas

## Estado Actual

✅ **Implementado**:
- Clase `CargaTermica` en `src/domain/entities/carga.py`
- Cálculo de deformación axial libre: δ = α·ΔT·L
- Cálculo de curvatura térmica: κ = (α·ΔT_grad) / h
- Métodos para trabajos virtuales:
  - `trabajo_virtual_uniforme(N_virtual)`
  - `trabajo_virtual_gradiente(M_virtual_func)`
- Ejemplo funcional: `ejemplo_carga_termica.py`
- 20 tests unitarios pasando (100%)

⏳ **Pendiente**:
- Integración en el motor de fuerzas (`motor_fuerzas.py`)
- Cálculo de términos independientes e₀ᵢ con efectos térmicos
- Validación con casos de literatura

## Fundamento Teórico

### 1. Efectos de Variación Uniforme de Temperatura (ΔT)

En una estructura hiperestática, una variación uniforme de temperatura genera:

**Deformación libre** (sin restricciones):
```
δ = α·ΔT·L
```

**En estructura restringida**:
- Se genera un esfuerzo axial: N = -E·A·α·ΔT
- Contribución al término independiente e₀ᵢ:

```
e₀ᵢ_térmico = α·ΔT·∫(Nᵢ dx)
```

donde Nᵢ(x) es el esfuerzo axial en la subestructura virtual Xi.

### 2. Efectos de Gradiente Térmico (ΔT_grad)

Un gradiente térmico lineal (diferencia entre fibra superior e inferior) genera:

**Curvatura libre**:
```
κ = (α·ΔT_grad) / h
```

**En estructura restringida**:
- Se generan momentos de empotramiento
- Contribución al término independiente e₀ᵢ:

```
e₀ᵢ_térmico = (α·ΔT_grad/h)·∫(Mᵢ dx)
```

donde Mᵢ(x) es el momento flector en la subestructura virtual Xi.

### 3. Combinación de Efectos

Para una carga térmica combinada (ΔT uniforme + gradiente):

```
e₀ᵢ_total = α·ΔT_unif·∫(Nᵢ dx) + (α·ΔT_grad/h)·∫(Mᵢ dx)
```

## Integración en motor_fuerzas.py

### Modificaciones Necesarias

1. **En la función de cálculo de e₀ᵢ**, agregar contribuciones térmicas:

```python
def calcular_termino_independiente(
    subestructura_fundamental,
    subestructura_Xi,
    cargas_termicas: List[CargaTermica]
) -> float:
    """
    Calcula e₀ᵢ = desplazamiento en dirección i debido a cargas reales.

    Incluye:
    - Trabajos virtuales mecánicos: ∫(M₀·Mᵢ)/(EI) + ∫(N₀·Nᵢ)/(EA)
    - Trabajos virtuales térmicos: α·ΔT·∫(Nᵢ) + κ·∫(Mᵢ)
    """
    e0_mecanico = calcular_trabajo_virtual_mecanico(...)
    e0_termico = calcular_trabajo_virtual_termico(subestructura_Xi, cargas_termicas)

    return e0_mecanico + e0_termico
```

2. **Nueva función para trabajos virtuales térmicos**:

```python
def calcular_trabajo_virtual_termico(
    subestructura_Xi,
    cargas_termicas: List[CargaTermica]
) -> float:
    """
    Calcula la contribución térmica al término independiente e₀ᵢ.

    Para cada carga térmica en cada barra:
    - Uniforme: α·ΔT·∫(Nᵢ dx)
    - Gradiente: κ·∫(Mᵢ dx)
    """
    trabajo_total = 0.0

    for carga in cargas_termicas:
        if not isinstance(carga, CargaTermica):
            continue

        barra = carga.barra
        if not barra:
            continue

        # Obtener esfuerzos virtuales en esta barra
        N_virtual = subestructura_Xi.esfuerzos[barra.id]['N']  # Función N(x)
        M_virtual = subestructura_Xi.esfuerzos[barra.id]['M']  # Función M(x)

        # Contribución uniforme
        if abs(carga.delta_T_uniforme) > 1e-10:
            # Para axil constante: ∫(Nᵢ dx) = Nᵢ·L
            # Para axil variable: integración numérica
            trabajo_uniforme = carga.trabajo_virtual_uniforme(N_virtual(0))
            trabajo_total += trabajo_uniforme

        # Contribución gradiente
        if abs(carga.delta_T_gradiente) > 1e-10:
            trabajo_gradiente = carga.trabajo_virtual_gradiente(M_virtual)
            trabajo_total += trabajo_gradiente

    return trabajo_total
```

3. **En el ensamblaje del SECE**, asegurar que se incluyan cargas térmicas:

```python
def ensamblar_sistema_compatibilidad(
    modelo: ModeloEstructural,
    subestructuras_Xi: List[Subestructura]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Ensambla [F]·{X} = -{e₀}
    """
    n = len(subestructuras_Xi)
    F = np.zeros((n, n))
    e0 = np.zeros(n)

    # Calcular matriz de flexibilidad (sin cambios)
    for i in range(n):
        for j in range(n):
            F[i, j] = calcular_coeficiente_flexibilidad(subestructuras_Xi[i], subestructuras_Xi[j])

    # Calcular términos independientes (CON cargas térmicas)
    cargas_termicas = [c for c in modelo.cargas if isinstance(c, CargaTermica)]

    for i in range(n):
        e0[i] = calcular_termino_independiente(
            modelo.estructura_fundamental,
            subestructuras_Xi[i],
            cargas_termicas  # ← NUEVO
        )

    return F, e0
```

## Caso de Validación

### Viga Biempotrada con ΔT Uniforme

**Datos**:
- L = 6 m
- E = 200 GPa = 200×10⁶ kN/m²
- A = 0.15 m² (sección 30×50 cm)
- α = 1.2×10⁻⁵ 1/°C
- ΔT = +30°C

**Solución teórica**:

1. Deformación libre: δ = α·ΔT·L = 1.2e-5 × 30 × 6 = 2.16 mm

2. Grado de hiperestaticidad: gh = 3 (viga biempotrada)

3. Redundantes típicos: X₁ = Rx_A, X₂ = Ry_A, X₃ = Mz_A

4. Para X₃ (momento en A):
   - Estructura fundamental: ambos empotramientos liberados en rotación → viga biapoyada
   - Estructura X₃: viga biapoyada con momento unitario en A

5. Cálculo de e₀₃:
   ```
   e₀₃ = α·ΔT·∫(N₃ dx)
   ```

   En una viga biapoyada con momento aplicado en un extremo:
   - El esfuerzo axial N₃ = 0 (no hay fuerzas horizontales)
   - Por lo tanto: **e₀₃ = 0** para este caso particular

6. **Resultado esperado**:
   - Como la viga es simétrica y solo hay ΔT uniforme (no gradiente):
   - No hay momento flector generado
   - Solo hay esfuerzo axial de compresión: N = -E·A·α·ΔT = -10,800 kN

### Viga Biempotrada con Gradiente Térmico

**Datos adicionales**:
- h = 0.50 m
- ΔT_grad = +20°C (cara superior más caliente)

**Solución teórica**:

1. Curvatura libre: κ = (α·ΔT_grad)/h = (1.2e-5 × 20)/0.5 = 4.8×10⁻⁴ 1/m

2. Momento de empotramiento:
   ```
   M_A = M_B = -E·Iz·κ·(L²/12)
   ```

   Con Iz = b·h³/12 = 0.30×0.50³/12 = 3.125×10⁻³ m⁴:
   ```
   M = -200e6 × 3.125e-3 × 4.8e-4 = -300 kNm
   ```

3. Cálculo de e₀₃ (rotación en A por gradiente térmico):
   ```
   e₀₃ = κ·∫(M₃ dx)
   ```

   Para viga biapoyada con M=1 en A:
   - M₃(x) = (1 - x/L) (lineal de 1 a 0)
   - ∫M₃ dx = ∫(1 - x/L)dx de 0 a L = L - L/2 = L/2 = 3 m
   - e₀₃ = 4.8e-4 × 3 = 1.44×10⁻³ rad

## Referencias

1. **Timoshenko & Young** (1965). *Theory of Structures*. Cap. 8: "Temperature Stresses"
   - Ecuación (8.1): δ = α·ΔT·L
   - Ecuación (8.7): κ = (α·ΔT_grad)/h

2. **Gere & Weaver** (1965). *Analysis of Framed Structures*. Sección 4.6: "Thermal Effects"
   - Trabajos virtuales con cargas térmicas
   - Ejemplos numéricos de vigas con gradiente térmico

3. **Hibbeler** (2018). *Structural Analysis*. 10th Ed. Sección 9.5
   - Método de las fuerzas con efectos térmicos
   - Caso de pórtico con variación de temperatura

## Próximos Pasos

1. ✅ Implementar clase `CargaTermica` → **COMPLETADO**
2. ✅ Crear ejemplo demostrativo → **COMPLETADO**
3. ✅ Crear tests unitarios → **COMPLETADO** (20/20 pasando)
4. ⏳ Implementar `calcular_trabajo_virtual_termico()` en motor
5. ⏳ Modificar `calcular_termino_independiente()` para incluir térmicos
6. ⏳ Validar con casos de literatura (viga biempotrada con ΔT)
7. ⏳ Crear test de integración end-to-end

## Ejemplo de Uso Futuro

```python
from src.domain.entities.carga import CargaTermica
from src.domain.analysis.motor_fuerzas import analizar_estructura

# Crear modelo (viga biempotrada, etc.)
modelo = ModeloEstructural("...")
# ... agregar nudos, barras, vínculos ...

# Aplicar carga térmica
carga_termica = CargaTermica(
    barra=barra1,
    delta_T_uniforme=30.0,    # Calentamiento uniforme +30°C
    delta_T_gradiente=20.0    # Gradiente: superior +20°C más caliente
)
modelo.agregar_carga(carga_termica)

# Resolver (motor incluirá efectos térmicos automáticamente)
resultado = analizar_estructura(modelo)

# Consultar esfuerzos generados por temperatura
print(f"Axil (compresión térmica): {resultado.N(barra1.id, 0):.1f} kN")
print(f"Momento (gradiente térmico): {resultado.M(barra1.id, 0):.1f} kNm")
```

## Notas de Implementación

- Los métodos `trabajo_virtual_uniforme()` y `trabajo_virtual_gradiente()` ya están implementados en la clase `CargaTermica`
- La integración numérica del gradiente usa `scipy.integrate.simpson` con 21 puntos por defecto
- Para axil constante, se usa la fórmula cerrada α·ΔT·N·L (más eficiente)
- Para momento variable, se requiere integración numérica ∫M(x)dx
- Ambos efectos (uniforme + gradiente) son independientes y se suman linealmente
