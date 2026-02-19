#!/usr/bin/env python3
"""
Punto de entrada principal de la aplicación de Análisis Estructural.

Sistema de análisis de pórticos planos 2D mediante el Método de las Fuerzas.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def main():
    """Función principal que inicia la aplicación."""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt

    # Configurar atributos de la aplicación antes de crear QApplication
    # Esto es necesario para HiDPI en algunos sistemas

    # Crear aplicación
    app = QApplication(sys.argv)
    app.setApplicationName("Análisis Estructural")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("py-anes-mf")

    # Estilo de la aplicación
    app.setStyle("Fusion")

    # Crear y mostrar ventana principal
    from src.gui.main_window import MainWindow

    window = MainWindow()
    window.show()

    # Ejecutar loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
