"""
Clases para secciones transversales de elementos estructurales.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class Seccion(ABC):
    """
    Clase base abstracta para secciones transversales.

    Define la interfaz común para todas las secciones, que deben
    proporcionar área, momento de inercia y altura.

    Attributes:
        nombre: Nombre identificador de la sección
    """

    nombre: str
    _id: int = field(default=0, repr=False, compare=False)

    @property
    @abstractmethod
    def A(self) -> float:
        """Área de la sección transversal [m²]."""
        pass

    @property
    @abstractmethod
    def Iz(self) -> float:
        """Momento de inercia respecto al eje Z (fuera del plano) [m⁴]."""
        pass

    @property
    @abstractmethod
    def h(self) -> float:
        """Altura de la sección (para gradiente térmico) [m]."""
        pass

    @property
    def Wz(self) -> float:
        """
        Módulo resistente elástico respecto al eje Z.

        Returns:
            Wz = Iz / (h/2) [m³]
        """
        if self.h <= 0:
            return 0.0
        return self.Iz / (self.h / 2)

    @property
    def rz(self) -> float:
        """
        Radio de giro respecto al eje Z.

        Returns:
            rz = sqrt(Iz / A) [m]
        """
        if self.A <= 0:
            return 0.0
        return math.sqrt(self.Iz / self.A)


@dataclass
class SeccionRectangular(Seccion):
    """
    Sección transversal rectangular maciza.

    Attributes:
        nombre: Nombre identificador
        b: Ancho de la sección [m]
        _h: Altura de la sección [m]

    Example:
        >>> sec = SeccionRectangular("Rect 30x50", b=0.30, _h=0.50)
        >>> f"{sec.A:.4f}"
        '0.1500'
    """

    b: float = 0.0  # Ancho [m]
    _h: float = 0.0  # Altura [m]

    def __post_init__(self) -> None:
        """Valida las dimensiones de la sección."""
        if self.b <= 0:
            raise ValueError(f"El ancho debe ser positivo, se recibió b={self.b}")
        if self._h <= 0:
            raise ValueError(f"La altura debe ser positiva, se recibió h={self._h}")

    @property
    def A(self) -> float:
        """Área = b * h [m²]."""
        return self.b * self._h

    @property
    def Iz(self) -> float:
        """Momento de inercia = b * h³ / 12 [m⁴]."""
        return self.b * self._h**3 / 12

    @property
    def h(self) -> float:
        """Altura de la sección [m]."""
        return self._h

    @property
    def Iy(self) -> float:
        """Momento de inercia respecto al eje Y = h * b³ / 12 [m⁴]."""
        return self._h * self.b**3 / 12

    def __str__(self) -> str:
        return f"{self.nombre} ({self.b*100:.0f}x{self._h*100:.0f} cm)"


@dataclass
class SeccionCircular(Seccion):
    """
    Sección transversal circular maciza.

    Attributes:
        nombre: Nombre identificador
        diametro: Diámetro de la sección [m]

    Example:
        >>> sec = SeccionCircular("Circular D=30", diametro=0.30)
        >>> f"{sec.A:.6f}"
        '0.070686'
    """

    diametro: float = 0.0

    def __post_init__(self) -> None:
        """Valida las dimensiones de la sección."""
        if self.diametro <= 0:
            raise ValueError(
                f"El diámetro debe ser positivo, se recibió diametro={self.diametro}"
            )

    @property
    def A(self) -> float:
        """Área = π * d² / 4 [m²]."""
        return math.pi * self.diametro**2 / 4

    @property
    def Iz(self) -> float:
        """Momento de inercia = π * d⁴ / 64 [m⁴]."""
        return math.pi * self.diametro**4 / 64

    @property
    def h(self) -> float:
        """Altura = diámetro [m]."""
        return self.diametro

    def __str__(self) -> str:
        return f"{self.nombre} (D={self.diametro*100:.0f} cm)"


@dataclass
class SeccionCircularHueca(Seccion):
    """
    Sección transversal circular hueca (tubo).

    Attributes:
        nombre: Nombre identificador
        diametro_ext: Diámetro exterior [m]
        espesor: Espesor de pared [m]
    """

    diametro_ext: float = 0.0
    espesor: float = 0.0

    def __post_init__(self) -> None:
        """Valida las dimensiones de la sección."""
        if self.diametro_ext <= 0:
            raise ValueError(
                f"El diámetro exterior debe ser positivo, "
                f"se recibió diametro_ext={self.diametro_ext}"
            )
        if self.espesor <= 0:
            raise ValueError(f"El espesor debe ser positivo, se recibió espesor={self.espesor}")
        if self.espesor >= self.diametro_ext / 2:
            raise ValueError(
                f"El espesor ({self.espesor}) debe ser menor que el radio "
                f"({self.diametro_ext/2})"
            )

    @property
    def diametro_int(self) -> float:
        """Diámetro interior [m]."""
        return self.diametro_ext - 2 * self.espesor

    @property
    def A(self) -> float:
        """Área = π/4 * (De² - Di²) [m²]."""
        return math.pi / 4 * (self.diametro_ext**2 - self.diametro_int**2)

    @property
    def Iz(self) -> float:
        """Momento de inercia = π/64 * (De⁴ - Di⁴) [m⁴]."""
        return math.pi / 64 * (self.diametro_ext**4 - self.diametro_int**4)

    @property
    def h(self) -> float:
        """Altura = diámetro exterior [m]."""
        return self.diametro_ext

    def __str__(self) -> str:
        return f"{self.nombre} (De={self.diametro_ext*1000:.0f}mm, t={self.espesor*1000:.1f}mm)"


@dataclass
class SeccionPerfil(Seccion):
    """
    Sección de perfil estructural con propiedades predefinidas.

    Útil para perfiles laminados (IPE, HEA, HEB, etc.) cuyas propiedades
    se obtienen de catálogos.

    Attributes:
        nombre: Nombre/designación del perfil (ej: "IPE 220")
        _A: Área de la sección [m²]
        _Iz: Momento de inercia eje fuerte [m⁴]
        _h: Altura del perfil [m]
        _Iy: Momento de inercia eje débil [m⁴] (opcional)
        _b: Ancho del ala [m] (opcional)
        _tf: Espesor del ala [m] (opcional)
        _tw: Espesor del alma [m] (opcional)

    Example:
        >>> ipe220 = SeccionPerfil(
        ...     nombre="IPE 220",
        ...     _A=33.4e-4,
        ...     _Iz=2772e-8,
        ...     _h=0.220
        ... )
        >>> f"{ipe220.A:.6f}"
        '0.003340'
    """

    _A: float = 0.0
    _Iz: float = 0.0
    _h: float = 0.0
    _Iy: Optional[float] = None
    _b: Optional[float] = None
    _tf: Optional[float] = None
    _tw: Optional[float] = None

    def __post_init__(self) -> None:
        """Valida las propiedades del perfil."""
        if self._A <= 0:
            raise ValueError(f"El área debe ser positiva, se recibió A={self._A}")
        if self._Iz <= 0:
            raise ValueError(f"El momento de inercia debe ser positivo, se recibió Iz={self._Iz}")
        if self._h <= 0:
            raise ValueError(f"La altura debe ser positiva, se recibió h={self._h}")

    @property
    def A(self) -> float:
        """Área de la sección [m²]."""
        return self._A

    @property
    def Iz(self) -> float:
        """Momento de inercia respecto al eje Z [m⁴]."""
        return self._Iz

    @property
    def h(self) -> float:
        """Altura del perfil [m]."""
        return self._h

    @property
    def Iy(self) -> Optional[float]:
        """Momento de inercia respecto al eje Y (eje débil) [m⁴]."""
        return self._Iy

    @property
    def b(self) -> Optional[float]:
        """Ancho del ala [m]."""
        return self._b

    def __str__(self) -> str:
        return f"{self.nombre}"


# =============================================================================
# FUNCIONES DE CONVENIENCIA PARA CREAR PERFILES COMUNES
# =============================================================================

def crear_seccion_rectangular(
    ancho_cm: float,
    altura_cm: float,
    nombre: Optional[str] = None
) -> SeccionRectangular:
    """
    Crea una sección rectangular a partir de dimensiones en centímetros.

    Args:
        ancho_cm: Ancho de la sección en centímetros
        altura_cm: Altura de la sección en centímetros
        nombre: Nombre opcional (se genera automáticamente si no se proporciona)

    Returns:
        SeccionRectangular configurada
    """
    if nombre is None:
        nombre = f"Rect {ancho_cm:.0f}x{altura_cm:.0f}"

    return SeccionRectangular(
        nombre=nombre,
        b=ancho_cm / 100,  # Convertir a metros
        _h=altura_cm / 100,
    )


def crear_seccion_circular(
    diametro_cm: float,
    nombre: Optional[str] = None
) -> SeccionCircular:
    """
    Crea una sección circular a partir del diámetro en centímetros.

    Args:
        diametro_cm: Diámetro en centímetros
        nombre: Nombre opcional

    Returns:
        SeccionCircular configurada
    """
    if nombre is None:
        nombre = f"Circ D{diametro_cm:.0f}"

    return SeccionCircular(
        nombre=nombre,
        diametro=diametro_cm / 100,
    )


def dimensiones_seccion(seccion: Seccion) -> Tuple[float, float]:
    """
    Obtiene las dimensiones aproximadas de una sección para visualización.

    Args:
        seccion: Cualquier tipo de sección

    Returns:
        Tupla (ancho, altura) en metros
    """
    if isinstance(seccion, SeccionRectangular):
        return (seccion.b, seccion.h)
    elif isinstance(seccion, (SeccionCircular, SeccionCircularHueca)):
        return (seccion.h, seccion.h)  # Diámetro x Diámetro
    elif isinstance(seccion, SeccionPerfil):
        b = seccion.b if seccion.b else seccion.h * 0.5  # Estimación
        return (b, seccion.h)
    else:
        # Aproximación genérica basada en área y altura
        if seccion.h > 0:
            b_aprox = seccion.A / seccion.h
            return (b_aprox, seccion.h)
        return (0.0, 0.0)
