from PyQt5.QtCore import (
    QModelIndex,
    QSize,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QStandardItem,
    QStandardItemModel,
)
from PyQt5.QtWidgets import (
    QApplication,
    QListView,
    QToolBar,
    QVBoxLayout,
    QHBoxLayout,
    QAction,
    QWidget,
    QStyle,
    QMessageBox,
    QInputDialog,
    QLineEdit,
    QFrame,
)

try:
    from ..models.steps import EditStepsModel
except ValueError:
    import importlib.util
    spec = importlib.util.spec_from_file_location("apluslms_roman_qt.models.steps", "../models/steps.py")
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)
    EditStepsModel = foo.EditStepsModel

ID_ROLE = Qt.UserRole + 1


def get_step_id(item):
    #return item.data(ID_ROLE)
    return item.id

def set_step_id(item, id):
    #item.setData(id, ID_ROLE)
    item.id = id


class EditableStepsWidget(QFrame):
    step_added = pyqtSignal(int, str)
    step_removed = pyqtSignal(int)
    step_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._next_id = 0
        self.list = list_ = QListView(self)
        #model = QStandardItemModel(self)
        model = EditStepsModel(self)

        list_.setModel(model)
        list_.setEditTriggers(QListView.NoEditTriggers)
        list_.selectionModel().currentChanged.connect(self._on_select)
        # Remove borders
        list_.setAttribute(Qt.WA_MacShowFocusRect, 0)
        list_.setFrameStyle(QFrame.Plain | QFrame.NoFrame)
        # Add borders to full set
        self.setAttribute(Qt.WA_MacShowFocusRect, 1)
        self.setFrameStyle(QFrame.Sunken | QFrame.Panel)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(list_)

        style = self.style()
        icon = style.standardIcon(QStyle.SP_DialogCancelButton)
        self._a_add = a_add = QAction(
            style.standardIcon(QStyle.SP_FileIcon),
            "Add new step",
            self,
            statusTip="Add a new step to compile process",
            triggered=self._on_add,
        )
        self._a_del = a_del = QAction(
            style.standardIcon(QStyle.SP_DialogDiscardButton),
            "Remove a step",
            self,
            statusTip="Remove selected step from compile process",
            triggered=self._on_del,
        )
        self._a_up = a_up = QAction(
            style.standardIcon(QStyle.SP_ArrowUp),
            "Move step up",
            self,
            statusTip="Move selected step up a position",
            triggered=self._on_up,
        )
        self._a_down = a_down = QAction(
            style.standardIcon(QStyle.SP_ArrowDown),
            "Move step down",
            self,
            statusTip="Move selected step down a position",
            triggered=self._on_down,
        )

        actions = QToolBar(self)
        actions.setFloatable(False)
        actions.setMovable(False)
        actions.setIconSize(QSize(16, 16))
        actions.addAction(a_add)
        actions.addAction(a_del)
        actions.addAction(a_up)
        actions.addAction(a_down)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(list_)
        layout.addWidget(actions)
        self.setLayout(layout)

    def _get_next_id(self):
        i = self._next_id
        self._next_id += 1
        return i

    def get_steps(self):
        model = self.list.model()
        return [get_step_id(model.item(row)) for row in range(model.rowCount())]

    def add_step(self, image):
        model = self.list.model()
        #item = QStandardItem(image)
        item = model.createStep(image)
        id_ = self._get_next_id()
        set_step_id(item, id_)
        #model.appendRow(item)

        self.step_added.emit(id_, image)
        if model.rowCount() == 1:
            self.list.setCurrentIndex(model.index(0, 0))
        self._update_action_states()

    def _move_selected(self, move_up=True):
        model = self.list.model()

        source_index = self.list.selectionModel().currentIndex().row()
        destination_index = source_index - 1 if move_up else source_index + 1
        if destination_index < 0 or destination_index >= model.rowCount():
            return

        model.simpleMoveRow(source_index, destination_index)
        # NOTE: notices shape change automatically
        #self.list.setCurrentIndex(model.index(destination_index, 0))
        self._update_action_states()

    def _update_action_states(self):
        count = self.list.model().rowCount()
        if count > 0:
            cur_idx = self.list.selectionModel().currentIndex()
            cur_row = cur_idx.row() if cur_idx.isValid() else None
        else:
            cur_row = None
        self._a_del.setEnabled(count > 0)
        self._a_up.setEnabled(cur_row is not None and cur_row > 0)
        self._a_down.setEnabled(cur_row is not None and cur_row < count-1)

    def _on_select(self, current, previous):
        if not current:
            current = previous
        if current.isValid():
            item_id = get_step_id(self.list.model().itemFromIndex(current))
        else:
            item_id = -1
        self.step_selected.emit(item_id)
        self._update_action_states()

    def _on_add(self):
        image, ok = QInputDialog.getText(self, "New step",
            "Compile step image:",
            QLineEdit.Normal,
        )
        if ok and image:
            self.add_step(image)
            model = self.list.model()
            self.list.setCurrentIndex(model.index(model.rowCount()-1, 0))

    def _on_del(self):
        index = self.list.selectionModel().currentIndex()
        if index.isValid():
            row = index.row()
            model = self.list.model()
            item = model.item(row)
            ret = QMessageBox.warning(self, "Remove step",
                "You are about to remove compile step with image '{}'.\n"
                "Are you sure?".format(item.data(Qt.DisplayRole)),
                QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.step_removed.emit(get_step_id(item))
                model.removeRow(row)
        self._update_action_states()

    def _on_up(self):
        self._move_selected(move_up=True)

    def _on_down(self):
        self._move_selected(move_up=False)


if __name__ == '__main__':
    import sys
    import random
    app = QApplication(sys.argv)

    steps = ['step {}'.format(i) for i in range(4)]

    view = EditableStepsWidget()
    map_ = {}
    view.setWindowTitle("Test for EditableStepsWidget")

    def print_selected(i):
        name = map_.get(i)
        if name is not None:
            print("Activat:", i, name)
        else:
            print("Activat: empty page")

    def add_new(i, name):
        map_[i] = name
        print("Add new:", i, name)

    def del_step(i):
        print("Removed:", i, map_[i])
        del map_[i]

    view.step_selected.connect(print_selected)
    view.step_added.connect(add_new)
    view.step_removed.connect(del_step)
    for step in steps:
        view.add_step(step)

    view.show()
    sys.exit(app.exec_())
