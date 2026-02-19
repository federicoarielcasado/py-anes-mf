"""
Solver del Sistema de Ecuaciones de Compatibilidad Elástica (SECE).

Resuelve el sistema [F]·{X} = -{e₀} para obtener los valores
de los redundantes.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from src.utils.constants import (
    COMPATIBILITY_TOLERANCE,
    CONDITION_NUMBER_WARNING,
)


@dataclass
class SolucionSECE:
    """
    Resultado de la resolución del SECE.

    Attributes:
        X: Vector de redundantes resueltos [n]
        residual: Norma del residual ||[F]{X} + {e₀}||
        condicionamiento: Número de condición de la matriz F
        convergio: True si la solución es válida
        advertencias: Lista de advertencias generadas
    """
    X: NDArray[np.float64]
    residual: float
    condicionamiento: float
    convergio: bool
    advertencias: List[str]

    def Xi(self, i: int) -> float:
        """
        Obtiene el valor del redundante Xi.

        Args:
            i: Índice del redundante (1-indexed)

        Returns:
            Valor de Xi
        """
        return self.X[i - 1]

    @property
    def es_valida(self) -> bool:
        """True si la solución es numéricamente válida."""
        return (
            self.convergio and
            self.residual < COMPATIBILITY_TOLERANCE and
            np.all(np.isfinite(self.X))
        )


class SolverSECE:
    """
    Resuelve el Sistema de Ecuaciones de Compatibilidad Elástica.

    El SECE tiene la forma:
        [F]·{X} = -{e₀}

    Donde:
        [F]: Matriz de flexibilidad (simétrica, definida positiva)
        {X}: Vector de redundantes (incógnitas)
        {e₀}: Vector de términos independientes

    La solución da los valores de los redundantes X₁, X₂, ..., Xₙ
    que aseguran compatibilidad de deformaciones.
    """

    def __init__(
        self,
        F: NDArray[np.float64],
        e0: NDArray[np.float64],
        eh: Optional[NDArray[np.float64]] = None,
    ):
        """
        Inicializa el solver.

        Args:
            F: Matriz de flexibilidad [n×n]
            e0: Vector de términos independientes [n]
            eh: Vector de desplazamientos impuestos en hiperestático [n]
                (por defecto 0, salvo para movimientos impuestos)
        """
        self.F = F
        self.e0 = e0
        self.eh = eh if eh is not None else np.zeros_like(e0)
        self.n = len(e0)

        self._X: Optional[NDArray] = None
        self._advertencias: List[str] = []

    def resolver(self, metodo: str = "directo") -> SolucionSECE:
        """
        Resuelve el SECE.

        El sistema es: e₀ + [F]·{X} = eₕ
        Reordenando: [F]·{X} = eₕ - e₀ = -e₀ (si eₕ = 0)

        Args:
            metodo: Método de resolución
                - "directo": numpy.linalg.solve (recomendado)
                - "cholesky": Descomposición de Cholesky
                - "iterativo": Método iterativo (para sistemas grandes)

        Returns:
            SolucionSECE con los redundantes resueltos
        """
        self._advertencias = []

        # Verificar condicionamiento
        condicionamiento = np.linalg.cond(self.F)
        if condicionamiento > CONDITION_NUMBER_WARNING:
            self._advertencias.append(
                f"Matriz mal condicionada (cond={condicionamiento:.2e}). "
                "Considere reseleccionar redundantes."
            )

        # Verificar simetría
        if not np.allclose(self.F, self.F.T, atol=1e-10):
            self._advertencias.append(
                "Matriz de flexibilidad no es simétrica. "
                "Verifique el cálculo de coeficientes."
            )

        # Verificar diagonal positiva
        if np.any(np.diag(self.F) <= 0):
            self._advertencias.append(
                "Elementos diagonales no positivos en F. "
                "Esto indica un error en el cálculo de flexibilidades."
            )

        # Término derecho: b = eh - e0
        b = self.eh - self.e0

        # Resolver según método
        try:
            if metodo == "directo":
                self._X = self._resolver_directo(b)
            elif metodo == "cholesky":
                self._X = self._resolver_cholesky(b)
            elif metodo == "iterativo":
                self._X = self._resolver_iterativo(b)
            else:
                raise ValueError(f"Método desconocido: {metodo}")

            convergio = True

        except np.linalg.LinAlgError as e:
            self._advertencias.append(f"Error en resolución: {e}")
            self._X = np.zeros(self.n)
            convergio = False

        # Calcular residual
        residual = np.linalg.norm(self.F @ self._X - b)

        if residual > COMPATIBILITY_TOLERANCE:
            self._advertencias.append(
                f"Residual alto: {residual:.2e}. "
                "La solución puede no ser precisa."
            )

        return SolucionSECE(
            X=self._X,
            residual=residual,
            condicionamiento=condicionamiento,
            convergio=convergio,
            advertencias=self._advertencias,
        )

    def _resolver_directo(self, b: NDArray) -> NDArray:
        """
        Resolución directa con numpy.linalg.solve.

        Si la matriz es singular, usa mínimos cuadrados (lstsq).

        Args:
            b: Término derecho del sistema

        Returns:
            Vector solución X
        """
        try:
            return np.linalg.solve(self.F, b)
        except np.linalg.LinAlgError:
            # Si es singular, usar mínimos cuadrados
            self._advertencias.append(
                "Matriz singular, usando mínimos cuadrados (lstsq)."
            )
            X, residuals, rank, s = np.linalg.lstsq(self.F, b, rcond=None)
            return X

    def _resolver_cholesky(self, b: NDArray) -> NDArray:
        """
        Resolución mediante descomposición de Cholesky.

        Aprovecha que F es simétrica y definida positiva.
        F = L·Lᵀ → L·y = b, Lᵀ·x = y

        Args:
            b: Término derecho del sistema

        Returns:
            Vector solución X
        """
        try:
            L = np.linalg.cholesky(self.F)
            y = np.linalg.solve(L, b)
            X = np.linalg.solve(L.T, y)
            return X
        except np.linalg.LinAlgError:
            # Si Cholesky falla, usar método directo
            self._advertencias.append(
                "Cholesky falló (matriz no definida positiva). "
                "Usando método directo."
            )
            return self._resolver_directo(b)

    def _resolver_iterativo(self, b: NDArray, tol: float = 1e-10, max_iter: int = 1000) -> NDArray:
        """
        Resolución iterativa (Gradiente Conjugado).

        Útil para sistemas grandes donde la descomposición directa
        es costosa.

        Args:
            b: Término derecho del sistema
            tol: Tolerancia de convergencia
            max_iter: Máximo número de iteraciones

        Returns:
            Vector solución X
        """
        from scipy.sparse.linalg import cg

        X, info = cg(self.F, b, tol=tol, maxiter=max_iter)

        if info > 0:
            self._advertencias.append(
                f"Método iterativo no convergió en {info} iteraciones."
            )
        elif info < 0:
            self._advertencias.append(
                "Error en método iterativo."
            )

        return X

    def verificar_solucion(self) -> Tuple[bool, dict]:
        """
        Verifica que la solución sea válida.

        Comprueba:
        1. Residual del sistema
        2. Compatibilidad de deformaciones
        3. Valores finitos

        Returns:
            Tupla (es_valida, detalles)
        """
        if self._X is None:
            return False, {"error": "No se ha resuelto el sistema"}

        b = self.eh - self.e0
        residual = np.linalg.norm(self.F @ self._X - b)
        relativo = residual / (np.linalg.norm(b) + 1e-15)

        detalles = {
            "residual_absoluto": residual,
            "residual_relativo": relativo,
            "valores_finitos": np.all(np.isfinite(self._X)),
            "condicionamiento": np.linalg.cond(self.F),
        }

        es_valida = (
            residual < COMPATIBILITY_TOLERANCE and
            detalles["valores_finitos"]
        )

        return es_valida, detalles


def resolver_sece(
    F: NDArray[np.float64],
    e0: NDArray[np.float64],
    eh: Optional[NDArray[np.float64]] = None,
    metodo: str = "directo",
) -> SolucionSECE:
    """
    Función de conveniencia para resolver el SECE.

    Args:
        F: Matriz de flexibilidad
        e0: Vector de términos independientes
        eh: Vector de desplazamientos impuestos (opcional)
        metodo: Método de resolución

    Returns:
        SolucionSECE con los resultados
    """
    solver = SolverSECE(F, e0, eh)
    return solver.resolver(metodo)
