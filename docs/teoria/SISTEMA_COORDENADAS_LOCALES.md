# Sistema de Coordenadas Locales para Cargas en Barras

## Resumen Rápido

**Regla de oro**: Los ángulos de carga se miden desde el **eje local de la barra** (dirección i→j).

- **0°** = A lo largo de la barra
- **+90°** = Rotación HORARIA (⟲) desde la barra
- **-90°** = Rotación ANTIHORARIA (⟳) desde la barra

---

## Convención General

Para cualquier barra orientada de **nudo i** a **nudo j**:

```
                Ángulo -90° (antihoraria ⟳)
                         ↑
                         |
                         |
    Nudo i  ←-------- X'(local) ------→  Nudo j
                         |              Ángulo 0°
                         |
                         ↓
                Ángulo +90° (horaria ⟲)
```

---

## Casos Específicos

### 1. Barra Horizontal (de izquierda a derecha)

```
    Geometría:
    i ======================== j
    (0,0)                    (L,0)

    Sistema local:
              -90° ↑
                   |
    i ====== 0° → ====== j
                   |
              +90° ↓
```

**Tabla de conversión**:

| Dirección deseada (global) | Ángulo local necesario |
|----------------------------|------------------------|
| ↓ Vertical hacia abajo     | **+90°**              |
| ↑ Vertical hacia arriba    | **-90°**              |
| → Horizontal derecha       | **0°**                |
| ← Horizontal izquierda     | **180°** o **-180°**  |

**Ejemplo práctico**:
```
Quiero aplicar P = 10 kN hacia abajo en x = 3m
→ Usar: P = 10.0, a = 3.0, ángulo = +90°
```

---

### 2. Barra Vertical (de abajo hacia arriba)

```
    Geometría:
           j (0,L)
           |
           |
           |
           i (0,0)

    Sistema local:
              +90° →
           |
      0° ↑ |
           |
           ← -90°
           i
```

**Tabla de conversión**:

| Dirección deseada (global) | Ángulo local necesario |
|----------------------------|------------------------|
| → Horizontal derecha       | **+90°**              |
| ← Horizontal izquierda     | **-90°**              |
| ↑ Vertical hacia arriba    | **0°**                |
| ↓ Vertical hacia abajo     | **180°**              |

---

### 3. Barra Inclinada 45° (↗)

```
    Geometría:
                    j (L,L)
                   /
                  /
                 /
                i (0,0)

    Sistema local:
         -90° ↖    0° ↗ (eje local)
               \  /
                \/
                i
                /\
               /  \
              ↙    ↘ +90°
```

**Tabla de conversión**:

| Dirección deseada (global) | Ángulo local necesario |
|----------------------------|------------------------|
| ↓ Vertical hacia abajo     | **+135°** (aprox)     |
| → Horizontal derecha       | **+45°** (aprox)      |
| ↗ A lo largo de la barra   | **0°**                |

---

## Fórmula de Transformación

Si conoces el **ángulo global deseado** (θ_global) y el **ángulo de la barra** (θ_barra):

```
θ_local = θ_global - θ_barra
```

### Ejemplo:

1. **Barra horizontal** (θ_barra = 0°)
   - Quiero carga vertical hacia abajo (θ_global = -90° en convención Qt, donde 0°=derecha, -90°=arriba, +90°=abajo)
   - Pero en convención matemática estándar: θ_global = 270° o -90°
   - Para obtener "abajo" en barra horizontal: θ_local = +90°

2. **Barra vertical hacia arriba** (θ_barra = 90°)
   - Quiero carga horizontal derecha (θ_global = 0°)
   - θ_local = 0° - 90° = -90°... **¡ERROR!**
   - Correcto: θ_local = +90° (ver tabla)

---

## Recomendaciones Prácticas

### ✅ Mejor práctica: Usar la tabla de referencia

En lugar de calcular, **usa las opciones del diálogo**:

1. **→ A lo largo de la barra (0°)**: Carga paralela a la barra
2. **⟲ Perpendicular horaria (+90°)**: Gira 90° en sentido horario desde la barra
3. **⟳ Perpendicular antihoraria (-90°)**: Gira 90° en sentido antihorario desde la barra

### 🎯 Regla mnemotécnica

Para una **barra horizontal (→)**:
- Imagina que estás **parado sobre la barra mirando de i a j**
- **Girar a tu derecha** = +90° (hacia abajo ↓)
- **Girar a tu izquierda** = -90° (hacia arriba ↑)

---

## Verificación Visual en el Canvas

Después de aplicar la carga:

1. **Mira la flecha** en el canvas
2. **Verifica que apunte en la dirección correcta**
3. Si está invertida:
   - Cambia +90° por -90° (o viceversa)
   - O usa el ángulo opuesto: 180° + ángulo_actual

---

## Casos de Uso Comunes

### Carga de gravedad (peso propio)

```
Barra horizontal (→):  ángulo = +90° (hacia abajo ↓)
Barra vertical (↑):    ángulo = 180° (hacia abajo ↓)
Barra inclinada (↗):   ángulo ≈ +135° (perpendicular + ajuste)
```

### Carga de viento horizontal

```
Barra vertical (↑):    ángulo = +90° (hacia derecha →)
Barra horizontal (→):  ángulo = -90° (hacia arriba ↑) o +90° (hacia abajo ↓)
```

---

## Preguntas Frecuentes

**P: ¿Por qué no usar directamente ángulos globales?**

R: El sistema local permite definir cargas independientemente de la orientación de la barra. Por ejemplo, "carga perpendicular a la barra" siempre es ±90°, sin importar si la barra es horizontal, vertical o inclinada.

**P: ¿Qué pasa si mi barra apunta hacia la izquierda (←)?**

R: El sistema local se invierte automáticamente. Si defines i a la derecha y j a la izquierda:
- 0° apunta hacia la izquierda (←)
- +90° apunta hacia abajo (↓)
- -90° apunta hacia arriba (↑)

**P: ¿Cómo sé si la carga quedó correcta?**

R: Siempre verifica visualmente en el canvas. La flecha debe apuntar en la dirección física correcta (gravedad = hacia abajo, viento = horizontal, etc.).

---

## Resumen de Opciones del Diálogo

| Texto en diálogo | Ángulo | Uso típico |
|------------------|--------|------------|
| → A lo largo de la barra | 0° | Carga axial, fuerza de tracción/compresión |
| ⟲ Perpendicular horaria | +90° | Peso propio en barra horizontal (→) |
| ⟳ Perpendicular antihoraria | -90° | Sustentación, reacción de apoyo |
| ← Opuesta a la barra | 180° | Carga axial de compresión inversa |
| Diagonal +45° | 45° | Cargas combinadas |
| Diagonal -45° | -45° | Cargas combinadas |

---

**Última actualización**: 2025
**Autor**: Sistema de Análisis Estructural py-anes-mf
