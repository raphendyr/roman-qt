import enum

from PyQt5.QtCore import (
    QModelIndex,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QIcon,
    QStandardItem,
    QStandardItemModel,
)
from PyQt5.QtWidgets import (
    QApplication,
    QListView,
    QStyle,
)


@enum.unique
class StepState(enum.Enum):
    UNKNOWN = QStyle.SP_TitleBarContextHelpButton
    ACTIVE = QStyle.SP_BrowserReload
    SUCCESS = QStyle.SP_DialogApplyButton
    FAILED = QStyle.SP_DialogCancelButton

class CompileStepsWidget(QListView):
    step_selected = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        model = QStandardItemModel()
        self.setModel(model)
        self.setEditTriggers(QListView.NoEditTriggers)
        self.selectionModel().currentChanged.connect(self.show_step)

    def add_step(self, step):
        model = self.model()
        icon = self.style().standardIcon(StepState.UNKNOWN.value)
        item = QStandardItem(icon, step)
        model.appendRow(item)

        if model.rowCount() == 1:
            self.setCurrentIndex(model.index(0, 0))

    def set_state(self, index, state):
        icon = self.style().standardIcon(state.value)
        item = self.model().item(index)
        item.setIcon(icon)

    def show_step(self, current, previous):
        self.step_selected.emit(current.row(), current.data())


if __name__ == '__main__':
    import sys
    import random
    app = QApplication(sys.argv)

    steps = [
        '_/hello-world',
        'apluslms/ariel',
        'apluslms/compile-rst',
    ]*3
    states = list(StepState)[1:]

    view = CompileStepsWidget()
    view.setWindowTitle("Test for CompileStepsWidget")

    def print_selected(i, name):
        print("Activated:", i, name)
        view.set_state(i, random.choice(states))

    view.step_selected.connect(print_selected)
    for step in steps:
        view.add_step(step)

    view.show()
    sys.exit(app.exec_())
