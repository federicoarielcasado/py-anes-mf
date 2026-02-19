#!/usr/bin/env python
"""
Punto de entrada principal para la aplicación de análisis estructural.

Uso:
    python main.py
"""

import sys
from PyQt6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def main():
    """Función principal que inicia la aplicación."""
    app = QApplication(sys.argv)

    # Configurar aplicación
    app.setApplicationName("PyANES-MF")
    app.setOrganizationName("PyANES")
    app.setApplicationVersion("0.1.0")

    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()

    # Ejecutar loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
