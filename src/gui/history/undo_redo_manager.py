"""
Gestor de Undo/Redo basado en el patrón Memento.

Estrategia: snapshot completo del modelo en JSON en cada mutación.
Es simple, robusto y consistente con el serializer existente.
El overhead es despreciable (modelos < 100 barras → snapshots < 50 KB).

Uso típico:
    manager = UndoRedoManager(max_history=50)
    manager.guardar_estado(modelo)          # Antes de una mutación
    # ... mutación del modelo ...
    manager.marcar_accion_completada()      # Después de la mutación

    # Deshacer
    snapshot = manager.deshacer()
    if snapshot:
        nuevo_modelo = cargar_desde_snapshot(snapshot)

    # Rehacer
    snapshot = manager.rehacer()
    if snapshot:
        nuevo_modelo = cargar_desde_snapshot(snapshot)
"""

from __future__ import annotations

import json
from collections import deque
from typing import Callable, Deque, List, Optional

from src.domain.model.modelo_estructural import ModeloEstructural


class UndoRedoManager:
    """
    Gestor de historial de acciones Undo/Redo basado en snapshots JSON.

    El modelo se serializa a JSON antes de cada mutación, generando una
    pila de estados anteriores (undo) y futuros (redo).

    Attributes:
        max_historial: Número máximo de estados en cada pila
        _puede_deshacer_changed: Callback llamado cuando cambia `puede_deshacer`
        _puede_rehacer_changed: Callback llamado cuando cambia `puede_rehacer`
    """

    def __init__(
        self,
        max_historial: int = 50,
        puede_deshacer_changed: Optional[Callable[[bool], None]] = None,
        puede_rehacer_changed: Optional[Callable[[bool], None]] = None,
    ) -> None:
        self.max_historial = max_historial

        # Callbacks para actualizar UI (habilitar/deshabilitar botones)
        self._puede_deshacer_changed = puede_deshacer_changed
        self._puede_rehacer_changed = puede_rehacer_changed

        # Pilas de snapshots (serialización JSON del modelo)
        self._pila_undo: Deque[str] = deque(maxlen=max_historial)
        self._pila_redo: Deque[str] = deque(maxlen=max_historial)

    # ------------------------------------------------------------------
    # Estado actual
    # ------------------------------------------------------------------

    @property
    def puede_deshacer(self) -> bool:
        """True si hay acciones que se pueden deshacer."""
        return len(self._pila_undo) > 0

    @property
    def puede_rehacer(self) -> bool:
        """True si hay acciones que se pueden rehacer."""
        return len(self._pila_redo) > 0

    # ------------------------------------------------------------------
    # API principal
    # ------------------------------------------------------------------

    def guardar_estado(self, modelo: ModeloEstructural) -> None:
        """
        Guarda el estado actual del modelo en la pila de undo.

        Debe llamarse ANTES de realizar una mutación sobre el modelo.
        Limpia la pila de redo (una nueva acción invalida los futuros).

        Args:
            modelo: El modelo en su estado PREVIO a la mutación.
        """
        snapshot = self._serializar(modelo)
        pudo_deshacer_antes = self.puede_deshacer
        pudo_rehacer_antes = self.puede_rehacer

        self._pila_undo.append(snapshot)
        self._pila_redo.clear()  # Nueva acción invalida el redo

        self._notificar_cambios(pudo_deshacer_antes, pudo_rehacer_antes)

    def deshacer(self) -> Optional[ModeloEstructural]:
        """
        Deshace la última acción.

        Returns:
            El modelo restaurado al estado anterior, o None si no hay nada que deshacer.
        """
        if not self._pila_undo:
            return None

        pudo_deshacer_antes = self.puede_deshacer
        pudo_rehacer_antes = self.puede_rehacer

        snapshot = self._pila_undo.pop()
        # El snapshot actual del modelo se mueve al redo (lo hace el caller
        # pasando el modelo actual antes de restaurar)
        self._pila_redo.append(snapshot)

        modelo = self._deserializar(snapshot)

        self._notificar_cambios(pudo_deshacer_antes, pudo_rehacer_antes)
        return modelo

    def rehacer(self) -> Optional[ModeloEstructural]:
        """
        Rehace la última acción deshecha.

        Returns:
            El modelo restaurado al estado siguiente, o None si no hay nada que rehacer.
        """
        if not self._pila_redo:
            return None

        pudo_deshacer_antes = self.puede_deshacer
        pudo_rehacer_antes = self.puede_rehacer

        snapshot = self._pila_redo.pop()
        self._pila_undo.append(snapshot)

        modelo = self._deserializar(snapshot)

        self._notificar_cambios(pudo_deshacer_antes, pudo_rehacer_antes)
        return modelo

    def limpiar(self) -> None:
        """Elimina todo el historial (p.ej. al abrir un nuevo archivo)."""
        pudo_deshacer_antes = self.puede_deshacer
        pudo_rehacer_antes = self.puede_rehacer
        self._pila_undo.clear()
        self._pila_redo.clear()
        self._notificar_cambios(pudo_deshacer_antes, pudo_rehacer_antes)

    # ------------------------------------------------------------------
    # Serialización / Deserialización
    # ------------------------------------------------------------------

    @staticmethod
    def _serializar(modelo: ModeloEstructural) -> str:
        """Convierte el modelo a JSON en memoria (sin escribir a disco)."""
        from src.data.proyecto_serializer import _modelo_a_dict
        data = _modelo_a_dict(modelo)
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def _deserializar(snapshot: str) -> ModeloEstructural:
        """Restaura un modelo desde un JSON en memoria."""
        from src.data.proyecto_serializer import _dict_a_modelo
        data = json.loads(snapshot)
        return _dict_a_modelo(data)

    # ------------------------------------------------------------------
    # Notificaciones a la UI
    # ------------------------------------------------------------------

    def _notificar_cambios(
        self,
        pudo_deshacer_antes: bool,
        pudo_rehacer_antes: bool,
    ) -> None:
        """Llama los callbacks si el estado de deshacer/rehacer cambió."""
        if self._puede_deshacer_changed is not None:
            if self.puede_deshacer != pudo_deshacer_antes:
                self._puede_deshacer_changed(self.puede_deshacer)

        if self._puede_rehacer_changed is not None:
            if self.puede_rehacer != pudo_rehacer_antes:
                self._puede_rehacer_changed(self.puede_rehacer)
