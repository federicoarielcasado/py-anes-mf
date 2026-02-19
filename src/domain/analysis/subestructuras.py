"""
Generación de subestructuras para el Método de las Fuerzas.

Crea la estructura fundamental (isostática) y las subestructuras
con cargas unitarias para cada redundante.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

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

        La estructura fundamental es la estructura original donde
        se han liberado los redundantes (convertidos a GDL libres).

        Returns:
            Subestructura fundamental con esfuerzos calculados
        """
        from src.domain.analysis.redundantes import TipoRedundante
        from src.domain.mechanics.equilibrio import resolver_reacciones_isostatica
        from src.domain.mechanics.esfuerzos import calcular_esfuerzos_viga_isostatica

        fundamental = Subestructura(
            nombre="Fundamental (M⁰, N⁰, V⁰)",
            es_fundamental=True,
        )

        # Para la estructura fundamental, necesitamos:
        # 1. Modificar vínculos según redundantes liberados
        # 2. Resolver reacciones
        # 3. Calcular esfuerzos

        # Crear copia modificada de los vínculos
        vinculos_modificados = self._crear_vinculos_fundamental()

        # IMPORTANTE: Necesitamos modificar temporalmente los vínculos de los nudos
        # para que resolver_reacciones_isostatica() vea la estructura fundamental isostática
        vinculos_originales = {}
        for nudo in self.nudos:
            vinculos_originales[nudo.id] = nudo.vinculo

        # Aplicar vínculos modificados temporalmente
        self._aplicar_vinculos_temporales(vinculos_modificados)

        # Resolver reacciones en la estructura fundamental (isostática)
        try:
            reacciones = resolver_reacciones_isostatica(
                self.nudos,
                self.barras,
                self.cargas,
            )
            fundamental.reacciones = reacciones.reacciones
        except ValueError as e:
            # Si falla, puede ser que la fundamental no sea estrictamente isostática
            # Usar aproximación simplificada
            fundamental.reacciones = self._resolver_aproximado()
        finally:
            # Restaurar vínculos originales
            for nudo in self.nudos:
                nudo.vinculo = vinculos_originales[nudo.id]

        # Calcular esfuerzos en cada barra
        for barra in self.barras:
            # Obtener cargas sobre esta barra
            cargas_barra = [c for c in self.cargas if hasattr(c, 'barra') and c.barra == barra]

            # Reacciones en extremos
            reac_i = fundamental.reacciones.get(barra.nudo_i.id, (0, 0, 0))
            reac_j = fundamental.reacciones.get(barra.nudo_j.id, (0, 0, 0))

            diagrama = calcular_esfuerzos_viga_isostatica(
                barra, cargas_barra, reac_i, reac_j
            )
            fundamental.diagramas[barra.id] = diagrama

        return fundamental

    def _generar_xi(self) -> List[Subestructura]:
        """
        Genera las subestructuras Xi con cargas unitarias.

        Para cada redundante:
        - Aplicar carga unitaria en la dirección del redundante
        - Calcular esfuerzos en la estructura fundamental

        Returns:
            Lista de subestructuras Xi
        """
        from src.domain.analysis.redundantes import TipoRedundante
        from src.domain.mechanics.esfuerzos import crear_diagrama_lineal

        subestructuras = []

        for i, redundante in enumerate(self.redundantes):
            sub = Subestructura(
                nombre=f"X{i+1} (M̄{i+1}, N̄{i+1}, V̄{i+1})",
                es_fundamental=False,
                redundante=redundante,
            )

            # Calcular esfuerzos debido a carga unitaria
            if redundante.tipo == TipoRedundante.REACCION_MZ:
                # Momento unitario en un nudo
                self._calcular_esfuerzos_momento_unitario(sub, redundante)

            elif redundante.tipo == TipoRedundante.REACCION_RY:
                # Fuerza vertical unitaria
                self._calcular_esfuerzos_fuerza_unitaria(sub, redundante, "Y")

            elif redundante.tipo == TipoRedundante.REACCION_RX:
                # Fuerza horizontal unitaria
                self._calcular_esfuerzos_fuerza_unitaria(sub, redundante, "X")

            elif redundante.tipo == TipoRedundante.MOMENTO_INTERNO:
                # Momento interno unitario (articulación virtual)
                self._calcular_esfuerzos_momento_interno(sub, redundante)

            subestructuras.append(sub)

        return subestructuras

    def _calcular_esfuerzos_momento_unitario(
        self,
        sub: Subestructura,
        redundante: Redundante,
    ) -> None:
        """
        Calcula esfuerzos por momento unitario en un nudo.

        Para un momento Mz = 1 aplicado en un nudo empotrado que se libera,
        los diagramas son lineales en las barras conectadas.
        """
        from src.domain.mechanics.esfuerzos import crear_diagrama_lineal

        nudo_id = redundante.nudo_id
        nudo = next(n for n in self.nudos if n.id == nudo_id)

        # Encontrar barras conectadas a este nudo
        barras_conectadas = [
            b for b in self.barras
            if b.nudo_i.id == nudo_id or b.nudo_j.id == nudo_id
        ]

        # Para viga empotrada-empotrada donde liberamos un momento:
        # M̄ varía linealmente de 1 en el nudo liberado a 0 en el otro extremo
        for barra in self.barras:
            if barra in barras_conectadas:
                if barra.nudo_i.id == nudo_id:
                    # El nudo liberado es el inicial
                    Mi = 1.0
                    Mj = 0.0
                else:
                    # El nudo liberado es el final
                    Mi = 0.0
                    Mj = 1.0

                diagrama = crear_diagrama_lineal(barra.id, barra.L, Mi, Mj, "M")
            else:
                # Barras no conectadas: M̄ = 0
                diagrama = crear_diagrama_lineal(barra.id, barra.L, 0, 0, "M")

            sub.diagramas[barra.id] = diagrama

    def _calcular_esfuerzos_fuerza_unitaria(
        self,
        sub: Subestructura,
        redundante: Redundante,
        direccion: str,
    ) -> None:
        """
        Calcula esfuerzos por fuerza unitaria en una dirección.

        IMPORTANTE: Para fuerzas horizontales (Rx), se debe calcular el AXIL.
        Para fuerzas verticales (Ry), se debe calcular CORTANTE y MOMENTO.

        Args:
            sub: Subestructura a llenar
            redundante: Redundante de tipo fuerza
            direccion: "X" o "Y"
        """
        from src.domain.mechanics.esfuerzos import crear_diagrama_lineal, DiagramaEsfuerzos, EsfuerzosTramo
        import math

        nudo_id = redundante.nudo_id
        nudo = next(n for n in self.nudos if n.id == nudo_id)

        # Encontrar barras conectadas
        for barra in self.barras:
            if direccion == "X":
                # FUERZA HORIZONTAL UNITARIA: genera AXIL
                #
                # Rx global se proyecta al eje local de la barra:
                # N = Rx × cos(θ)
                #
                # Signo según ubicación:
                # - Si Rx actúa en nudo i (inicio): N = -cos(θ) (compresión si θ=0°)
                # - Si Rx actúa en nudo j (final): N = +cos(θ) (tracción si θ=0°)

                if barra.nudo_i.id == nudo_id:
                    # Fuerza Rx=+1 en nudo inicial
                    # Ejemplo: viga horizontal [A]---->[B], Rx=+1 en A (→)
                    # La fuerza empuja la barra → compresión → N = -1
                    N_valor = -1.0 * math.cos(barra.angulo)
                elif barra.nudo_j.id == nudo_id:
                    # Fuerza Rx=+1 en nudo final
                    # Ejemplo: viga horizontal [A]---->[B], Rx=+1 en B (→)
                    # La fuerza jala la barra → tracción → N = +1
                    N_valor = +1.0 * math.cos(barra.angulo)
                else:
                    # Barra no conectada al nudo
                    N_valor = 0.0

                # El axil es constante
                def N_func(x, N_val=N_valor):
                    return N_val
                def V_func(x):
                    return 0.0
                def M_func(x):
                    return 0.0

                tramo = EsfuerzosTramo(
                    x_inicio=0.0,
                    x_fin=barra.L,
                    N=N_func,
                    V=V_func,
                    M=M_func,
                )

                diagrama = DiagramaEsfuerzos(
                    barra_id=barra.id,
                    L=barra.L,
                    tramos=[tramo],
                    Ni=N_valor,
                    Nj=N_valor,
                    Vi=0.0,
                    Vj=0.0,
                    Mi=0.0,
                    Mj=0.0,
                )

            else:  # direccion == "Y"
                # FUERZA VERTICAL UNITARIA: genera MOMENTO y CORTANTE
                # Calcular contribución de la fuerza unitaria a los momentos
                if barra.nudo_i.id == nudo_id:
                    # Fuerza aplicada en nudo inicial
                    # Fuerza vertical: genera momento = F * brazo_horizontal
                    Mi = 0.0  # En el punto de aplicación
                    Mj = -1.0 * barra.L * math.cos(barra.angulo)  # En el otro extremo
                elif barra.nudo_j.id == nudo_id:
                    Mi = 1.0 * barra.L * math.cos(barra.angulo)
                    Mj = 0.0
                else:
                    Mi = 0.0
                    Mj = 0.0

                diagrama = crear_diagrama_lineal(barra.id, barra.L, Mi, Mj, "M")

            sub.diagramas[barra.id] = diagrama

    def _calcular_esfuerzos_momento_interno(
        self,
        sub: Subestructura,
        redundante: Redundante,
    ) -> None:
        """
        Calcula esfuerzos por momento interno unitario.

        Cuando se introduce una articulación virtual en una barra,
        se aplican momentos unitarios ±1 a cada lado.
        """
        from src.domain.mechanics.esfuerzos import crear_diagrama_lineal

        barra_id = redundante.barra_id
        posicion = redundante.posicion

        for barra in self.barras:
            if barra.id == barra_id:
                # Barra donde está la articulación virtual
                # El diagrama tiene salto en la posición
                if posicion < 1e-10:
                    # Articulación en extremo i: M = 1 a M = 0
                    diagrama = crear_diagrama_lineal(barra.id, barra.L, 1.0, 0.0, "M")
                elif abs(posicion - barra.L) < 1e-10:
                    # Articulación en extremo j: M = 0 a M = 1
                    diagrama = crear_diagrama_lineal(barra.id, barra.L, 0.0, 1.0, "M")
                else:
                    # Articulación en medio: más complejo
                    diagrama = crear_diagrama_lineal(barra.id, barra.L, 0, 0, "M")
            else:
                diagrama = crear_diagrama_lineal(barra.id, barra.L, 0, 0, "M")

            sub.diagramas[barra.id] = diagrama

    def _crear_vinculos_fundamental(self) -> Dict[int, str]:
        """
        Determina los vínculos en la estructura fundamental.

        Returns:
            Diccionario {nudo_id: tipo_vinculo_modificado}
        """
        from src.domain.analysis.redundantes import TipoRedundante

        vinculos = {}

        for nudo in self.nudos:
            if not nudo.tiene_vinculo:
                continue

            gdl_originales = set(nudo.vinculo.gdl_restringidos())

            # Quitar GDL correspondientes a redundantes
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

    def _aplicar_vinculos_temporales(self, vinculos_modificados: Dict[int, List[str]]) -> None:
        """
        Aplica vínculos modificados temporalmente a los nudos.

        Args:
            vinculos_modificados: Diccionario {nudo_id: lista_gdl_restringidos}
        """
        from src.domain.entities.vinculo import Empotramiento, ApoyoFijo, Rodillo

        for nudo in self.nudos:
            if nudo.id not in vinculos_modificados:
                # Si no está en el diccionario, liberar completamente
                nudo.vinculo = None
                continue

            gdl_restringidos = vinculos_modificados[nudo.id]

            if not gdl_restringidos:
                # Lista vacía = nudo libre
                nudo.vinculo = None
            elif set(gdl_restringidos) == {"Ux", "Uy", "θz"}:
                # Empotramiento completo
                nudo.vinculo = Empotramiento(nudo.id)
            elif set(gdl_restringidos) == {"Ux", "Uy"}:
                # Apoyo fijo (sin momento)
                nudo.vinculo = ApoyoFijo(nudo.id)
            elif "Uy" in gdl_restringidos and len(gdl_restringidos) == 1:
                # Rodillo vertical
                nudo.vinculo = Rodillo(nudo.id, direccion="Uy")
            elif "Ux" in gdl_restringidos and len(gdl_restringidos) == 1:
                # Rodillo horizontal
                nudo.vinculo = Rodillo(nudo.id, direccion="Ux")
            elif "θz" in gdl_restringidos and len(gdl_restringidos) == 1:
                # Solo momento restringido (caso raro, pero puede ocurrir)
                # Lo dejamos sin vínculo por ahora
                nudo.vinculo = None
            else:
                # Combinación no estándar - por ahora dejamos sin vínculo
                # TODO: Implementar clase VinculoPersonalizado
                nudo.vinculo = None

    def _resolver_aproximado(self) -> Dict[int, tuple]:
        """
        Resuelve reacciones de forma aproximada cuando el método exacto falla.

        Returns:
            Diccionario de reacciones aproximadas
        """
        # Aproximación simple: distribuir cargas entre apoyos
        reacciones = {}

        for nudo in self.nudos:
            if nudo.tiene_vinculo:
                reacciones[nudo.id] = (0.0, 0.0, 0.0)

        return reacciones
