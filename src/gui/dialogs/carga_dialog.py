"""
Diálogos para agregar cargas a la estructura.
"""

from typing import Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QComboBox,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from src.domain.model.modelo_estructural import ModeloEstructural
from src.domain.entities.nudo import Nudo
from src.domain.entities.barra import Barra
from src.domain.entities.carga import (
    CargaPuntualNudo,
    CargaPuntualBarra,
    CargaDistribuida,
)


class CargaPuntualNudoDialog(QDialog):
    """
    Diálogo para agregar una carga puntual en un nudo.

    Permite al usuario seleccionar un nudo e ingresar las componentes
    Fx, Fy, y Mz de la carga.
    """

    def __init__(self, modelo: ModeloEstructural, parent=None):
        super().__init__(parent)
        self.modelo = modelo
        self.carga_creada: Optional[CargaPuntualNudo] = None

        self.setWindowTitle("Agregar Carga Puntual en Nudo")
        self.setMinimumWidth(400)

        self._init_ui()

    def _init_ui(self):
        """Inicializa la interfaz de usuario."""
        layout = QVBoxLayout(self)

        # Grupo de selección de nudo
        group_nudo = QGroupBox("Selección de Nudo")
        form_nudo = QFormLayout()

        self.combo_nudo = QComboBox()
        self._cargar_nudos()
        form_nudo.addRow("Nudo:", self.combo_nudo)

        group_nudo.setLayout(form_nudo)
        layout.addWidget(group_nudo)

        # Grupo de componentes de carga
        group_carga = QGroupBox("Componentes de la Carga")
        form_carga = QFormLayout()

        # Fx (horizontal, positivo a la derecha)
        self.spin_fx = QDoubleSpinBox()
        self.spin_fx.setRange(-10000, 10000)
        self.spin_fx.setDecimals(2)
        self.spin_fx.setSuffix(" kN")
        self.spin_fx.setValue(0.0)
        form_carga.addRow("Fx (→ +):", self.spin_fx)

        # Fy (vertical, positivo hacia arriba)
        self.spin_fy = QDoubleSpinBox()
        self.spin_fy.setRange(-10000, 10000)
        self.spin_fy.setDecimals(2)
        self.spin_fy.setSuffix(" kN")
        self.spin_fy.setValue(0.0)
        form_carga.addRow("Fy (↑ +):", self.spin_fy)

        # Mz (momento, positivo antihorario)
        self.spin_mz = QDoubleSpinBox()
        self.spin_mz.setRange(-10000, 10000)
        self.spin_mz.setDecimals(2)
        self.spin_mz.setSuffix(" kNm")
        self.spin_mz.setValue(0.0)
        form_carga.addRow("Mz (⟲ +):", self.spin_mz)

        group_carga.setLayout(form_carga)
        layout.addWidget(group_carga)

        # Nota informativa
        label_nota = QLabel(
            "<i>Convención: Fx positivo → derecha, Fy positivo → arriba, "
            "Mz positivo → antihorario</i>"
        )
        label_nota.setWordWrap(True)
        label_nota.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(label_nota)

        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _cargar_nudos(self):
        """Carga los nudos disponibles en el ComboBox."""
        self.combo_nudo.clear()

        if self.modelo.num_nudos == 0:
            self.combo_nudo.addItem("(No hay nudos)", None)
            self.combo_nudo.setEnabled(False)
            return

        for nudo in self.modelo.nudos:
            texto = f"Nudo {nudo.id}"
            if nudo.nombre:
                texto += f" - {nudo.nombre}"
            texto += f" ({nudo.x:.2f}, {nudo.y:.2f})"
            self.combo_nudo.addItem(texto, nudo.id)

    def _on_accept(self):
        """Valida y crea la carga."""
        if self.combo_nudo.currentData() is None:
            QMessageBox.warning(
                self,
                "Error",
                "No hay nudos disponibles. Cree nudos primero."
            )
            return

        # Obtener valores
        nudo_id = self.combo_nudo.currentData()
        fx = self.spin_fx.value()
        fy = self.spin_fy.value()
        mz = self.spin_mz.value()

        # Validar que al menos una componente sea no nula
        if abs(fx) < 0.001 and abs(fy) < 0.001 and abs(mz) < 0.001:
            QMessageBox.warning(
                self,
                "Carga nula",
                "Al menos una componente debe ser diferente de cero."
            )
            return

        # Obtener nudo
        nudo = self.modelo.obtener_nudo(nudo_id)
        if nudo is None:
            QMessageBox.critical(self, "Error", f"Nudo {nudo_id} no encontrado.")
            return

        # Crear carga
        self.carga_creada = CargaPuntualNudo(
            nudo=nudo,
            Fx=fx,
            Fy=fy,
            Mz=mz
        )

        self.accept()


class CargaPuntualBarraDialog(QDialog):
    """
    Diálogo para agregar una carga puntual sobre una barra.

    Permite especificar la magnitud, posición y dirección de la carga.
    """

    def __init__(self, modelo: ModeloEstructural, parent=None):
        super().__init__(parent)
        self.modelo = modelo
        self.carga_creada: Optional[CargaPuntualBarra] = None

        self.setWindowTitle("Agregar Carga Puntual en Barra")
        self.setMinimumWidth(400)

        self._init_ui()

    def _init_ui(self):
        """Inicializa la interfaz de usuario."""
        layout = QVBoxLayout(self)

        # Grupo de selección de barra
        group_barra = QGroupBox("Selección de Barra")
        form_barra = QFormLayout()

        self.combo_barra = QComboBox()
        form_barra.addRow("Barra:", self.combo_barra)

        # Label informativo de longitud
        self.label_longitud = QLabel()
        form_barra.addRow("Longitud:", self.label_longitud)

        group_barra.setLayout(form_barra)
        layout.addWidget(group_barra)

        # Grupo de parámetros de carga
        group_carga = QGroupBox("Parámetros de la Carga")
        form_carga = QFormLayout()

        # Magnitud
        self.spin_p = QDoubleSpinBox()
        self.spin_p.setRange(0.01, 10000)
        self.spin_p.setDecimals(2)
        self.spin_p.setSuffix(" kN")
        self.spin_p.setValue(10.0)
        form_carga.addRow("Magnitud P:", self.spin_p)

        # Posición desde nudo i
        self.spin_a = QDoubleSpinBox()
        self.spin_a.setRange(0, 100)
        self.spin_a.setDecimals(3)
        self.spin_a.setSuffix(" m")
        self.spin_a.setValue(0.0)
        form_carga.addRow("Distancia 'a' desde nudo i:", self.spin_a)

        # Ángulo (en coordenadas locales de la barra)
        self.combo_angulo = QComboBox()
        self.combo_angulo.addItem("→ A lo largo de la barra (0°)", 0)
        self.combo_angulo.addItem("⟲ Perpendicular horaria (+90°)", 90)
        self.combo_angulo.addItem("⟳ Perpendicular antihoraria (-90°)", -90)
        self.combo_angulo.addItem("← Opuesta a la barra (180°)", 180)
        self.combo_angulo.addItem("Diagonal +45° (45°)", 45)
        self.combo_angulo.addItem("Diagonal -45° (-45°)", -45)
        form_carga.addRow("Dirección (local):", self.combo_angulo)

        # SpinBox personalizado para ángulo (opcional)
        self.spin_angulo = QDoubleSpinBox()
        self.spin_angulo.setRange(-360, 360)
        self.spin_angulo.setDecimals(1)
        self.spin_angulo.setSuffix("°")
        self.spin_angulo.setValue(90)
        self.combo_angulo.currentIndexChanged.connect(
            lambda: self.spin_angulo.setValue(self.combo_angulo.currentData())
        )
        form_carga.addRow("Ángulo personalizado:", self.spin_angulo)

        group_carga.setLayout(form_carga)
        layout.addWidget(group_carga)

        # Nota informativa
        label_nota = QLabel(
            "<b>Sistema de coordenadas locales:</b><br>"
            "• 0° = A lo largo de la barra (de i→j)<br>"
            "• +90° = Rotación horaria (⟲) desde la barra<br>"
            "• -90° = Rotación antihoraria (⟳) desde la barra<br>"
            "<br>"
            "<i>Ejemplo: Para barra horizontal (→), +90° apunta hacia abajo (↓)</i>"
        )
        label_nota.setWordWrap(True)
        label_nota.setStyleSheet("color: #444; padding: 8px; background: #f0f0f0; border-radius: 4px;")
        layout.addWidget(label_nota)

        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Conectar y cargar barras AL FINAL, después de crear TODOS los widgets
        self.combo_barra.currentIndexChanged.connect(self._on_barra_changed)
        self._cargar_barras()

        # Actualizar info inicial
        self._on_barra_changed()

    def _cargar_barras(self):
        """Carga las barras disponibles en el ComboBox."""
        self.combo_barra.clear()

        if self.modelo.num_barras == 0:
            self.combo_barra.addItem("(No hay barras)", None)
            self.combo_barra.setEnabled(False)
            return

        for barra in self.modelo.barras:
            texto = f"Barra {barra.id}: N{barra.nudo_i.id} → N{barra.nudo_j.id} (L={barra.L:.2f}m)"
            self.combo_barra.addItem(texto, barra.id)

    def _on_barra_changed(self):
        """Actualiza información cuando cambia la barra seleccionada."""
        if self.combo_barra.currentData() is None:
            self.label_longitud.setText("N/A")
            self.spin_a.setMaximum(0)
            return

        barra_id = self.combo_barra.currentData()
        barra = self.modelo.obtener_barra(barra_id)

        if barra:
            self.label_longitud.setText(f"{barra.L:.3f} m")
            self.spin_a.setMaximum(barra.L)
            self.spin_a.setValue(barra.L / 2)  # Por defecto, en el centro

    def _on_accept(self):
        """Valida y crea la carga."""
        if self.combo_barra.currentData() is None:
            QMessageBox.warning(
                self,
                "Error",
                "No hay barras disponibles. Cree barras primero."
            )
            return

        # Obtener valores
        barra_id = self.combo_barra.currentData()
        p = self.spin_p.value()
        a = self.spin_a.value()
        angulo = self.spin_angulo.value()

        # Obtener barra
        barra = self.modelo.obtener_barra(barra_id)
        if barra is None:
            QMessageBox.critical(self, "Error", f"Barra {barra_id} no encontrada.")
            return

        # Validar que 'a' esté dentro del rango
        if a < 0 or a > barra.L:
            QMessageBox.warning(
                self,
                "Posición inválida",
                f"La distancia 'a' debe estar entre 0 y {barra.L:.3f} m."
            )
            return

        # Crear carga
        try:
            self.carga_creada = CargaPuntualBarra(
                barra=barra,
                P=p,
                a=a,
                angulo=angulo
            )
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Error de validación", str(e))


class CargaDistribuidaDialog(QDialog):
    """
    Diálogo para agregar una carga distribuida sobre una barra.

    Permite crear cargas uniformes, triangulares o trapezoidales.
    """

    def __init__(self, modelo: ModeloEstructural, parent=None):
        super().__init__(parent)
        self.modelo = modelo
        self.carga_creada: Optional[CargaDistribuida] = None

        self.setWindowTitle("Agregar Carga Distribuida")
        self.setMinimumWidth(450)

        self._init_ui()

    def _init_ui(self):
        """Inicializa la interfaz de usuario."""
        layout = QVBoxLayout(self)

        # Grupo de selección de barra
        group_barra = QGroupBox("Selección de Barra")
        form_barra = QFormLayout()

        self.combo_barra = QComboBox()
        form_barra.addRow("Barra:", self.combo_barra)

        # Label informativo de longitud
        self.label_longitud = QLabel()
        form_barra.addRow("Longitud:", self.label_longitud)

        group_barra.setLayout(form_barra)
        layout.addWidget(group_barra)

        # Grupo de tipo de carga
        group_tipo = QGroupBox("Tipo de Carga")
        form_tipo = QFormLayout()

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("Uniforme (q1 = q2)", "uniforme")
        self.combo_tipo.addItem("Triangular (q1 = 0)", "triangular_inicio")
        self.combo_tipo.addItem("Triangular (q2 = 0)", "triangular_fin")
        self.combo_tipo.addItem("Trapezoidal (q1 ≠ q2)", "trapezoidal")
        self.combo_tipo.currentIndexChanged.connect(self._on_tipo_changed)
        form_tipo.addRow("Tipo:", self.combo_tipo)

        group_tipo.setLayout(form_tipo)
        layout.addWidget(group_tipo)

        # Grupo de parámetros
        group_params = QGroupBox("Parámetros de la Carga")
        form_params = QFormLayout()

        # q1 (intensidad inicial)
        self.spin_q1 = QDoubleSpinBox()
        self.spin_q1.setRange(0, 1000)
        self.spin_q1.setDecimals(2)
        self.spin_q1.setSuffix(" kN/m")
        self.spin_q1.setValue(10.0)
        form_params.addRow("q₁ (inicio):", self.spin_q1)

        # q2 (intensidad final)
        self.spin_q2 = QDoubleSpinBox()
        self.spin_q2.setRange(0, 1000)
        self.spin_q2.setDecimals(2)
        self.spin_q2.setSuffix(" kN/m")
        self.spin_q2.setValue(10.0)
        form_params.addRow("q₂ (final):", self.spin_q2)

        # x1 (inicio de la carga)
        self.spin_x1 = QDoubleSpinBox()
        self.spin_x1.setRange(0, 100)
        self.spin_x1.setDecimals(3)
        self.spin_x1.setSuffix(" m")
        self.spin_x1.setValue(0.0)
        form_params.addRow("x₁ (inicio):", self.spin_x1)

        # x2 (fin de la carga)
        self.spin_x2 = QDoubleSpinBox()
        self.spin_x2.setRange(0, 100)
        self.spin_x2.setDecimals(3)
        self.spin_x2.setSuffix(" m")
        self.spin_x2.setValue(0.0)
        form_params.addRow("x₂ (fin):", self.spin_x2)

        # Dirección (en coordenadas locales)
        self.combo_direccion = QComboBox()
        self.combo_direccion.addItem("→ A lo largo de la barra (0°)", 0)
        self.combo_direccion.addItem("⟲ Perpendicular horaria (+90°)", 90)
        self.combo_direccion.addItem("⟳ Perpendicular antihoraria (-90°)", -90)
        form_params.addRow("Dirección (local):", self.combo_direccion)

        group_params.setLayout(form_params)
        layout.addWidget(group_params)

        # Label de resultante
        self.label_resultante = QLabel()
        self.label_resultante.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.label_resultante)

        # Conectar cambios para actualizar resultante
        self.spin_q1.valueChanged.connect(self._actualizar_resultante)
        self.spin_q2.valueChanged.connect(self._actualizar_resultante)
        self.spin_x1.valueChanged.connect(self._actualizar_resultante)
        self.spin_x2.valueChanged.connect(self._actualizar_resultante)

        # Nota informativa
        label_nota = QLabel(
            "<i>Nota: x₁ y x₂ son medidos desde el nudo i de la barra. "
            "Para carga en toda la barra, use x₁=0 y x₂=L.</i><br>"
            "<b>Dirección:</b> 0°=a lo largo, +90°=rotación horaria (⟲), -90°=antihoraria (⟳)"
        )
        label_nota.setWordWrap(True)
        label_nota.setStyleSheet("color: #444; padding: 8px; background: #f0f0f0; border-radius: 4px;")
        layout.addWidget(label_nota)

        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Conectar y cargar barras AL FINAL, después de crear TODOS los widgets
        self.combo_barra.currentIndexChanged.connect(self._on_barra_changed)
        self._cargar_barras()

        # Actualizar info inicial
        self._on_barra_changed()
        self._on_tipo_changed()

    def _cargar_barras(self):
        """Carga las barras disponibles en el ComboBox."""
        self.combo_barra.clear()

        if self.modelo.num_barras == 0:
            self.combo_barra.addItem("(No hay barras)", None)
            self.combo_barra.setEnabled(False)
            return

        for barra in self.modelo.barras:
            texto = f"Barra {barra.id}: N{barra.nudo_i.id} → N{barra.nudo_j.id} (L={barra.L:.2f}m)"
            self.combo_barra.addItem(texto, barra.id)

    def _on_barra_changed(self):
        """Actualiza información cuando cambia la barra seleccionada."""
        if self.combo_barra.currentData() is None:
            self.label_longitud.setText("N/A")
            self.spin_x2.setMaximum(0)
            return

        barra_id = self.combo_barra.currentData()
        barra = self.modelo.obtener_barra(barra_id)

        if barra:
            self.label_longitud.setText(f"{barra.L:.3f} m")
            self.spin_x1.setMaximum(barra.L)
            self.spin_x2.setMaximum(barra.L)
            self.spin_x2.setValue(barra.L)  # Por defecto, toda la barra

        self._actualizar_resultante()

    def _on_tipo_changed(self):
        """Actualiza los spinboxes según el tipo de carga."""
        tipo = self.combo_tipo.currentData()

        if tipo == "uniforme":
            self.spin_q2.setValue(self.spin_q1.value())
            self.spin_q2.setEnabled(False)
        elif tipo == "triangular_inicio":
            self.spin_q1.setValue(0)
            self.spin_q1.setEnabled(False)
            self.spin_q2.setEnabled(True)
        elif tipo == "triangular_fin":
            self.spin_q2.setValue(0)
            self.spin_q1.setEnabled(True)
            self.spin_q2.setEnabled(False)
        elif tipo == "trapezoidal":
            self.spin_q1.setEnabled(True)
            self.spin_q2.setEnabled(True)

        self._actualizar_resultante()

    def _actualizar_resultante(self):
        """Calcula y muestra la resultante de la carga."""
        q1 = self.spin_q1.value()
        q2 = self.spin_q2.value()
        x1 = self.spin_x1.value()
        x2 = self.spin_x2.value()

        if x2 <= x1:
            self.label_resultante.setText("Resultante: N/A (x₂ debe ser > x₁)")
            return

        L = x2 - x1
        R = (q1 + q2) * L / 2

        self.label_resultante.setText(f"Resultante: R = {R:.2f} kN")

    def _on_accept(self):
        """Valida y crea la carga."""
        if self.combo_barra.currentData() is None:
            QMessageBox.warning(
                self,
                "Error",
                "No hay barras disponibles. Cree barras primero."
            )
            return

        # Obtener valores
        barra_id = self.combo_barra.currentData()
        q1 = self.spin_q1.value()
        q2 = self.spin_q2.value()
        x1 = self.spin_x1.value()
        x2 = self.spin_x2.value()
        angulo = self.combo_direccion.currentData()

        # Validar
        if x2 <= x1:
            QMessageBox.warning(
                self,
                "Posiciones inválidas",
                "x₂ debe ser mayor que x₁."
            )
            return

        if abs(q1) < 0.001 and abs(q2) < 0.001:
            QMessageBox.warning(
                self,
                "Carga nula",
                "Al menos una de las intensidades debe ser diferente de cero."
            )
            return

        # Obtener barra
        barra = self.modelo.obtener_barra(barra_id)
        if barra is None:
            QMessageBox.critical(self, "Error", f"Barra {barra_id} no encontrada.")
            return

        # Validar rango
        if x1 < 0 or x2 > barra.L:
            QMessageBox.warning(
                self,
                "Rango inválido",
                f"Las posiciones deben estar entre 0 y {barra.L:.3f} m."
            )
            return

        # Crear carga
        try:
            self.carga_creada = CargaDistribuida(
                barra=barra,
                q1=q1,
                q2=q2,
                x1=x1,
                x2=x2,
                angulo=angulo
            )
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Error de validación", str(e))
