"""
Solver Adaptativo: Método de Deformaciones + búsqueda iterativa de redundantes MF.

Este módulo implementa una estrategia de análisis en dos pasos:

1. **MD como referencia** (Método de las Deformaciones): siempre converge para
   estructuras bien vinculadas, produciendo el resultado correcto de forma
   sistemática (no requiere elección de redundantes).

2. **Búsqueda exhaustiva para MF** (Método de las Fuerzas): itera sobre todas
   las combinaciones posibles de redundantes candidatos, descartando las que
   generan inestabilidad y deteniendo la búsqueda en cuanto los resultados MF
   coincidan con MD dentro de la tolerancia indicada.

Esto resuelve el problema de mala elección de redundantes en MF y provee
validación cruzada automática cuando ambos métodos convergen.

Uso típico::

    from src.domain.analysis.solver_adaptativo import resolver_con_fallback

    resultado = resolver_con_fallback(modelo, tol=1e-3, verbose=True)

    if resultado.validacion_cruzada:
        print(f"Ambos métodos OK — max diff: {resultado.max_diferencia:.2e}")
    else:
        print("Solo MD disponible — usar resultado_md")

    diagrama = resultado.mejor_resultado.diagramas_finales[barra_id]
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from itertools import combinations
from math import comb
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from src.domain.model.modelo_estructural import ModeloEstructural

from .motor_deformaciones import analizar_estructura_deformaciones, comparar_resultados
from .motor_fuerzas import MotorMetodoFuerzas, ResultadoAnalisis
from .redundantes import Redundante, SelectorRedundantes

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclass de resultado
# ---------------------------------------------------------------------------


@dataclass
class ResultadoAdaptativo:
    """
    Resultado del solver adaptativo con diagnóstico completo.

    Attributes:
        resultado_md: Resultado del Método de las Deformaciones (siempre
            presente si el modelo es válido).
        resultado_mf: Resultado del Método de las Fuerzas con la mejor
            combinación de redundantes encontrada (None si ninguna coincidió).
        redundantes_usados: Combinación de redundantes que produjo coincidencia
            (None si MF no convergió).
        metodo_exitoso: Indica qué métodos resolvieron exitosamente.
            Valores posibles: ``"MD"``, ``"MF"``, ``"ambos"``.
        validacion_cruzada: Diccionario de ``comparar_resultados()`` con
            ``coinciden``, ``max_diferencia``, ``diferencias_por_barra`` y
            ``diferencias_reacciones``. None si MF no llegó a compararse.
        intentos_mf: Número de combinaciones de redundantes probadas con MF.
        combinaciones_totales: Total de combinaciones C(n_cand, GH) posibles.
        combinaciones_invalidas: Combinaciones descartadas por inestabilidad.
        mensaje: Texto descriptivo del resultado del proceso.
    """

    resultado_md: Optional[ResultadoAnalisis] = None
    resultado_mf: Optional[ResultadoAnalisis] = None
    redundantes_usados: Optional[List[Redundante]] = None
    metodo_exitoso: str = ""
    validacion_cruzada: Optional[dict] = None
    intentos_mf: int = 0
    combinaciones_totales: int = 0
    combinaciones_invalidas: int = 0
    mensaje: str = ""

    @property
    def mejor_resultado(self) -> Optional[ResultadoAnalisis]:
        """
        Retorna el resultado más completo disponible.

        Prefiere MD cuando ambos están disponibles porque el MD es siempre
        correcto y no depende de elección de redundantes. Si se requiere
        la información de redundantes (valores Xi), usar ``resultado_mf``.
        """
        return self.resultado_md

    @property
    def max_diferencia(self) -> float:
        """Máxima diferencia absoluta entre MF y MD (inf si no comparado)."""
        if self.validacion_cruzada is None:
            return float("inf")
        return self.validacion_cruzada["max_diferencia"]

    @property
    def ambos_validos(self) -> bool:
        """True si ambos métodos convergieron y coincidieron dentro de tol."""
        return self.metodo_exitoso == "ambos"

    def resumen(self) -> str:
        """Texto resumido del resultado para imprimir en consola."""
        lineas = [
            f"=== Solver Adaptativo ===",
            f"  Metodo exitoso  : {self.metodo_exitoso or 'ninguno'}",
            f"  GH              : {self.combinaciones_totales} combinaciones posibles",
            f"  Intentos MF     : {self.intentos_mf}",
            f"  Invalidas (inest): {self.combinaciones_invalidas}",
        ]
        if self.validacion_cruzada:
            lineas.append(
                f"  Max diferencia  : {self.max_diferencia:.2e}"
            )
            lineas.append(
                f"  Validacion OK   : {self.validacion_cruzada['coinciden']}"
            )
        if self.redundantes_usados:
            nombres = [r.descripcion for r in self.redundantes_usados]
            lineas.append(f"  Redundantes MF  : {nombres}")
        lineas.append(f"  Mensaje         : {self.mensaje}")
        return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------


def resolver_con_fallback(
    modelo: "ModeloEstructural",
    tol: float = 1e-3,
    max_combinaciones: int = 500,
    verbose: bool = False,
) -> ResultadoAdaptativo:
    """
    Resuelve la estructura con MD como referencia e itera combinaciones de
    redundantes en MF hasta encontrar una que coincida.

    Algoritmo:

    1. Resolver con **MD** (Método de las Deformaciones) — siempre correcto.
    2. Obtener todos los candidatos a redundantes via ``SelectorRedundantes``.
    3. Iterar ``C(n_candidatos, GH)`` combinaciones:

       a. Descartar combinaciones que crean inestabilidad (``_crea_inestabilidad``).
       b. Intentar MF con esa combinación.
       c. Comparar MF contra MD usando ``comparar_resultados()``.
       d. Si ``coinciden`` → retornar con metodo="ambos".

    4. Si se agota el límite sin coincidencia, retornar solo MD.

    Args:
        modelo: Modelo estructural con nudos, barras, vínculos y cargas.
        tol: Tolerancia [kN o kNm] para considerar que MF y MD coinciden.
        max_combinaciones: Límite de combinaciones a probar (evita explosión
            combinatoria). Para GH alto o muchos candidatos, aumentar.
        verbose: Si True, emite mensajes de logging nivel DEBUG/INFO/WARNING.

    Returns:
        :class:`ResultadoAdaptativo` con diagnóstico completo y acceso a los
        resultados de ambos métodos.

    Example::

        resultado = resolver_con_fallback(modelo, tol=1e-2, verbose=True)
        if resultado.ambos_validos:
            print(resultado.resumen())
        M_centro = resultado.mejor_resultado.M(barra_id=1, x=3.0)
    """
    res = ResultadoAdaptativo()
    gh = modelo.grado_hiperestaticidad

    # -----------------------------------------------------------------------
    # Paso 1 — MD como referencia (siempre)
    # -----------------------------------------------------------------------
    try:
        res.resultado_md = analizar_estructura_deformaciones(modelo)
        res.metodo_exitoso = "MD"
        if verbose:
            logger.info("MD completado exitosamente (resultado de referencia)")
    except Exception as exc:
        res.mensaje = f"MD fallo: {exc}"
        logger.error(res.mensaje)
        return res

    # Estructura isostática: MD es suficiente, no hay redundantes que probar
    if gh == 0:
        res.metodo_exitoso = "MD"
        res.mensaje = "Estructura isostatica: MD resuelve directamente, sin MF necesario"
        if verbose:
            logger.info(res.mensaje)
        return res

    # -----------------------------------------------------------------------
    # Paso 2 — Identificar candidatos
    # -----------------------------------------------------------------------
    selector = SelectorRedundantes(modelo)
    selector._identificar_candidatos()
    candidatos: List[Redundante] = selector.candidatos

    n_cand = len(candidatos)
    total_combos = comb(n_cand, gh) if n_cand >= gh else 0
    res.combinaciones_totales = total_combos

    if total_combos == 0:
        res.mensaje = (
            f"No hay candidatos suficientes (n={n_cand}, GH={gh}). "
            "Usando solo MD."
        )
        if verbose:
            logger.warning(res.mensaje)
        return res

    if verbose:
        logger.info(
            f"GH={gh}, candidatos={n_cand}, combinaciones posibles={total_combos}, "
            f"limite={max_combinaciones}"
        )

    # -----------------------------------------------------------------------
    # Paso 3 — Iterar combinaciones
    # -----------------------------------------------------------------------
    intentos = 0
    invalidas = 0

    for combo_tuple in combinations(candidatos, gh):
        if intentos >= max_combinaciones:
            if verbose:
                logger.warning(
                    f"Limite de {max_combinaciones} combinaciones alcanzado sin coincidencia"
                )
            break

        # Clonar redundantes para no mutar los candidatos originales
        combo: List[Redundante] = [copy.copy(r) for r in combo_tuple]

        # Descartar combinaciones inestables sin siquiera intentar MF
        if selector._crea_inestabilidad(combo):
            invalidas += 1
            if verbose:
                logger.debug(
                    f"Combo {[r.descripcion for r in combo]} descartada por inestabilidad"
                )
            continue

        intentos += 1

        # Asignar índices 1-based
        for i, r in enumerate(combo):
            r.indice = i + 1

        # Intentar MF con esta combinación
        try:
            motor_mf = MotorMetodoFuerzas(
                modelo,
                seleccion_manual_redundantes=combo,
            )
            r_mf = motor_mf.resolver()

            if not r_mf.exitoso:
                if verbose:
                    logger.debug(
                        f"Intento {intentos}: MF no exitoso con "
                        f"{[r.descripcion for r in combo]}"
                    )
                continue

            # Comparar MF con MD
            comp = comparar_resultados(r_mf, res.resultado_md, tol=tol)

            if comp["coinciden"]:
                res.resultado_mf = r_mf
                res.redundantes_usados = combo
                res.metodo_exitoso = "ambos"
                res.validacion_cruzada = comp
                res.intentos_mf = intentos
                res.combinaciones_invalidas = invalidas
                res.mensaje = (
                    f"Validacion cruzada OK en {intentos} intento(s). "
                    f"Max diff={comp['max_diferencia']:.2e} < tol={tol}"
                )
                if verbose:
                    logger.info(res.mensaje)
                return res

            if verbose:
                logger.debug(
                    f"Intento {intentos}: diff={comp['max_diferencia']:.2e} > tol={tol} "
                    f"con {[r.descripcion for r in combo]}"
                )

        except Exception as exc:
            if verbose:
                logger.debug(f"Intento {intentos}: excepcion — {exc}")
            continue

    # -----------------------------------------------------------------------
    # Fin sin coincidencia — devolver solo MD
    # -----------------------------------------------------------------------
    res.intentos_mf = intentos
    res.combinaciones_invalidas = invalidas
    res.mensaje = (
        f"MF no coincidio con MD en {intentos} combinaciones probadas "
        f"({invalidas} inestables descartadas). "
        "Usar resultado_md (siempre correcto)."
    )
    if verbose:
        logger.warning(res.mensaje)

    return res
