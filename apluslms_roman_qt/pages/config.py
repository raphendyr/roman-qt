from enum import Enum

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
    QVBoxLayout,
    QLineEdit,
    QLabel,
    QDataWidgetMapper,
    QGroupBox,
    QGridLayout,
    QTabWidget,
)

from ..widgets.editablesteps import EditableStepsWidget


class GeneralTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QGridLayout()
        layout.addWidget(QLabel("Name"), 0, 0)
        layout.addWidget(QLineEdit(), 0, 1)
        layout.addWidget(QLabel("Teacher"), 1, 0)
        layout.addWidget(QLineEdit(), 1, 1)
        self.setLayout(layout)


class ServicesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = model = QStandardItemModel(0, 4, self)
        self.step_map = {}
        self._create_steps_list()
        self._create_form_groupbox()

        layout = QHBoxLayout()
        layout.addWidget(self.steps)
        layout.addWidget(self.groupbox)
        self.setLayout(layout)
        self._on_step_select(-1)

        self.set_config(['mooc-grader', 'radar'])

    def _create_steps_list(self):
        self.steps = steps = EditableStepsWidget()
        steps.step_added.connect(self._on_step_add)
        steps.step_removed.connect(self._on_step_rem)
        steps.step_selected.connect(self._on_step_select)

    def _create_form_groupbox(self):
        imageLabel = QLabel("Name:")
        self.image = imageEdit = QLineEdit()
        imageLabel.setBuddy(imageEdit)

        commandLabel = QLabel("Service:")
        commandEdit = QLineEdit()
        commandLabel.setBuddy(commandEdit)

        environmentLabel = QLabel("Options:")
        environmentEdit = QLineEdit()
        environmentLabel.setBuddy(environmentEdit)

        self.mapper = mapper = QDataWidgetMapper(self)
        mapper.setSubmitPolicy(QDataWidgetMapper.AutoSubmit)
        mapper.setModel(self.model)
        mapper.addMapping(imageEdit, StepItem.Cols.IMAGE.value)
        mapper.addMapping(commandEdit, StepItem.Cols.COMMAND.value)
        mapper.addMapping(environmentEdit, StepItem.Cols.ENVIRONMENT.value)

        self.groupbox = config = QGroupBox()
        config_layout = QGridLayout()
        config_layout.addWidget(imageLabel, 0, 0)
        config_layout.addWidget(imageEdit, 0, 1)
        config_layout.addWidget(commandLabel, 1, 0)
        config_layout.addWidget(commandEdit, 1, 1)
        config_layout.addWidget(environmentLabel, 2, 0)
        config_layout.addWidget(environmentEdit, 2, 1)
        config.setLayout(config_layout)

        self.all_fields = [
            imageEdit,
            commandEdit,
            environmentEdit,
        ]

    def set_config(self, config):
        for step in config:
            self.steps.add_step(step)

    def get_data(self):
        step_ids = self.steps.get_steps()
        row_id_f = self.step_map.get
        row_ids = [row_id_f(step_id) for step_id in step_ids]

        model = self.model
        data = []
        for row in row_ids:
            data.append([model.index(row, col).data() for col in range(model.columnCount())])

        return data

    def _on_step_select(self, id_):
        if id_ >= 0:
            self.mapper.setCurrentIndex(self.step_map[id_])
            self.get_data()
        else:
            for field in self.all_fields:
                field.clear()
                field.setEnabled(False)

    def _on_step_add(self, id_, image):
        data_id = len(self.step_map)
        self.step_map[id_] = data_id
        model = self.model
        for col, item in enumerate(StepItem.new_row(image)):
            model.setItem(data_id, col, QStandardItem(item))
        for field in self.all_fields:
            field.setEnabled(True)

    def _on_step_rem(self, id_):
        pass


class StepItem:
    class Cols(Enum):
        IMAGE = 0
        COMMAND = 1
        MOUNT = 2
        ENVIRONMENT = 3

    @classmethod
    def new_row(cls, image):
        row = [""] * len(cls.Cols)
        row[cls.Cols.IMAGE.value] = image
        return row


class StepsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = model = QStandardItemModel(0, 4, self)
        self.step_map = {}
        self._create_steps_list()
        self._create_form_groupbox()

        layout_top = QHBoxLayout()
        layout_top.addWidget(self.steps)
        layout_top.addWidget(self.groupbox)

        #layout = QVBoxLayout()
        #layout.addLayout(layout_top)
        #layout.addWidget(self.log_tabs)
        self.setLayout(layout_top)
        self._on_step_select(-1)

        self.set_config(['apluslms/compile-rst', 'apluslms/compile-jsvee'])

    def _create_steps_list(self):
        self.steps = steps = EditableStepsWidget()
        steps.step_added.connect(self._on_step_add)
        steps.step_removed.connect(self._on_step_rem)
        steps.step_selected.connect(self._on_step_select)

    def _create_form_groupbox(self):
        imageLabel = QLabel("Image:")
        self.image = imageEdit = QLineEdit()
        imageLabel.setBuddy(imageEdit)

        commandLabel = QLabel("Command:")
        commandEdit = QLineEdit()
        commandLabel.setBuddy(commandEdit)

        mountLabel = QLabel("Mount:")
        mountEdit = QLineEdit()
        mountLabel.setBuddy(mountEdit)

        environmentLabel = QLabel("Environment:")
        environmentEdit = QLineEdit()
        environmentLabel.setBuddy(environmentEdit)

        self.mapper = mapper = QDataWidgetMapper(self)
        mapper.setSubmitPolicy(QDataWidgetMapper.AutoSubmit)
        mapper.setModel(self.model)
        mapper.addMapping(imageEdit, StepItem.Cols.IMAGE.value)
        mapper.addMapping(commandEdit, StepItem.Cols.COMMAND.value)
        mapper.addMapping(mountEdit, StepItem.Cols.MOUNT.value)
        mapper.addMapping(environmentEdit, StepItem.Cols.ENVIRONMENT.value)

        self.groupbox = config = QGroupBox("Edit step parameters")
        config.setCheckable(True)
        config.setChecked(False)
        config_layout = QGridLayout()
        config_layout.addWidget(imageLabel, 0, 0)
        config_layout.addWidget(imageEdit, 0, 1)
        config_layout.addWidget(commandLabel, 1, 0)
        config_layout.addWidget(commandEdit, 1, 1)
        config_layout.addWidget(mountLabel, 2, 0)
        config_layout.addWidget(mountEdit, 2, 1)
        config_layout.addWidget(environmentLabel, 3, 0)
        config_layout.addWidget(environmentEdit, 3, 1)
        config.setLayout(config_layout)

        self.all_fields = [
            imageEdit,
            commandEdit,
            mountEdit,
            environmentEdit,
        ]

    def set_config(self, config):
        for step in config:
            self.steps.add_step(step)

    def get_data(self):
        step_ids = self.steps.get_steps()
        row_id_f = self.step_map.get
        row_ids = [row_id_f(step_id) for step_id in step_ids]

        model = self.model
        data = []
        for row in row_ids:
            data.append([model.index(row, col).data() for col in range(model.columnCount())])

        return data

    def _on_step_select(self, id_):
        print("step selected", repr(id_))
        if id_ >= 0:
            self.mapper.setCurrentIndex(self.step_map[id_])
            self.get_data()
        else:
            for field in self.all_fields:
                field.clear()
                field.setEnabled(False)

    def _on_step_add(self, id_, image):
        print("step added", id_, image)
        data_id = len(self.step_map)
        self.step_map[id_] = data_id
        model = self.model
        for col, item in enumerate(StepItem.new_row(image)):
            model.setItem(data_id, col, QStandardItem(item))
        for field in self.all_fields:
            field.setEnabled(True)

    def _on_step_rem(self, id_):
        pass


class ConfigPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        tabs = QTabWidget()
        tabs.addTab(GeneralTab(), "Generic")
        tabs.addTab(ServicesTab(), "Services")
        tabs.addTab(StepsTab(), "Build steps")

        layout = QVBoxLayout()
        layout.addWidget(tabs)
        self.setLayout(layout)
