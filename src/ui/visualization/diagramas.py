"""
Visualización de diagramas de esfuerzos internos (N, V, M).

Genera gráficos profesionales de diagramas de esfuerzos usando matplotlib,
con convenciones estándar de ingeniería estructural.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.figure import Figure
from matplotlib.axes import Axes

if TYPE_CHECKING:
    from src.domain.analysis.motor_fuerzas import ResultadoAnalisis
    from src.domain.model.modelo_estructural import ModeloEstructural
    from src.domain.entities.barra import Barra


# Configuración de estilo por defecto
COLORES = {
    "momento": "#DC143C",      # Rojo carmesí
    "cortante": "#228B22",      # Verde bosque
    "axil": "#1E90FF",          # Azul dodger
    "estructura": "#2F4F4F",    # Gris pizarra oscuro
    "carga": "#FF8C00",         # Naranja oscuro
    "vinculo": "#8B4513",       # Marrón silla
}

LINEAS = {
    "diagrama": 2.0,
    "estructura": 2.5,
    "referencia": 0.8,
    "carga": 1.5,
}


def graficar_diagrama_momentos(
    modelo: ModeloEstructural,
    resultado: ResultadoAnalisis,
    n_puntos: int = 51,
    escala: Optional[float] = None,
    titulo: str = "Diagrama de Momentos Flectores",
    mostrar_valores: bool = True,
    ax: Optional[Axes] = None,
) -> Tuple[Figure, Axes]:
    """
    Grafica el diagrama de momentos flectores.

    Args:
        modelo: Modelo estructural
        resultado: Resultado del análisis
        n_puntos: Número de puntos para el diagrama
        escala: Factor de escala (None = automático)
        titulo: Título del gráfico
        mostrar_valores: Si True, muestra valores numéricos
        ax: Axes existente (None = crear nuevo)

    Returns:
        Tupla (figura, axes)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    else:
        fig = ax.figure

    # Dibujar geometría de fondo
    _dibujar_estructura_base(modelo, ax)

    # Encontrar valor máximo para escala
    M_max = 0.0
    for barra in modelo.barras:
        x_vals = np.linspace(0, barra.L, n_puntos)
        M_vals = [resultado.M(barra.id, x) for x in x_vals]
        M_max = max(M_max, max(abs(v) for v in M_vals))

    # Calcular escala automática si no se proporciona
    if escala is None:
        # Escala: diagrama ocupa ~30% de la altura promedio de barras
        altura_promedio = np.mean([abs(b.nudo_j.y - b.nudo_i.y) for b in modelo.barras])
        L_promedio = np.mean([b.L for b in modelo.barras])
        if M_max > 1e-6:
            escala = 0.3 * max(altura_promedio, L_promedio * 0.2) / M_max
        else:
            escala = 1.0

    # Dibujar diagrama para cada barra
    for barra in modelo.barras:
        _dibujar_diagrama_barra(
            barra, resultado, ax,
            tipo="momento",
            n_puntos=n_puntos,
            escala=escala,
            mostrar_valores=mostrar_valores,
        )

    # Configurar ejes
    ax.set_aspect('equal', adjustable='datalim')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlabel('X [m]', fontsize=10)
    ax.set_ylabel('Y [m]', fontsize=10)
    ax.set_title(titulo, fontsize=14, fontweight='bold')

    # Leyenda
    from matplotlib.patches import Patch
    leyenda_elementos = [
        Patch(facecolor=COLORES["momento"], alpha=0.3, label='Momento Flector [kNm]'),
        Patch(facecolor=COLORES["estructura"], label='Estructura'),
    ]
    ax.legend(handles=leyenda_elementos, loc='upper right', fontsize=9)

    # Añadir texto con valor máximo
    if M_max > 1e-6:
        ax.text(
            0.02, 0.98, f'M_max = {M_max:.2f} kNm',
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )

    plt.tight_layout()
    return fig, ax


def graficar_diagrama_cortantes(
    modelo: ModeloEstructural,
    resultado: ResultadoAnalisis,
    n_puntos: int = 51,
    escala: Optional[float] = None,
    titulo: str = "Diagrama de Esfuerzos Cortantes",
    mostrar_valores: bool = True,
    ax: Optional[Axes] = None,
) -> Tuple[Figure, Axes]:
    """
    Grafica el diagrama de esfuerzos cortantes.

    Args:
        modelo: Modelo estructural
        resultado: Resultado del análisis
        n_puntos: Número de puntos
        escala: Factor de escala (None = automático)
        titulo: Título del gráfico
        mostrar_valores: Si True, muestra valores numéricos
        ax: Axes existente

    Returns:
        Tupla (figura, axes)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    else:
        fig = ax.figure

    _dibujar_estructura_base(modelo, ax)

    # Encontrar V_max
    V_max = 0.0
    for barra in modelo.barras:
        x_vals = np.linspace(0, barra.L, n_puntos)
        V_vals = [resultado.V(barra.id, x) for x in x_vals]
        V_max = max(V_max, max(abs(v) for v in V_vals))

    # Escala automática
    if escala is None:
        altura_promedio = np.mean([abs(b.nudo_j.y - b.nudo_i.y) for b in modelo.barras])
        L_promedio = np.mean([b.L for b in modelo.barras])
        if V_max > 1e-6:
            escala = 0.25 * max(altura_promedio, L_promedio * 0.2) / V_max
        else:
            escala = 1.0

    # Dibujar diagramas
    for barra in modelo.barras:
        _dibujar_diagrama_barra(
            barra, resultado, ax,
            tipo="cortante",
            n_puntos=n_puntos,
            escala=escala,
            mostrar_valores=mostrar_valores,
        )

    ax.set_aspect('equal', adjustable='datalim')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlabel('X [m]', fontsize=10)
    ax.set_ylabel('Y [m]', fontsize=10)
    ax.set_title(titulo, fontsize=14, fontweight='bold')

    from matplotlib.patches import Patch
    leyenda_elementos = [
        Patch(facecolor=COLORES["cortante"], alpha=0.3, label='Cortante [kN]'),
        Patch(facecolor=COLORES["estructura"], label='Estructura'),
    ]
    ax.legend(handles=leyenda_elementos, loc='upper right', fontsize=9)

    if V_max > 1e-6:
        ax.text(
            0.02, 0.98, f'V_max = {V_max:.2f} kN',
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5)
        )

    plt.tight_layout()
    return fig, ax


def graficar_diagrama_axiles(
    modelo: ModeloEstructural,
    resultado: ResultadoAnalisis,
    n_puntos: int = 51,
    escala: Optional[float] = None,
    titulo: str = "Diagrama de Esfuerzos Axiles",
    mostrar_valores: bool = True,
    ax: Optional[Axes] = None,
) -> Tuple[Figure, Axes]:
    """
    Grafica el diagrama de esfuerzos axiles.

    Args:
        modelo: Modelo estructural
        resultado: Resultado del análisis
        n_puntos: Número de puntos
        escala: Factor de escala
        titulo: Título del gráfico
        mostrar_valores: Si True, muestra valores numéricos
        ax: Axes existente

    Returns:
        Tupla (figura, axes)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    else:
        fig = ax.figure

    _dibujar_estructura_base(modelo, ax)

    # Encontrar N_max
    N_max = 0.0
    for barra in modelo.barras:
        x_vals = np.linspace(0, barra.L, n_puntos)
        N_vals = [resultado.N(barra.id, x) for x in x_vals]
        N_max = max(N_max, max(abs(v) for v in N_vals))

    # Escala automática
    if escala is None:
        altura_promedio = np.mean([abs(b.nudo_j.y - b.nudo_i.y) for b in modelo.barras])
        L_promedio = np.mean([b.L for b in modelo.barras])
        if N_max > 1e-6:
            escala = 0.25 * max(altura_promedio, L_promedio * 0.2) / N_max
        else:
            escala = 1.0

    # Dibujar diagramas
    for barra in modelo.barras:
        _dibujar_diagrama_barra(
            barra, resultado, ax,
            tipo="axil",
            n_puntos=n_puntos,
            escala=escala,
            mostrar_valores=mostrar_valores,
        )

    ax.set_aspect('equal', adjustable='datalim')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlabel('X [m]', fontsize=10)
    ax.set_ylabel('Y [m]', fontsize=10)
    ax.set_title(titulo, fontsize=14, fontweight='bold')

    from matplotlib.patches import Patch
    leyenda_elementos = [
        Patch(facecolor=COLORES["axil"], alpha=0.3, label='Axil [kN] (+: Tracción)'),
        Patch(facecolor=COLORES["estructura"], label='Estructura'),
    ]
    ax.legend(handles=leyenda_elementos, loc='upper right', fontsize=9)

    if N_max > 1e-6:
        ax.text(
            0.02, 0.98, f'N_max = {N_max:.2f} kN',
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5)
        )

    plt.tight_layout()
    return fig, ax


def graficar_diagramas_combinados(
    modelo: ModeloEstructural,
    resultado: ResultadoAnalisis,
    n_puntos: int = 51,
    mostrar_valores: bool = False,
    titulo_general: str = "Diagramas de Esfuerzos Internos",
) -> Tuple[Figure, List[Axes]]:
    """
    Grafica los tres diagramas (M, V, N) en subplots combinados.

    Args:
        modelo: Modelo estructural
        resultado: Resultado del análisis
        n_puntos: Número de puntos por diagrama
        mostrar_valores: Si True, muestra valores numéricos
        titulo_general: Título general de la figura

    Returns:
        Tupla (figura, lista_de_axes)
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))

    # Momento
    graficar_diagrama_momentos(
        modelo, resultado, n_puntos=n_puntos,
        titulo="Momentos Flectores (M)",
        mostrar_valores=mostrar_valores,
        ax=axes[0]
    )

    # Cortante
    graficar_diagrama_cortantes(
        modelo, resultado, n_puntos=n_puntos,
        titulo="Esfuerzos Cortantes (V)",
        mostrar_valores=mostrar_valores,
        ax=axes[1]
    )

    # Axil
    graficar_diagrama_axiles(
        modelo, resultado, n_puntos=n_puntos,
        titulo="Esfuerzos Axiles (N)",
        mostrar_valores=mostrar_valores,
        ax=axes[2]
    )

    fig.suptitle(titulo_general, fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.97])

    return fig, axes


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def _dibujar_estructura_base(modelo: ModeloEstructural, ax: Axes) -> None:
    """
    Dibuja la geometría básica de la estructura (barras y nudos).

    Args:
        modelo: Modelo estructural
        ax: Axes donde dibujar
    """
    # Dibujar barras
    for barra in modelo.barras:
        xi, yi = barra.nudo_i.x, barra.nudo_i.y
        xj, yj = barra.nudo_j.x, barra.nudo_j.y

        ax.plot(
            [xi, xj], [yi, yj],
            color=COLORES["estructura"],
            linewidth=LINEAS["estructura"],
            zorder=10,
            solid_capstyle='round',
        )

    # Dibujar nudos
    for nudo in modelo.nudos:
        ax.plot(
            nudo.x, nudo.y, 'o',
            color=COLORES["estructura"],
            markersize=6,
            zorder=15,
        )

        # Dibujar vínculos
        if nudo.tiene_vinculo:
            _dibujar_vinculo(nudo, ax)


def _dibujar_vinculo(nudo, ax: Axes) -> None:
    """Dibuja el símbolo del vínculo en un nudo."""
    from src.domain.entities.vinculo import Empotramiento, ApoyoFijo, Rodillo

    x, y = nudo.x, nudo.y
    size = 0.3

    if isinstance(nudo.vinculo, Empotramiento):
        # Triángulo relleno
        tri = patches.Polygon(
            [[x - size/2, y - size], [x + size/2, y - size], [x, y]],
            facecolor=COLORES["vinculo"],
            edgecolor='black',
            linewidth=1.5,
            zorder=20,
        )
        ax.add_patch(tri)

    elif isinstance(nudo.vinculo, ApoyoFijo):
        # Triángulo + base
        tri = patches.Polygon(
            [[x - size/2, y - size], [x + size/2, y - size], [x, y]],
            facecolor='white',
            edgecolor='black',
            linewidth=1.5,
            zorder=20,
        )
        ax.add_patch(tri)
        ax.plot([x - size/2, x + size/2], [y - size, y - size], 'k-', linewidth=2, zorder=19)

    elif isinstance(nudo.vinculo, Rodillo):
        # Triángulo + círculo
        tri = patches.Polygon(
            [[x - size/2, y - size*1.2], [x + size/2, y - size*1.2], [x, y]],
            facecolor='white',
            edgecolor='black',
            linewidth=1.5,
            zorder=20,
        )
        ax.add_patch(tri)
        circle = patches.Circle(
            (x, y - size*1.5), size/4,
            facecolor='white',
            edgecolor='black',
            linewidth=1.5,
            zorder=20,
        )
        ax.add_patch(circle)


def _dibujar_diagrama_barra(
    barra: Barra,
    resultado: ResultadoAnalisis,
    ax: Axes,
    tipo: str,
    n_puntos: int,
    escala: float,
    mostrar_valores: bool,
) -> None:
    """
    Dibuja el diagrama de esfuerzos para una barra.

    Args:
        barra: Barra a dibujar
        resultado: Resultado del análisis
        ax: Axes donde dibujar
        tipo: "momento", "cortante" o "axil"
        n_puntos: Número de puntos del diagrama
        escala: Factor de escala
        mostrar_valores: Si True, añade etiquetas con valores
    """
    # Obtener función de esfuerzo
    if tipo == "momento":
        func_esfuerzo = lambda x: resultado.M(barra.id, x)
        color = COLORES["momento"]
    elif tipo == "cortante":
        func_esfuerzo = lambda x: resultado.V(barra.id, x)
        color = COLORES["cortante"]
    else:  # axil
        func_esfuerzo = lambda x: resultado.N(barra.id, x)
        color = COLORES["axil"]

    # Calcular puntos del diagrama en coordenadas locales
    x_local = np.linspace(0, barra.L, n_puntos)
    esfuerzos = np.array([func_esfuerzo(x) for x in x_local])

    # Si todos los esfuerzos son ~0, no dibujar
    if np.max(np.abs(esfuerzos)) < 1e-6:
        return

    # Vector perpendicular a la barra (para offset del diagrama)
    angulo = barra.angulo
    perp_x = -np.sin(angulo)  # Perpendicular (rotación 90°)
    perp_y = np.cos(angulo)

    # Convertir a coordenadas globales
    cos_a = np.cos(angulo)
    sin_a = np.sin(angulo)

    x_global = []
    y_global = []

    for i, x_loc in enumerate(x_local):
        # Posición a lo largo de la barra
        x_barra = barra.nudo_i.x + x_loc * cos_a
        y_barra = barra.nudo_i.y + x_loc * sin_a

        # Offset perpendicular según esfuerzo
        offset = esfuerzos[i] * escala
        x_offset = x_barra + offset * perp_x
        y_offset = y_barra + offset * perp_y

        x_global.append(x_offset)
        y_global.append(y_offset)

    x_global = np.array(x_global)
    y_global = np.array(y_global)

    # Dibujar área rellena
    x_barra_linea = barra.nudo_i.x + x_local * cos_a
    y_barra_linea = barra.nudo_i.y + x_local * sin_a

    vertices_x = np.concatenate([x_barra_linea, x_global[::-1]])
    vertices_y = np.concatenate([y_barra_linea, y_global[::-1]])

    ax.fill(vertices_x, vertices_y, color=color, alpha=0.3, zorder=5)

    # Dibujar contorno
    ax.plot(x_global, y_global, color=color, linewidth=LINEAS["diagrama"], zorder=6)

    # Etiquetas de valores (opcional)
    if mostrar_valores:
        # Valores en extremos y máximo
        val_max = esfuerzos[np.argmax(np.abs(esfuerzos))]
        idx_max = np.argmax(np.abs(esfuerzos))

        if abs(val_max) > 1e-3:
            ax.text(
                x_global[idx_max], y_global[idx_max],
                f'{val_max:.1f}',
                fontsize=8,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor=color),
                ha='center',
                zorder=25,
            )
