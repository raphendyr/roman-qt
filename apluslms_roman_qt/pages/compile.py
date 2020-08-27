from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QStandardItemModel,
    QStandardItem,
)
from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QDataWidgetMapper,
    QGroupBox,
    QGridLayout,
    QStackedWidget,
    QVBoxLayout,
    QPushButton,
    QFrame,
)

from ..widgets.processtabs import ProcessTabBar
from ..widgets.textlog import TextLogWidget


class CompletedPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        redoLabel = QLabel("Rebuild")
        redoButton = QPushButton("rebuild")
        redoLabel.setBuddy(redoButton)

        uploadLabel = QLabel("You should upload this")

        layout = QGridLayout()
        layout.addWidget(redoLabel, 0, 0)
        layout.addWidget(redoButton, 0, 1)
        layout.addWidget(uploadLabel, 1, 0, 1, 2)
        self.setLayout(layout)


class CompilePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tabs = tabs = ProcessTabBar()
        self.stack = stack = QStackedWidget()

        tabs.tab_selected.connect(stack.setCurrentIndex)

        frame = QFrame()
        frame.setAttribute(Qt.WA_MacShowFocusRect, 0)
        frame.setFrameStyle(QFrame.Sunken | QFrame.Panel)
        frame.setLineWidth(2)
        frame_layout = QVBoxLayout()
        frame_layout.setSpacing(0)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(tabs)
        frame_layout.addWidget(stack)
        frame.setLayout(frame_layout)

        layout = QVBoxLayout()
        layout.addWidget(frame)
        self.setLayout(layout)

    def set_tabs(self, num):
        self.tabs.set_tab_count(num)
        for i in range(num):
            w = TextLogWidget()
            w.setSize(80, 20)
            self.stack.addWidget(w)
            w.write("log %d" % (i,))
        self.stack.addWidget(CompletedPage())
