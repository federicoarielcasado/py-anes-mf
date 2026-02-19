"""
Panel de propiedades para editar elementos seleccionados.
"""

from typing import List, Tuple, Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QDoubleSpinBox,
    QSpinBox,
    QSpacerItem,
    QSizePolicy,
    QCheckBox,
    QFrame,
)
from PyQt6.QtCore import pyqtSignal, Qt


class PropertiesPanel(QWidget):
    """
    Panel para ver y editar propiedades de elementos seleccionados.

    Muestra diferentes controles según el tipo de elemento seleccionado:
    - Nudo: coordenadas, nombre, vínculo
    - Barra: material, sección, articulaciones
    - Carga: tipo, magnitud, posición

    También incluye:
    - Entrada paramétrica para crear nudos/barras con precisión
    - Configuración de grilla y snap
    """

    # Señales
    property_changed = pyqtSignal()
    create_node_requested = pyqtSignal(float, float)  # x, y
    create_bar_requested = pyqtSignal(int, int)  # nudo_i_id, nudo_j_id
    grid_settings_changed = pyqtSignal(float, bool)  # grid_size, snap_enabled

    def __init__(self, parent=None):
        super().__init__(parent)

        self._selected_items: List[Tuple[str, int]] = []
        self._canvas = None  # Referencia al canvas

        self._setup_ui()

    def set_canvas(self, canvas):
        """Establece referencia al canvas para entrada paramétrica."""
        self._canvas = canvas

    def _setup_ui(self):
        """Configura la interfaz del panel."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # =====================================================================
        # GRUPO: Configuración de Grilla
        # =====================================================================
        self.group_grilla = QGroupBox("Grilla y Snap")
        grilla_layout = QFormLayout(self.group_grilla)

        self.spin_grid_size = QDoubleSpinBox()
        self.spin_grid_size.setRange(0.1, 10.0)
        self.spin_grid_size.setValue(1.0)
        self.spin_grid_size.setDecimals(2)
        self.spin_grid_size.setSuffix(" m")
        self.spin_grid_size.setSingleStep(0.5)
        self.spin_grid_size.valueChanged.connect(self._on_grid_settings_changed)
        grilla_layout.addRow("Tamaño celda:", self.spin_grid_size)

        self.check_snap = QCheckBox("Snap to Grid (G)")
        self.check_snap.setChecked(True)
        self.check_snap.stateChanged.connect(self._on_grid_settings_changed)
        grilla_layout.addRow("", self.check_snap)

        layout.addWidget(self.group_grilla)

        # =====================================================================
        # GRUPO: Entrada Paramétrica de Nudos
        # =====================================================================
        self.group_crear_nudo = QGroupBox("Crear Nudo (Paramétrico)")
        crear_nudo_layout = QFormLayout(self.group_crear_nudo)

        self.spin_nuevo_x = QDoubleSpinBox()
        self.spin_nuevo_x.setRange(-1000, 1000)
        self.spin_nuevo_x.setDecimals(3)
        self.spin_nuevo_x.setSuffix(" m")
        self.spin_nuevo_x.setValue(0.0)
        crear_nudo_layout.addRow("X:", self.spin_nuevo_x)

        self.spin_nuevo_y = QDoubleSpinBox()
        self.spin_nuevo_y.setRange(-1000, 1000)
        self.spin_nuevo_y.setDecimals(3)
        self.spin_nuevo_y.setSuffix(" m")
        self.spin_nuevo_y.setValue(0.0)
        crear_nudo_layout.addRow("Y:", self.spin_nuevo_y)

        self.btn_crear_nudo = QPushButton("Crear Nudo")
        self.btn_crear_nudo.clicked.connect(self._on_crear_nudo)
        crear_nudo_layout.addRow("", self.btn_crear_nudo)

        layout.addWidget(self.group_crear_nudo)

        # =====================================================================
        # GRUPO: Entrada Paramétrica de Barras
        # =====================================================================
        self.group_crear_barra = QGroupBox("Crear Barra (Paramétrico)")
        crear_barra_layout = QFormLayout(self.group_crear_barra)

        self.spin_barra_nudo_i = QSpinBox()
        self.spin_barra_nudo_i.setRange(1, 9999)
        self.spin_barra_nudo_i.setPrefix("N")
        crear_barra_layout.addRow("Nudo inicial:", self.spin_barra_nudo_i)

        self.spin_barra_nudo_j = QSpinBox()
        self.spin_barra_nudo_j.setRange(1, 9999)
        self.spin_barra_nudo_j.setPrefix("N")
        crear_barra_layout.addRow("Nudo final:", self.spin_barra_nudo_j)

        self.btn_crear_barra = QPushButton("Crear Barra")
        self.btn_crear_barra.clicked.connect(self._on_crear_barra)
        crear_barra_layout.addRow("", self.btn_crear_barra)

        layout.addWidget(self.group_crear_barra)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # =====================================================================
        # GRUPO: Propiedades del elemento seleccionado
        # =====================================================================

        # Etiqueta de selección
        self.label_seleccion = QLabel("Sin selección")
        self.label_seleccion.setStyleSheet("font-weight: bold; padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.label_seleccion)

        # Grupo de propiedades de nudo
        self.group_nudo = QGroupBox("Propiedades del Nudo")
        nudo_layout = QFormLayout(self.group_nudo)

        self.spin_nudo_x = QDoubleSpinBox()
        self.spin_nudo_x.setRange(-1000, 1000)
        self.spin_nudo_x.setDecimals(3)
        self.spin_nudo_x.setSuffix(" m")
        nudo_layout.addRow("X:", self.spin_nudo_x)

        self.spin_nudo_y = QDoubleSpinBox()
        self.spin_nudo_y.setRange(-1000, 1000)
        self.spin_nudo_y.setDecimals(3)
        self.spin_nudo_y.setSuffix(" m")
        nudo_layout.addRow("Y:", self.spin_nudo_y)

        self.edit_nudo_nombre = QLineEdit()
        self.edit_nudo_nombre.setPlaceholderText("Nombre opcional")
        nudo_layout.addRow("Nombre:", self.edit_nudo_nombre)

        self.combo_vinculo = QComboBox()
        self.combo_vinculo.addItems([
            "Sin vínculo",
            "Empotramiento",
            "Apoyo Fijo",
            "Rodillo Horizontal",
            "Rodillo Vertical",
            "Guía Horizontal",
            "Guía Vertical",
        ])
        nudo_layout.addRow("Vínculo:", self.combo_vinculo)

        self.group_nudo.setVisible(False)
        layout.addWidget(self.group_nudo)

        # Grupo de propiedades de barra
        self.group_barra = QGroupBox("Propiedades de la Barra")
        barra_layout = QFormLayout(self.group_barra)

        self.label_longitud = QLabel("0.000 m")
        barra_layout.addRow("Longitud:", self.label_longitud)

        self.label_angulo = QLabel("0.00°")
        barra_layout.addRow("Ángulo:", self.label_angulo)

        self.combo_material = QComboBox()
        self.combo_material.addItems([
            "Acero A-36",
            "Acero S235",
            "Acero S275",
            "Acero S355",
            "Hormigón H-25",
            "Hormigón H-30",
        ])
        barra_layout.addRow("Material:", self.combo_material)

        self.combo_seccion = QComboBox()
        self.combo_seccion.addItems([
            "IPE 200",
            "IPE 220",
            "IPE 240",
            "IPE 270",
            "IPE 300",
            "HEA 200",
            "HEA 220",
        ])
        barra_layout.addRow("Sección:", self.combo_seccion)

        # Articulaciones
        self.btn_art_i = QPushButton("Articulación en i")
        self.btn_art_i.setCheckable(True)
        barra_layout.addRow("", self.btn_art_i)

        self.btn_art_j = QPushButton("Articulación en j")
        self.btn_art_j.setCheckable(True)
        barra_layout.addRow("", self.btn_art_j)

        self.group_barra.setVisible(False)
        layout.addWidget(self.group_barra)

        # Grupo de cargas
        self.group_carga = QGroupBox("Agregar Carga")
        carga_layout = QFormLayout(self.group_carga)

        self.combo_tipo_carga = QComboBox()
        self.combo_tipo_carga.addItems([
            "Puntual en nudo",
            "Puntual en barra",
            "Distribuida uniforme",
        ])
        carga_layout.addRow("Tipo:", self.combo_tipo_carga)

        self.spin_carga_valor = QDoubleSpinBox()
        self.spin_carga_valor.setRange(-10000, 10000)
        self.spin_carga_valor.setDecimals(2)
        self.spin_carga_valor.setValue(-10.0)
        self.spin_carga_valor.setSuffix(" kN")
        carga_layout.addRow("Valor:", self.spin_carga_valor)

        self.spin_carga_pos = QDoubleSpinBox()
        self.spin_carga_pos.setRange(0, 100)
        self.spin_carga_pos.setDecimals(2)
        self.spin_carga_pos.setSuffix(" m")
        carga_layout.addRow("Posición:", self.spin_carga_pos)

        self.btn_agregar_carga = QPushButton("Agregar Carga")
        carga_layout.addRow("", self.btn_agregar_carga)

        self.group_carga.setVisible(False)
        layout.addWidget(self.group_carga)

        # Espaciador
        layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Botón aplicar
        self.btn_aplicar = QPushButton("Aplicar Cambios")
        self.btn_aplicar.setEnabled(False)
        layout.addWidget(self.btn_aplicar)

    def _on_grid_settings_changed(self):
        """Maneja cambios en la configuración de grilla."""
        grid_size = self.spin_grid_size.value()
        snap_enabled = self.check_snap.isChecked()

        # Actualizar canvas si está disponible
        if self._canvas is not None:
            self._canvas.grid_size = grid_size
            self._canvas.snap_enabled = snap_enabled
            self._canvas.viewport().update()

        self.grid_settings_changed.emit(grid_size, snap_enabled)

    def _on_crear_nudo(self):
        """Crea un nudo con las coordenadas especificadas."""
        x = self.spin_nuevo_x.value()
        y = self.spin_nuevo_y.value()

        if self._canvas is not None:
            nudo = self._canvas.create_node_parametric(x, y)
            if nudo:
                # Actualizar spinbox de barra con el nuevo nudo
                self.spin_barra_nudo_j.setValue(nudo.id)

        self.create_node_requested.emit(x, y)

    def _on_crear_barra(self):
        """Crea una barra entre los nudos especificados."""
        nudo_i_id = self.spin_barra_nudo_i.value()
        nudo_j_id = self.spin_barra_nudo_j.value()

        if nudo_i_id == nudo_j_id:
            return  # No crear barra entre el mismo nudo

        if self._canvas is not None:
            self._canvas.create_bar_parametric(nudo_i_id, nudo_j_id)

        self.create_bar_requested.emit(nudo_i_id, nudo_j_id)

    def update_selection(self, selected_items: List[Tuple[str, int]]):
        """
        Actualiza el panel según la selección actual.

        Args:
            selected_items: Lista de tuplas (tipo, id)
        """
        self._selected_items = selected_items

        # Ocultar todos los grupos de selección
        self.group_nudo.setVisible(False)
        self.group_barra.setVisible(False)
        self.group_carga.setVisible(False)
        self.btn_aplicar.setEnabled(False)

        if not selected_items:
            self.label_seleccion.setText("Sin selección")
            return

        if len(selected_items) == 1:
            tipo, id_ = selected_items[0]

            if tipo == "nudo":
                self.label_seleccion.setText(f"Nudo N{id_}")
                self.group_nudo.setVisible(True)
                self.group_carga.setVisible(True)
                self.btn_aplicar.setEnabled(True)

                # Cargar datos del nudo si hay canvas
                if self._canvas is not None:
                    nudo = self._canvas.modelo.obtener_nudo(id_)
                    if nudo:
                        self.spin_nudo_x.setValue(nudo.x)
                        self.spin_nudo_y.setValue(nudo.y)
                        self.edit_nudo_nombre.setText(nudo.nombre or "")

            elif tipo == "barra":
                self.label_seleccion.setText(f"Barra B{id_}")
                self.group_barra.setVisible(True)
                self.group_carga.setVisible(True)
                self.btn_aplicar.setEnabled(True)

                # Cargar datos de la barra si hay canvas
                if self._canvas is not None:
                    barra = self._canvas.modelo.obtener_barra(id_)
                    if barra:
                        import math
                        self.label_longitud.setText(f"{barra.L:.3f} m")
                        self.label_angulo.setText(f"{math.degrees(barra.angulo):.2f}°")
                        self.btn_art_i.setChecked(barra.articulacion_i)
                        self.btn_art_j.setChecked(barra.articulacion_j)

        else:
            self.label_seleccion.setText(f"{len(selected_items)} elementos seleccionados")

    def sync_snap_state(self, snap_enabled: bool):
        """Sincroniza el estado del checkbox de snap con el canvas."""
        self.check_snap.blockSignals(True)
        self.check_snap.setChecked(snap_enabled)
        self.check_snap.blockSignals(False)

    def clear(self):
        """Limpia el panel."""
        self._selected_items.clear()
        self.update_selection([])
