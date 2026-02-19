"""
Serialización y deserialización de proyectos estructurales en formato JSON.

Convierte un ModeloEstructural completo a/desde un diccionario JSON que
incluye nudos, barras, materiales, secciones, vínculos y cargas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.domain.model.modelo_estructural import ModeloEstructural
from src.domain.entities.nudo import Nudo
from src.domain.entities.barra import Barra
from src.domain.entities.material import Material
from src.domain.entities.seccion import Seccion, SeccionRectangular, SeccionCircular
from src.domain.entities.vinculo import (
    Empotramiento, ApoyoFijo, Rodillo, Guia, ResorteElastico
)
from src.domain.entities.carga import (
    CargaPuntualNudo, CargaPuntualBarra, CargaDistribuida, CargaTermica, MovimientoImpuesto
)

VERSION_FORMATO = "1.0"


# =============================================================================
# GUARDAR
# =============================================================================

def guardar_proyecto(modelo: ModeloEstructural, ruta: str | Path) -> None:
    """
    Serializa el modelo estructural a un archivo JSON.

    Args:
        modelo: Modelo a guardar.
        ruta: Ruta del archivo de salida (.json).
    """
    ruta = Path(ruta)
    if ruta.suffix.lower() != ".json":
        ruta = ruta.with_suffix(".json")

    datos = _modelo_a_dict(modelo)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)


def _modelo_a_dict(modelo: ModeloEstructural) -> Dict[str, Any]:
    """Convierte un ModeloEstructural a diccionario serializable."""
    return {
        "version": VERSION_FORMATO,
        "nombre": modelo.nombre,
        "descripcion": modelo.descripcion,
        "materiales": [_material_a_dict(m) for m in modelo._materiales.values()],
        "secciones": [_seccion_a_dict(s) for s in modelo._secciones.values()],
        "nudos": [_nudo_a_dict(n) for n in modelo.nudos],
        "barras": [_barra_a_dict(b) for b in modelo.barras],
        "cargas": [_carga_a_dict(c) for c in modelo.cargas],
    }


def _material_a_dict(m: Material) -> Dict[str, Any]:
    return {
        "nombre": m.nombre,
        "E": m.E,
        "alpha": m.alpha,
        "rho": getattr(m, "rho", 0.0),
    }


def _seccion_a_dict(s: Seccion) -> Dict[str, Any]:
    base = {
        "nombre": s.nombre,
        "tipo": type(s).__name__,
        "A": s.A,
        "Jz": s.Jz,
        "h": getattr(s, "h", 0.0),
    }
    if isinstance(s, SeccionRectangular):
        base["b"] = s.b
        base["_h"] = s._h
    elif isinstance(s, SeccionCircular):
        base["diametro"] = s.diametro
    return base


def _vinculo_a_dict(v) -> Optional[Dict[str, Any]]:
    if v is None:
        return None
    t = type(v).__name__
    d: Dict[str, Any] = {"tipo": t}
    if isinstance(v, Rodillo):
        d["direccion"] = v.direccion
    elif isinstance(v, Guia):
        d["direccion_libre"] = v.direccion_libre
    elif isinstance(v, ResorteElastico):
        d["kx"] = v.kx
        d["ky"] = v.ky
        d["ktheta"] = v.ktheta
    return d


def _nudo_a_dict(n: Nudo) -> Dict[str, Any]:
    return {
        "id": n.id,
        "x": n.x,
        "y": n.y,
        "nombre": n.nombre,
        "vinculo": _vinculo_a_dict(n.vinculo),
    }


def _barra_a_dict(b: Barra) -> Dict[str, Any]:
    return {
        "id": b.id,
        "nudo_i_id": b.nudo_i.id,
        "nudo_j_id": b.nudo_j.id,
        "material_nombre": b.material.nombre,
        "seccion_nombre": b.seccion.nombre,
    }


def _carga_a_dict(c: Any) -> Optional[Dict[str, Any]]:
    if isinstance(c, CargaPuntualNudo):
        return {
            "tipo": "CargaPuntualNudo",
            "nudo_id": c.nudo.id if c.nudo else None,
            "Fx": c.Fx,
            "Fy": c.Fy,
            "Mz": c.Mz,
        }
    if isinstance(c, CargaPuntualBarra):
        return {
            "tipo": "CargaPuntualBarra",
            "barra_id": c.barra.id if c.barra else None,
            "P": c.P,
            "a": c.a,
            "angulo": c.angulo,
        }
    if isinstance(c, CargaDistribuida):
        return {
            "tipo": "CargaDistribuida",
            "barra_id": c.barra.id if c.barra else None,
            "q1": c.q1,
            "q2": c.q2,
            "x1": c.x1,
            "x2": c.x2,
            "angulo": c.angulo,
        }
    if isinstance(c, CargaTermica):
        return {
            "tipo": "CargaTermica",
            "barra_id": c.barra.id if c.barra else None,
            "delta_T_uniforme": c.delta_T_uniforme,
            "delta_T_gradiente": c.delta_T_gradiente,
        }
    if isinstance(c, MovimientoImpuesto):
        return {
            "tipo": "MovimientoImpuesto",
            "nudo_id": c.nudo.id if c.nudo else None,
            "delta_x": getattr(c, "delta_x", 0.0),
            "delta_y": getattr(c, "delta_y", 0.0),
            "delta_theta": getattr(c, "delta_theta", 0.0),
        }
    return None  # Tipo desconocido — omitir


# =============================================================================
# CARGAR
# =============================================================================

def cargar_proyecto(ruta: str | Path) -> ModeloEstructural:
    """
    Deserializa un archivo JSON a un ModeloEstructural.

    Args:
        ruta: Ruta del archivo .json.

    Returns:
        ModeloEstructural reconstruido.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el formato no es compatible.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)

    version = datos.get("version", "0.0")
    if version != VERSION_FORMATO:
        # Intentar cargar de todas formas (compatibilidad hacia adelante básica)
        import warnings
        warnings.warn(
            f"Versión del archivo ({version}) difiere de la esperada ({VERSION_FORMATO}). "
            "El proyecto puede no cargarse correctamente."
        )

    return _dict_a_modelo(datos)


def _dict_a_modelo(d: Dict[str, Any]) -> ModeloEstructural:
    """Reconstruye un ModeloEstructural desde un diccionario."""
    modelo = ModeloEstructural(
        nombre=d.get("nombre", "Sin título"),
        descripcion=d.get("descripcion", ""),
    )

    # 1. Materiales (se pre-cargan para que agregar_barra los encuentre)
    materiales: Dict[str, Material] = {}
    for m_d in d.get("materiales", []):
        m = Material(
            nombre=m_d["nombre"],
            E=m_d["E"],
            alpha=m_d.get("alpha", 1.2e-5),
            rho=m_d.get("rho", 0.0),
        )
        materiales[m.nombre] = m
        # Insertar directamente en el catálogo interno del modelo
        modelo._materiales[m.nombre] = m

    # 2. Secciones (igual: pre-cargar antes de crear barras)
    secciones: Dict[str, Seccion] = {}
    for s_d in d.get("secciones", []):
        s = _dict_a_seccion(s_d)
        if s is not None:
            secciones[s.nombre] = s
            modelo._secciones[s.nombre] = s

    # 3. Nudos (sin vínculos todavía)
    nudos: Dict[int, Nudo] = {}
    for n_d in d.get("nudos", []):
        # Usar ID guardado; se reasigna a través del modelo
        n = modelo.agregar_nudo(n_d["x"], n_d["y"], n_d.get("nombre", ""))
        # Si el ID generado difiere del original, remapear
        # (asumimos que los IDs son asignados en orden creciente)
        nudos[n_d["id"]] = n

    # 4. Vínculos (asignados luego de crear nudos para mantener referencias)
    for n_d in d.get("nudos", []):
        nudo = nudos[n_d["id"]]
        v_d = n_d.get("vinculo")
        if v_d:
            vinculo = _dict_a_vinculo(v_d)
            if vinculo is not None:
                modelo.asignar_vinculo(nudo.id, vinculo)

    # 5. Barras
    barras: Dict[int, Barra] = {}
    # Obtener material y sección por defecto si no se encuentran
    mat_default = Material("Acero A-36", E=200e6)
    sec_default = SeccionRectangular("Rect 30x50", b=0.30, _h=0.50)

    for b_d in d.get("barras", []):
        ni = nudos.get(b_d["nudo_i_id"])
        nj = nudos.get(b_d["nudo_j_id"])
        if ni is None or nj is None:
            continue
        mat = materiales.get(b_d.get("material_nombre", ""), mat_default)
        sec = secciones.get(b_d.get("seccion_nombre", ""), sec_default)
        barra = modelo.agregar_barra(ni, nj, mat, sec)
        barras[b_d["id"]] = barra

    # 6. Cargas
    for c_d in d.get("cargas", []):
        carga = _dict_a_carga(c_d, nudos, barras)
        if carga is not None:
            modelo.agregar_carga(carga)

    modelo.marcar_guardado()
    return modelo


def _dict_a_seccion(s_d: Dict[str, Any]) -> Optional[Seccion]:
    tipo = s_d.get("tipo", "Seccion")
    nombre = s_d.get("nombre", "")
    try:
        if tipo == "SeccionRectangular":
            return SeccionRectangular(nombre, b=s_d["b"], _h=s_d["_h"])
        elif tipo == "SeccionCircular":
            return SeccionCircular(nombre, diametro=s_d["diametro"])
        else:
            # Sección genérica con A y Jz
            return Seccion(nombre=nombre, A=s_d["A"], Jz=s_d["Jz"], h=s_d.get("h", 0.0))
    except Exception:
        return None


def _dict_a_vinculo(v_d: Dict[str, Any]):
    tipo = v_d.get("tipo", "")
    if tipo == "Empotramiento":
        return Empotramiento()
    elif tipo == "ApoyoFijo":
        return ApoyoFijo()
    elif tipo == "Rodillo":
        return Rodillo(direccion=v_d.get("direccion", "Uy"))
    elif tipo == "Guia":
        return Guia(direccion_libre=v_d.get("direccion_libre", "Ux"))
    elif tipo == "ResorteElastico":
        return ResorteElastico(
            kx=v_d.get("kx", 0.0),
            ky=v_d.get("ky", 0.0),
            ktheta=v_d.get("ktheta", 0.0),
        )
    return None


def _dict_a_carga(c_d: Dict[str, Any], nudos: Dict[int, Nudo], barras: Dict[int, Barra]):
    tipo = c_d.get("tipo", "")
    try:
        if tipo == "CargaPuntualNudo":
            nudo = nudos.get(c_d.get("nudo_id"))
            if nudo is None:
                return None
            return CargaPuntualNudo(
                nudo=nudo,
                Fx=c_d.get("Fx", 0.0),
                Fy=c_d.get("Fy", 0.0),
                Mz=c_d.get("Mz", 0.0),
            )
        elif tipo == "CargaPuntualBarra":
            barra = barras.get(c_d.get("barra_id"))
            if barra is None:
                return None
            return CargaPuntualBarra(
                barra=barra,
                P=c_d.get("P", 0.0),
                a=c_d.get("a", 0.0),
                angulo=c_d.get("angulo", -90.0),
            )
        elif tipo == "CargaDistribuida":
            barra = barras.get(c_d.get("barra_id"))
            if barra is None:
                return None
            return CargaDistribuida(
                barra=barra,
                q1=c_d.get("q1", 0.0),
                q2=c_d.get("q2", 0.0),
                x1=c_d.get("x1", 0.0),
                x2=c_d.get("x2"),
                angulo=c_d.get("angulo", -90.0),
            )
        elif tipo == "CargaTermica":
            barra = barras.get(c_d.get("barra_id"))
            if barra is None:
                return None
            return CargaTermica(
                barra=barra,
                delta_T_uniforme=c_d.get("delta_T_uniforme", 0.0),
                delta_T_gradiente=c_d.get("delta_T_gradiente", 0.0),
            )
        elif tipo == "MovimientoImpuesto":
            nudo = nudos.get(c_d.get("nudo_id"))
            if nudo is None:
                return None
            return MovimientoImpuesto(
                nudo=nudo,
                delta_x=c_d.get("delta_x", 0.0),
                delta_y=c_d.get("delta_y", 0.0),
                delta_theta=c_d.get("delta_theta", 0.0),
            )
    except Exception:
        pass
    return None
