"""
Jerarquía de clases para vínculos externos (condiciones de borde).
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from src.utils.constants import GDL, TipoVinculo

if TYPE_CHECKING:
    from .nudo import Nudo


@dataclass
class Vinculo(ABC):
    """
    Clase base abstracta para vínculos externos.

    Un vínculo restringe uno o más grados de libertad de un nudo,
    impidiendo desplazamientos y/o rotaciones, y generando reacciones.

    Attributes:
        nudo: Nudo al que está asociado el vínculo

    Note:
        Las subclases deben implementar:
        - gdl_restringidos(): Lista de GDL restringidos
        - tipo_str: Cadena descriptiva del tipo de vínculo
        - simbolo_grafico: Código para representación visual
    """

    nudo: Optional[Nudo] = field(default=None, repr=False)
    _id: int = field(default=0, repr=False, compare=False)

    # Reacciones calculadas (post-análisis)
    Rx: float = field(default=0.0, repr=False)
    Ry: float = field(default=0.0, repr=False)
    Mz: float = field(default=0.0, repr=False)

    @abstractmethod
    def gdl_restringidos(self) -> List[str]:
        """
        Retorna la lista de grados de libertad restringidos.

        Returns:
            Lista de strings: "Ux", "Uy", y/o "θz"
        """
        pass

    @property
    @abstractmethod
    def tipo_str(self) -> str:
        """Nombre descriptivo del tipo de vínculo."""
        pass

    @property
    @abstractmethod
    def simbolo_grafico(self) -> str:
        """Código para representación gráfica."""
        pass

    @property
    def tipo(self) -> TipoVinculo:
        """Tipo de vínculo como enumeración."""
        pass

    @property
    def num_reacciones(self) -> int:
        """Número de reacciones que genera este vínculo."""
        return len(self.gdl_restringidos())

    def reacciones(self) -> tuple[float, float, float]:
        """
        Retorna las reacciones calculadas.

        Returns:
            Tupla (Rx, Ry, Mz) en unidades del sistema (kN, kN, kNm)
        """
        return (self.Rx, self.Ry, self.Mz)

    def reiniciar_reacciones(self) -> None:
        """Reinicia las reacciones a cero."""
        self.Rx = 0.0
        self.Ry = 0.0
        self.Mz = 0.0

    def restringe_ux(self) -> bool:
        """Indica si restringe el desplazamiento horizontal."""
        return GDL.UX.value in self.gdl_restringidos()

    def restringe_uy(self) -> bool:
        """Indica si restringe el desplazamiento vertical."""
        return GDL.UY.value in self.gdl_restringidos()

    def restringe_theta(self) -> bool:
        """Indica si restringe la rotación."""
        return GDL.THETA_Z.value in self.gdl_restringidos()


@dataclass
class Empotramiento(Vinculo):
    """
    Empotramiento perfecto: restringe los 3 GDL (Ux, Uy, θz).

    Genera 3 reacciones: Rx, Ry, Mz.

    Representación gráfica típica: rectángulo con líneas inclinadas.

    Example:
        >>> emp = Empotramiento()
        >>> emp.gdl_restringidos()
        ['Ux', 'Uy', 'θz']
    """

    def gdl_restringidos(self) -> List[str]:
        return [GDL.UX.value, GDL.UY.value, GDL.THETA_Z.value]

    @property
    def tipo_str(self) -> str:
        return "Empotramiento"

    @property
    def simbolo_grafico(self) -> str:
        return "FIXED"

    @property
    def tipo(self) -> TipoVinculo:
        return TipoVinculo.EMPOTRAMIENTO


@dataclass
class ApoyoFijo(Vinculo):
    """
    Apoyo fijo (articulación): restringe 2 GDL (Ux, Uy), permite rotación.

    Genera 2 reacciones: Rx, Ry.

    Representación gráfica típica: triángulo.

    Example:
        >>> apoyo = ApoyoFijo()
        >>> apoyo.gdl_restringidos()
        ['Ux', 'Uy']
    """

    def gdl_restringidos(self) -> List[str]:
        return [GDL.UX.value, GDL.UY.value]

    @property
    def tipo_str(self) -> str:
        return "Apoyo Fijo"

    @property
    def simbolo_grafico(self) -> str:
        return "PINNED"

    @property
    def tipo(self) -> TipoVinculo:
        return TipoVinculo.APOYO_FIJO


@dataclass
class Rodillo(Vinculo):
    """
    Apoyo de rodillo: restringe 1 GDL (desplazamiento perpendicular al plano de apoyo).

    Genera 1 reacción perpendicular a la superficie de apoyo.

    Attributes:
        direccion: GDL restringido ("Ux" o "Uy")
        angulo_superficie: Ángulo de la superficie de apoyo respecto a horizontal [rad]
                          0 = horizontal (restringe Uy)
                          π/2 = vertical (restringe Ux)

    Example:
        >>> rodillo_h = Rodillo(direccion="Uy")  # Rodillo horizontal
        >>> rodillo_h.gdl_restringidos()
        ['Uy']
    """

    direccion: str = GDL.UY.value  # Por defecto, rodillo horizontal (apoya en superficie horizontal)
    angulo_superficie: float = 0.0  # Radianes

    def __post_init__(self) -> None:
        """Valida la dirección especificada."""
        direcciones_validas = [GDL.UX.value, GDL.UY.value]
        if self.direccion not in direcciones_validas:
            raise ValueError(
                f"Dirección inválida: {self.direccion}. "
                f"Debe ser una de: {direcciones_validas}"
            )

    def gdl_restringidos(self) -> List[str]:
        return [self.direccion]

    @property
    def tipo_str(self) -> str:
        if self.direccion == GDL.UY.value:
            return "Rodillo Horizontal"
        elif self.direccion == GDL.UX.value:
            return "Rodillo Vertical"
        else:
            return f"Rodillo ({self.angulo_superficie*180/math.pi:.1f}°)"

    @property
    def simbolo_grafico(self) -> str:
        if self.direccion == GDL.UY.value:
            return "ROLLER_H"
        else:
            return "ROLLER_V"

    @property
    def tipo(self) -> TipoVinculo:
        if abs(self.angulo_superficie) < 1e-6:
            return TipoVinculo.RODILLO_HORIZONTAL
        elif abs(self.angulo_superficie - math.pi/2) < 1e-6:
            return TipoVinculo.RODILLO_VERTICAL
        else:
            return TipoVinculo.RODILLO_INCLINADO


@dataclass
class RodilloInclinado(Vinculo):
    """
    Rodillo sobre superficie inclinada.

    Restringe el desplazamiento perpendicular a una superficie inclinada.

    Attributes:
        angulo: Ángulo de la normal a la superficie respecto al eje Y [rad]
                0 = normal vertical (equivalente a rodillo horizontal)
                π/2 = normal horizontal (equivalente a rodillo vertical)
    """

    angulo: float = 0.0  # Ángulo de la normal respecto a Y

    def gdl_restringidos(self) -> List[str]:
        # Técnicamente restringe una combinación lineal de Ux y Uy
        # Para simplificar, indicamos ambos como parcialmente restringidos
        return [f"U_n({self.angulo*180/math.pi:.1f}°)"]

    @property
    def componentes_restriccion(self) -> tuple[float, float]:
        """
        Componentes de la dirección restringida en ejes globales.

        Returns:
            Tupla (cos(α), sin(α)) donde α es el ángulo de la normal
        """
        return (math.sin(self.angulo), math.cos(self.angulo))

    @property
    def tipo_str(self) -> str:
        return f"Rodillo Inclinado ({self.angulo*180/math.pi:.1f}°)"

    @property
    def simbolo_grafico(self) -> str:
        return "ROLLER_INC"

    @property
    def tipo(self) -> TipoVinculo:
        return TipoVinculo.RODILLO_INCLINADO


@dataclass
class Guia(Vinculo):
    """
    Guía (carril): restringe 2 GDL, permite 1 desplazamiento.

    Permite desplazamiento en una dirección pero restringe el perpendicular
    y la rotación.

    Attributes:
        direccion_libre: Dirección del desplazamiento permitido ("Ux" o "Uy")

    Example:
        >>> guia_h = Guia(direccion_libre="Ux")  # Permite deslizamiento horizontal
        >>> guia_h.gdl_restringidos()
        ['Uy', 'θz']
    """

    direccion_libre: str = GDL.UX.value  # Dirección en la que puede deslizar

    def __post_init__(self) -> None:
        """Valida la dirección especificada."""
        direcciones_validas = [GDL.UX.value, GDL.UY.value]
        if self.direccion_libre not in direcciones_validas:
            raise ValueError(
                f"Dirección libre inválida: {self.direccion_libre}. "
                f"Debe ser una de: {direcciones_validas}"
            )

    def gdl_restringidos(self) -> List[str]:
        if self.direccion_libre == GDL.UX.value:
            return [GDL.UY.value, GDL.THETA_Z.value]
        else:  # direccion_libre == "Uy"
            return [GDL.UX.value, GDL.THETA_Z.value]

    @property
    def tipo_str(self) -> str:
        if self.direccion_libre == GDL.UX.value:
            return "Guía Horizontal"
        else:
            return "Guía Vertical"

    @property
    def simbolo_grafico(self) -> str:
        if self.direccion_libre == GDL.UX.value:
            return "GUIDE_H"
        else:
            return "GUIDE_V"

    @property
    def tipo(self) -> TipoVinculo:
        if self.direccion_libre == GDL.UX.value:
            return TipoVinculo.GUIA_HORIZONTAL
        else:
            return TipoVinculo.GUIA_VERTICAL


@dataclass
class ArticulacionInterna:
    """
    Articulación interna (rótula): permite rotación relativa en un punto.

    A diferencia de los vínculos externos, una articulación interna no es
    una condición de borde sino una condición de continuidad que permite
    rotación relativa entre los elementos que confluyen en ese punto.

    Se aplica en un nudo donde confluyen barras, liberando la continuidad
    de momento (M = 0 en ese punto).

    Attributes:
        nudo_id: ID del nudo donde se ubica la articulación
        barra_id: ID de la barra afectada (opcional, si None afecta todas)

    Note:
        - Reduce el grado de hiperestaticidad en 1 por cada articulación
        - En el nudo articulado: M = 0 (momento nulo)
        - Los desplazamientos Ux, Uy son continuos
        - La rotación θz puede ser discontinua

    Example:
        >>> art = ArticulacionInterna(nudo_id=3)
        >>> # El momento en el nudo 3 será cero
    """

    nudo_id: int
    barra_id: Optional[int] = None  # Si None, afecta a todas las barras en el nudo
    descripcion: str = ""

    def __post_init__(self):
        if not self.descripcion:
            if self.barra_id:
                self.descripcion = f"Rótula en nudo {self.nudo_id} (barra {self.barra_id})"
            else:
                self.descripcion = f"Rótula en nudo {self.nudo_id}"

    @property
    def tipo_str(self) -> str:
        return "Articulación Interna"

    @property
    def simbolo_grafico(self) -> str:
        return "HINGE"

    def reduce_hiperestaticidad(self) -> int:
        """
        Número de GDL que libera esta articulación.

        Returns:
            1 (libera continuidad de momento)
        """
        return 1


@dataclass
class ResorteElastico(Vinculo):
    """
    Vínculo elástico con rigidez finita.

    A diferencia de los vínculos rígidos, un resorte no restringe completamente
    el GDL, sino que genera una fuerza proporcional al desplazamiento.

    Attributes:
        kx: Rigidez traslacional en dirección X [kN/m]
        ky: Rigidez traslacional en dirección Y [kN/m]
        ktheta: Rigidez rotacional [kNm/rad]

    Note:
        Los resortes no "restringen" GDL en el sentido tradicional,
        pero generan fuerzas de reacción proporcionales al desplazamiento.

    Example:
        >>> resorte = ResorteElastico(kx=0, ky=1000, ktheta=0)  # Resorte vertical
        >>> resorte.es_resorte_traslacional
        True
    """

    kx: float = 0.0  # [kN/m]
    ky: float = 0.0  # [kN/m]
    ktheta: float = 0.0  # [kNm/rad]

    def __post_init__(self) -> None:
        """Valida las rigideces."""
        if self.kx < 0:
            raise ValueError(f"kx no puede ser negativo: {self.kx}")
        if self.ky < 0:
            raise ValueError(f"ky no puede ser negativo: {self.ky}")
        if self.ktheta < 0:
            raise ValueError(f"ktheta no puede ser negativo: {self.ktheta}")

        if self.kx == 0 and self.ky == 0 and self.ktheta == 0:
            raise ValueError("Al menos una rigidez debe ser positiva")

    def gdl_restringidos(self) -> List[str]:
        # Los resortes no restringen completamente, pero para efectos
        # del conteo de vínculos, contamos los que tienen rigidez finita
        restringidos = []
        if self.kx > 0:
            restringidos.append(GDL.UX.value)
        if self.ky > 0:
            restringidos.append(GDL.UY.value)
        if self.ktheta > 0:
            restringidos.append(GDL.THETA_Z.value)
        return restringidos

    @property
    def es_resorte_traslacional(self) -> bool:
        """True si tiene al menos una rigidez traslacional."""
        return self.kx > 0 or self.ky > 0

    @property
    def es_resorte_rotacional(self) -> bool:
        """True si tiene rigidez rotacional."""
        return self.ktheta > 0

    @property
    def rigideces(self) -> tuple[float, float, float]:
        """Retorna las tres rigideces como tupla."""
        return (self.kx, self.ky, self.ktheta)

    @property
    def tipo_str(self) -> str:
        partes = []
        if self.kx > 0:
            partes.append(f"kx={self.kx:.0f}")
        if self.ky > 0:
            partes.append(f"ky={self.ky:.0f}")
        if self.ktheta > 0:
            partes.append(f"ktheta={self.ktheta:.0f}")
        return f"Resorte ({', '.join(partes)})"

    @property
    def simbolo_grafico(self) -> str:
        return "SPRING"

    @property
    def tipo(self) -> TipoVinculo:
        return TipoVinculo.RESORTE


# =============================================================================
# FUNCIONES DE CONVENIENCIA
# =============================================================================

def crear_empotramiento() -> Empotramiento:
    """Crea un empotramiento perfecto."""
    return Empotramiento()


def crear_apoyo_fijo() -> ApoyoFijo:
    """Crea un apoyo fijo (articulación)."""
    return ApoyoFijo()


def crear_rodillo_horizontal() -> Rodillo:
    """Crea un rodillo sobre superficie horizontal (restringe Uy)."""
    return Rodillo(direccion=GDL.UY.value)


def crear_rodillo_vertical() -> Rodillo:
    """Crea un rodillo sobre superficie vertical (restringe Ux)."""
    return Rodillo(direccion=GDL.UX.value)


def crear_guia_horizontal() -> Guia:
    """Crea una guía que permite desplazamiento horizontal."""
    return Guia(direccion_libre=GDL.UX.value)


def crear_guia_vertical() -> Guia:
    """Crea una guía que permite desplazamiento vertical."""
    return Guia(direccion_libre=GDL.UY.value)


def crear_resorte_vertical(k: float) -> ResorteElastico:
    """
    Crea un resorte vertical.

    Args:
        k: Rigidez [kN/m]

    Returns:
        ResorteElastico con ky=k
    """
    return ResorteElastico(kx=0, ky=k, ktheta=0)


def crear_resorte_horizontal(k: float) -> ResorteElastico:
    """
    Crea un resorte horizontal.

    Args:
        k: Rigidez [kN/m]

    Returns:
        ResorteElastico con kx=k
    """
    return ResorteElastico(kx=k, ky=0, ktheta=0)


def crear_resorte_rotacional(k: float) -> ResorteElastico:
    """
    Crea un resorte rotacional.

    Args:
        k: Rigidez [kNm/rad]

    Returns:
        ResorteElastico con ktheta=k
    """
    return ResorteElastico(kx=0, ky=0, ktheta=k)


def crear_articulacion_interna(nudo_id: int, barra_id: Optional[int] = None) -> ArticulacionInterna:
    """
    Crea una articulación interna (rótula).

    Args:
        nudo_id: ID del nudo donde se ubica
        barra_id: ID de la barra afectada (opcional)

    Returns:
        ArticulacionInterna
    """
    return ArticulacionInterna(nudo_id=nudo_id, barra_id=barra_id)
