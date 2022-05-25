import sys

import qdarktheme
from PyQt6 import QtCore, QtGui, QtWidgets

sys.coinit_flags = 2

import dofus_handler


def auto_travel_widget(handler: dofus_handler.DofusHandler):

    int_validator = QtGui.QIntValidator()

    map_id_input = QtWidgets.QLineEdit()
    map_id_input.setPlaceholderText("Current map ID")
    map_id_input.setValidator(int_validator)

    dest_x_input = QtWidgets.QLineEdit()
    dest_y_input = QtWidgets.QLineEdit()
    dest_x_input.setPlaceholderText("dest x")
    dest_y_input.setPlaceholderText("dest y")

    dest_x_input.setValidator(int_validator)
    dest_y_input.setValidator(int_validator)

    go_to_dest_button = QtWidgets.QPushButton("Go!")
    go_to_dest_button.clicked.connect(
        lambda: handler.go_to_dest(
            map_id_input.text(),
            (dest_x_input.text(), dest_y_input.text()),
        )
    )

    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(map_id_input)

    dest_layout = QtWidgets.QHBoxLayout()
    dest_layout.addWidget(dest_x_input)
    dest_layout.addWidget(dest_y_input)

    layout.addLayout(dest_layout)
    layout.addWidget(go_to_dest_button)

    container = QtWidgets.QWidget()
    container.setLayout(layout)

    return container


def debug_move_widget(handler: dofus_handler.DofusHandler):

    left_button = QtWidgets.QToolButton()
    right_button = QtWidgets.QToolButton()
    up_button = QtWidgets.QToolButton()
    down_button = QtWidgets.QToolButton()

    left_button.setArrowType(QtCore.Qt.ArrowType.LeftArrow)
    right_button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
    up_button.setArrowType(QtCore.Qt.ArrowType.UpArrow)
    down_button.setArrowType(QtCore.Qt.ArrowType.DownArrow)

    left_button.clicked.connect(handler.move_left)
    right_button.clicked.connect(handler.move_right)
    up_button.clicked.connect(handler.move_up)
    down_button.clicked.connect(handler.move_down)

    grid_layout = QtWidgets.QGridLayout()

    grid_layout.addWidget(left_button, 1, 0)
    grid_layout.addWidget(right_button, 1, 2)
    grid_layout.addWidget(up_button, 0, 1)
    grid_layout.addWidget(down_button, 2, 1)

    container = QtWidgets.QWidget()
    container.setLayout(grid_layout)

    return container


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, handler: dofus_handler.DofusHandler):
        super().__init__()

        self.setWindowTitle("Dofus Helper")
        # self.setWindowOpacity(0.5)
        self.setWindowFlags(
            QtCore.Qt.WindowType.WindowStaysOnTopHint
        )  # Qt.WindowType.FramelessWindowHint
        self.setFixedSize(250, 150)
        self.move(0, 0)

        self.setStyleSheet(qdarktheme.load_stylesheet())

        tab = QtWidgets.QTabWidget()
        tab.addTab(auto_travel_widget(handler), "Auto Travel")
        tab.addTab(debug_move_widget(handler), "Debug Move")

        self.setCentralWidget(tab)


def run_app(argv: list[str], handler: dofus_handler.DofusHandler):
    app = QtWidgets.QApplication(argv)

    window = MainWindow(handler)
    window.show()

    app.exec()
