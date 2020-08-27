import enum

from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
    QModelIndex,
    QAbstractItemModel,
    QVariant,
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


class StepItem(QStandardItem):
    IdRole = Qt.UserRole + 1

    def __init__(self, id_, name, parent=None):
        super().__init__(name, parent)
        self.setData(id_, self.IdRole)

    @property
    def step_id(self):
        self.data(self.IdRole)


class StepItem:
    def __init__(self):
        self.id = None
        self.image = ""

    def data(self, role: int = Qt.DisplayRole):
        map = {Qt.DisplayRole: 'image'}
        var = map.get(role)
        if var is not None:
            return getattr(self, var)
        return None

class StepsModel(list):
    def __init__(self):
        super().__init__()

    def move_row(self, source: int, destination: int):
        if destination > source:
            destination -= 1 # destroyinations is in orignal index. take care of the shift in the data
            item = self[source]
            self[source:destination] = self[source+1:destination+1]
            self[destination] = item
        elif source > destination:
            item = self[source]
            self[destination+1:source+1] = self[destination:source]
            self[destination] = item


class EditStepsModel(QAbstractItemModel):
    ITEM_FLAGS = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren

    def __init__(self, parent=None):
        super().__init__(parent)

        self._model = StepsModel()

    def columnCount(self, parent: QModelIndex = None) -> int:
        if parent is None or not parent.isValid():
            return 1
        return 0

    def rowCount(self, parent: QModelIndex = None) -> int:
        if parent is None or not parent.isValid():
            return len(self._model)
        return 0

    def flags(self, parent: QModelIndex = None) -> int:
        if parent is None:
            parent = QModelIndex()
        return self.ITEM_FLAGS | super().flags(parent)

    def parent(self, child: QModelIndex = None):
        if child is None:
            return super().parent()
        return QModelIndex()

    def hasChildren(self, parent: QModelIndex = None) -> bool:
        return False

    def hasIndex(self, row: int, column: int, parent: QModelIndex = None) -> bool:
        if parent is not None and parent.isValid():
            return False
        if column > 0:
            return False
        return 0 <= row < self.rowCount()

    def index(self, row: int, column: int = 0, parent: QModelIndex = None) -> QModelIndex:
        if parent is not None and parent.isValid():
            return QModelIndex()
        return self.createIndex(row, column, self._model[row])

    def insertRows(self, row: int, count: int, parent: QModelIndex = None) -> bool:
        if parent is None:
            parent = QModelIndex()
        if parent.isValid():
            return False
        self.beginInsertRows(parent, row, row + count - 1)
        for i in range(row, row+count):
            self._model.insert(i, StepItem())
        self.endInsertRows()
        return True

    def createStep(self, image: str) -> StepItem:
        i = self.rowCount()
        if self.insertRow(i):
            item = self._model[i]
            item.image = image
            print(" -- created item:", item)
            return item
        return None

    def moveRow(self,
                sourceParent: QModelIndex,
                sourceRow: int,
                destinationParent: QModelIndex,
                destinationChild: int,
    ) -> bool:
        if sourceParent is not None and sourceParent.isValid():
            return False
        if destinationParent is not None and destinationParent.isValid():
            return False
        # NOTE: destinationChilds that are +same or +1 result on no movement
        if sourceRow == destinationChild or sourceRow == destinationChild - 1:
            return False
        if not self.beginMoveRows(sourceParent, sourceRow, sourceRow, destinationParent, destinationChild):
            return False
        self._model.move_row(sourceRow, destinationChild)
        self.endMoveRows()
        return True

    def simpleMoveRow(self, sourceRow: int, destinationRow: int) -> bool:
        if destinationRow > sourceRow:
            # Qt API considers insert index in original shape, thus original
            # spot is not yet empty
            destinationRow += 1
        return self.moveRow(QModelIndex(), sourceRow, QModelIndex(), destinationRow)

    def itemFromIndex(self, index: QModelIndex) -> StepItem:
        if index.isValid():
            return self._model[index.row()]
        return None

    def item(self, row: int, column: int = 0) -> StepItem:
        if self.hasIndex(row, column):
            return self._model[row]
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> QVariant:
        item = self.itemFromIndex(index)
        return item.data(role)
