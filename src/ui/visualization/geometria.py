"""
Visualizacion de geometria estructural.

Genera graficos profesionales de la estructura porticada 2D mostrando:
- Barras con ID y propiedades
- Nudos con numeracion
- Vinculos externos (empotramiento, apoyo fijo, rodillo, guia, resorte)
- Cargas aplicadas (puntuales en nudos, puntuales en barras, distribuidas)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as pe
import numpy as np
from matplotlib.figure import Figure
from matplotlib.axes import Axes

if TYPE_CHECKING:
    from src.domain.model.modelo_estructural import ModeloEstructural
    from src.domain.entities.nudo import Nudo
    from src.domain.entities.barra import Barra
    from src.domain.entities.carga import Carga


# Colores y grosores consistentes con diagramas.py
COLORES = {
    "barra": "#2F4F4F",          # Gris pizarra oscuro
    "nudo": "#1A1A2E",            # Azul marino oscuro
    "vinculo": "#8B4513",         # Marron
    "carga_puntual": "#FF4500",   # Naranja rojizo
    "carga_distribuida": "#FF8C00",  # Naranja
    "carga_momento": "#9400D3",   # Violeta
    "texto": "#1A1A1A",           # Casi negro
    "fondo_vinculo": "#D2B48C",   # Tan
    "resorte": "#20B2AA",         # Verde agua
    "guia": "#4682B4",            # Azul acero
}

LINEAS = {
    "barra": 2.5,
    "vinculo": 1.5,
    "carga": 1.8,
    "referencia": 0.8,
}


def graficar_estructura(
    modelo: ModeloEstructural,
    titulo: str = "Geometria Estructural",
    mostrar_ids: bool = True,
    mostrar_longitudes: bool = False,
    ax: Optional[Axes] = None,
) -> Tuple[Figure, Axes]:
    """
    Grafica la geometria de la estructura sin cargas.

    Dibuja barras, nudos y vinculos externos con simbolos normalizados.

    Args:
        modelo: Modelo estructural a graficar
        titulo: Titulo del grafico
        mostrar_ids: Si True, muestra numeros de nudos y barras
        mostrar_longitudes: Si True, muestra longitudes de barras
        ax: Axes existente (None = crear nuevo)

    Returns:
        Tupla (figura, axes)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    else:
        fig = ax.figure

    if not modelo.barras and not modelo.nudos:
        ax.set_title("Modelo vacio", fontsize=12)
        return fig, ax

    # Calcular tamanio de simbolos en funcion del modelo
    size_ref = _calcular_size_referencia(modelo)

    # Dibujar barras
    for barra in modelo.barras:
        _dibujar_barra(barra, ax, size_ref, mostrar_ids, mostrar_longitudes)

    # Dibujar nudos y vinculos
    for nudo in modelo.nudos:
        _dibujar_nudo(nudo, ax, size_ref, mostrar_ids)
        if nudo.tiene_vinculo:
            _dibujar_vinculo(nudo, ax, size_ref)

    # Configurar ejes
    _configurar_ejes(modelo, ax, titulo)

    plt.tight_layout()
    return fig, ax


def graficar_estructura_con_cargas(
    modelo: ModeloEstructural,
    titulo: str = "Estructura con Cargas",
    mostrar_ids: bool = True,
    mostrar_valores_cargas: bool = True,
    ax: Optional[Axes] = None,
) -> Tuple[Figure, Axes]:
    """
    Grafica la estructura con todas las cargas aplicadas.

    Dibuja barras, nudos, vinculos y sobre ellos las cargas
    puntuales (en nudos y barras) y distribuidas.

    Args:
        modelo: Modelo estructural a graficar
        titulo: Titulo del grafico
        mostrar_ids: Si True, muestra numeros de nudos y barras
        mostrar_valores_cargas: Si True, muestra magnitudes de cargas
        ax: Axes existente (None = crear nuevo)

    Returns:
        Tupla (figura, axes)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    else:
        fig = ax.figure

    if not modelo.barras and not modelo.nudos:
        ax.set_title("Modelo vacio", fontsize=12)
        return fig, ax

    size_ref = _calcular_size_referencia(modelo)

    # Dibujar geometria base
    for barra in modelo.barras:
        _dibujar_barra(barra, ax, size_ref, mostrar_ids, mostrar_longitudes=False)

    for nudo in modelo.nudos:
        _dibujar_nudo(nudo, ax, size_ref, mostrar_ids)
        if nudo.tiene_vinculo:
            _dibujar_vinculo(nudo, ax, size_ref)

    # Dibujar cargas
    for carga in modelo.cargas:
        _dibujar_carga(carga, ax, size_ref, mostrar_valores_cargas)

    _configurar_ejes(modelo, ax, titulo)

    # Leyenda de cargas
    from matplotlib.lines import Line2D
    elementos_leyenda = []
    from src.domain.entities.carga import CargaPuntualNudo, CargaPuntualBarra, CargaDistribuida
    tipos_presentes = set(type(c) for c in modelo.cargas)

    if CargaPuntualNudo in tipos_presentes or CargaPuntualBarra in tipos_presentes:
        elementos_leyenda.append(
            Line2D([0], [0], color=COLORES["carga_puntual"],
                   linewidth=2, marker='^', label='Carga puntual')
        )
    if CargaDistribuida in tipos_presentes:
        elementos_leyenda.append(
            Line2D([0], [0], color=COLORES["carga_distribuida"],
                   linewidth=2, label='Carga distribuida')
        )

    if elementos_leyenda:
        ax.legend(handles=elementos_leyenda, loc='upper right', fontsize=9)

    plt.tight_layout()
    return fig, ax


# =============================================================================
# FUNCIONES AUXILIARES DE DIBUJO
# =============================================================================

def _calcular_size_referencia(modelo: ModeloEstructural) -> float:
    """
    Calcula un tamano de referencia para simbolos en funcion del modelo.

    Returns:
        Escala de referencia en metros
    """
    if not modelo.barras:
        if modelo.nudos:
            xs = [n.x for n in modelo.nudos]
            ys = [n.y for n in modelo.nudos]
            rango = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
        else:
            rango = 1.0
        return rango * 0.05

    longitudes = [b.L for b in modelo.barras if b.L > 1e-6]
    if not longitudes:
        return 0.3
    L_min = min(longitudes)
    L_prom = sum(longitudes) / len(longitudes)
    return min(L_min * 0.12, L_prom * 0.06)


def _dibujar_barra(
    barra: Barra,
    ax: Axes,
    size_ref: float,
    mostrar_id: bool,
    mostrar_longitudes: bool,
) -> None:
    """Dibuja una barra como linea con etiquetas opcionales."""
    xi, yi = barra.nudo_i.x, barra.nudo_i.y
    xj, yj = barra.nudo_j.x, barra.nudo_j.y

    ax.plot(
        [xi, xj], [yi, yj],
        color=COLORES["barra"],
        linewidth=LINEAS["barra"],
        solid_capstyle='round',
        zorder=10,
    )

    if mostrar_id or mostrar_longitudes:
        # Centro de la barra
        xc = (xi + xj) / 2
        yc = (yi + yj) / 2

        # Normal perpendicular a la barra (para offset de texto)
        ang = math.atan2(yj - yi, xj - xi)
        nx = -math.sin(ang)  # Normal apuntando "arriba" de la barra
        ny = math.cos(ang)

        offset = size_ref * 0.8
        xt = xc + nx * offset
        yt = yc + ny * offset

        lineas_texto = []
        if mostrar_id:
            lineas_texto.append(f"B{barra.id}")
        if mostrar_longitudes:
            lineas_texto.append(f"L={barra.L:.2f}m")

        ax.text(
            xt, yt, "\n".join(lineas_texto),
            fontsize=7,
            color="#555555",
            ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      edgecolor='none', alpha=0.7),
            zorder=12,
        )


def _dibujar_nudo(
    nudo: Nudo,
    ax: Axes,
    size_ref: float,
    mostrar_id: bool,
) -> None:
    """Dibuja un nudo como circulo con numero opcional."""
    ax.plot(
        nudo.x, nudo.y, 'o',
        color=COLORES["nudo"],
        markersize=5,
        zorder=15,
    )

    if mostrar_id:
        ax.text(
            nudo.x + size_ref * 0.5,
            nudo.y + size_ref * 0.5,
            f"N{nudo.id}",
            fontsize=7,
            color=COLORES["texto"],
            ha='left', va='bottom',
            zorder=16,
            fontweight='bold',
        )


def _dibujar_vinculo(nudo: Nudo, ax: Axes, size_ref: float) -> None:
    """
    Dibuja el simbolo normalizado del vinculo en el nudo.

    Simbolos implementados:
    - Empotramiento: rectangulo relleno con rayas
    - ApoyoFijo: triangulo con circulo en vertice
    - Rodillo: triangulo con circulo y linea de rodamiento
    - Guia: simbolo de guia deslizante
    - ResorteElastico: zigzag de resorte
    """
    from src.domain.entities.vinculo import (
        Empotramiento, ApoyoFijo, Rodillo, Guia, ResorteElastico
    )

    x, y = nudo.x, nudo.y
    s = size_ref * 1.2  # Tamano base del simbolo

    vinculo = nudo.vinculo

    if isinstance(vinculo, Empotramiento):
        _dibujar_empotramiento(ax, x, y, s)

    elif isinstance(vinculo, ApoyoFijo):
        _dibujar_apoyo_fijo(ax, x, y, s)

    elif isinstance(vinculo, Rodillo):
        _dibujar_rodillo(ax, x, y, s, vinculo.direccion)

    elif isinstance(vinculo, Guia):
        _dibujar_guia(ax, x, y, s, vinculo)

    elif isinstance(vinculo, ResorteElastico):
        _dibujar_resorte(ax, x, y, s, vinculo)


def _dibujar_empotramiento(ax: Axes, x: float, y: float, s: float) -> None:
    """Empotramiento: rectangulo rayado con linea de union."""
    # Rectangulo de fondo
    rect = patches.FancyBboxPatch(
        (x - s * 0.6, y - s * 0.3), s * 1.2, s * 0.6,
        boxstyle="square,pad=0",
        facecolor=COLORES["fondo_vinculo"],
        edgecolor=COLORES["vinculo"],
        linewidth=1.5,
        zorder=5,
    )
    ax.add_patch(rect)

    # Rayas internas (hatching manual para mejor control)
    n_rayas = 5
    for i in range(n_rayas):
        xi_raya = x - s * 0.6 + (i + 0.5) * s * 1.2 / n_rayas
        ax.plot(
            [xi_raya, xi_raya - s * 0.2],
            [y - s * 0.3, y - s * 0.6],
            color=COLORES["vinculo"],
            linewidth=0.8,
            zorder=6,
        )

    # Linea de union con el nudo
    ax.plot([x, x], [y - s * 0.0, y - s * 0.3],
            color=COLORES["vinculo"], linewidth=1.5, zorder=6)


def _dibujar_apoyo_fijo(ax: Axes, x: float, y: float, s: float) -> None:
    """Apoyo fijo (biarticulado): triangulo con base rayada."""
    # Triangulo
    triangulo = patches.Polygon(
        [[x, y], [x - s * 0.5, y - s], [x + s * 0.5, y - s]],
        facecolor=COLORES["fondo_vinculo"],
        edgecolor=COLORES["vinculo"],
        linewidth=1.5,
        zorder=5,
    )
    ax.add_patch(triangulo)

    # Circulo en vertice (articulacion)
    circulo = patches.Circle(
        (x, y), s * 0.12,
        facecolor='white',
        edgecolor=COLORES["vinculo"],
        linewidth=1.2,
        zorder=8,
    )
    ax.add_patch(circulo)

    # Linea de base
    ax.plot(
        [x - s * 0.6, x + s * 0.6], [y - s, y - s],
        color=COLORES["vinculo"], linewidth=2.0, zorder=6
    )

    # Rayas de base
    for i in range(4):
        xi = x - s * 0.5 + i * s * 0.33
        ax.plot(
            [xi, xi - s * 0.15], [y - s, y - s * 1.2],
            color=COLORES["vinculo"], linewidth=0.8, zorder=6
        )


def _dibujar_rodillo(ax: Axes, x: float, y: float, s: float, direccion: str) -> None:
    """
    Rodillo: triangulo con circulitos en la base (ruedas).

    La direccion puede ser 'Ux' (rodillo horizontal) o 'Uy' (rodillo vertical).
    """
    # Triangulo orientado segun la direccion restringida
    if direccion == 'Uy':
        # Rodillo vertical: restringe Y, libre en X → triangulo apuntando arriba
        pts = [[x, y], [x - s * 0.5, y - s], [x + s * 0.5, y - s]]
    else:
        # Rodillo horizontal: restringe X, libre en Y → triangulo apuntando a la derecha
        pts = [[x, y], [x - s, y + s * 0.5], [x - s, y - s * 0.5]]

    triangulo = patches.Polygon(
        pts,
        facecolor=COLORES["fondo_vinculo"],
        edgecolor=COLORES["vinculo"],
        linewidth=1.5,
        zorder=5,
    )
    ax.add_patch(triangulo)

    # Circulo de articulacion en vertice
    circulo = patches.Circle(
        (x, y), s * 0.12,
        facecolor='white',
        edgecolor=COLORES["vinculo"],
        linewidth=1.2,
        zorder=8,
    )
    ax.add_patch(circulo)

    # Ruedas (circulos pequenos en base)
    if direccion == 'Uy':
        for dx in [-s * 0.3, 0, s * 0.3]:
            rueda = patches.Circle(
                (x + dx, y - s - s * 0.12), s * 0.1,
                facecolor=COLORES["fondo_vinculo"],
                edgecolor=COLORES["vinculo"],
                linewidth=1.0,
                zorder=6,
            )
            ax.add_patch(rueda)
        # Linea de rodamiento
        ax.plot(
            [x - s * 0.6, x + s * 0.6], [y - s * 1.25, y - s * 1.25],
            color=COLORES["vinculo"], linewidth=1.5, zorder=6
        )
    else:
        for dy in [-s * 0.3, 0, s * 0.3]:
            rueda = patches.Circle(
                (x - s - s * 0.12, y + dy), s * 0.1,
                facecolor=COLORES["fondo_vinculo"],
                edgecolor=COLORES["vinculo"],
                linewidth=1.0,
                zorder=6,
            )
            ax.add_patch(rueda)
        # Linea de rodamiento vertical
        ax.plot(
            [x - s * 1.25, x - s * 1.25], [y - s * 0.6, y + s * 0.6],
            color=COLORES["vinculo"], linewidth=1.5, zorder=6
        )


def _dibujar_guia(ax: Axes, x: float, y: float, s: float, vinculo) -> None:
    """
    Guia: simbolo de deslizamiento con flechas bidireccionales.

    La guia restringe una traslacion y la rotacion, pero permite la otra traslacion.
    """
    from src.domain.entities.vinculo import TipoVinculo

    tipo = vinculo.tipo if hasattr(vinculo, 'tipo') else None

    # Determinar orientacion: guia horizontal restringe Y+rot, permite X
    # guia vertical restringe X+rot, permite Y
    es_horizontal = (tipo == TipoVinculo.GUIA_HORIZONTAL if tipo else True)

    if es_horizontal:
        # Lineas de guia horizontales
        for dy in [-s * 0.4, s * 0.4]:
            ax.plot(
                [x - s * 0.8, x + s * 0.8], [y + dy, y + dy],
                color=COLORES["guia"], linewidth=1.5, zorder=5
            )
        # Rayas de restriccion
        for i in range(5):
            xi = x - s * 0.6 + i * s * 0.3
            ax.plot(
                [xi, xi], [y - s * 0.4, y - s * 0.7],
                color=COLORES["guia"], linewidth=0.8, zorder=5
            )
        # Nudo central
        ax.plot(x, y, 's', color=COLORES["guia"], markersize=6, zorder=10)
    else:
        # Guia vertical
        for dx in [-s * 0.4, s * 0.4]:
            ax.plot(
                [x + dx, x + dx], [y - s * 0.8, y + s * 0.8],
                color=COLORES["guia"], linewidth=1.5, zorder=5
            )
        for i in range(5):
            yi = y - s * 0.6 + i * s * 0.3
            ax.plot(
                [x - s * 0.4, x - s * 0.7], [yi, yi],
                color=COLORES["guia"], linewidth=0.8, zorder=5
            )
        ax.plot(x, y, 's', color=COLORES["guia"], markersize=6, zorder=10)


def _dibujar_resorte(ax: Axes, x: float, y: float, s: float, vinculo) -> None:
    """Resorte elastico: zigzag de resorte con valor de rigidez."""
    # Dibujar zigzag de resorte hacia abajo
    n_ciclos = 5
    altura_resorte = s * 2.0
    y_inicio = y - s * 0.3
    y_fin = y_inicio - altura_resorte

    xs_resorte = []
    ys_resorte = []
    n_puntos = n_ciclos * 4 + 2
    for i in range(n_puntos):
        t = i / (n_puntos - 1)
        yi = y_inicio - t * altura_resorte
        if i == 0 or i == n_puntos - 1:
            xi = x
        else:
            fase = (i - 0.5) * math.pi / 2
            xi = x + s * 0.3 * math.sin(fase)
        xs_resorte.append(xi)
        ys_resorte.append(yi)

    ax.plot(xs_resorte, ys_resorte,
            color=COLORES["resorte"], linewidth=1.5, zorder=5)

    # Base del resorte
    ax.plot([x - s * 0.3, x + s * 0.3], [y_fin, y_fin],
            color=COLORES["resorte"], linewidth=2.0, zorder=5)

    # Etiqueta de rigidez
    k_texto = []
    if hasattr(vinculo, 'kx') and vinculo.kx > 0:
        k_texto.append(f"kx={vinculo.kx:.0f}")
    if hasattr(vinculo, 'ky') and vinculo.ky > 0:
        k_texto.append(f"ky={vinculo.ky:.0f}")
    if hasattr(vinculo, 'ktheta') and vinculo.ktheta > 0:
        k_texto.append(f"kr={vinculo.ktheta:.0f}")

    if k_texto:
        ax.text(
            x + s * 0.5, y_inicio - altura_resorte / 2,
            "\n".join(k_texto),
            fontsize=6, color=COLORES["resorte"],
            ha='left', va='center', zorder=11,
        )


# =============================================================================
# DIBUJO DE CARGAS
# =============================================================================

def _dibujar_carga(carga, ax: Axes, size_ref: float, mostrar_valor: bool) -> None:
    """Despacha el dibujo segun el tipo de carga."""
    from src.domain.entities.carga import CargaPuntualNudo, CargaPuntualBarra, CargaDistribuida

    if isinstance(carga, CargaPuntualNudo):
        _dibujar_carga_puntual_nudo(carga, ax, size_ref, mostrar_valor)
    elif isinstance(carga, CargaPuntualBarra):
        _dibujar_carga_puntual_barra(carga, ax, size_ref, mostrar_valor)
    elif isinstance(carga, CargaDistribuida):
        _dibujar_carga_distribuida(carga, ax, size_ref, mostrar_valor)


def _dibujar_carga_puntual_nudo(carga, ax: Axes, size_ref: float, mostrar_valor: bool) -> None:
    """Flecha con punta en el nudo para carga puntual nodal."""
    if carga.nudo is None:
        return

    x, y = carga.nudo.x, carga.nudo.y
    long_flecha = size_ref * 3.0
    color = COLORES["carga_puntual"]

    # Fuerza X
    if abs(carga.Fx) > 1e-6:
        signo = 1 if carga.Fx > 0 else -1
        dx = signo * long_flecha
        ax.annotate(
            "", xy=(x, y), xytext=(x - dx, y),
            arrowprops=dict(arrowstyle='->', color=color,
                            lw=LINEAS["carga"]),
            zorder=20,
        )
        if mostrar_valor:
            ax.text(x - dx * 0.5, y + size_ref * 0.5,
                    f"{abs(carga.Fx):.1f}kN",
                    fontsize=7, color=color, ha='center', zorder=21)

    # Fuerza Y
    if abs(carga.Fy) > 1e-6:
        signo = 1 if carga.Fy > 0 else -1
        dy = signo * long_flecha
        ax.annotate(
            "", xy=(x, y), xytext=(x, y - dy),
            arrowprops=dict(arrowstyle='->', color=color,
                            lw=LINEAS["carga"]),
            zorder=20,
        )
        if mostrar_valor:
            ax.text(x + size_ref * 0.5, y - dy * 0.5,
                    f"{abs(carga.Fy):.1f}kN",
                    fontsize=7, color=color, ha='left', zorder=21)

    # Momento
    if abs(carga.Mz) > 1e-6:
        _dibujar_momento_nudo(ax, x, y, carga.Mz, size_ref, COLORES["carga_momento"])
        if mostrar_valor:
            ax.text(x + size_ref * 1.2, y,
                    f"{abs(carga.Mz):.1f}kNm",
                    fontsize=7, color=COLORES["carga_momento"],
                    ha='left', va='center', zorder=21)


def _dibujar_momento_nudo(
    ax: Axes, x: float, y: float, Mz: float, size_ref: float, color: str
) -> None:
    """Arco circular con flecha para representar momento en nudo."""
    radio = size_ref * 1.0
    # Mz > 0 → antihorario, Mz < 0 → horario
    sentido = 1 if Mz > 0 else -1
    theta = np.linspace(30, 330, 40) * math.pi / 180

    xs_arc = x + radio * np.cos(theta)
    ys_arc = y + radio * np.sin(theta)
    ax.plot(xs_arc, ys_arc, color=color, linewidth=LINEAS["carga"], zorder=20)

    # Flecha al final del arco
    ang_flecha = 330 * math.pi / 180
    dx_flecha = sentido * radio * 0.3 * math.sin(ang_flecha)
    dy_flecha = -sentido * radio * 0.3 * math.cos(ang_flecha)
    x_tip = x + radio * math.cos(ang_flecha)
    y_tip = y + radio * math.sin(ang_flecha)
    ax.annotate(
        "", xy=(x_tip + dx_flecha, y_tip + dy_flecha),
        xytext=(x_tip, y_tip),
        arrowprops=dict(arrowstyle='->', color=color, lw=1.5),
        zorder=21,
    )


def _dibujar_carga_puntual_barra(carga, ax: Axes, size_ref: float, mostrar_valor: bool) -> None:
    """Flecha apuntando al punto de aplicacion de la carga en la barra."""
    if carga.barra is None:
        return

    barra = carga.barra
    ang_barra = math.atan2(
        barra.nudo_j.y - barra.nudo_i.y,
        barra.nudo_j.x - barra.nudo_i.x
    )

    # Punto de aplicacion
    xa = barra.nudo_i.x + carga.a * math.cos(ang_barra)
    ya = barra.nudo_i.y + carga.a * math.sin(ang_barra)

    # Componentes globales de la carga
    Px, Py = carga.componentes_globales()
    mag = math.hypot(Px, Py)
    if mag < 1e-10:
        return

    long_flecha = size_ref * 3.0
    ux = Px / mag
    uy = Py / mag

    color = COLORES["carga_puntual"]
    ax.annotate(
        "", xy=(xa, ya),
        xytext=(xa - ux * long_flecha, ya - uy * long_flecha),
        arrowprops=dict(arrowstyle='->', color=color, lw=LINEAS["carga"]),
        zorder=20,
    )

    if mostrar_valor:
        ax.text(
            xa - ux * long_flecha * 0.5 + size_ref * 0.3,
            ya - uy * long_flecha * 0.5,
            f"{carga.P:.1f}kN",
            fontsize=7, color=color, ha='left', va='center', zorder=21,
        )


def _dibujar_carga_distribuida(carga, ax: Axes, size_ref: float, mostrar_valor: bool) -> None:
    """
    Dibuja la carga distribuida como un conjunto de flechas paralelas
    con intensidad proporcional (trapecio).
    """
    if carga.barra is None:
        return

    barra = carga.barra
    x2 = carga.x2 if carga.x2 is not None else barra.L

    ang_barra = math.atan2(
        barra.nudo_j.y - barra.nudo_i.y,
        barra.nudo_j.x - barra.nudo_i.x
    )
    cos_b = math.cos(ang_barra)
    sin_b = math.sin(ang_barra)

    # Direccion de la carga (perpendicular rotada por angulo)
    ang_carga_rad = math.radians(carga.angulo)
    # La carga en coord. locales: Px_local = cos(ang), Py_local = sin(ang)
    # Rotamos al global
    Px_unit_local = math.cos(ang_carga_rad)
    Py_unit_local = math.sin(ang_carga_rad)
    Px_unit = Px_unit_local * cos_b - Py_unit_local * sin_b
    Py_unit = Px_unit_local * sin_b + Py_unit_local * cos_b

    n_flechas = 8
    q_max = max(abs(carga.q1), abs(carga.q2))
    if q_max < 1e-10:
        return

    long_max = size_ref * 2.5
    color = COLORES["carga_distribuida"]

    # Puntos a lo largo de la barra
    ts = np.linspace(0, 1, n_flechas)
    xs_base = []
    ys_base = []
    xs_tip = []
    ys_tip = []

    for t in ts:
        x_local = carga.x1 + t * (x2 - carga.x1)
        # Intensidad en este punto (interpolacion lineal)
        q_en_x = carga.q1 + t * (carga.q2 - carga.q1)
        long_flecha = (abs(q_en_x) / q_max) * long_max if q_max > 0 else 0

        # Posicion global del punto en la barra
        x_global = barra.nudo_i.x + x_local * cos_b
        y_global = barra.nudo_i.y + x_local * sin_b

        # La flecha apunta hacia el punto en la barra (punta en la barra)
        x_tip = x_global
        y_tip = y_global
        x_base = x_global - Px_unit * long_flecha
        y_base = y_global - Py_unit * long_flecha

        xs_base.append(x_base)
        ys_base.append(y_base)
        xs_tip.append(x_tip)
        ys_tip.append(y_tip)

        if long_flecha > 1e-6:
            ax.annotate(
                "", xy=(x_tip, y_tip), xytext=(x_base, y_base),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.2),
                zorder=19,
            )

    # Linea de contorno del trapecio (union de las bases)
    ax.plot(xs_base, ys_base, color=color, linewidth=1.0,
            linestyle='-', zorder=18)

    # Mostrar valores en extremos
    if mostrar_valor:
        # Valor en inicio
        xi_ini = barra.nudo_i.x + carga.x1 * cos_b
        yi_ini = barra.nudo_i.y + carga.x1 * sin_b
        long_ini = (abs(carga.q1) / q_max) * long_max if q_max > 0 else 0
        ax.text(
            xi_ini - Px_unit * long_ini - size_ref * 0.2,
            yi_ini - Py_unit * long_ini,
            f"{carga.q1:.1f}kN/m",
            fontsize=6, color=color, ha='right', va='center', zorder=21,
        )
        # Valor en fin (solo si es diferente)
        if abs(carga.q2 - carga.q1) > 1e-3:
            xi_fin = barra.nudo_i.x + x2 * cos_b
            yi_fin = barra.nudo_i.y + x2 * sin_b
            long_fin = (abs(carga.q2) / q_max) * long_max if q_max > 0 else 0
            ax.text(
                xi_fin - Px_unit * long_fin - size_ref * 0.2,
                yi_fin - Py_unit * long_fin,
                f"{carga.q2:.1f}kN/m",
                fontsize=6, color=color, ha='right', va='center', zorder=21,
            )


# =============================================================================
# CONFIGURACION DE EJES
# =============================================================================

def _configurar_ejes(modelo: ModeloEstructural, ax: Axes, titulo: str) -> None:
    """Configura los ejes del grafico (limites, grilla, titulo, etc.)."""
    if not modelo.nudos:
        ax.set_title(titulo, fontsize=14, fontweight='bold')
        return

    xs = [n.x for n in modelo.nudos]
    ys = [n.y for n in modelo.nudos]

    margen_x = max((max(xs) - min(xs)) * 0.15, 1.0)
    margen_y = max((max(ys) - min(ys)) * 0.15, 1.0)

    ax.set_xlim(min(xs) - margen_x, max(xs) + margen_x)
    ax.set_ylim(min(ys) - margen_y * 2.5, max(ys) + margen_y)

    ax.set_aspect('equal', adjustable='box')
    ax.grid(True, alpha=0.25, linestyle='--')
    ax.set_xlabel('X [m]', fontsize=10)
    ax.set_ylabel('Y [m]', fontsize=10)
    ax.set_title(titulo, fontsize=14, fontweight='bold')
