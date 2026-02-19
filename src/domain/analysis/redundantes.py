"""
Selección de redundantes para el Método de las Fuerzas.

Define los tipos de redundantes y proporciona algoritmos para
seleccionar automáticamente los redundantes óptimos.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from src.domain.model.modelo_estructural import ModeloEstructural
    from src.domain.entities.nudo import Nudo
    from src.domain.entities.barra import Barra


class TipoRedundante(Enum):
    """
    Tipos de redundantes que se pueden elegir.

    Los redundantes pueden ser:
    - Reacciones de vínculo externo (Rx, Ry, Mz)
    - Esfuerzos internos en barras (N, V, M en un punto)
    """
    # Reacciones de vínculo
    REACCION_RX = auto()      # Reacción horizontal
    REACCION_RY = auto()      # Reacción vertical
    REACCION_MZ = auto()      # Momento de reacción

    # Esfuerzos internos (en articulaciones virtuales)
    MOMENTO_INTERNO = auto()   # Momento en sección de barra
    CORTANTE_INTERNO = auto()  # Cortante en sección (menos común)
    AXIL_INTERNO = auto()      # Axil en sección (para armaduras)


@dataclass
class Redundante:
    """
    Representa un redundante seleccionado.

    Attributes:
        tipo: Tipo de redundante
        nudo_id: ID del nudo donde se aplica (para reacciones)
        barra_id: ID de la barra (para esfuerzos internos)
        posicion: Posición en la barra donde se libera el esfuerzo [m]
        descripcion: Descripción legible del redundante
        indice: Índice en el sistema de ecuaciones (X1, X2, etc.)
    """
    tipo: TipoRedundante
    nudo_id: Optional[int] = None
    barra_id: Optional[int] = None
    posicion: float = 0.0
    descripcion: str = ""
    indice: int = 0

    def __post_init__(self):
        """Genera descripción automática si no se proporciona."""
        if not self.descripcion:
            self.descripcion = self._generar_descripcion()

    def _generar_descripcion(self) -> str:
        """Genera una descripción legible del redundante."""
        if self.tipo == TipoRedundante.REACCION_RX:
            return f"Rx en nudo {self.nudo_id}"
        elif self.tipo == TipoRedundante.REACCION_RY:
            return f"Ry en nudo {self.nudo_id}"
        elif self.tipo == TipoRedundante.REACCION_MZ:
            return f"Mz en nudo {self.nudo_id}"
        elif self.tipo == TipoRedundante.MOMENTO_INTERNO:
            return f"M interno en barra {self.barra_id} (x={self.posicion:.2f}m)"
        elif self.tipo == TipoRedundante.CORTANTE_INTERNO:
            return f"V interno en barra {self.barra_id} (x={self.posicion:.2f}m)"
        elif self.tipo == TipoRedundante.AXIL_INTERNO:
            return f"N interno en barra {self.barra_id}"
        return f"Redundante {self.indice}"

    @property
    def nombre_corto(self) -> str:
        """Nombre corto para usar en matrices y vectores."""
        return f"X{self.indice}"


class SelectorRedundantes:
    """
    Selecciona automáticamente los redundantes para el método de las fuerzas.

    Implementa diferentes estrategias de selección:
    1. Priorizar momentos de reacción (empotramientos)
    2. Priorizar reacciones verticales
    3. Evitar crear subestructuras inestables
    4. Optimizar para matrices bien condicionadas

    Attributes:
        modelo: Modelo estructural a analizar
    """

    def __init__(self, modelo: ModeloEstructural):
        """
        Inicializa el selector.

        Args:
            modelo: Modelo estructural
        """
        self.modelo = modelo
        self._candidatos: List[Redundante] = []
        self._seleccionados: List[Redundante] = []

    def seleccionar_automatico(self) -> List[Redundante]:
        """
        Selecciona automáticamente los redundantes.

        Utiliza una heurística que prioriza:
        1. Momentos de reacción (Mz) en empotramientos
        2. Reacciones verticales (Ry) en apoyos simples
        3. Reacciones horizontales (Rx)

        Returns:
            Lista de redundantes seleccionados

        Raises:
            ValueError: Si la estructura es hipostática
        """
        gh = self.modelo.grado_hiperestaticidad

        if gh <= 0:
            if gh < 0:
                raise ValueError(
                    f"Estructura hipostática (GH={gh}). "
                    "No se pueden seleccionar redundantes."
                )
            return []  # Isostática, no hay redundantes

        # Identificar todos los candidatos posibles
        self._identificar_candidatos()

        # Aplicar heurística de selección
        self._seleccionados = self._aplicar_heuristica(gh)

        # Asignar índices
        for i, red in enumerate(self._seleccionados):
            red.indice = i + 1

        return self._seleccionados

    def seleccionar_manual(self, redundantes: List[Redundante]) -> List[Redundante]:
        """
        Acepta una selección manual de redundantes.

        Args:
            redundantes: Lista de redundantes elegidos por el usuario

        Returns:
            Lista de redundantes con índices asignados

        Raises:
            ValueError: Si el número de redundantes no coincide con GH
        """
        gh = self.modelo.grado_hiperestaticidad

        if len(redundantes) != gh:
            raise ValueError(
                f"Se requieren {gh} redundantes, se proporcionaron {len(redundantes)}"
            )

        # Validar que los redundantes son válidos
        for red in redundantes:
            self._validar_redundante(red)

        # Asignar índices
        self._seleccionados = list(redundantes)
        for i, red in enumerate(self._seleccionados):
            red.indice = i + 1

        return self._seleccionados

    def _identificar_candidatos(self) -> None:
        """Identifica todos los posibles redundantes."""
        self._candidatos = []

        # Candidatos de reacciones de vínculo
        for nudo in self.modelo.nudos:
            if not nudo.tiene_vinculo:
                continue

            gdl_restringidos = nudo.vinculo.gdl_restringidos()

            if "Ux" in gdl_restringidos:
                self._candidatos.append(Redundante(
                    tipo=TipoRedundante.REACCION_RX,
                    nudo_id=nudo.id,
                ))

            if "Uy" in gdl_restringidos:
                self._candidatos.append(Redundante(
                    tipo=TipoRedundante.REACCION_RY,
                    nudo_id=nudo.id,
                ))

            if "θz" in gdl_restringidos:
                self._candidatos.append(Redundante(
                    tipo=TipoRedundante.REACCION_MZ,
                    nudo_id=nudo.id,
                ))

        # Candidatos de momentos internos (en nudos de conexión de barras)
        for nudo in self.modelo.nudos:
            barras_conectadas = self.modelo.barras_conectadas_a_nudo(nudo.id)
            if len(barras_conectadas) >= 2 and not nudo.tiene_vinculo:
                # Nudo interno con múltiples barras: candidato para articulación virtual
                for barra in barras_conectadas:
                    if barra.nudo_i.id == nudo.id:
                        pos = 0.0
                    else:
                        pos = barra.L

                    self._candidatos.append(Redundante(
                        tipo=TipoRedundante.MOMENTO_INTERNO,
                        barra_id=barra.id,
                        nudo_id=nudo.id,
                        posicion=pos,
                    ))

    def _aplicar_heuristica(self, n_redundantes: int) -> List[Redundante]:
        """
        Aplica heurística para seleccionar los mejores redundantes.

        Orden de prioridad:
        1. Momentos de reacción (Mz) - suelen dar mejor condicionamiento
        2. Reacciones verticales (Ry) - fáciles de interpretar
        3. Reacciones horizontales (Rx)
        4. Momentos internos

        Args:
            n_redundantes: Número de redundantes a seleccionar

        Returns:
            Lista de redundantes seleccionados
        """
        # Ordenar candidatos por prioridad
        def prioridad(red: Redundante) -> int:
            if red.tipo == TipoRedundante.REACCION_MZ:
                return 0  # Máxima prioridad
            elif red.tipo == TipoRedundante.REACCION_RY:
                return 1
            elif red.tipo == TipoRedundante.REACCION_RX:
                return 2
            elif red.tipo == TipoRedundante.MOMENTO_INTERNO:
                return 3
            else:
                return 4

        candidatos_ordenados = sorted(self._candidatos, key=prioridad)

        # Seleccionar los primeros n_redundantes, verificando estabilidad
        seleccionados = []
        usados: Set[Tuple[int, TipoRedundante]] = set()

        for candidato in candidatos_ordenados:
            if len(seleccionados) >= n_redundantes:
                break

            # Evitar redundantes duplicados
            clave = (candidato.nudo_id, candidato.tipo)
            if clave in usados:
                continue

            # Verificar que la selección no crea inestabilidad
            if self._crea_inestabilidad(seleccionados + [candidato]):
                continue

            seleccionados.append(candidato)
            usados.add(clave)

        if len(seleccionados) < n_redundantes:
            raise ValueError(
                f"No se pudieron seleccionar {n_redundantes} redundantes válidos. "
                f"Solo se encontraron {len(seleccionados)} candidatos viables."
            )

        return seleccionados

    def _crea_inestabilidad(self, redundantes: List[Redundante]) -> bool:
        """
        Verifica si la selección de redundantes crea una subestructura inestable.

        Una selección es inestable si al liberar los redundantes, la estructura
        fundamental resultante es un mecanismo.

        Args:
            redundantes: Lista de redundantes a verificar

        Returns:
            True si la selección crea inestabilidad
        """
        # Contar reacciones que quedarían
        reacciones_totales = self.modelo.num_reacciones
        reacciones_liberadas = sum(
            1 for r in redundantes
            if r.tipo in (
                TipoRedundante.REACCION_RX,
                TipoRedundante.REACCION_RY,
                TipoRedundante.REACCION_MZ,
            )
        )
        reacciones_restantes = reacciones_totales - reacciones_liberadas

        # Para estructura isostática necesitamos al menos 3 reacciones
        if reacciones_restantes < 3:
            return True

        # Verificar que no se liberan todas las reacciones de un nudo
        for nudo in self.modelo.nudos:
            if not nudo.tiene_vinculo:
                continue

            gdl = nudo.vinculo.gdl_restringidos()
            gdl_liberados = sum(
                1 for r in redundantes
                if r.nudo_id == nudo.id and r.tipo in (
                    TipoRedundante.REACCION_RX,
                    TipoRedundante.REACCION_RY,
                    TipoRedundante.REACCION_MZ,
                )
            )

            # Si se liberan todos los GDL de un nudo, es inestable
            if gdl_liberados >= len(gdl):
                return True

        return False

    def _validar_redundante(self, red: Redundante) -> None:
        """
        Valida que un redundante sea válido para el modelo.

        Args:
            red: Redundante a validar

        Raises:
            ValueError: Si el redundante no es válido
        """
        if red.tipo in (
            TipoRedundante.REACCION_RX,
            TipoRedundante.REACCION_RY,
            TipoRedundante.REACCION_MZ,
        ):
            # Verificar que el nudo existe y tiene el vínculo apropiado
            nudo = self.modelo.obtener_nudo(red.nudo_id)
            if nudo is None:
                raise ValueError(f"Nudo {red.nudo_id} no existe")
            if not nudo.tiene_vinculo:
                raise ValueError(f"Nudo {red.nudo_id} no tiene vínculo")

            gdl = nudo.vinculo.gdl_restringidos()
            if red.tipo == TipoRedundante.REACCION_RX and "Ux" not in gdl:
                raise ValueError(f"Nudo {red.nudo_id} no restringe Ux")
            if red.tipo == TipoRedundante.REACCION_RY and "Uy" not in gdl:
                raise ValueError(f"Nudo {red.nudo_id} no restringe Uy")
            if red.tipo == TipoRedundante.REACCION_MZ and "θz" not in gdl:
                raise ValueError(f"Nudo {red.nudo_id} no restringe θz")

        elif red.tipo == TipoRedundante.MOMENTO_INTERNO:
            # Verificar que la barra existe
            barra = self.modelo.obtener_barra(red.barra_id)
            if barra is None:
                raise ValueError(f"Barra {red.barra_id} no existe")

    @property
    def candidatos(self) -> List[Redundante]:
        """Lista de todos los candidatos identificados."""
        return self._candidatos

    @property
    def seleccionados(self) -> List[Redundante]:
        """Lista de redundantes seleccionados."""
        return self._seleccionados
