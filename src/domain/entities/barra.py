"""
Clase Barra para elementos estructurales lineales.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, List, Optional

import numpy as np
from numpy.typing import NDArray

from src.utils.constants import LENGTH_TOLERANCE
from src.utils.geometry import (
    angulo_entre_puntos,
    distancia,
    matriz_transformacion_barra,
    matriz_transformacion_barra_6x6,
)

if TYPE_CHECKING:
    from .carga import Carga
    from .material import Material
    from .nudo import Nudo
    from .seccion import Seccion


@dataclass
class Barra:
    """
    Representa un elemento estructural lineal (barra/viga/columna) en un pórtico plano.

    Una barra conecta dos nudos y tiene propiedades geométricas (sección) y
    mecánicas (material) que definen su comportamiento estructural.

    Attributes:
        id: Identificador único de la barra
        nudo_i: Nudo inicial (extremo i)
        nudo_j: Nudo final (extremo j)
        material: Material de la barra
        seccion: Sección transversal

    Propiedades calculadas:
        L: Longitud de la barra [m]
        angulo: Ángulo respecto al eje X global [rad]

    Esfuerzos (post-análisis):
        N: Función N(x) de esfuerzo axil [kN]
        V: Función V(x) de esfuerzo cortante [kN]
        M: Función M(x) de momento flector [kNm]

    Example:
        >>> from src.domain.entities import Nudo, Material, SeccionRectangular
        >>> n1 = Nudo(1, 0, 0)
        >>> n2 = Nudo(2, 6, 0)
        >>> mat = Material("Acero", E=200e6)
        >>> sec = SeccionRectangular("30x50", b=0.30, _h=0.50)
        >>> barra = Barra(1, n1, n2, mat, sec)
        >>> barra.L
        6.0
    """

    id: int
    nudo_i: Nudo
    nudo_j: Nudo
    material: Material
    seccion: Seccion

    # Nombre opcional
    nombre: str = ""

    # Lista de cargas aplicadas sobre esta barra
    cargas: List[Carga] = field(default_factory=list, repr=False)

    # Articulaciones internas (liberación de momento en extremos)
    articulacion_i: bool = field(default=False, repr=False)
    articulacion_j: bool = field(default=False, repr=False)

    # Funciones de esfuerzos internos (se calculan post-análisis)
    # Por defecto, funciones que retornan 0
    _N: Callable[[float], float] = field(
        default=lambda x: 0.0, repr=False, compare=False
    )
    _V: Callable[[float], float] = field(
        default=lambda x: 0.0, repr=False, compare=False
    )
    _M: Callable[[float], float] = field(
        default=lambda x: 0.0, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        """Valida la barra después de la inicialización."""
        self._validar()

    def _validar(self) -> None:
        """
        Valida que la barra sea geométricamente válida.

        Raises:
            ValueError: Si la barra tiene longitud cero o nudos iguales
        """
        if self.id <= 0:
            raise ValueError(f"El ID de la barra debe ser positivo, se recibió id={self.id}")

        if self.nudo_i.id == self.nudo_j.id:
            raise ValueError(
                f"La barra {self.id} tiene el mismo nudo en ambos extremos (nudo {self.nudo_i.id})"
            )

        if self.L < LENGTH_TOLERANCE:
            raise ValueError(
                f"La barra {self.id} tiene longitud prácticamente cero: L={self.L:.2e} m"
            )

    # =========================================================================
    # PROPIEDADES GEOMÉTRICAS
    # =========================================================================

    @property
    def L(self) -> float:
        """
        Longitud de la barra [m].

        Calculada como la distancia euclidiana entre nudos.
        """
        return distancia(
            self.nudo_i.x, self.nudo_i.y,
            self.nudo_j.x, self.nudo_j.y
        )

    @property
    def angulo(self) -> float:
        """
        Ángulo de la barra respecto al eje X global [rad].

        El ángulo está en el rango [-π, π].
        - 0 = barra horizontal hacia la derecha
        - π/2 = barra vertical hacia arriba
        - π o -π = barra horizontal hacia la izquierda
        - -π/2 = barra vertical hacia abajo
        """
        return angulo_entre_puntos(
            self.nudo_i.x, self.nudo_i.y,
            self.nudo_j.x, self.nudo_j.y
        )

    @property
    def angulo_grados(self) -> float:
        """Ángulo de la barra en grados."""
        return math.degrees(self.angulo)

    @property
    def es_horizontal(self) -> bool:
        """True si la barra es horizontal (±0.1°)."""
        return abs(self.angulo) < 0.00175 or abs(abs(self.angulo) - math.pi) < 0.00175

    @property
    def es_vertical(self) -> bool:
        """True si la barra es vertical (±0.1°)."""
        return abs(abs(self.angulo) - math.pi/2) < 0.00175

    @property
    def dx(self) -> float:
        """Diferencia de coordenadas X entre nudos [m]."""
        return self.nudo_j.x - self.nudo_i.x

    @property
    def dy(self) -> float:
        """Diferencia de coordenadas Y entre nudos [m]."""
        return self.nudo_j.y - self.nudo_i.y

    @property
    def punto_medio(self) -> tuple[float, float]:
        """Coordenadas del punto medio de la barra."""
        return (
            (self.nudo_i.x + self.nudo_j.x) / 2,
            (self.nudo_i.y + self.nudo_j.y) / 2,
        )

    # =========================================================================
    # PROPIEDADES MECÁNICAS
    # =========================================================================

    @property
    def E(self) -> float:
        """Módulo de elasticidad del material [kN/m²]."""
        return self.material.E

    @property
    def A(self) -> float:
        """Área de la sección transversal [m²]."""
        return self.seccion.A

    @property
    def I(self) -> float:
        """Momento de inercia de la sección [m⁴]."""
        return self.seccion.Iz

    @property
    def EA(self) -> float:
        """Rigidez axil E·A [kN]."""
        return self.E * self.A

    @property
    def EI(self) -> float:
        """Rigidez a flexión E·I [kN·m²]."""
        return self.E * self.I

    @property
    def rigidez_axil(self) -> float:
        """Rigidez axil k = EA/L [kN/m]."""
        return self.EA / self.L

    @property
    def rigidez_flexion(self) -> float:
        """Rigidez a flexión básica 4EI/L [kNm/rad]."""
        return 4 * self.EI / self.L

    # =========================================================================
    # MATRICES DE TRANSFORMACIÓN
    # =========================================================================

    @property
    def T(self) -> NDArray[np.float64]:
        """
        Matriz de transformación 3x3 (local → global).

        Transforma vectores [ux, uy, θz] del sistema local al global.
        """
        return matriz_transformacion_barra(self.angulo)

    @property
    def T6(self) -> NDArray[np.float64]:
        """
        Matriz de transformación 6x6 para ambos extremos.

        Transforma [uxi, uyi, θzi, uxj, uyj, θzj] de local a global.
        """
        return matriz_transformacion_barra_6x6(self.angulo)

    @property
    def cosenos_directores(self) -> tuple[float, float]:
        """
        Cosenos directores de la barra.

        Returns:
            Tupla (cos(θ), sin(θ))
        """
        return (math.cos(self.angulo), math.sin(self.angulo))

    # =========================================================================
    # ESFUERZOS INTERNOS
    # =========================================================================

    def N(self, x: float) -> float:
        """
        Esfuerzo axil en la posición x [kN].

        Args:
            x: Posición a lo largo de la barra desde nudo_i [m]

        Returns:
            Esfuerzo axil (positivo = tracción)
        """
        self._validar_posicion(x)
        return self._N(x)

    def V(self, x: float) -> float:
        """
        Esfuerzo cortante en la posición x [kN].

        Args:
            x: Posición a lo largo de la barra desde nudo_i [m]

        Returns:
            Esfuerzo cortante
        """
        self._validar_posicion(x)
        return self._V(x)

    def M(self, x: float) -> float:
        """
        Momento flector en la posición x [kNm].

        Args:
            x: Posición a lo largo de la barra desde nudo_i [m]

        Returns:
            Momento flector (positivo = tracciona fibra inferior)
        """
        self._validar_posicion(x)
        return self._M(x)

    def _validar_posicion(self, x: float) -> None:
        """Valida que x esté dentro de la longitud de la barra."""
        if x < -LENGTH_TOLERANCE or x > self.L + LENGTH_TOLERANCE:
            raise ValueError(
                f"Posición x={x:.3f} fuera de rango [0, {self.L:.3f}] para barra {self.id}"
            )

    def asignar_esfuerzos(
        self,
        N: Callable[[float], float],
        V: Callable[[float], float],
        M: Callable[[float], float]
    ) -> None:
        """
        Asigna las funciones de esfuerzos internos.

        Args:
            N: Función N(x) de esfuerzo axil
            V: Función V(x) de esfuerzo cortante
            M: Función M(x) de momento flector
        """
        self._N = N
        self._V = V
        self._M = M

    def esfuerzos_en_extremos(self) -> dict[str, tuple[float, float]]:
        """
        Retorna los esfuerzos en ambos extremos de la barra.

        Returns:
            Diccionario con claves 'N', 'V', 'M' y valores (valor_i, valor_j)
        """
        return {
            'N': (self.N(0), self.N(self.L)),
            'V': (self.V(0), self.V(self.L)),
            'M': (self.M(0), self.M(self.L)),
        }

    def esfuerzos_maximos(self, n_puntos: int = 21) -> dict[str, tuple[float, float]]:
        """
        Calcula los esfuerzos máximos (absolutos) en la barra.

        Args:
            n_puntos: Número de puntos para muestrear la barra

        Returns:
            Diccionario con claves 'N', 'V', 'M' y valores (max_valor, posicion_x)
        """
        x_vals = np.linspace(0, self.L, n_puntos)

        N_vals = [abs(self.N(x)) for x in x_vals]
        V_vals = [abs(self.V(x)) for x in x_vals]
        M_vals = [abs(self.M(x)) for x in x_vals]

        return {
            'N': (max(N_vals), x_vals[np.argmax(N_vals)]),
            'V': (max(V_vals), x_vals[np.argmax(V_vals)]),
            'M': (max(M_vals), x_vals[np.argmax(M_vals)]),
        }

    # =========================================================================
    # CARGAS
    # =========================================================================

    def agregar_carga(self, carga: Carga) -> None:
        """
        Agrega una carga a la barra.

        Args:
            carga: Carga a agregar
        """
        carga.barra = self
        self.cargas.append(carga)

    def remover_carga(self, carga: Carga) -> bool:
        """
        Remueve una carga de la barra.

        Args:
            carga: Carga a remover

        Returns:
            True si se removió, False si no existía
        """
        if carga in self.cargas:
            self.cargas.remove(carga)
            carga.barra = None
            return True
        return False

    def limpiar_cargas(self) -> None:
        """Remueve todas las cargas de la barra."""
        for carga in self.cargas:
            carga.barra = None
        self.cargas.clear()

    # =========================================================================
    # COORDENADAS
    # =========================================================================

    def punto_en_barra(self, x: float) -> tuple[float, float]:
        """
        Coordenadas globales de un punto a distancia x desde nudo_i.

        Args:
            x: Distancia desde nudo_i a lo largo de la barra [m]

        Returns:
            Tupla (X_global, Y_global)
        """
        self._validar_posicion(x)
        t = x / self.L if self.L > 0 else 0
        return (
            self.nudo_i.x + t * self.dx,
            self.nudo_i.y + t * self.dy,
        )

    def local_a_global(self, u_local: float, v_local: float) -> tuple[float, float]:
        """
        Transforma componentes de coordenadas locales a globales.

        TERNA GLOBAL: X+ derecha, Y+ abajo, giro+ horario

        Sistema local:
        - u_local: a lo largo de la barra (de i a j)
        - v_local: perpendicular HORARIO (+90°) a la barra

        Para una barra horizontal (i a la izquierda, j a la derecha):
        - u_local positivo -> X_global positivo (derecha)
        - v_local positivo -> Y_global positivo (abajo)

        Args:
            u_local: Componente en dirección de la barra (eje local x')
            v_local: Componente perpendicular horario a la barra (eje local y')

        Returns:
            Tupla (U_global, V_global)
        """
        c, s = self.cosenos_directores
        return (
            c * u_local - s * v_local,
            s * u_local + c * v_local,
        )

    def global_a_local(self, u_global: float, v_global: float) -> tuple[float, float]:
        """
        Transforma desplazamientos de coordenadas globales a locales.

        Args:
            u_global: Componente en dirección X global
            v_global: Componente en dirección Y global

        Returns:
            Tupla (u_local, v_local)
        """
        c, s = self.cosenos_directores
        return (
            c * u_global + s * v_global,
            -s * u_global + c * v_global,
        )

    # =========================================================================
    # ARTICULACIONES
    # =========================================================================

    def articular_extremo_i(self) -> None:
        """Libera el momento en el extremo i (crea articulación)."""
        self.articulacion_i = True

    def articular_extremo_j(self) -> None:
        """Libera el momento en el extremo j (crea articulación)."""
        self.articulacion_j = True

    @property
    def tiene_articulacion(self) -> bool:
        """True si la barra tiene al menos una articulación interna."""
        return self.articulacion_i or self.articulacion_j

    # =========================================================================
    # REPRESENTACIÓN
    # =========================================================================

    def __str__(self) -> str:
        """Representación legible de la barra."""
        nombre_str = f" '{self.nombre}'" if self.nombre else ""
        return (
            f"Barra {self.id}{nombre_str}: "
            f"Nudo {self.nudo_i.id} → Nudo {self.nudo_j.id} "
            f"(L={self.L:.3f}m, θ={self.angulo_grados:.1f}°)"
        )

    def __hash__(self) -> int:
        """Hash basado en el ID."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Igualdad basada en el ID."""
        if not isinstance(other, Barra):
            return NotImplemented
        return self.id == other.id


# =============================================================================
# FUNCIONES DE CONVENIENCIA
# =============================================================================

def crear_barra(
    id: int,
    nudo_i: Nudo,
    nudo_j: Nudo,
    material: Material,
    seccion: Seccion,
    nombre: str = ""
) -> Barra:
    """
    Crea una barra con los parámetros especificados.

    Esta función es un alias simple del constructor de Barra.

    Args:
        id: Identificador único
        nudo_i: Nudo inicial
        nudo_j: Nudo final
        material: Material de la barra
        seccion: Sección transversal
        nombre: Nombre opcional

    Returns:
        Nueva instancia de Barra
    """
    return Barra(
        id=id,
        nudo_i=nudo_i,
        nudo_j=nudo_j,
        material=material,
        seccion=seccion,
        nombre=nombre,
    )
