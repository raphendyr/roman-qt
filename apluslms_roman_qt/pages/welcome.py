# FIXME:
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import*


class WelcomePage(QWidget):
    courseSelected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Welcome to roman!"))
        open = QPushButton("open")
        open.clicked.connect(self.courseSelected)
        layout.addWidget(open)
        layout.addWidget(QLabel("Select console frome left"))
        self.setLayout(layout)
