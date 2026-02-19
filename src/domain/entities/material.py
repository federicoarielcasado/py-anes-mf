"""
Clase Material para propiedades de materiales estructurales.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Material:
    """
    Representa las propiedades mecánicas de un material estructural.

    Attributes:
        nombre: Nombre identificador del material
        E: Módulo de elasticidad (módulo de Young) [kN/m²]
        alpha: Coeficiente de dilatación térmica [1/°C]
        rho: Densidad del material [kg/m³] (para cálculo de peso propio)
        nu: Coeficiente de Poisson (adimensional)
        fy: Tensión de fluencia [kN/m²] (para verificaciones futuras)

    Example:
        >>> acero = Material(
        ...     nombre="Acero A-36",
        ...     E=200e6,  # 200 GPa
        ...     alpha=1.2e-5,
        ...     rho=7850
        ... )
        >>> acero.E
        200000000.0

    Note:
        El sistema de unidades por defecto es:
        - Fuerzas: kN
        - Longitudes: m
        - Por lo tanto E está en kN/m² (= kPa)
        - 200 GPa = 200e6 kPa = 200e6 kN/m²
    """

    nombre: str
    E: float  # Módulo elástico [kN/m²]
    alpha: float = 1.2e-5  # Coeficiente dilatación térmica [1/°C]
    rho: float = 0.0  # Densidad [kg/m³]
    nu: float = 0.3  # Coeficiente de Poisson
    fy: Optional[float] = None  # Tensión de fluencia [kN/m²]

    # Campo interno para ID único
    _id: int = field(default=0, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Valida los parámetros del material después de la inicialización."""
        self._validar()

    def _validar(self) -> None:
        """
        Valida que las propiedades del material sean físicamente válidas.

        Raises:
            ValueError: Si alguna propiedad tiene un valor inválido
        """
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre del material no puede estar vacío")

        if self.E <= 0:
            raise ValueError(f"El módulo de elasticidad debe ser positivo, se recibió E={self.E}")

        if self.alpha < 0:
            raise ValueError(
                f"El coeficiente de dilatación térmica no puede ser negativo, "
                f"se recibió alpha={self.alpha}"
            )

        if self.rho < 0:
            raise ValueError(f"La densidad no puede ser negativa, se recibió rho={self.rho}")

        if not (-1 < self.nu < 0.5):
            raise ValueError(
                f"El coeficiente de Poisson debe estar en el rango (-1, 0.5), "
                f"se recibió nu={self.nu}"
            )

        if self.fy is not None and self.fy <= 0:
            raise ValueError(
                f"La tensión de fluencia debe ser positiva, se recibió fy={self.fy}"
            )

    @property
    def G(self) -> float:
        """
        Calcula el módulo de corte (módulo de rigidez).

        Returns:
            Módulo de corte G = E / (2 * (1 + nu)) [kN/m²]
        """
        return self.E / (2 * (1 + self.nu))

    @property
    def K(self) -> float:
        """
        Calcula el módulo de compresibilidad volumétrica.

        Returns:
            Módulo volumétrico K = E / (3 * (1 - 2*nu)) [kN/m²]
        """
        return self.E / (3 * (1 - 2 * self.nu))

    def copia(self, nombre: Optional[str] = None) -> Material:
        """
        Crea una copia del material con opción de cambiar el nombre.

        Args:
            nombre: Nuevo nombre para la copia (opcional)

        Returns:
            Nueva instancia de Material con los mismos valores
        """
        return Material(
            nombre=nombre if nombre else f"{self.nombre} (copia)",
            E=self.E,
            alpha=self.alpha,
            rho=self.rho,
            nu=self.nu,
            fy=self.fy,
        )

    def __str__(self) -> str:
        """Representación legible del material."""
        return f"{self.nombre} (E={self.E/1e6:.0f} GPa)"


# =============================================================================
# MATERIALES PREDEFINIDOS
# =============================================================================

def acero_estructural(grado: str = "A-36") -> Material:
    """
    Crea un material de acero estructural con propiedades típicas.

    Args:
        grado: Grado del acero ("A-36", "A-572 Gr50", "A-992")

    Returns:
        Material configurado para acero estructural
    """
    propiedades = {
        "A-36": {"E": 200e6, "fy": 250e3, "rho": 7850},
        "A-572 Gr50": {"E": 200e6, "fy": 345e3, "rho": 7850},
        "A-992": {"E": 200e6, "fy": 345e3, "rho": 7850},
    }

    if grado not in propiedades:
        raise ValueError(f"Grado de acero no reconocido: {grado}")

    props = propiedades[grado]
    return Material(
        nombre=f"Acero {grado}",
        E=props["E"],
        alpha=1.2e-5,
        rho=props["rho"],
        nu=0.3,
        fy=props["fy"],
    )


def hormigon(resistencia_mpa: float = 25) -> Material:
    """
    Crea un material de hormigón con propiedades calculadas.

    Args:
        resistencia_mpa: Resistencia a compresión f'c en MPa

    Returns:
        Material configurado para hormigón

    Note:
        El módulo de elasticidad se calcula según ACI 318:
        E = 4700 * sqrt(f'c) [MPa]
    """
    import math

    # E según ACI 318 (resultado en MPa, convertir a kN/m²)
    E_mpa = 4700 * math.sqrt(resistencia_mpa)
    E_kn_m2 = E_mpa * 1000  # 1 MPa = 1000 kN/m²

    return Material(
        nombre=f"Hormigón H-{int(resistencia_mpa)}",
        E=E_kn_m2,
        alpha=1.0e-5,
        rho=2400,
        nu=0.2,
        fy=resistencia_mpa * 1000,  # Aproximación: fy ≈ f'c
    )
