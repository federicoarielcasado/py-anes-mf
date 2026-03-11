"""
Numeración de Grados de Libertad (GDL) para el Método de las Deformaciones.

Asigna índices globales a cada GDL (Ux, Uy, theta_z) de cada nudo
del modelo estructural, distinguiendo entre GDL libres y restringidos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Set, Tuple

if TYPE_CHECKING:
    from src.domain.model.modelo_estructural import ModeloEstructural

# Mapeo de nombre de GDL (string) a offset dentro del nudo
_NOMBRE_A_OFFSET: Dict[str, int] = {
    "Ux": 0,
    "Uy": 1,
    "theta_z": 2,
    "\u03b8z": 2,   # θz (Unicode)
    "Rz": 2,        # alias alternativo
}


@dataclass
class NumeradorGDL:
    """
    Asigna índices globales únicos a cada GDL del modelo.

    Numeración: para el nudo con índice i (ordenado por nudo.id),
    sus GDL globales son:
        GDL_Ux    = 3*i
        GDL_Uy    = 3*i + 1
        GDL_theta = 3*i + 2

    Attributes:
        modelo: Modelo estructural a numerar

    Example:
        >>> numerador = NumeradorGDL(modelo)
        >>> gdl_map = numerador.numerar()
        >>> gdl_nudo_1 = gdl_map[1]  # (0, 1, 2) para nudo id=1
    """

    modelo: "ModeloEstructural"

    # Resultados computados (se calculan en numerar())
    _gdl_map: Dict[int, Tuple[int, int, int]] = field(
        default_factory=dict, repr=False
    )
    _indices_libres: List[int] = field(default_factory=list, repr=False)
    _indices_restringidos: List[int] = field(default_factory=list, repr=False)
    _calculado: bool = field(default=False, repr=False)

    def numerar(self) -> Dict[int, Tuple[int, int, int]]:
        """
        Calcula y retorna el mapeo de nudo_id a índices GDL globales.

        Returns:
            Diccionario {nudo_id: (gdl_ux, gdl_uy, gdl_theta)}
        """
        self._gdl_map = {}
        gdl_restringidos: Set[int] = set()

        # Ordenar nudos por id para numeración determinista
        nudos_ordenados = sorted(self.modelo.nudos, key=lambda n: n.id)

        for i, nudo in enumerate(nudos_ordenados):
            gdl_ux = 3 * i
            gdl_uy = 3 * i + 1
            gdl_theta = 3 * i + 2
            self._gdl_map[nudo.id] = (gdl_ux, gdl_uy, gdl_theta)

            # Identificar GDL restringidos por el vínculo
            if nudo.vinculo is not None:
                for nombre_gdl in nudo.vinculo.gdl_restringidos():
                    offset = _NOMBRE_A_OFFSET.get(nombre_gdl)
                    if offset is not None:
                        gdl_restringidos.add(3 * i + offset)

        # Separar libres y restringidos
        n_total = 3 * len(nudos_ordenados)
        self._indices_restringidos = sorted(gdl_restringidos)
        self._indices_libres = [
            g for g in range(n_total) if g not in gdl_restringidos
        ]
        self._calculado = True
        return self._gdl_map

    @property
    def gdl_map(self) -> Dict[int, Tuple[int, int, int]]:
        """Mapeo {nudo_id: (gdl_ux, gdl_uy, gdl_theta)}. Calcula si es necesario."""
        if not self._calculado:
            self.numerar()
        return self._gdl_map

    @property
    def indices_libres(self) -> List[int]:
        """Índices GDL globales sin restricción (incógnitas del sistema)."""
        if not self._calculado:
            self.numerar()
        return self._indices_libres

    @property
    def indices_restringidos(self) -> List[int]:
        """Índices GDL globales restringidos por vínculos."""
        if not self._calculado:
            self.numerar()
        return self._indices_restringidos

    @property
    def n_total(self) -> int:
        """Número total de GDL = 3 × número de nudos."""
        return 3 * len(self.modelo.nudos)

    @property
    def n_libres(self) -> int:
        """Número de GDL libres (incógnitas del sistema)."""
        if not self._calculado:
            self.numerar()
        return len(self._indices_libres)

    @property
    def n_restringidos(self) -> int:
        """Número de GDL restringidos."""
        if not self._calculado:
            self.numerar()
        return len(self._indices_restringidos)

    def gdl_de_nudo(self, nudo_id: int) -> Tuple[int, int, int]:
        """
        Retorna los índices GDL de un nudo específico.

        Args:
            nudo_id: ID del nudo

        Returns:
            Tupla (gdl_ux, gdl_uy, gdl_theta)

        Raises:
            KeyError: Si el nudo_id no existe en el modelo
        """
        if not self._calculado:
            self.numerar()
        if nudo_id not in self._gdl_map:
            raise KeyError(f"Nudo con id={nudo_id} no encontrado en el modelo")
        return self._gdl_map[nudo_id]

    def gdl_de_barra(self, barra_id: int) -> Tuple[List[int], List[int]]:
        """
        Retorna los índices GDL de los nudos extremos de una barra.

        Args:
            barra_id: ID de la barra

        Returns:
            Tupla (gdl_i, gdl_j) donde cada elemento es [ux, uy, theta]
        """
        if not self._calculado:
            self.numerar()

        barra = self.modelo.obtener_barra(barra_id)
        gdl_i = list(self._gdl_map[barra.nudo_i.id])
        gdl_j = list(self._gdl_map[barra.nudo_j.id])
        return gdl_i, gdl_j

    def indices_elemento(self, barra_id: int) -> List[int]:
        """
        Retorna los 6 índices GDL globales para una barra (nudo_i + nudo_j).

        Args:
            barra_id: ID de la barra

        Returns:
            Lista de 6 índices: [ux_i, uy_i, theta_i, ux_j, uy_j, theta_j]
        """
        gdl_i, gdl_j = self.gdl_de_barra(barra_id)
        return gdl_i + gdl_j

    def es_libre(self, gdl: int) -> bool:
        """Retorna True si el GDL de índice `gdl` es libre (no restringido)."""
        if not self._calculado:
            self.numerar()
        return gdl in self._indices_libres
