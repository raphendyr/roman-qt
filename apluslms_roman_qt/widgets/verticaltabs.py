from PyQt5.QtCore import (
    Qt,
    QSize,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QStandardItem,
    QStandardItemModel,
)
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QListView,
    QStackedWidget,
    QWidget,
)

MENU_CSS = """
QListView {
    /* make the selection span the entire width of the view */
    show-decoration-selected: 1;
    font-size: 18pt;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #ABAFE5, stop: 1 #8588B2);
}

QListView::item:alternate {
    background: #EEEEEE;
}

QListView::item:selected {
    border: 1px solid #6a6ea9;
}

QListView::item:selected {
    color: black;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #6a6ea9, stop: 1 #888dd9);
}

QListView::item:hover {
    color: black;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #FAFBFE, stop: 1 #DCDEF1);
}
"""


class VerticalTabsWidget(QWidget):
    item_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # List of icons with title, stacked as list
        self.menu = menu = QListView()
        menu.setViewMode(QListView.IconMode)
        menu.setMovement(QListView.Static)
        menu.setFlow(QListView.TopToBottom)
        menu.setIconSize(QSize(96, 84))
        menu.setMaximumWidth(96)
        menu.setEditTriggers(QListView.NoEditTriggers)
        menu.setStyleSheet(MENU_CSS)
        # Remove borders
        menu.setAttribute(Qt.WA_MacShowFocusRect, 0)
        menu.setFrameStyle(QFrame.Plain | QFrame.NoFrame)

        self.menu_model = model = QStandardItemModel()
        menu.setModel(model)
        menu.selectionModel().currentChanged.connect(self._on_change)

        self.pages = pages = QStackedWidget()

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(menu)
        layout.addWidget(pages, 1)
        self.setLayout(layout)

        #self.setCurrentRow(0)

    def add_page(self, name, icon, widget):
        # Create menu entry
        item = QStandardItem(icon, name)
        item.setTextAlignment(Qt.AlignHCenter)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.menu_model.appendRow(item)

        if self.menu_model.rowCount() == 1:
            self.menu.setCurrentIndex(self.menu_model.index(0, 0))

        # Add widget to stack
        self.pages.addWidget(widget)

    def _on_change(self, current, previous):
        if not current:
            current = previous
        self.pages.setCurrentIndex(current.row())


if __name__ == '__main__':
    import sys
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QApplication, QLabel, QStyle, QVBoxLayout, QWidget

    class TestPage(QWidget):
        def __init__(self, name, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Page..."))
            layout.addWidget(QLabel("...and the name is..."))
            layout.addWidget(QLabel(name))
            self.setLayout(layout)

    app = QApplication(sys.argv)

    view = VerticalTabsWidget()
    view.setWindowTitle("Test for VerticalTabsWidget")
    view.setFixedSize(500, 300)
    icon = view.style().standardIcon(QStyle.SP_DialogCancelButton)

    page1 = TestPage("ekasivu")
    view.add_page("Sivu 1", icon, page1)
    page2 = TestPage("tokasivu")
    view.add_page("Sivu 2", icon, page2)

    view.show()
    sys.exit(app.exec_())
