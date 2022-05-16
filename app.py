import sys

import qdarktheme
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

sys.coinit_flags = 2


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dofus Helper")
        # self.setWindowOpacity(0.5)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
        )  # Qt.WindowType.FramelessWindowHint
        self.setFixedSize(250, 100)
        self.move(0, 0)

        self.setStyleSheet(qdarktheme.load_stylesheet())

        self.auto_travel_layout()

    def auto_travel_layout(self):

        int_validator = QIntValidator()

        map_id_input = QLineEdit()
        map_id_input.setPlaceholderText("Current map ID")
        map_id_input.setValidator(int_validator)

        dest_x_input = QLineEdit()
        dest_y_input = QLineEdit()
        dest_x_input.setPlaceholderText("dest x")
        dest_y_input.setPlaceholderText("dest y")

        dest_x_input.setValidator(int_validator)
        dest_y_input.setValidator(int_validator)

        go_to_dest_button = QPushButton("Go!")
        go_to_dest_button.clicked.connect(
            lambda: self.go_to_dest(
                map_id_input.text(),
                (dest_x_input.text(), dest_y_input.text()),
            )
        )

        layout = QVBoxLayout()
        layout.addWidget(map_id_input)

        dest_layout = QHBoxLayout()
        dest_layout.addWidget(dest_x_input)
        dest_layout.addWidget(dest_y_input)

        layout.addLayout(dest_layout)
        layout.addWidget(go_to_dest_button)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

    def go_to_dest(self, map_id: str, dest: tuple[str, str]):
        print(f"map_id: {map_id}, dest: {dest}")


def run_app(argv: list[str]):
    app = QApplication(argv)

    window = MainWindow()
    window.show()

    app.exec()
