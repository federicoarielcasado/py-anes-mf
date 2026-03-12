"""
Generación de subestructuras para el Método de las Fuerzas.

Crea la estructura fundamental (isostática) y las subestructuras
con cargas unitarias para cada redundante.
"""

from __future__ import annotations

import copy
import math
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from src.domain.mechanics.esfuerzos import DiagramaEsfuerzos

if TYPE_CHECKING:
    from src.domain.entities.barra import Barra
    from src.domain.entities.carga import Carga
    from src.domain.entities.nudo import Nudo
    from src.domain.entities.vinculo import Vinculo
    from src.domain.analysis.redundantes import Redundante, TipoRedundante


@dataclass
class Subestructura:
    """
    Representa una configuración de carga (estructura fundamental o Xi).

    Cada subestructura contiene:
    - La geometría (referencia a nudos y barras del modelo original)
    - Las cargas aplicadas (reales para fundamental, unitaria para Xi)
    - Los esfuerzos calculados (N, V, M en cada barra)
    - Las reacciones de vínculo

    Attributes:
        nombre: Identificador ("Fundamental", "X1", "X2", etc.)
        es_fundamental: True si es la estructura con cargas reales
        redundante: Redundante asociado (None para fundamental)
    """
    nombre: str
    es_fundamental: bool = True
    redundante: Optional[Redundante] = None

    # Diagramas de esfuerzos para cada barra {barra_id: DiagramaEsfuerzos}
    diagramas: Dict[int, DiagramaEsfuerzos] = field(default_factory=dict)

    # Reacciones en vínculos {nudo_id: (Rx, Ry, Mz)}
    reacciones: Dict[int, tuple] = field(default_factory=dict)

    # Desplazamientos en nudos liberados (para verificación)
    desplazamientos_liberados: Dict[int, float] = field(default_factory=dict)

    def M(self, barra_id: int, x: float) -> float:
        """
        Obtiene el momento flector en una posición de una barra.

        Args:
            barra_id: ID de la barra
            x: Posición desde el nudo i [m]

        Returns:
            Momento flector M(x) [kNm]
        """
        if barra_id not in self.diagramas:
            return 0.0
        return self.diagramas[barra_id].M(x)

    def V(self, barra_id: int, x: float) -> float:
        """
        Obtiene el cortante en una posición de una barra.

        Args:
            barra_id: ID de la barra
            x: Posición desde el nudo i [m]

        Returns:
            Esfuerzo cortante V(x) [kN]
        """
        if barra_id not in self.diagramas:
            return 0.0
        return self.diagramas[barra_id].V(x)

    def N(self, barra_id: int, x: float) -> float:
        """
        Obtiene el esfuerzo axil en una posición de una barra.

        Args:
            barra_id: ID de la barra
            x: Posición desde el nudo i [m]

        Returns:
            Esfuerzo axil N(x) [kN]
        """
        if barra_id not in self.diagramas:
            return 0.0
        return self.diagramas[barra_id].N(x)

    def obtener_reaccion(self, nudo_id: int) -> tuple:
        """
        Obtiene las reacciones en un nudo.

        Args:
            nudo_id: ID del nudo

        Returns:
            Tupla (Rx, Ry, Mz)
        """
        return self.reacciones.get(nudo_id, (0.0, 0.0, 0.0))


class GeneradorSubestructuras:
    """
    Genera las subestructuras necesarias para el método de las fuerzas.

    Proceso:
    1. Crear estructura fundamental liberando redundantes
    2. Calcular esfuerzos en fundamental con cargas reales
    3. Para cada redundante Xi, calcular esfuerzos con carga unitaria

    Implementa propagación topológica (BFS desde nodos de apoyo) para
    calcular correctamente los diagramas N, V, M en pórticos planos,
    propagando fuerzas a través de nudos internos libres.
    """

    def __init__(
        self,
        nudos: List[Nudo],
        barras: List[Barra],
        cargas: List[Carga],
        redundantes: List[Redundante],
    ):
        """
        Inicializa el generador.

        Args:
            nudos: Lista de nudos del modelo
            barras: Lista de barras del modelo
            cargas: Lista de cargas aplicadas
            redundantes: Lista de redundantes seleccionados
        """
        self.nudos = nudos
        self.barras = barras
        self.cargas = cargas
        self.redundantes = redundantes

        self.fundamental: Optional[Subestructura] = None
        self.subestructuras_xi: List[Subestructura] = []

    def generar_todas(self) -> tuple:
        """
        Genera todas las subestructuras necesarias.

        Returns:
            Tupla (fundamental, lista_xi)
        """
        self.fundamental = self._generar_fundamental()
        self.subestructuras_xi = self._generar_xi()

        return self.fundamental, self.subestructuras_xi

    def _generar_fundamental(self) -> Subestructura:
        """
        Genera la estructura fundamental con cargas reales.

        Usa propagación topológica (BFS desde nodos de apoyo) para calcular
        correctamente N, V, M en todos los tramos del pórtico, incluyendo
        la transmisión de fuerzas a través de nudos internos.

        Returns:
            Subestructura fundamental con esfuerzos calculados
        """
        vinculos_modificados = self._crear_vinculos_fundamental()

        fundamental = Subestructura(
            nombre="Fundamental (M0, N0, V0)",
            es_fundamental=True,
        )

        # Resolver reacciones en la fundamental y calcular diagramas por propagación
        diagramas, reacciones = self._calcular_diagramas_propagacion(
            self.cargas, vinculos_modificados
        )
        fundamental.diagramas = diagramas
        fundamental.reacciones = reacciones

        return fundamental

    def _generar_xi(self) -> List[Subestructura]:
        """
        Genera las subestructuras Xi con cargas unitarias.

        Para cada redundante aplica una carga unitaria (CargaPuntualNudo)
        en la dirección del redundante sobre la estructura fundamental, y
        calcula los diagramas N, V, M mediante propagación topológica.

        Returns:
            Lista de subestructuras Xi
        """
        from src.domain.analysis.redundantes import TipoRedundante
        from src.domain.entities.carga import CargaPuntualNudo

        vinculos_fundamental = self._crear_vinculos_fundamental()

        subestructuras = []

        for i, redundante in enumerate(self.redundantes):
            sub = Subestructura(
                nombre=f"X{i+1} (M{i+1}-bar, N{i+1}-bar, V{i+1}-bar)",
                es_fundamental=False,
                redundante=redundante,
            )

            # Construir la carga unitaria del redundante
            nudo_carga = next(
                (n for n in self.nudos if n.id == redundante.nudo_id), None
            )
            if nudo_carga is None:
                subestructuras.append(sub)
                continue

            if redundante.tipo == TipoRedundante.REACCION_MZ:
                carga_unit = CargaPuntualNudo(nudo=nudo_carga, Fx=0.0, Fy=0.0, Mz=1.0)
            elif redundante.tipo == TipoRedundante.REACCION_RY:
                carga_unit = CargaPuntualNudo(nudo=nudo_carga, Fx=0.0, Fy=1.0, Mz=0.0)
            elif redundante.tipo == TipoRedundante.REACCION_RX:
                carga_unit = CargaPuntualNudo(nudo=nudo_carga, Fx=1.0, Fy=0.0, Mz=0.0)
            elif redundante.tipo == TipoRedundante.MOMENTO_INTERNO:
                # Momento interno unitario (articulación virtual) – usar diagrama lineal
                self._calcular_esfuerzos_momento_interno(sub, redundante)
                self._calcular_reacciones_xi(sub, redundante, vinculos_fundamental)
                subestructuras.append(sub)
                continue
            else:
                subestructuras.append(sub)
                continue

            # Calcular diagramas por propagación con carga unitaria
            diagramas, reacciones = self._calcular_diagramas_propagacion(
                [carga_unit], vinculos_fundamental
            )
            sub.diagramas = diagramas
            sub.reacciones = reacciones

            subestructuras.append(sub)

        return subestructuras

    # -----------------------------------------------------------------------
    # Propagación topológica (motor principal)
    # -----------------------------------------------------------------------

    def _calcular_diagramas_propagacion(
        self,
        cargas: List,
        vinculos_fundamental: Dict,
    ) -> Tuple[Dict[int, DiagramaEsfuerzos], Dict[int, tuple]]:
        """
        Calcula diagramas N, V, M para todas las barras mediante propagación
        topológica (BFS desde nodos de apoyo de la estructura fundamental).

        Algoritmo:
        1. Aplicar temporalmente los vínculos de la fundamental.
        2. Resolver reacciones globales con las 3 ecs. de equilibrio.
        3. BFS: empezar en nodos de apoyo con fuerzas conocidas.
        4. Para cada barra con i-end en nodo listo, calcular diagrama.
        5. Propagar fuerzas al nodo j-end mediante equilibrio de la barra.
        6. Repetir hasta cubrir todas las barras.

        Args:
            cargas: Cargas a aplicar (reales o unitarias).
            vinculos_fundamental: Vínculos modificados de la fundamental.

        Returns:
            Tupla (diagramas, reacciones_soporte).
        """
        from src.domain.mechanics.equilibrio import (
            resolver_reacciones_isostatica,
            momento_fuerza_respecto_punto,
        )
        from src.domain.mechanics.esfuerzos import calcular_esfuerzos_viga_isostatica
        from src.domain.entities.carga import (
            CargaPuntualNudo,
            CargaDistribuida,
            CargaPuntualBarra,
        )

        # --- 1. Resolver reacciones con vínculos de la fundamental --------
        vinculos_orig = {n.id: n.vinculo for n in self.nudos}
        self._aplicar_vinculos_temporales(vinculos_fundamental)

        try:
            reacciones_obj = resolver_reacciones_isostatica(
                self.nudos, self.barras, cargas
            )
            reacciones_soporte: Dict[int, tuple] = dict(reacciones_obj.reacciones)
        except ValueError:
            # Si la fundamental no puede resolverse, devolver vacío
            return {}, {}
        finally:
            for n in self.nudos:
                n.vinculo = vinculos_orig[n.id]

        # --- 2. Cargas nodales externas (CargaPuntualNudo) ----------------
        ext_loads: Dict[int, List[float]] = {}
        for carga in cargas:
            if isinstance(carga, CargaPuntualNudo) and carga.nudo is not None:
                nid = carga.nudo.id
                if nid not in ext_loads:
                    ext_loads[nid] = [0.0, 0.0, 0.0]
                ext_loads[nid][0] += carga.Fx
                ext_loads[nid][1] += carga.Fy
                ext_loads[nid][2] += carga.Mz

        # --- 3. Cargas distribuidas/puntuales sobre barras ----------------
        cargas_por_barra: Dict[int, List] = {b.id: [] for b in self.barras}
        for carga in cargas:
            if isinstance(carga, (CargaDistribuida, CargaPuntualBarra)):
                if getattr(carga, "barra", None) is not None:
                    cargas_por_barra[carga.barra.id].append(carga)

        # --- 4. Inicializar supply de nodos de apoyo ----------------------
        # node_supply[nid] = (Rx, Ry, Mz) que el nudo provee como reac_i
        # a las barras cuyo i-end está en ese nudo.
        # Para nudos de apoyo: supply = reacción_soporte + cargas_nodales_ext
        node_supply: Dict[int, tuple] = {}
        for nid, (Rx, Ry, Mz) in reacciones_soporte.items():
            ext = ext_loads.get(nid, [0.0, 0.0, 0.0])
            node_supply[nid] = (Rx + ext[0], Ry + ext[1], Mz + ext[2])

        # --- 5. BFS desde nodos con supply conocido ----------------------
        # Para nodos libres, acumular fuerzas de barras cuyo j-end llega ahí.
        # incoming_bars[nid] = lista de barra_ids con j-end en ese nudo
        incoming_bars: Dict[int, List[int]] = {n.id: [] for n in self.nudos}
        for barra in self.barras:
            incoming_bars[barra.nudo_j.id].append(barra.id)

        # Acumuladores para nodos libres
        force_accum: Dict[int, List[float]] = {n.id: [0.0, 0.0, 0.0] for n in self.nudos}
        computed_incoming: Dict[int, int] = {n.id: 0 for n in self.nudos}

        diagrams: Dict[int, DiagramaEsfuerzos] = {}
        computed_bars: set = set()

        queue: deque = deque(list(node_supply.keys()))

        max_iter = (len(self.barras) + 1) * (len(self.nudos) + 1) * 4
        iteration = 0

        while queue and len(computed_bars) < len(self.barras) and iteration < max_iter:
            iteration += 1
            nid = queue.popleft()

            if nid not in node_supply:
                continue

            for barra in self.barras:
                if barra.id in computed_bars:
                    continue
                if barra.nudo_i.id != nid:
                    continue

                # Calcular diagrama desde el i-end
                reac_i = node_supply[nid]
                cargas_b = cargas_por_barra[barra.id]
                diagrams[barra.id] = calcular_esfuerzos_viga_isostatica(
                    barra, cargas_b, reac_i, (0.0, 0.0, 0.0)
                )
                computed_bars.add(barra.id)

                # Propagar fuerzas al j-end
                reac_j = self._calcular_reac_j_global(barra, reac_i, cargas_b)
                # Fuerza que la barra ejerce sobre el nudo_j = -reac_j
                F_bar_on_j = (-reac_j[0], -reac_j[1], -reac_j[2])

                nj_id = barra.nudo_j.id
                force_accum[nj_id][0] += F_bar_on_j[0]
                force_accum[nj_id][1] += F_bar_on_j[1]
                force_accum[nj_id][2] += F_bar_on_j[2]
                computed_incoming[nj_id] += 1

                # Si todas las barras de entrada al nudo_j fueron computadas,
                # calcular su supply y agregarlo a la cola
                if nj_id not in reacciones_soporte:
                    total_in = len(incoming_bars[nj_id])
                    if computed_incoming[nj_id] >= total_in and nj_id not in node_supply:
                        ext = ext_loads.get(nj_id, [0.0, 0.0, 0.0])
                        fa = force_accum[nj_id]
                        node_supply[nj_id] = (
                            fa[0] + ext[0],
                            fa[1] + ext[1],
                            fa[2] + ext[2],
                        )
                        queue.append(nj_id)

        # --- 6. Barras no computadas: intentar desde j-end ---------------
        # (ocurre si alguna barra tiene su i-end en un nudo no alcanzado por BFS)
        for barra in self.barras:
            if barra.id in computed_bars:
                continue
            nj_id = barra.nudo_j.id
            if nj_id in node_supply:
                reac_j_node = node_supply[nj_id]
                cargas_b = cargas_por_barra[barra.id]
                reac_i = self._calcular_reac_i_desde_reac_j(
                    barra, reac_j_node, cargas_b
                )
                diagrams[barra.id] = calcular_esfuerzos_viga_isostatica(
                    barra, cargas_b, reac_i, (0.0, 0.0, 0.0)
                )
                computed_bars.add(barra.id)

        return diagrams, reacciones_soporte

    def _calcular_reac_j_global(
        self,
        barra,
        reac_i: tuple,
        cargas_barra: list,
    ) -> tuple:
        """
        Calcula (Rx_j, Ry_j, Mz_j): fuerza que el nudo_j ejerce sobre la barra
        en su extremo j, a partir del equilibrio del cuerpo libre de la barra.

        Ecuaciones usadas:
            ΣFx = 0  →  Rx_j = -Rx_i - Fx_cargas
            ΣFy = 0  →  Ry_j = -Ry_i - Fy_cargas
            ΣMz en j = 0  →  Mz_j = -Mz_i - M(Ri, sobre j) - Mz_cargas_at_j

        Args:
            barra: Barra analizada.
            reac_i: (Rx_i, Ry_i, Mz_i) fuerza del nudo_i sobre la barra.
            cargas_barra: Cargas distribuidas y puntuales sobre la barra.

        Returns:
            (Rx_j, Ry_j, Mz_j)
        """
        from src.domain.mechanics.equilibrio import momento_fuerza_respecto_punto
        from src.domain.entities.carga import CargaDistribuida, CargaPuntualBarra

        Rx_i, Ry_i, Mz_i = reac_i
        xi, yi = barra.nudo_i.x, barra.nudo_i.y
        xj, yj = barra.nudo_j.x, barra.nudo_j.y

        Fx_cargas = 0.0
        Fy_cargas = 0.0
        Mz_cargas_at_j = 0.0

        for carga in cargas_barra:
            if isinstance(carga, CargaDistribuida):
                ang_rad = math.radians(carga.angulo)
                R = carga.resultante
                Fx_c = R * math.cos(ang_rad)
                Fy_c = R * math.sin(ang_rad)
                Fx_cargas += Fx_c
                Fy_cargas += Fy_c

                x_cent_local = carga.posicion_resultante_global
                x_c_global = xi + x_cent_local * math.cos(barra.angulo)
                y_c_global = yi + x_cent_local * math.sin(barra.angulo)
                Mz_cargas_at_j += momento_fuerza_respecto_punto(
                    Fx_c, Fy_c, x_c_global, y_c_global, xj, yj
                )

            elif isinstance(carga, CargaPuntualBarra):
                ang_rad_c = math.radians(carga.angulo)
                Px = carga.P * math.cos(ang_rad_c)
                Py = carga.P * math.sin(ang_rad_c)
                Fx_cargas += Px
                Fy_cargas += Py

                x_c_global = xi + carga.a * math.cos(barra.angulo)
                y_c_global = yi + carga.a * math.sin(barra.angulo)
                Mz_cargas_at_j += momento_fuerza_respecto_punto(
                    Px, Py, x_c_global, y_c_global, xj, yj
                )

        Rx_j = -Rx_i - Fx_cargas
        Ry_j = -Ry_i - Fy_cargas

        M_Ri_at_j = 0.0
        if abs(Rx_i) > 1e-14 or abs(Ry_i) > 1e-14:
            from src.domain.mechanics.equilibrio import momento_fuerza_respecto_punto
            M_Ri_at_j = momento_fuerza_respecto_punto(Rx_i, Ry_i, xi, yi, xj, yj)

        Mz_j = -(Mz_i + M_Ri_at_j + Mz_cargas_at_j)

        return (Rx_j, Ry_j, Mz_j)

    def _calcular_reac_i_desde_reac_j(
        self,
        barra,
        reac_j: tuple,
        cargas_barra: list,
    ) -> tuple:
        """
        Calcula reac_i a partir de reac_j conocido.

        Invertido respecto a _calcular_reac_j_global: usa equilibrio global
        de la barra para obtener la fuerza en el extremo i cuando el extremo j
        es conocido. Útil para barras donde BFS alcanza primero el j-end.

        Args:
            barra: Barra analizada.
            reac_j: (Rx_j, Ry_j, Mz_j) fuerza del nudo_j sobre la barra.
            cargas_barra: Cargas sobre la barra.

        Returns:
            (Rx_i, Ry_i, Mz_i)
        """
        from src.domain.mechanics.equilibrio import momento_fuerza_respecto_punto
        from src.domain.entities.carga import CargaDistribuida, CargaPuntualBarra

        Rx_j, Ry_j, Mz_j = reac_j
        xi, yi = barra.nudo_i.x, barra.nudo_i.y
        xj, yj = barra.nudo_j.x, barra.nudo_j.y

        Fx_cargas = 0.0
        Fy_cargas = 0.0
        Mz_cargas_at_i = 0.0

        for carga in cargas_barra:
            if isinstance(carga, CargaDistribuida):
                ang_rad = math.radians(carga.angulo)
                R = carga.resultante
                Fx_c = R * math.cos(ang_rad)
                Fy_c = R * math.sin(ang_rad)
                Fx_cargas += Fx_c
                Fy_cargas += Fy_c

                x_cent_local = carga.posicion_resultante_global
                x_c_global = xi + x_cent_local * math.cos(barra.angulo)
                y_c_global = yi + x_cent_local * math.sin(barra.angulo)
                Mz_cargas_at_i += momento_fuerza_respecto_punto(
                    Fx_c, Fy_c, x_c_global, y_c_global, xi, yi
                )

            elif isinstance(carga, CargaPuntualBarra):
                ang_rad_c = math.radians(carga.angulo)
                Px = carga.P * math.cos(ang_rad_c)
                Py = carga.P * math.sin(ang_rad_c)
                Fx_cargas += Px
                Fy_cargas += Py

                x_c_global = xi + carga.a * math.cos(barra.angulo)
                y_c_global = yi + carga.a * math.sin(barra.angulo)
                Mz_cargas_at_i += momento_fuerza_respecto_punto(
                    Px, Py, x_c_global, y_c_global, xi, yi
                )

        Rx_i = -Rx_j - Fx_cargas
        Ry_i = -Ry_j - Fy_cargas

        M_Rj_at_i = momento_fuerza_respecto_punto(Rx_j, Ry_j, xj, yj, xi, yi)
        Mz_i = -(Mz_j + M_Rj_at_i + Mz_cargas_at_i)

        return (Rx_i, Ry_i, Mz_i)

    # -----------------------------------------------------------------------
    # Reacciones Xi (para superposición final)
    # -----------------------------------------------------------------------

    def _calcular_reacciones_xi(
        self,
        sub: Subestructura,
        redundante,
        vinculos_fundamental: Dict,
    ) -> None:
        """
        Calcula las reacciones de vínculo en la subestructura Xi.

        Aplica temporalmente los vínculos de la fundamental y resuelve el
        equilibrio bajo la carga unitaria del redundante.

        Args:
            sub: Subestructura Xi a completar
            redundante: Redundante cuya carga unitaria se aplica
            vinculos_fundamental: Vínculos de la estructura fundamental
        """
        from src.domain.analysis.redundantes import TipoRedundante
        from src.domain.entities.carga import CargaPuntualNudo
        from src.domain.mechanics.equilibrio import resolver_reacciones_isostatica

        nudo_carga = next((n for n in self.nudos if n.id == redundante.nudo_id), None)
        if nudo_carga is None:
            return

        if redundante.tipo == TipoRedundante.REACCION_MZ:
            carga_unitaria = CargaPuntualNudo(nudo=nudo_carga, Fx=0.0, Fy=0.0, Mz=1.0)
        elif redundante.tipo == TipoRedundante.REACCION_RY:
            carga_unitaria = CargaPuntualNudo(nudo=nudo_carga, Fx=0.0, Fy=1.0, Mz=0.0)
        elif redundante.tipo == TipoRedundante.REACCION_RX:
            carga_unitaria = CargaPuntualNudo(nudo=nudo_carga, Fx=1.0, Fy=0.0, Mz=0.0)
        else:
            return

        vinculos_originales = {n.id: n.vinculo for n in self.nudos}
        self._aplicar_vinculos_temporales(vinculos_fundamental)

        try:
            reacciones = resolver_reacciones_isostatica(
                self.nudos,
                self.barras,
                [carga_unitaria],
            )
            sub.reacciones = reacciones.reacciones
        except ValueError:
            sub.reacciones = {}
        finally:
            for nudo in self.nudos:
                nudo.vinculo = vinculos_originales[nudo.id]

    # -----------------------------------------------------------------------
    # Momento interno (articulación virtual)
    # -----------------------------------------------------------------------

    def _calcular_esfuerzos_momento_interno(
        self,
        sub: Subestructura,
        redundante,
    ) -> None:
        """
        Calcula esfuerzos por momento interno unitario (articulación virtual).

        Cuando se introduce una articulación virtual en una barra,
        se aplican momentos unitarios ±1 a cada lado.
        """
        from src.domain.mechanics.esfuerzos import crear_diagrama_lineal

        barra_id = redundante.barra_id
        posicion = redundante.posicion

        for barra in self.barras:
            if barra.id == barra_id:
                if posicion < 1e-10:
                    diagrama = crear_diagrama_lineal(barra.id, barra.L, 1.0, 0.0, "M")
                elif abs(posicion - barra.L) < 1e-10:
                    diagrama = crear_diagrama_lineal(barra.id, barra.L, 0.0, 1.0, "M")
                else:
                    diagrama = crear_diagrama_lineal(barra.id, barra.L, 0, 0, "M")
            else:
                diagrama = crear_diagrama_lineal(barra.id, barra.L, 0, 0, "M")

            sub.diagramas[barra.id] = diagrama

    # -----------------------------------------------------------------------
    # Gestión de vínculos de la fundamental
    # -----------------------------------------------------------------------

    def _crear_vinculos_fundamental(self) -> Dict[int, str]:
        """
        Determina los vínculos en la estructura fundamental.

        Returns:
            Diccionario {nudo_id: lista_gdl_restringidos_en_fundamental}
        """
        from src.domain.analysis.redundantes import TipoRedundante

        vinculos = {}

        for nudo in self.nudos:
            if not nudo.tiene_vinculo:
                continue

            gdl_originales = set(nudo.vinculo.gdl_restringidos())

            for red in self.redundantes:
                if red.nudo_id != nudo.id:
                    continue

                if red.tipo == TipoRedundante.REACCION_RX:
                    gdl_originales.discard("Ux")
                elif red.tipo == TipoRedundante.REACCION_RY:
                    gdl_originales.discard("Uy")
                elif red.tipo == TipoRedundante.REACCION_MZ:
                    gdl_originales.discard("θz")

            vinculos[nudo.id] = list(gdl_originales)

        return vinculos

    def _aplicar_vinculos_temporales(self, vinculos_modificados: Dict) -> None:
        """
        Aplica vínculos modificados temporalmente a los nudos.

        Args:
            vinculos_modificados: Diccionario {nudo_id: lista_gdl_restringidos}
        """
        from src.domain.entities.vinculo import Empotramiento, ApoyoFijo, Rodillo

        for nudo in self.nudos:
            if nudo.id not in vinculos_modificados:
                nudo.vinculo = None
                continue

            gdl_restringidos = vinculos_modificados[nudo.id]

            if not gdl_restringidos:
                nudo.vinculo = None
            elif set(gdl_restringidos) == {"Ux", "Uy", "θz"}:
                nudo.vinculo = Empotramiento(nudo.id)
            elif set(gdl_restringidos) == {"Ux", "Uy"}:
                nudo.vinculo = ApoyoFijo(nudo.id)
            elif "Uy" in gdl_restringidos and len(gdl_restringidos) == 1:
                nudo.vinculo = Rodillo(nudo.id, direccion="Uy")
            elif "Ux" in gdl_restringidos and len(gdl_restringidos) == 1:
                nudo.vinculo = Rodillo(nudo.id, direccion="Ux")
            elif "θz" in gdl_restringidos and len(gdl_restringidos) == 1:
                nudo.vinculo = None
            else:
                nudo.vinculo = None

    def _resolver_aproximado(self) -> Dict[int, tuple]:
        """
        Llamado cuando el solver isostático falla.

        Raises:
            ValueError: Siempre, con diagnóstico del fallo.
        """
        nudos_con_vinculo = [n for n in self.nudos if n.tiene_vinculo]
        n_vinculos = sum(
            len(n.vinculo.gdl_restringidos()) for n in nudos_con_vinculo
        )
        n_nudos = len(self.nudos)

        raise ValueError(
            f"No se pudo resolver la subestructura generada.\n"
            f"  - Nudos con vínculo: {len(nudos_con_vinculo)}\n"
            f"  - GDL restringidos totales: {n_vinculos}\n"
            f"  - Nudos totales: {n_nudos}\n"
            f"Causa probable: la subestructura no es isostática o tiene "
            f"inestabilidad geométrica. Verifique la selección de redundantes."
        )
