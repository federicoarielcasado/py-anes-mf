"""
Jerarquía de clases para cargas aplicadas a la estructura.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Tuple

from src.utils.constants import TipoCarga

if TYPE_CHECKING:
    from .barra import Barra
    from .nudo import Nudo


@dataclass
class Carga(ABC):
    """
    Clase base abstracta para todas las cargas.

    Define la interfaz común para cargas puntuales, distribuidas,
    térmicas y movimientos impuestos.
    """

    _id: int = field(default=0, repr=False, compare=False)

    @property
    @abstractmethod
    def tipo(self) -> TipoCarga:
        """Tipo de carga como enumeración."""
        pass

    @property
    @abstractmethod
    def descripcion(self) -> str:
        """Descripción breve de la carga."""
        pass


# =============================================================================
# CARGAS PUNTUALES EN NUDOS
# =============================================================================

@dataclass
class CargaPuntualNudo(Carga):
    """
    Carga puntual aplicada directamente en un nudo.

    Attributes:
        nudo: Nudo donde se aplica la carga
        Fx: Fuerza en dirección X global [kN] (positivo → derecha)
        Fy: Fuerza en dirección Y global [kN] (positivo → arriba)
        Mz: Momento alrededor de Z [kNm] (positivo → antihorario)

    Example:
        >>> from src.domain.entities import Nudo
        >>> nudo = Nudo(1, 0, 3)
        >>> carga = CargaPuntualNudo(nudo=nudo, Fx=10, Fy=-20, Mz=0)
        >>> carga.Fy
        -20
    """

    nudo: Optional[Nudo] = None
    Fx: float = 0.0  # [kN]
    Fy: float = 0.0  # [kN]
    Mz: float = 0.0  # [kNm]

    @property
    def tipo(self) -> TipoCarga:
        return TipoCarga.PUNTUAL_NUDO

    @property
    def descripcion(self) -> str:
        partes = []
        if self.Fx != 0:
            partes.append(f"Fx={self.Fx:.1f}kN")
        if self.Fy != 0:
            partes.append(f"Fy={self.Fy:.1f}kN")
        if self.Mz != 0:
            partes.append(f"Mz={self.Mz:.1f}kNm")
        return f"Carga nodal: {', '.join(partes) or 'nula'}"

    @property
    def magnitud(self) -> float:
        """Magnitud de la fuerza resultante [kN]."""
        return math.hypot(self.Fx, self.Fy)

    @property
    def direccion(self) -> float:
        """Ángulo de la fuerza resultante respecto a X [rad]."""
        return math.atan2(self.Fy, self.Fx)

    def componentes(self) -> Tuple[float, float, float]:
        """Retorna las tres componentes como tupla."""
        return (self.Fx, self.Fy, self.Mz)

    def __str__(self) -> str:
        nudo_str = f" en Nudo {self.nudo.id}" if self.nudo else ""
        return f"CargaPuntualNudo{nudo_str}: ({self.Fx}, {self.Fy}, {self.Mz})"


# =============================================================================
# CARGAS PUNTUALES EN BARRAS
# =============================================================================

@dataclass
class CargaPuntualBarra(Carga):
    """
    Carga puntual aplicada sobre una barra a cierta distancia del extremo i.

    Attributes:
        barra: Barra sobre la que actúa la carga
        P: Magnitud de la carga [kN] (positivo según ángulo)
        a: Distancia desde el nudo i [m]
        angulo: Ángulo de aplicación respecto al eje local x [°]
                TERNA: Y+ abajo, rotación horaria +
                - 0° = en dirección de la barra (hacia j)
                - +90° = perpendicular HORARIO a la barra (hacia abajo en barra horizontal)
                - -90° = perpendicular ANTIHORARIO a la barra (hacia arriba en barra horizontal)
                - 180° = en dirección opuesta a la barra (hacia i)

    Example:
        >>> carga = CargaPuntualBarra(P=10.0, a=3.0, angulo=-90)
        >>> carga.componentes_locales
        (0.0, -10.0)
    """

    barra: Optional[Barra] = None
    P: float = 0.0  # [kN]
    a: float = 0.0  # [m] distancia desde nudo i
    angulo: float = -90.0  # [°] respecto a eje x local

    def __post_init__(self) -> None:
        """Valida los parámetros de la carga."""
        if self.a < 0:
            raise ValueError(f"La distancia 'a' no puede ser negativa: a={self.a}")

        if self.barra is not None and self.a > self.barra.L:
            raise ValueError(
                f"La distancia a={self.a} excede la longitud de la barra L={self.barra.L}"
            )

    @property
    def tipo(self) -> TipoCarga:
        return TipoCarga.PUNTUAL_BARRA

    @property
    def descripcion(self) -> str:
        return f"Carga puntual: P={self.P:.1f}kN a {self.a:.2f}m ({self.angulo:.0f}°)"

    @property
    def angulo_rad(self) -> float:
        """Ángulo en radianes."""
        return math.radians(self.angulo)

    @property
    def componentes_locales(self) -> Tuple[float, float]:
        """
        Componentes de la carga en el sistema local de la barra.

        Returns:
            Tupla (Px_local, Py_local) donde:
            - Px_local: componente en dirección de la barra
            - Py_local: componente perpendicular a la barra
        """
        ang_rad = self.angulo_rad
        return (
            self.P * math.cos(ang_rad),
            self.P * math.sin(ang_rad),
        )

    @property
    def b(self) -> float:
        """Distancia desde el punto de aplicación hasta el nudo j [m]."""
        if self.barra is None:
            return 0.0
        return self.barra.L - self.a

    def componentes_globales(self) -> Tuple[float, float]:
        """
        Componentes de la carga en el sistema global.

        Requiere que la barra esté asignada.

        Returns:
            Tupla (Px_global, Py_global)
        """
        if self.barra is None:
            raise ValueError("La barra debe estar asignada para calcular componentes globales")

        Px_local, Py_local = self.componentes_locales
        return self.barra.local_a_global(Px_local, Py_local)

    def __str__(self) -> str:
        barra_str = f" en Barra {self.barra.id}" if self.barra else ""
        return f"CargaPuntualBarra{barra_str}: P={self.P}kN, a={self.a}m, θ={self.angulo}°"


# =============================================================================
# CARGAS DISTRIBUIDAS
# =============================================================================

@dataclass
class CargaDistribuida(Carga):
    """
    Carga distribuida sobre una barra (uniforme, triangular o trapezoidal).

    Attributes:
        barra: Barra sobre la que actúa la carga
        q1: Intensidad de carga en el inicio [kN/m]
        q2: Intensidad de carga en el final [kN/m]
        x1: Posición de inicio de la carga desde nudo i [m]
        x2: Posición de fin de la carga desde nudo i [m]
        angulo: Ángulo de aplicación respecto al eje local x [°]
                - -90° = perpendicular hacia abajo (gravedad)
                - 0° = en dirección de la barra

    Tipos de carga según q1 y q2:
        - q1 == q2: Carga uniforme
        - q1 == 0 o q2 == 0: Carga triangular
        - q1 != q2 (ninguno cero): Carga trapezoidal

    Example:
        >>> carga_unif = CargaDistribuida(q1=10, q2=10, x1=0, x2=6)
        >>> carga_unif.es_uniforme
        True
        >>> carga_unif.resultante
        60.0
    """

    barra: Optional[Barra] = None
    q1: float = 0.0  # [kN/m] intensidad en x1
    q2: float = 0.0  # [kN/m] intensidad en x2
    x1: float = 0.0  # [m] inicio de la carga
    x2: Optional[float] = None  # [m] fin de la carga (None = hasta el final)
    angulo: float = -90.0  # [°] respecto a eje x local

    def __post_init__(self) -> None:
        """Valida y ajusta los parámetros."""
        if self.x1 < 0:
            raise ValueError(f"x1 no puede ser negativo: x1={self.x1}")

        # Si x2 no se especifica y hay barra, usar longitud completa
        if self.x2 is None and self.barra is not None:
            self.x2 = self.barra.L
        elif self.x2 is None:
            self.x2 = self.x1  # Evitar None

        if self.x2 < self.x1:
            raise ValueError(f"x2 ({self.x2}) debe ser mayor o igual que x1 ({self.x1})")

    @property
    def tipo(self) -> TipoCarga:
        if self.es_uniforme:
            return TipoCarga.DISTRIBUIDA_UNIFORME
        elif self.es_triangular:
            return TipoCarga.DISTRIBUIDA_TRIANGULAR
        else:
            return TipoCarga.DISTRIBUIDA_TRAPEZOIDAL

    @property
    def descripcion(self) -> str:
        if self.es_uniforme:
            return f"Carga uniforme: q={self.q1:.1f}kN/m"
        elif self.es_triangular:
            return f"Carga triangular: q={max(self.q1, self.q2):.1f}kN/m"
        else:
            return f"Carga trapezoidal: q1={self.q1:.1f}, q2={self.q2:.1f}kN/m"

    @property
    def es_uniforme(self) -> bool:
        """True si la carga es uniforme (q1 == q2)."""
        return abs(self.q1 - self.q2) < 1e-10

    @property
    def es_triangular(self) -> bool:
        """True si la carga es triangular (q1=0 o q2=0, pero no ambos)."""
        return (abs(self.q1) < 1e-10) != (abs(self.q2) < 1e-10)

    @property
    def longitud(self) -> float:
        """Longitud sobre la que actúa la carga [m]."""
        return (self.x2 or 0) - self.x1

    @property
    def resultante(self) -> float:
        """
        Fuerza resultante de la carga distribuida [kN].

        Para carga trapezoidal: R = (q1 + q2) * L / 2
        """
        return (self.q1 + self.q2) * self.longitud / 2

    @property
    def posicion_resultante(self) -> float:
        """
        Posición de la resultante desde x1 [m].

        Para carga uniforme: L/2
        Para carga triangular (q1=0): 2L/3 desde x1
        Para carga triangular (q2=0): L/3 desde x1
        Para carga trapezoidal: según centroide del trapecio
        """
        L = self.longitud
        if L < 1e-10:
            return 0.0

        if self.es_uniforme:
            return L / 2

        # Fórmula general para trapecio
        # x_centroide = L * (q1 + 2*q2) / (3 * (q1 + q2))
        suma = self.q1 + self.q2
        if abs(suma) < 1e-10:
            return L / 2

        return L * (self.q1 + 2 * self.q2) / (3 * suma)

    @property
    def posicion_resultante_global(self) -> float:
        """Posición de la resultante desde nudo i [m]."""
        return self.x1 + self.posicion_resultante

    def intensidad_en(self, x: float) -> float:
        """
        Calcula la intensidad de la carga en una posición x.

        Args:
            x: Posición desde nudo i [m]

        Returns:
            Intensidad de la carga en x [kN/m], 0 si está fuera del rango
        """
        x2 = self.x2 or 0
        if x < self.x1 or x > x2:
            return 0.0

        if self.longitud < 1e-10:
            return self.q1

        # Interpolación lineal
        t = (x - self.x1) / self.longitud
        return self.q1 + t * (self.q2 - self.q1)

    def __str__(self) -> str:
        barra_str = f" en Barra {self.barra.id}" if self.barra else ""
        return f"CargaDistribuida{barra_str}: q1={self.q1}, q2={self.q2} kN/m"


# =============================================================================
# MOVIMIENTOS IMPUESTOS
# =============================================================================

@dataclass
class MovimientoImpuesto(Carga):
    """
    Movimiento impuesto (asentamiento, hundimiento, rotación prescrita).

    Representa un desplazamiento o rotación forzada en un vínculo,
    típicamente un hundimiento de apoyo.

    Attributes:
        nudo: Nudo donde se impone el movimiento
        delta_x: Desplazamiento impuesto en X [m]
        delta_y: Desplazamiento impuesto en Y [m] (negativo = hundimiento)
        delta_theta: Rotación impuesta [rad]

    Example:
        >>> mov = MovimientoImpuesto(delta_y=-0.010)  # Hundimiento de 10mm
        >>> mov.delta_y
        -0.01
    """

    nudo: Optional[Nudo] = None
    delta_x: float = 0.0  # [m]
    delta_y: float = 0.0  # [m]
    delta_theta: float = 0.0  # [rad]

    @property
    def tipo(self) -> TipoCarga:
        return TipoCarga.MOVIMIENTO_IMPUESTO

    @property
    def descripcion(self) -> str:
        partes = []
        if abs(self.delta_x) > 1e-10:
            partes.append(f"δx={self.delta_x*1000:.1f}mm")
        if abs(self.delta_y) > 1e-10:
            partes.append(f"δy={self.delta_y*1000:.1f}mm")
        if abs(self.delta_theta) > 1e-10:
            partes.append(f"δθ={self.delta_theta*1000:.2f}mrad")
        return f"Movimiento impuesto: {', '.join(partes) or 'nulo'}"

    @property
    def es_hundimiento(self) -> bool:
        """True si es un hundimiento vertical (delta_y < 0)."""
        return self.delta_y < 0

    @property
    def es_levantamiento(self) -> bool:
        """True si es un levantamiento vertical (delta_y > 0)."""
        return self.delta_y > 0

    def componentes(self) -> Tuple[float, float, float]:
        """Retorna los tres componentes como tupla."""
        return (self.delta_x, self.delta_y, self.delta_theta)

    def __str__(self) -> str:
        nudo_str = f" en Nudo {self.nudo.id}" if self.nudo else ""
        return f"MovimientoImpuesto{nudo_str}: ({self.delta_x*1000:.1f}mm, {self.delta_y*1000:.1f}mm, {self.delta_theta*1000:.2f}mrad)"


# =============================================================================
# CARGAS TÉRMICAS
# =============================================================================

@dataclass
class CargaTermica(Carga):
    """
    Carga térmica aplicada a una barra.

    Modela efectos de variación de temperatura en elementos estructurales:
    - ΔT uniforme: expansión/contracción axial (α·ΔT·L)
    - Gradiente térmico: curvatura por diferencia de temperatura entre fibras

    Para estructuras hiperestáticas, las cargas térmicas generan esfuerzos
    internos debido a restricciones de movimiento.

    Attributes:
        barra: Barra donde se aplica la carga térmica
        delta_T_uniforme: Variación uniforme de temperatura [°C]
                         (positivo = aumento, negativo = disminución)
        delta_T_gradiente: Diferencia de temperatura entre fibra superior e inferior [°C]
                          (positivo = fibra superior más caliente)

    Example:
        >>> # Calentamiento uniforme de +30°C
        >>> carga1 = CargaTermica(barra, delta_T_uniforme=30.0)
        >>>
        >>> # Gradiente térmico: cara superior +20°C, cara inferior 0°C
        >>> carga2 = CargaTermica(barra, delta_T_gradiente=20.0)
        >>>
        >>> # Combinación: calentamiento uniforme + gradiente
        >>> carga3 = CargaTermica(barra, delta_T_uniforme=15.0, delta_T_gradiente=10.0)

    Notes:
        - El coeficiente de dilatación térmica α se obtiene del material de la barra
        - Para una barra empotrada-empotrada con ΔT uniforme:
          * Deformación libre: δ = α·ΔT·L
          * Reacción generada: R = (E·A·α·ΔT)
        - Para gradiente térmico en viga:
          * Curvatura: κ = (α·ΔT_grad) / h
          * donde h = altura de la sección
    """

    barra: Optional[Barra] = None
    delta_T_uniforme: float = 0.0  # [°C]
    delta_T_gradiente: float = 0.0  # [°C]

    @property
    def tipo(self) -> TipoCarga:
        return TipoCarga.TERMICA

    @property
    def descripcion(self) -> str:
        partes = []
        if abs(self.delta_T_uniforme) > 1e-6:
            signo = "+" if self.delta_T_uniforme > 0 else ""
            partes.append(f"ΔT={signo}{self.delta_T_uniforme:.1f}°C")
        if abs(self.delta_T_gradiente) > 1e-6:
            partes.append(f"∇T={self.delta_T_gradiente:.1f}°C")

        barra_str = f" en Barra {self.barra.id}" if self.barra else ""
        contenido = ', '.join(partes) if partes else 'nula'
        return f"Carga térmica{barra_str}: {contenido}"

    def deformacion_axial_libre(self) -> float:
        """
        Calcula la deformación axial libre (sin restricciones).

        Returns:
            δ = α·ΔT·L [m]
        """
        if not self.barra:
            return 0.0

        alpha = self.barra.material.alpha
        L = self.barra.L
        return alpha * self.delta_T_uniforme * L

    def curvatura_termica(self) -> float:
        """
        Calcula la curvatura inducida por gradiente térmico.

        Returns:
            κ = (α·ΔT_grad) / h [1/m]
        """
        if not self.barra:
            return 0.0

        alpha = self.barra.material.alpha
        h = self.barra.seccion.h

        if h < 1e-10:
            return 0.0

        return (alpha * self.delta_T_gradiente) / h

    def trabajo_virtual_uniforme(self, esfuerzo_axil_virtual: float) -> float:
        """
        Calcula el trabajo virtual debido a variación uniforme de temperatura.

        Para integración en término e₀ᵢ del método de las fuerzas:
        δᵢ_térmico = α·ΔT·∫(Nᵢ dx)

        Args:
            esfuerzo_axil_virtual: Valor de N en la subestructura virtual Xi

        Returns:
            Contribución al desplazamiento virtual [m]
        """
        if not self.barra:
            return 0.0

        alpha = self.barra.material.alpha
        L = self.barra.L

        # ∫(Nᵢ dx) = Nᵢ·L (si Nᵢ es constante en la barra)
        return alpha * self.delta_T_uniforme * esfuerzo_axil_virtual * L

    def trabajo_virtual_gradiente(self, momento_flector_virtual_func) -> float:
        """
        Calcula el trabajo virtual debido a gradiente térmico.

        Para integración en término e₀ᵢ:
        δᵢ_térmico = κ_T·∫(Mᵢ dx)
        donde κ_T = (α·ΔT_grad) / h

        Args:
            momento_flector_virtual_func: Función M_i(x) de la subestructura virtual

        Returns:
            Contribución al desplazamiento virtual [m]
        """
        if not self.barra:
            return 0.0

        # Integración numérica de ∫(Mᵢ dx)
        from scipy.integrate import simpson
        import numpy as np

        n_puntos = 21
        x_vals = np.linspace(0, self.barra.L, n_puntos)
        M_vals = np.array([momento_flector_virtual_func(x) for x in x_vals])

        integral_M = simpson(M_vals, x=x_vals)

        curvatura = self.curvatura_termica()
        return curvatura * integral_M

    @property
    def tiene_componente_uniforme(self) -> bool:
        """True si tiene variación uniforme de temperatura."""
        return abs(self.delta_T_uniforme) > 1e-10

    @property
    def tiene_componente_gradiente(self) -> bool:
        """True si tiene gradiente térmico."""
        return abs(self.delta_T_gradiente) > 1e-10

    def __str__(self) -> str:
        barra_str = f" en Barra {self.barra.id}" if self.barra else ""
        partes = []
        if abs(self.delta_T_uniforme) > 1e-6:
            partes.append(f"ΔT_unif={self.delta_T_uniforme:+.1f}°C")
        if abs(self.delta_T_gradiente) > 1e-6:
            partes.append(f"ΔT_grad={self.delta_T_gradiente:+.1f}°C")

        contenido = ', '.join(partes) if partes else '0°C'
        return f"CargaTermica{barra_str}: {contenido}"


# =============================================================================
# FUNCIONES DE CONVENIENCIA
# =============================================================================

def crear_carga_puntual_vertical(P: float, nudo: Nudo) -> CargaPuntualNudo:
    """
    Crea una carga puntual vertical hacia abajo en un nudo.

    Args:
        P: Magnitud de la carga [kN] (positivo = hacia abajo)
        nudo: Nudo donde se aplica

    Returns:
        CargaPuntualNudo con Fy=-P
    """
    return CargaPuntualNudo(nudo=nudo, Fx=0, Fy=-abs(P), Mz=0)


def crear_carga_puntual_horizontal(P: float, nudo: Nudo) -> CargaPuntualNudo:
    """
    Crea una carga puntual horizontal hacia la derecha en un nudo.

    Args:
        P: Magnitud de la carga [kN] (positivo = hacia derecha)
        nudo: Nudo donde se aplica

    Returns:
        CargaPuntualNudo con Fx=P
    """
    return CargaPuntualNudo(nudo=nudo, Fx=P, Fy=0, Mz=0)


def crear_carga_uniforme(q: float, barra: Optional[Barra] = None) -> CargaDistribuida:
    """
    Crea una carga uniformemente distribuida en toda la barra.

    Args:
        q: Intensidad de la carga [kN/m] (positivo = hacia abajo)
        barra: Barra sobre la que actúa (opcional)

    Returns:
        CargaDistribuida uniforme
    """
    return CargaDistribuida(
        barra=barra,
        q1=q,
        q2=q,
        x1=0,
        x2=barra.L if barra else None,
        angulo=-90,
    )


def crear_hundimiento(delta_mm: float, nudo: Nudo) -> MovimientoImpuesto:
    """
    Crea un hundimiento de apoyo.

    Args:
        delta_mm: Hundimiento en milímetros (positivo = hacia abajo)
        nudo: Nudo donde se impone

    Returns:
        MovimientoImpuesto con delta_y negativo
    """
    return MovimientoImpuesto(
        nudo=nudo,
        delta_x=0,
        delta_y=-abs(delta_mm) / 1000,  # Convertir a metros, asegurar negativo
        delta_theta=0,
    )
