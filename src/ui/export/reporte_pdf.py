"""
Generador de reportes PDF para el sistema de analisis estructural.

Genera un informe tecnico completo con:
- Portada con datos del proyecto
- Datos del modelo (nudos, barras, cargas)
- Proceso de resolucion (redundantes, matriz F, vector e0)
- Diagramas M/V/N y deformada (imagenes matplotlib)
- Tabla de reacciones con verificacion de equilibrio

Uso:
    from src.ui.export.reporte_pdf import generar_reporte_pdf
    generar_reporte_pdf(modelo, resultado, "informe.pdf")
"""

from __future__ import annotations

import io
import datetime
import math
from typing import TYPE_CHECKING, List, Optional

import numpy as np

# reportlab
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable, KeepTogether,
)

# matplotlib — backend sin GUI
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Visualizacion existente
from src.ui.visualization.diagramas import graficar_diagramas_combinados
from src.ui.visualization.geometria import graficar_estructura

if TYPE_CHECKING:
    from src.domain.model.modelo_estructural import ModeloEstructural
    from src.domain.analysis.motor_fuerzas import ResultadoAnalisis


# ---------------------------------------------------------------------------
# Paleta de colores
# ---------------------------------------------------------------------------
COLOR_PRIMARIO = colors.HexColor("#1a3a5c")     # Azul oscuro
COLOR_SECUNDARIO = colors.HexColor("#2e7d9c")   # Azul medio
COLOR_ACENTO = colors.HexColor("#dc143c")        # Rojo (momentos)
COLOR_HEADER = colors.HexColor("#d0dde8")        # Azul muy claro (encabezados tabla)
COLOR_LINEA = colors.HexColor("#99b0c4")         # Linea separadora


# ---------------------------------------------------------------------------
# Helpers de estilo
# ---------------------------------------------------------------------------

def _get_styles():
    """Retorna diccionario de estilos ParagraphStyle personalizados."""
    base = getSampleStyleSheet()

    titulo_portada = ParagraphStyle(
        "TituloPortada",
        parent=base["Title"],
        fontSize=28,
        textColor=COLOR_PRIMARIO,
        spaceAfter=0.3 * cm,
        fontName="Helvetica-Bold",
        alignment=1,  # centrado
    )
    subtitulo_portada = ParagraphStyle(
        "SubtituloPortada",
        parent=base["Normal"],
        fontSize=16,
        textColor=COLOR_SECUNDARIO,
        spaceAfter=0.2 * cm,
        fontName="Helvetica",
        alignment=1,
    )
    seccion = ParagraphStyle(
        "Seccion",
        parent=base["Heading1"],
        fontSize=13,
        textColor=COLOR_PRIMARIO,
        spaceBefore=0.4 * cm,
        spaceAfter=0.2 * cm,
        fontName="Helvetica-Bold",
        borderPad=0,
    )
    subseccion = ParagraphStyle(
        "Subseccion",
        parent=base["Heading2"],
        fontSize=11,
        textColor=COLOR_SECUNDARIO,
        spaceBefore=0.3 * cm,
        spaceAfter=0.15 * cm,
        fontName="Helvetica-Bold",
    )
    normal = ParagraphStyle(
        "NormalPropio",
        parent=base["Normal"],
        fontSize=9,
        leading=14,
        fontName="Helvetica",
    )
    nota = ParagraphStyle(
        "Nota",
        parent=base["Normal"],
        fontSize=8,
        textColor=colors.grey,
        fontName="Helvetica-Oblique",
        spaceAfter=0.1 * cm,
    )
    pie = ParagraphStyle(
        "Pie",
        parent=base["Normal"],
        fontSize=7,
        textColor=colors.grey,
        fontName="Helvetica",
        alignment=1,
    )
    return {
        "titulo_portada": titulo_portada,
        "subtitulo_portada": subtitulo_portada,
        "seccion": seccion,
        "subseccion": subseccion,
        "normal": normal,
        "nota": nota,
        "pie": pie,
    }


def _estilo_tabla_basico(col_widths=None):
    """TableStyle estandar para tablas de datos."""
    return TableStyle([
        # Encabezado
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_PRIMARIO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        # Datos
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        # Bordes y padding
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_LINEA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8fb")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])


# ---------------------------------------------------------------------------
# Conversion figura matplotlib → Image reportlab
# ---------------------------------------------------------------------------

def _figura_a_imagen(fig, width_cm: float = 17.0, aspect: float = 0.55, dpi: int = 150) -> Image:
    """
    Convierte una figura matplotlib en un objeto Image de reportlab.

    Args:
        fig: Figura matplotlib
        width_cm: Ancho deseado en el PDF [cm]
        aspect: Relacion alto/ancho (height = width * aspect)
        dpi: Resolucion de la imagen

    Returns:
        Image de reportlab lista para insertar en el story
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    plt.close(fig)
    w = width_cm * cm
    h = w * aspect
    return Image(buf, width=w, height=h)


# ---------------------------------------------------------------------------
# Paginas del reporte
# ---------------------------------------------------------------------------

def _agregar_portada(story: list, modelo, resultado, styles: dict):
    """Pagina 1: Portada con titulo, nombre del proyecto y resumen."""
    story.append(Spacer(1, 3 * cm))

    story.append(Paragraph("INFORME DE ANALISIS ESTRUCTURAL", styles["titulo_portada"]))
    story.append(Paragraph("Metodo de las Fuerzas", styles["subtitulo_portada"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=COLOR_SECUNDARIO))
    story.append(Spacer(1, 0.5 * cm))

    nombre = getattr(modelo, "nombre", "") or "Sin nombre"
    story.append(Paragraph(nombre, styles["subtitulo_portada"]))
    story.append(Spacer(1, 2 * cm))

    # Tabla resumen
    fecha = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    gh = resultado.grado_hiperestaticidad
    num_red = len(resultado.redundantes) if resultado.redundantes else 0
    num_barras = len(modelo.barras)
    num_nudos = len(modelo.nudos)
    num_cargas = len(modelo.cargas)

    datos_resumen = [
        ["Parametro", "Valor"],
        ["Fecha de generacion", fecha],
        ["Grado de hiperestaticidad (GH)", str(gh)],
        ["Numero de redundantes", str(num_red)],
        ["Numero de barras", str(num_barras)],
        ["Numero de nudos", str(num_nudos)],
        ["Numero de cargas", str(num_cargas)],
        ["Estado del analisis", "EXITOSO" if resultado.exitoso else "CON ERRORES"],
    ]

    t = Table(datos_resumen, colWidths=[10 * cm, 7 * cm])
    t.setStyle(_estilo_tabla_basico())
    story.append(t)

    story.append(Spacer(1, 2 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_LINEA))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Generado con PyANES-MF v1.3.0 — Sistema de Analisis Estructural por Metodo de las Fuerzas",
        styles["pie"]
    ))


def _agregar_datos_modelo(story: list, modelo, styles: dict):
    """Pagina 2: Tablas de nudos, barras y cargas."""
    story.append(Paragraph("DATOS DEL MODELO", styles["seccion"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARIO))

    # --- Nudos ---
    story.append(Paragraph("Nudos", styles["subseccion"]))
    cabecera_nudos = ["ID", "x [m]", "y [m]", "Vinculo"]
    filas_nudos = [cabecera_nudos]
    for nudo in sorted(modelo.nudos, key=lambda n: n.id):
        vinculo_str = "Libre"
        if nudo.vinculo is not None:
            vinculo_str = type(nudo.vinculo).__name__
        filas_nudos.append([
            str(nudo.id),
            f"{nudo.x:.3f}",
            f"{nudo.y:.3f}",
            vinculo_str,
        ])

    t_nudos = Table(filas_nudos, colWidths=[2 * cm, 4 * cm, 4 * cm, 7 * cm])
    t_nudos.setStyle(_estilo_tabla_basico())
    story.append(t_nudos)
    story.append(Spacer(1, 0.4 * cm))

    # --- Barras ---
    story.append(Paragraph("Barras", styles["subseccion"]))
    cabecera_barras = ["ID", "Nudo i", "Nudo j", "L [m]", "E [kN/m2]", "A [m2]", "Iz [m4]"]
    filas_barras = [cabecera_barras]
    for barra in sorted(modelo.barras, key=lambda b: b.id):
        E_val = barra.material.E if barra.material else 0.0
        A_val = barra.seccion.A if barra.seccion else 0.0
        Iz_val = barra.seccion.Iz if barra.seccion else 0.0
        filas_barras.append([
            str(barra.id),
            str(barra.nudo_i.id),
            str(barra.nudo_j.id),
            f"{barra.L:.3f}",
            f"{E_val:.3e}",
            f"{A_val:.4e}",
            f"{Iz_val:.4e}",
        ])

    col_barras = [1.5 * cm, 2 * cm, 2 * cm, 3 * cm, 4 * cm, 3.5 * cm, 3.5 * cm]
    t_barras = Table(filas_barras, colWidths=col_barras)
    t_barras.setStyle(_estilo_tabla_basico())
    story.append(t_barras)
    story.append(Spacer(1, 0.4 * cm))

    # --- Cargas ---
    story.append(Paragraph("Cargas aplicadas", styles["subseccion"]))
    cargas = modelo.cargas
    if not cargas:
        story.append(Paragraph("No hay cargas definidas en el modelo.", styles["nota"]))
    else:
        cabecera_cargas = ["#", "Tipo", "Descripcion"]
        filas_cargas = [cabecera_cargas]
        for i, carga in enumerate(cargas, 1):
            tipo_str = type(carga).__name__
            desc_str = getattr(carga, "descripcion", str(carga))
            filas_cargas.append([str(i), tipo_str, desc_str])

        t_cargas = Table(filas_cargas, colWidths=[1.5 * cm, 5 * cm, 11 * cm])
        t_cargas.setStyle(_estilo_tabla_basico())
        story.append(t_cargas)


def _agregar_proceso_resolucion(story: list, resultado, styles: dict):
    """Pagina 3: Redundantes, matriz F, vector e0, condicionamiento."""
    story.append(Paragraph("PROCESO DE RESOLUCION", styles["seccion"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARIO))

    story.append(Paragraph(
        f"Grado de hiperestaticidad: GH = {resultado.grado_hiperestaticidad}",
        styles["normal"]
    ))
    story.append(Spacer(1, 0.2 * cm))

    # --- Redundantes y valores Xi ---
    story.append(Paragraph("Redundantes resueltos", styles["subseccion"]))
    if resultado.redundantes:
        cab_red = ["i", "Redundante Xi", "Descripcion", "Valor"]
        filas_red = [cab_red]
        for i, red in enumerate(resultado.redundantes, 1):
            valor = resultado.Xi(i)
            desc = getattr(red, "descripcion", str(red))
            filas_red.append([
                f"X{i}",
                str(red),
                desc,
                f"{valor:+.6f}",
            ])
        t_red = Table(filas_red, colWidths=[2 * cm, 4 * cm, 7.5 * cm, 4 * cm])
        t_red.setStyle(_estilo_tabla_basico())
        story.append(t_red)
    else:
        story.append(Paragraph(
            "La estructura es isostatica (GH=0). No hay redundantes.",
            styles["nota"]
        ))

    story.append(Spacer(1, 0.4 * cm))

    # --- Matriz de flexibilidad [F] ---
    story.append(Paragraph("Matriz de flexibilidad [F]", styles["subseccion"]))
    F = resultado.matriz_F
    if F is not None and F.size > 0:
        n = F.shape[0]
        # Encabezado de columnas
        cab_F = [""] + [f"X{j+1}" for j in range(n)]
        filas_F = [cab_F]
        for i in range(n):
            fila = [f"X{i+1}"] + [f"{F[i, j]:.4e}" for j in range(n)]
            filas_F.append(fila)

        ancho_col = min(2.5 * cm, 17 * cm / (n + 1))
        col_w_F = [1.5 * cm] + [ancho_col] * n
        t_F = Table(filas_F, colWidths=col_w_F)
        t_F.setStyle(_estilo_tabla_basico())
        story.append(t_F)
    else:
        story.append(Paragraph("Matriz F no disponible (estructura isostatica).", styles["nota"]))

    story.append(Spacer(1, 0.4 * cm))

    # --- Vector {e0} ---
    story.append(Paragraph("Vector de terminos independientes {e0}", styles["subseccion"]))
    e0 = resultado.vector_e0
    if e0 is not None and e0.size > 0:
        cab_e0 = ["i", "e0i"]
        filas_e0 = [cab_e0]
        for i, val in enumerate(e0, 1):
            filas_e0.append([f"e0{i}", f"{val:.6e}"])
        t_e0 = Table(filas_e0, colWidths=[4 * cm, 6 * cm])
        t_e0.setStyle(_estilo_tabla_basico())
        story.append(t_e0)
    else:
        story.append(Paragraph("Vector e0 no disponible.", styles["nota"]))

    story.append(Spacer(1, 0.4 * cm))

    # --- Metricas numericas ---
    story.append(Paragraph("Metricas numericas del sistema", styles["subseccion"]))
    cond = getattr(resultado, "condicionamiento", None)
    residual = getattr(resultado, "residual_sece", None)
    metricas = [["Metrica", "Valor"]]
    if cond is not None:
        cond_ok = cond < 1e12
        metricas.append(["Condicionamiento cond([F])", f"{cond:.3e}  {'OK' if cond_ok else 'ADVERTENCIA: mal condicionada'}"])
    if residual is not None:
        res_ok = residual < 1e-6
        metricas.append(["Residual del SECE ||[F]{X}+{e0}||", f"{residual:.3e}  {'OK' if res_ok else 'ADVERTENCIA: residual alto'}"])
    if len(metricas) > 1:
        t_met = Table(metricas, colWidths=[9 * cm, 8.5 * cm])
        t_met.setStyle(_estilo_tabla_basico())
        story.append(t_met)


def _agregar_diagramas(story: list, modelo, resultado, styles: dict):
    """Pagina 4: Imagenes matplotlib — geometria y diagramas M/V/N."""
    story.append(Paragraph("DIAGRAMAS DE ESFUERZOS", styles["seccion"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARIO))

    # Figura 1: Geometria
    story.append(Paragraph("Geometria de la estructura", styles["subseccion"]))
    try:
        fig_geo, _ = graficar_estructura(modelo, titulo="Geometria Estructural")
        story.append(_figura_a_imagen(fig_geo, width_cm=17.0, aspect=0.5))
    except Exception as exc:
        story.append(Paragraph(f"No se pudo generar la figura de geometria: {exc}", styles["nota"]))

    story.append(Spacer(1, 0.4 * cm))

    # Figura 2: Diagramas M/V/N combinados
    story.append(Paragraph("Diagramas de esfuerzos internos M, V, N", styles["subseccion"]))
    try:
        fig_diag, _ = graficar_diagramas_combinados(
            modelo, resultado,
            titulo_general="Diagramas de Esfuerzos Internos"
        )
        story.append(_figura_a_imagen(fig_diag, width_cm=17.0, aspect=0.7))
    except Exception as exc:
        story.append(Paragraph(f"No se pudo generar los diagramas: {exc}", styles["nota"]))

    # Figura 3: Deformada (import lazy — puede no estar disponible)
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Deformada elastica", styles["subseccion"]))
    try:
        from src.ui.visualization.deformada import graficar_deformada
        fig_def, _ = graficar_deformada(modelo, resultado, titulo="Deformada de la Estructura")
        story.append(_figura_a_imagen(fig_def, width_cm=17.0, aspect=0.5))
    except Exception as exc:
        story.append(Paragraph(
            f"La deformada no pudo calcularse para esta estructura: {exc}",
            styles["nota"]
        ))


def _agregar_reacciones(story: list, modelo, resultado, styles: dict):
    """Pagina 5: Tabla de reacciones y verificacion de equilibrio."""
    story.append(Paragraph("REACCIONES Y VERIFICACION DE EQUILIBRIO", styles["seccion"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARIO))

    # --- Tabla de reacciones ---
    story.append(Paragraph("Reacciones en vinculos", styles["subseccion"]))
    cab_reac = ["Nudo", "Vinculo", "Rx [kN]", "Ry [kN]", "Mz [kNm]"]
    filas_reac = [cab_reac]

    nudos_con_vinculo = [n for n in sorted(modelo.nudos, key=lambda n: n.id) if n.vinculo is not None]
    for nudo in nudos_con_vinculo:
        Rx, Ry, Mz = resultado.obtener_reaccion(nudo.id)
        vinculo_str = type(nudo.vinculo).__name__
        filas_reac.append([
            str(nudo.id),
            vinculo_str,
            f"{Rx:+.4f}",
            f"{Ry:+.4f}",
            f"{Mz:+.4f}",
        ])

    col_reac = [2 * cm, 4.5 * cm, 3.5 * cm, 3.5 * cm, 4 * cm]
    t_reac = Table(filas_reac, colWidths=col_reac)
    t_reac.setStyle(_estilo_tabla_basico())
    story.append(t_reac)
    story.append(Spacer(1, 0.5 * cm))

    # --- Verificacion de equilibrio ---
    story.append(Paragraph("Verificacion de equilibrio global", styles["subseccion"]))

    # Calcular sumas
    SumRx = sum(resultado.obtener_reaccion(n.id)[0] for n in nudos_con_vinculo)
    SumRy = sum(resultado.obtener_reaccion(n.id)[1] for n in nudos_con_vinculo)
    SumMz_ref = sum(resultado.obtener_reaccion(n.id)[2] for n in nudos_con_vinculo)

    # Sumar cargas externas en nudos
    SumFx_cargas = 0.0
    SumFy_cargas = 0.0
    from src.domain.entities.carga import CargaPuntualNudo
    for carga in modelo.cargas:
        if isinstance(carga, CargaPuntualNudo):
            SumFx_cargas += getattr(carga, "Fx", 0.0)
            SumFy_cargas += getattr(carga, "Fy", 0.0)

    tol = 1e-4
    eq_fx = abs(SumRx + SumFx_cargas) < tol
    eq_fy = abs(SumRy + SumFy_cargas) < tol

    def _simbolo(ok: bool) -> str:
        return "OK" if ok else "FALLA"

    cab_eq = ["Ecuacion", "Reacciones", "Cargas", "Suma", "Estado"]
    filas_eq = [
        cab_eq,
        ["SFx = 0",
         f"{SumRx:+.4f} kN",
         f"{SumFx_cargas:+.4f} kN",
         f"{SumRx + SumFx_cargas:+.2e}",
         _simbolo(eq_fx)],
        ["SFy = 0",
         f"{SumRy:+.4f} kN",
         f"{SumFy_cargas:+.4f} kN",
         f"{SumRy + SumFy_cargas:+.2e}",
         _simbolo(eq_fy)],
    ]

    col_eq = [3 * cm, 4 * cm, 4 * cm, 3.5 * cm, 3 * cm]
    t_eq = Table(filas_eq, colWidths=col_eq)
    estilo_eq = _estilo_tabla_basico()
    # Colorear celda de estado
    for fila_idx in range(1, len(filas_eq)):
        ok_val = filas_eq[fila_idx][4] == "OK"
        color_celda = colors.HexColor("#d4edda") if ok_val else colors.HexColor("#f8d7da")
        estilo_eq.add("BACKGROUND", (4, fila_idx), (4, fila_idx), color_celda)
    t_eq.setStyle(estilo_eq)
    story.append(t_eq)

    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_LINEA))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"Informe generado el {datetime.datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')} "
        f"con PyANES-MF v1.3.0",
        styles["pie"]
    ))


# ---------------------------------------------------------------------------
# Funcion publica principal
# ---------------------------------------------------------------------------

def generar_reporte_pdf(
    modelo: "ModeloEstructural",
    resultado: "ResultadoAnalisis",
    ruta_salida: str,
) -> None:
    """
    Genera un reporte PDF completo del analisis estructural.

    El PDF contiene 5 secciones:
    1. Portada con resumen del proyecto
    2. Datos del modelo (nudos, barras, cargas)
    3. Proceso de resolucion (redundantes, [F], {e0}, metricas)
    4. Diagramas de esfuerzos M, V, N y deformada
    5. Tabla de reacciones con verificacion de equilibrio

    Args:
        modelo: ModeloEstructural con la definicion de la estructura
        resultado: ResultadoAnalisis devuelto por el motor
        ruta_salida: Ruta completa del archivo PDF a generar (incluye .pdf)

    Raises:
        ImportError: Si reportlab no esta instalado
        Exception: Si ocurre un error durante la generacion
    """
    doc = SimpleDocTemplate(
        ruta_salida,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Informe Estructural — {getattr(modelo, 'nombre', 'Proyecto')}",
        author="PyANES-MF v1.3.0",
        subject="Analisis Estructural por Metodo de las Fuerzas",
    )

    styles = _get_styles()
    story: list = []

    # 1. Portada
    _agregar_portada(story, modelo, resultado, styles)
    story.append(PageBreak())

    # 2. Datos del modelo
    _agregar_datos_modelo(story, modelo, styles)
    story.append(PageBreak())

    # 3. Proceso de resolucion
    _agregar_proceso_resolucion(story, resultado, styles)
    story.append(PageBreak())

    # 4. Diagramas
    _agregar_diagramas(story, modelo, resultado, styles)
    story.append(PageBreak())

    # 5. Reacciones y equilibrio
    _agregar_reacciones(story, modelo, resultado, styles)

    doc.build(story)
