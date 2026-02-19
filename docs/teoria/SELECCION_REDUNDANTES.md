# Selección Manual de Redundantes

## ¿Qué son los redundantes?

En el **Método de las Fuerzas** (también llamado Método de Flexibilidad), los **redundantes** son reacciones de vínculo o esfuerzos internos que se **eliminan** temporalmente para convertir una estructura hiperestática en isostática.

### Ejemplo:

Para una **viga biempotrada** (GH=3):
- Tiene 6 reacciones: Rx, Ry, Mz en ambos extremos
- Una estructura plana isostática necesita solo 3 reacciones
- Por lo tanto: **GH = 6 - 3 = 3** (sobran 3 reacciones)
- Debemos elegir **3 redundantes** para eliminar

---

## Cómo Seleccionar Redundantes

### Opción 1: Selección Automática (Recomendado)

1. **Menú**: `Análisis → Resolver estructura` (o presiona `F5`)
2. Si la estructura es hiperestática, aparecerá un diálogo
3. Selecciona **"Sí"** para selección automática

**Criterio de selección automática:**
- Prioriza **momentos de reacción (Mz)** en empotramientos
- Luego **reacciones verticales (Ry)**
- Luego **reacciones horizontales (Rx)**
- Evita crear subestructuras inestables

**Ventajas:**
- ✓ Rápido y confiable
- ✓ Evita combinaciones que generen matrices mal condicionadas
- ✓ Ideal para la mayoría de casos

---

### Opción 2: Selección Manual

1. **Menú**: `Análisis → Seleccionar redundantes...` (o presiona `F4`)
2. Aparecerá el diálogo de selección con dos listas:
   - **Izquierda**: Candidatos disponibles
   - **Derecha**: Redundantes seleccionados

3. **Doble clic** en un candidato para agregarlo a la selección
4. **Doble clic** en un seleccionado para quitarlo
5. Cuando tengas **exactamente GH redundantes**, presiona **OK**

**Cuándo usar selección manual:**
- Cuando quieres controlar qué reacciones se liberan
- Para fines didácticos (comparar diferentes selecciones)
- Para optimizar el análisis según tu criterio

---

## Tipos de Redundantes

### 1. Reacciones de Vínculo

#### Rx - Reacción Horizontal
- Aparece en: empotramientos, apoyos fijos
- Ejemplo: `Rx en nudo 1`

#### Ry - Reacción Vertical
- Aparece en: empotramientos, apoyos fijos, rodillos verticales
- Ejemplo: `Ry en nudo 2`

#### Mz - Momento de Reacción
- Aparece en: empotramientos únicamente
- Ejemplo: `Mz en nudo 1`

### 2. Esfuerzos Internos (Avanzado)

#### M interno - Momento en sección
- Permite crear "articulaciones virtuales" en barras
- Ejemplo: `M interno en barra 1 (x=3.00m)`

---

## Reglas y Restricciones

### ⚠️ Reglas Importantes:

1. **Número exacto**: Debes seleccionar **exactamente GH redundantes**
   - GH=1 → 1 redundante
   - GH=3 → 3 redundantes
   - etc.

2. **No duplicados**: No puedes seleccionar dos veces el mismo redundante

3. **No crear inestabilidad**: No puedes eliminar todas las reacciones de un nudo
   - ❌ Eliminar Rx, Ry y Mz del mismo empotramiento
   - ✓ Eliminar Mz y Ry, dejar Rx

4. **Mínimo 3 reacciones**: La estructura fundamental debe mantener al menos 3 reacciones

---

## Ejemplos Prácticos

### Ejemplo 1: Viga Biempotrada (GH=3)

```
    ├──────────────────┤
    N1                N2
    (emp.)          (emp.)
```

**Redundantes típicos:**
- `Mz en nudo 1`
- `Mz en nudo 2`
- `Ry en nudo 2`

**Estructura fundamental resultante:**
```
    ├──────────────────○  (apoyo simple)
    N1                N2
```

---

### Ejemplo 2: Viga Empotramiento-Rodillo (GH=1)

```
    ├──────────────────▽
    N1                N2
    (emp.)        (rodillo)
```

**Redundantes típicos:**
- `Mz en nudo 1` (el más común)

**O alternativamente:**
- `Ry en nudo 2`

**Estructura fundamental con Mz liberado:**
```
    ○──────────────────▽  (apoyo fijo + rodillo)
    N1                N2
```

---

### Ejemplo 3: Pórtico Simple (GH=3)

```
        ┌─────────┐
        │         │
    ├───┘         └───┤
    N1   N2   N3   N4
```

**Redundantes automáticos típicos:**
- `Mz en nudo 1`
- `Mz en nudo 4`
- `Ry en nudo 4`

---

## Verificación Visual

Después de seleccionar redundantes:

1. Verifica la lista en el diálogo de confirmación
2. Asegúrate de que tiene sentido físico
3. Si usas selección manual, considera:
   - ¿La estructura fundamental será estable?
   - ¿Es fácil de resolver a mano? (para verificación)
   - ¿Los redundantes son físicamente significativos?

---

## Preguntas Frecuentes

**P: ¿Qué pasa si selecciono redundantes diferentes?**

R: La solución final (esfuerzos y deformaciones) será **la misma**, pero:
- El sistema de ecuaciones será diferente
- La matriz de flexibilidad [F] será diferente
- El condicionamiento numérico puede variar
- La interpretación física puede ser más o menos intuitiva

**P: ¿Cuál es la "mejor" selección de redundantes?**

R: Generalmente:
1. **Momentos (Mz)** son mejores que fuerzas (condicionamiento)
2. **Reacciones verticales (Ry)** son mejores que horizontales
3. Evitar redundantes que den matrices mal condicionadas

La selección automática sigue estos criterios.

**P: ¿Puedo cambiar los redundantes después de seleccionarlos?**

R: Sí, simplemente vuelve a abrir el diálogo (`F4`) y selecciona nuevamente.

**P: ¿Qué significa "GH negativo"?**

R: Significa que la estructura es **hipostática** (inestable). Faltan vínculos.
Ejemplo: GH=-2 → faltan 2 vínculos para que sea estable.

---

## Atajos de Teclado

| Tecla | Acción |
|-------|--------|
| `F4` | Abrir diálogo de selección de redundantes |
| `F5` | Resolver estructura (con selección automática si es necesario) |
| `Doble clic` | Agregar/quitar redundante en diálogo |

---

## Troubleshooting

### "Estructura hipostática (GH=-1)"
**Causa**: Faltan vínculos
**Solución**: Agrega más vínculos externos (empotramientos, apoyos, rodillos)

### "No se pudieron seleccionar N redundantes válidos"
**Causa**: La selección automática no encontró combinación estable
**Solución**:
- Verifica la geometría de la estructura
- Asegúrate de que los vínculos están bien colocados
- Intenta selección manual

### "Ya se seleccionaron N redundantes (máximo permitido)"
**Causa**: Intentas agregar más redundantes de los necesarios
**Solución**: Quita uno antes de agregar otro, o usa el botón de selección automática

---

**Última actualización**: 2025
**Versión del sistema**: 1.0.0
