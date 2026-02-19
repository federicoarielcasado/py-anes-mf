"""
Clase Nudo para representar puntos nodales en la estructura.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .vinculo import Vinculo


@dataclass
class Nudo:
    """
    Representa un nudo (punto nodal) en un pórtico plano 2D.

    Un nudo es un punto donde confluyen barras y/o se aplican vínculos
    externos o cargas concentradas. Cada nudo tiene 3 grados de libertad
    en análisis de pórticos planos: Ux, Uy, θz.

    Attributes:
        id: Identificador único del nudo (entero positivo)
        x: Coordenada X en el sistema global [m]
        y: Coordenada Y en el sistema global [m]
        nombre: Nombre descriptivo opcional
        vinculo: Vínculo externo asociado al nudo (si existe)

    Resultados post-análisis:
        Ux: Desplazamiento horizontal calculado [m]
        Uy: Desplazamiento vertical calculado [m]
        theta_z: Rotación calculada [rad]

    Example:
        >>> nudo_a = Nudo(id=1, x=0.0, y=0.0, nombre="Apoyo A")
        >>> nudo_b = Nudo(id=2, x=6.0, y=0.0, nombre="Apoyo B")
        >>> nudo_a.distancia_a(nudo_b)
        6.0
    """

    id: int
    x: float
    y: float
    nombre: str = ""

    # Vínculo externo (se asigna después de crear el nudo)
    vinculo: Optional[Vinculo] = field(default=None, repr=False)

    # Resultados del análisis (se calculan post-análisis)
    Ux: float = field(default=0.0, repr=False)
    Uy: float = field(default=0.0, repr=False)
    theta_z: float = field(default=0.0, repr=False)

    # Campos internos
    _barras_conectadas: list = field(default_factory=list, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Valida los parámetros del nudo."""
        self._validar()

    def _validar(self) -> None:
        """
        Valida que los parámetros del nudo sean correctos.

        Raises:
            ValueError: Si el ID no es positivo
        """
        if self.id <= 0:
            raise ValueError(f"El ID del nudo debe ser positivo, se recibió id={self.id}")

    @property
    def coordenadas(self) -> tuple[float, float]:
        """
        Retorna las coordenadas del nudo como tupla.

        Returns:
            Tupla (x, y)
        """
        return (self.x, self.y)

    @property
    def tiene_vinculo(self) -> bool:
        """
        Indica si el nudo tiene un vínculo externo asignado.

        Returns:
            True si tiene vínculo, False en caso contrario
        """
        return self.vinculo is not None

    @property
    def es_libre(self) -> bool:
        """
        Indica si el nudo está libre (sin vínculo externo).

        Returns:
            True si está libre, False si tiene vínculo
        """
        return self.vinculo is None

    @property
    def gdl_restringidos(self) -> list[str]:
        """
        Lista de grados de libertad restringidos por el vínculo.

        Returns:
            Lista de strings con los GDL restringidos (ej: ["Ux", "Uy", "θz"])
            Lista vacía si no tiene vínculo
        """
        if self.vinculo is None:
            return []
        return self.vinculo.gdl_restringidos()

    @property
    def num_gdl_restringidos(self) -> int:
        """
        Número de grados de libertad restringidos.

        Returns:
            Entero entre 0 y 3
        """
        return len(self.gdl_restringidos)

    @property
    def num_reacciones(self) -> int:
        """
        Número de reacciones de vínculo en este nudo.

        Equivalente a num_gdl_restringidos para vínculos rígidos.

        Returns:
            Número de reacciones
        """
        return self.num_gdl_restringidos

    def distancia_a(self, otro: Nudo) -> float:
        """
        Calcula la distancia euclidiana a otro nudo.

        Args:
            otro: Otro nudo

        Returns:
            Distancia entre los dos nudos [m]
        """
        import math
        return math.hypot(otro.x - self.x, otro.y - self.y)

    def coincide_con(self, otro: Nudo, tolerancia: float = 1e-9) -> bool:
        """
        Determina si este nudo coincide geométricamente con otro.

        Args:
            otro: Otro nudo a comparar
            tolerancia: Tolerancia para la comparación [m]

        Returns:
            True si los nudos tienen las mismas coordenadas
        """
        return self.distancia_a(otro) < tolerancia

    def mover_a(self, x: float, y: float) -> None:
        """
        Mueve el nudo a nuevas coordenadas.

        Args:
            x: Nueva coordenada X [m]
            y: Nueva coordenada Y [m]
        """
        self.x = x
        self.y = y

    def desplazar(self, dx: float, dy: float) -> None:
        """
        Desplaza el nudo una cantidad relativa.

        Args:
            dx: Desplazamiento en X [m]
            dy: Desplazamiento en Y [m]
        """
        self.x += dx
        self.y += dy

    def asignar_vinculo(self, vinculo: Vinculo) -> None:
        """
        Asigna un vínculo externo al nudo.

        Args:
            vinculo: Vínculo a asignar

        Raises:
            ValueError: Si el nudo ya tiene un vínculo asignado
        """
        if self.vinculo is not None:
            raise ValueError(
                f"El nudo {self.id} ya tiene un vínculo asignado. "
                "Use liberar_vinculo() primero."
            )
        vinculo.nudo = self
        self.vinculo = vinculo

    def liberar_vinculo(self) -> Optional[Vinculo]:
        """
        Libera el vínculo del nudo.

        Returns:
            El vínculo que estaba asignado, o None si no tenía
        """
        vinculo_anterior = self.vinculo
        if vinculo_anterior is not None:
            vinculo_anterior.nudo = None
        self.vinculo = None
        return vinculo_anterior

    def reiniciar_resultados(self) -> None:
        """Reinicia los resultados del análisis a cero."""
        self.Ux = 0.0
        self.Uy = 0.0
        self.theta_z = 0.0

    def desplazamientos(self) -> tuple[float, float, float]:
        """
        Retorna los desplazamientos calculados como tupla.

        Returns:
            Tupla (Ux, Uy, θz)
        """
        return (self.Ux, self.Uy, self.theta_z)

    def __str__(self) -> str:
        """Representación legible del nudo."""
        nombre_str = f" '{self.nombre}'" if self.nombre else ""
        vinculo_str = f" [{self.vinculo.tipo_str}]" if self.vinculo else ""
        return f"Nudo {self.id}{nombre_str} ({self.x:.3f}, {self.y:.3f}){vinculo_str}"

    def __hash__(self) -> int:
        """Hash basado en el ID para uso en conjuntos y diccionarios."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Igualdad basada en el ID del nudo."""
        if not isinstance(other, Nudo):
            return NotImplemented
        return self.id == other.id
