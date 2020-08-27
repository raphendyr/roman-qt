from PyQt.QtWidgets import QStackedWidget

class StackedWidget(QStackedWidget):
    def __init__(setl, parent=None):
        super().__init__(parent)

    def remove_all_widgets(self):
        while self.count() > 0:
            w = self.widget(0)
            self.removeWidget(w)
            w.deleteLater()
