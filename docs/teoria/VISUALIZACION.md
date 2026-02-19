# Visualización de Resultados

Este documento describe cómo usar el módulo de visualización para generar diagramas de esfuerzos internos.

## Características

✅ **Implementado**:
- Diagramas de momentos flectores (M)
- Diagramas de esfuerzos cortantes (V)
- Diagramas de esfuerzos axiles (N)
- Visualización combinada de los tres diagramas
- Exportación a PNG de alta resolución
- Escala automática
- Visualización de geometría y vínculos

⏳ **Pendiente**:
- Deformada exagerada
- Exportación a PDF vectorial
- Animación de superposición (M0 + ΣXi·Mi)
- Visualización interactiva (zoom, pan)

## Uso Básico

### 1. Importar módulo

```python
from src.ui.visualization.diagramas import (
    graficar_diagrama_momentos,
    graficar_diagrama_cortantes,
    graficar_diagrama_axiles,
    graficar_diagramas_combinados,
)
```

### 2. Crear y resolver modelo

```python
from src.domain.model.modelo_estructural import ModeloEstructural
from src.domain.analysis.motor_fuerzas import analizar_estructura

# Crear modelo (ver CLAUDE.md para detalles)
modelo = ModeloEstructural("Mi estructura")
# ... agregar nudos, barras, vínculos, cargas ...

# Resolver
resultado = analizar_estructura(modelo)
```

### 3. Generar diagramas

#### Opción A: Diagrama individual

```python
import matplotlib.pyplot as plt

# Solo momentos
fig, ax = graficar_diagrama_momentos(modelo, resultado)
plt.show()

# Solo cortantes
fig, ax = graficar_diagrama_cortantes(modelo, resultado)
plt.show()

# Solo axiles
fig, ax = graficar_diagrama_axiles(modelo, resultado)
plt.show()
```

#### Opción B: Diagramas combinados (recomendado)

```python
import matplotlib.pyplot as plt

fig, axes = graficar_diagramas_combinados(
    modelo,
    resultado,
    n_puntos=51,  # Resolución del diagrama
    mostrar_valores=True,  # Muestra valores numéricos
    titulo_general="Mi Estructura Analizada"
)

plt.show()
```

### 4. Guardar imagen

```python
# Guardar como PNG de alta resolución
fig.savefig("diagramas.png", dpi=300, bbox_inches='tight')

# Guardar como PDF (vectorial)
fig.savefig("diagramas.pdf", bbox_inches='tight')
```

## Ejemplo Completo

Ver `ejemplo_visualizacion.py` para un ejemplo funcional completo:

```bash
python ejemplo_visualizacion.py
```

Este ejemplo:
1. Crea una viga biempotrada de 6m
2. Aplica carga puntual de 10 kN en el centro
3. Resuelve por el método de las fuerzas
4. Genera diagramas combinados M, V, N
5. Guarda imagen PNG de alta calidad

## Parámetros Avanzados

### `n_puntos` (default: 51)
Número de puntos para muestrear el diagrama. Aumentar para mayor suavidad.

```python
fig, ax = graficar_diagrama_momentos(modelo, resultado, n_puntos=101)
```

### `escala` (default: automático)
Factor de escala para el diagrama. Si es None, se calcula automáticamente.

```python
fig, ax = graficar_diagrama_momentos(
    modelo, resultado,
    escala=2.0  # Diagrama 2x más grande
)
```

### `mostrar_valores` (default: True en combinados, False en individuales)
Si True, muestra valores numéricos en puntos clave (máximos, extremos).

```python
fig, ax = graficar_diagrama_momentos(
    modelo, resultado,
    mostrar_valores=True
)
```

### `ax` (default: None)
Axes de matplotlib existente. Útil para subplots personalizados.

```python
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

graficar_diagrama_momentos(modelo, resultado, ax=ax1)
graficar_diagrama_cortantes(modelo, resultado, ax=ax2)

plt.tight_layout()
plt.show()
```

## Personalización de Estilo

Los colores y estilos se definen en `src/ui/visualization/diagramas.py`:

```python
COLORES = {
    "momento": "#DC143C",      # Rojo carmesí
    "cortante": "#228B22",      # Verde bosque
    "axil": "#1E90FF",          # Azul dodger
    "estructura": "#2F4F4F",    # Gris pizarra oscuro
    "carga": "#FF8C00",         # Naranja oscuro
    "vinculo": "#8B4513",       # Marrón silla
}
```

Puedes modificar estos valores para personalizar la apariencia.

## Convenciones de Signos

El módulo de visualización respeta la convención TERNA del proyecto:

- **Y+ hacia abajo** (gravedad positiva)
- **Rotación horaria positiva**
- **Momento positivo**: tracciona fibra inferior

Los diagramas se dibujan perpendiculares a la barra, con:
- Valores positivos: offset hacia un lado
- Valores negativos: offset hacia el otro lado

## Interpretación de Diagramas

### Momentos Flectores (M)
- **Rojo**: Momento flector [kNm]
- Área bajo la curva representa la variación de cortante
- Máximos en empotramientos y cargas concentradas

### Esfuerzos Cortantes (V)
- **Verde**: Cortante [kN]
- Discontinuidades en cargas puntuales
- Lineal bajo carga distribuida uniforme

### Esfuerzos Axiles (N)
- **Azul**: Axil [kN]
- Positivo = tracción
- Negativo = compresión
- Importante en pórticos y columnas

## Solución de Problemas

### "No se muestra la ventana"
Si estás usando un entorno sin GUI (servidor remoto, contenedor Docker), usa backend no interactivo:

```python
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt

# ... generar diagramas ...
fig.savefig("output.png")  # Solo guardar, no mostrar
```

### "Los diagramas se ven muy pequeños/grandes"
Ajusta manualmente la escala:

```python
fig, ax = graficar_diagrama_momentos(
    modelo, resultado,
    escala=0.5  # Más pequeño
)
```

### "Caracteres especiales no se muestran"
En Windows, matplotlib puede tener problemas con Unicode. Usa:

```python
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False
```

## Próximos Pasos

Funcionalidades planificadas para futuras versiones:

1. **Deformada exagerada**: Visualización de desplazamientos con factor de escala
2. **Animación de superposición**: Ver cómo cada Xi contribuye al resultado final
3. **Exportación a PDF vectorial**: Gráficos escalables para reportes profesionales
4. **Interfaz interactiva**: Zoom, pan, selección de barras, valores al hacer clic
5. **Reportes automáticos**: Generación de informes técnicos completos en PDF

## Referencias

- Ejemplo: `ejemplo_visualizacion.py`
- Tests: `tests/integration/test_casos_clasicos.py`
- Código fuente: `src/ui/visualization/diagramas.py`
