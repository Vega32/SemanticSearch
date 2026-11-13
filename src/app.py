import sys

from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


def create_application():
    app = QApplication(sys.argv)

    app.setApplicationName("Semantic Search")

    window = MainWindow()
    window.show()

    return app.exec()
