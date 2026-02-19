"""
Visualización de deformada estructural.

Genera gráficos de la deformada exagerada de la estructura,
mostrando desplazamientos y rotaciones bajo cargas aplicadas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.figure import Figure
from matplotlib.axes import Axes

if TYPE_CHECKING:
    from src.domain.analysis.motor_fuerzas import ResultadoAnalisis
    from src.domain.model.modelo_estructural import ModeloEstructural
    from src.domain.entities.barra import Barra


# Configuración de colores
COLORES = {
    "estructura_original": "#A9A9A9",  # Gris claro
    "estructura_deformada": "#DC143C",  # Rojo carmesí
    "nudo_original": "#696969",  # Gris oscuro
    "nudo_deformado": "#8B0000",  # Rojo oscuro
}


def graficar_deformada(
    modelo: ModeloEstructural,
    resultado: ResultadoAnalisis,
    factor_escala: Optional[float] = None,
    n_puntos: int = 21,
    mostrar_original: bool = True,
    titulo: str = "Deformada de la Estructura",
    ax: Optional[Axes] = None,
) -> Tuple[Figure, Axes]:
    """
    Grafica la deformada exagerada de la estructura.

    NOTA: Esta es una implementación simplificada que calcula desplazamientos
    usando superposición de los desplazamientos de las subestructuras.
    Para una implementación completa, se requeriría calcular la matriz de
    rigidez y resolver para desplazamientos nodales.

    Args:
        modelo: Modelo estructural
        resultado: Resultado del análisis
        factor_escala: Factor de exageración (None = automático)
        n_puntos: Número de puntos por barra
        mostrar_original: Si True, muestra geometría original superpuesta
        titulo: Título del gráfico
        ax: Axes existente (None = crear nuevo)

    Returns:
        Tupla (figura, axes)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 10))
    else:
        fig = ax.figure

    # Calcular factor de escala automático si no se proporciona
    if factor_escala is None:
        factor_escala = _calcular_factor_escala_automatico(modelo, resultado)

    # Dibujar estructura original (geometría sin deformar)
    if mostrar_original:
        _dibujar_estructura_original(modelo, ax)

    # Dibujar estructura deformada
    _dibujar_estructura_deformada(modelo, resultado, ax, factor_escala, n_puntos)

    # Configurar ejes
    ax.set_aspect('equal', adjustable='box')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlabel('X [m]', fontsize=10)
    ax.set_ylabel('Y [m]', fontsize=10)
    ax.set_title(titulo, fontsize=14, fontweight='bold')

    # Leyenda
    from matplotlib.lines import Line2D
    leyenda_elementos = [
        Line2D([0], [0], color=COLORES["estructura_original"], linewidth=2,
               linestyle='--', label='Estructura original'),
        Line2D([0], [0], color=COLORES["estructura_deformada"], linewidth=2.5,
               label='Estructura deformada'),
    ]
    ax.legend(handles=leyenda_elementos, loc='upper right', fontsize=10)

    # Añadir texto con factor de escala
    ax.text(
        0.02, 0.98,
        f'Factor de escala: {factor_escala:.0f}x',
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8)
    )

    plt.tight_layout()
    return fig, ax


def _calcular_factor_escala_automatico(
    modelo: ModeloEstructural,
    resultado: ResultadoAnalisis,
) -> float:
    """
    Calcula un factor de escala automático para visualización.

    El factor se elige de modo que el desplazamiento máximo sea ~10% de
    la dimensión característica de la estructura.

    Args:
        modelo: Modelo estructural
        resultado: Resultado del análisis

    Returns:
        Factor de escala sugerido
    """
    # Calcular dimensión característica (diagonal del bounding box)
    xs = [n.x for n in modelo.nudos]
    ys = [n.y for n in modelo.nudos]

    ancho = max(xs) - min(xs) if len(xs) > 1 else 1.0
    alto = max(ys) - min(ys) if len(ys) > 1 else 1.0
    dimension_caracteristica = np.hypot(ancho, alto)

    # Estimar desplazamiento máximo aproximado usando teoría de vigas
    # Para una viga simplemente apoyada: δ_max ≈ 5wL⁴/(384EI)
    # Como aproximación, usamos L³/EI como medida característica

    desplazamiento_estimado = 0.0
    for barra in modelo.barras:
        # Momento máximo aproximado en la barra
        x_vals = np.linspace(0, barra.L, 11)
        M_vals = [abs(resultado.M(barra.id, x)) for x in x_vals]
        M_max = max(M_vals) if M_vals else 0.0

        if M_max > 1e-6:
            # Curvatura máxima: κ = M/(EI)
            # Desplazamiento aproximado: δ ≈ κ × L²
            EI = barra.material.E * barra.seccion.Iz
            curvatura = M_max / EI
            delta_aprox = curvatura * (barra.L ** 2) / 8  # Factor 1/8 empírico
            desplazamiento_estimado = max(desplazamiento_estimado, delta_aprox)

    # Factor de escala: hacer que el desplazamiento sea ~10% de la dimensión
    if desplazamiento_estimado > 1e-9:
        factor = (0.1 * dimension_caracteristica) / desplazamiento_estimado
        # Redondear a potencias de 10 para valores legibles
        factor = 10 ** round(np.log10(factor))
        return max(1.0, min(factor, 10000.0))  # Limitar entre 1 y 10000
    else:
        return 100.0  # Factor por defecto


def _dibujar_estructura_original(modelo: ModeloEstructural, ax: Axes) -> None:
    """
    Dibuja la estructura en su configuración original (sin deformar).

    Args:
        modelo: Modelo estructural
        ax: Axes donde dibujar
    """
    # Dibujar barras originales
    for barra in modelo.barras:
        xi, yi = barra.nudo_i.x, barra.nudo_i.y
        xj, yj = barra.nudo_j.x, barra.nudo_j.y

        ax.plot(
            [xi, xj], [yi, yj],
            color=COLORES["estructura_original"],
            linewidth=2.0,
            linestyle='--',
            alpha=0.6,
            zorder=5,
        )

    # Dibujar nudos originales
    for nudo in modelo.nudos:
        ax.plot(
            nudo.x, nudo.y, 'o',
            color=COLORES["nudo_original"],
            markersize=6,
            alpha=0.6,
            zorder=10,
        )


def _dibujar_estructura_deformada(
    modelo: ModeloEstructural,
    resultado: ResultadoAnalisis,
    ax: Axes,
    factor_escala: float,
    n_puntos: int,
) -> None:
    """
    Dibuja la estructura deformada.

    NOTA IMPORTANTE: Esta implementación es una APROXIMACIÓN simplificada.
    Calcula la deformada de cada barra usando la ecuación de la línea elástica:

    d²y/dx² = M(x) / (EI)

    Integrando dos veces con condiciones de borde apropiadas.

    Para una implementación completa, se debería:
    1. Calcular desplazamientos nodales desde la matriz de rigidez
    2. Usar funciones de forma para interpolar dentro de cada barra
    3. Considerar efectos de axil y cortante

    Args:
        modelo: Modelo estructural
        resultado: Resultado del análisis
        ax: Axes donde dibujar
        factor_escala: Factor de exageración
        n_puntos: Puntos por barra
    """
    # Dibujar cada barra deformada
    for barra in modelo.barras:
        _dibujar_barra_deformada(barra, resultado, ax, factor_escala, n_puntos)

    # Dibujar nudos deformados
    # Calculamos la posición deformada del nudo tomando el extremo de cada barra conectada
    # y promediando si hay varias (garantiza compatibilidad visual entre barras contiguas).
    posiciones_deformadas = _calcular_posiciones_nudos_deformados(
        modelo, resultado, factor_escala, n_puntos
    )
    for nudo in modelo.nudos:
        xd, yd = posiciones_deformadas.get(nudo.id, (nudo.x, nudo.y))
        ax.plot(
            xd, yd, 'o',
            color=COLORES["nudo_deformado"],
            markersize=7,
            zorder=15,
        )


def _dibujar_barra_deformada(
    barra,
    resultado: ResultadoAnalisis,
    ax: Axes,
    factor_escala: float,
    n_puntos: int,
) -> None:
    """
    Dibuja una barra deformada usando la línea elástica.

    Aproximación: integra M(x)/(EI) dos veces para obtener deflexión.

    Args:
        barra: Barra a dibujar
        resultado: Resultado del análisis
        ax: Axes donde dibujar
        factor_escala: Factor de exageración
        n_puntos: Puntos de muestreo
    """
    L = barra.L
    EI = barra.material.E * barra.seccion.Iz

    # Muestrear momento a lo largo de la barra
    x_local = np.linspace(0, L, n_puntos)
    M_vals = np.array([resultado.M(barra.id, x) for x in x_local])

    # Calcular curvatura κ(x) = M(x) / EI
    if EI < 1e-10:
        curvatura = np.zeros_like(M_vals)
    else:
        curvatura = M_vals / EI

    # Integrar para obtener rotación θ(x) y deflexión v(x)
    # Usando condiciones de borde simplificadas: v(0) = 0, θ(0) = 0
    dx = L / (n_puntos - 1)

    # Primera integración: κ → θ (rotación)
    theta = np.zeros(n_puntos)
    for i in range(1, n_puntos):
        theta[i] = theta[i-1] + curvatura[i] * dx

    # Segunda integración: θ → v (deflexión)
    v_local = np.zeros(n_puntos)
    for i in range(1, n_puntos):
        v_local[i] = v_local[i-1] + theta[i] * dx

    # Aplicar factor de escala
    v_local_scaled = v_local * factor_escala

    # Transformar a coordenadas globales
    angulo = barra.angulo
    cos_a = np.cos(angulo)
    sin_a = np.sin(angulo)

    # Vector perpendicular (para offset de deflexión)
    perp_x = -sin_a
    perp_y = cos_a

    x_deformada = []
    y_deformada = []

    for i, x_loc in enumerate(x_local):
        # Posición sin deformar
        x_barra = barra.nudo_i.x + x_loc * cos_a
        y_barra = barra.nudo_i.y + x_loc * sin_a

        # Añadir deflexión perpendicular
        x_def = x_barra + v_local_scaled[i] * perp_x
        y_def = y_barra + v_local_scaled[i] * perp_y

        x_deformada.append(x_def)
        y_deformada.append(y_def)

    # Dibujar barra deformada
    ax.plot(
        x_deformada, y_deformada,
        color=COLORES["estructura_deformada"],
        linewidth=2.5,
        zorder=8,
        solid_capstyle='round',
    )


def _calcular_posiciones_nudos_deformados(
    modelo,
    resultado,
    factor_escala: float,
    n_puntos: int,
) -> dict:
    """
    Calcula las posiciones deformadas de cada nudo.

    Para cada nudo, recorre las barras conectadas y obtiene la posición
    del extremo de la barra que coincide con ese nudo (calculada con la
    misma lógica de integración doble que _dibujar_barra_deformada).
    Si varias barras convergen en un nudo, promedia las estimaciones.

    Args:
        modelo: Modelo estructural
        resultado: Resultado del análisis
        factor_escala: Factor de exageración
        n_puntos: Puntos usados en la integración

    Returns:
        Diccionario {nudo_id: (x_deformado, y_deformado)}
    """
    from collections import defaultdict

    acumulado = defaultdict(list)  # nudo_id → lista de (x, y)

    for barra in modelo.barras:
        L = barra.L
        EI = barra.material.E * barra.seccion.Iz

        x_local = np.linspace(0, L, n_puntos)
        M_vals = np.array([resultado.M(barra.id, x) for x in x_local])

        if EI < 1e-10:
            curvatura = np.zeros_like(M_vals)
        else:
            curvatura = M_vals / EI

        dx_int = L / (n_puntos - 1)

        # Primera integración: curvatura → rotación (θ(0) = 0)
        theta = np.zeros(n_puntos)
        for k in range(1, n_puntos):
            theta[k] = theta[k - 1] + curvatura[k] * dx_int

        # Segunda integración: rotación → deflexión perpendicular (v(0) = 0)
        v_local = np.zeros(n_puntos)
        for k in range(1, n_puntos):
            v_local[k] = v_local[k - 1] + theta[k] * dx_int

        angulo = barra.angulo
        cos_a = np.cos(angulo)
        sin_a = np.sin(angulo)
        perp_x = -sin_a
        perp_y = cos_a

        # Posición deformada del extremo i (índice 0)
        v_i_scaled = v_local[0] * factor_escala
        xi_def = barra.nudo_i.x + v_i_scaled * perp_x
        yi_def = barra.nudo_i.y + v_i_scaled * perp_y
        acumulado[barra.nudo_i.id].append((xi_def, yi_def))

        # Posición deformada del extremo j (índice -1)
        v_j_scaled = v_local[-1] * factor_escala
        xj_def = barra.nudo_j.x + v_j_scaled * perp_x
        yj_def = barra.nudo_j.y + v_j_scaled * perp_y
        acumulado[barra.nudo_j.id].append((xj_def, yj_def))

    # Promediar si varias barras estimaron la posición del mismo nudo
    resultado_final = {}
    for nudo_id, posiciones in acumulado.items():
        x_prom = sum(p[0] for p in posiciones) / len(posiciones)
        y_prom = sum(p[1] for p in posiciones) / len(posiciones)
        resultado_final[nudo_id] = (x_prom, y_prom)

    return resultado_final


def graficar_comparacion_deformadas(
    modelo: ModeloEstructural,
    resultado: ResultadoAnalisis,
    factores: list[float] = [50, 100, 200],
    n_puntos: int = 21,
) -> Tuple[Figure, list[Axes]]:
    """
    Grafica múltiples deformadas con diferentes factores de escala.

    Args:
        modelo: Modelo estructural
        resultado: Resultado del análisis
        factores: Lista de factores de escala a comparar
        n_puntos: Puntos por barra

    Returns:
        Tupla (figura, lista_de_axes)
    """
    n_graficos = len(factores)
    fig, axes = plt.subplots(1, n_graficos, figsize=(6*n_graficos, 6))

    if n_graficos == 1:
        axes = [axes]

    for i, factor in enumerate(factores):
        graficar_deformada(
            modelo, resultado,
            factor_escala=factor,
            n_puntos=n_puntos,
            mostrar_original=True,
            titulo=f"Deformada (escala {factor}x)",
            ax=axes[i]
        )

    fig.suptitle("Comparación de Deformadas con Diferentes Escalas",
                 fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    return fig, axes
