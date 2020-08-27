#!/usr/bin/env python

from PyQt5.QtCore import (
    QFile,
    QFileInfo,
    QPoint,
    QSettings,
    QSize,
    Qt,
    QTextStream,
)
from PyQt5.QtGui import (
    QIcon,
    QKeySequence,
)
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTextEdit,
    QStyle,
    QWidget,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QStackedWidget,
    QLineEdit,
)

from . import (
    roman_rc, # load Qt resources
    __version__,
    __author__,
    __app_name__,
    __app_id__,
)
#from .widgets.verticaltabs import VerticalTabsWidget
from .widgets.fancytabbar import FancyTabWidget
from .pages import (
    WelcomePage,
    ConfigPage,
    CompilePage,
)


def createApplication(argv):
    app = QApplication(argv)
    app.setOrganizationName(__author__)
    app.setOrganizationDomain('.'.join(reversed(__author__.split('.'))))
    app.setApplicationName(__app_name__)
    return app


class MainWindow(QMainWindow):
    sequenceNumber = 1
    windowList = []

    def __init__(self, fileName=None):
        super(MainWindow, self).__init__()

        self.init()
        if fileName:
            self.loadFile(fileName)
        else:
            self.setCurrentFile('')

    def closeEvent(self, event):
        if self.maybeSave():
            self.writeSettings()
            event.accept()
        else:
            event.ignore()

    def newFile(self):
        other = MainWindow()
        MainWindow.windowList.append(other)
        other.move(self.x() + 40, self.y() + 40)
        other.show()

    def open(self):
        fileName, _ = QFileDialog.getOpenFileName(self)
        if fileName:
            existing = self.findMainWindow(fileName)
            if existing:
                existing.show()
                existing.raise_()
                existing.activateWindow()
                return

            if self.isUntitled and self.textEdit.document().isEmpty() and not self.isWindowModified():
                self.loadFile(fileName)
            else:
                other = MainWindow(fileName)
                if other.isUntitled:
                    del other
                    return

                MainWindow.windowList.append(other)
                other.move(self.x() + 40, self.y() + 40)
                other.show()

    def save(self):
        if self.isUntitled:
            return self.saveAs()
        else:
            return self.saveFile(self.curFile)

    def saveAs(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Save As",
                self.curFile)
        if not fileName:
            return False

        return self.saveFile(fileName)

    def about(self):
        QMessageBox.about(self, "About SDI",
                "The <b>SDI</b> example demonstrates how to write single "
                "document interface applications using Qt.")

    def documentWasModified(self):
        self.setWindowModified(True)

    def init(self):
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.isUntitled = True
        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)

        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()

        self.readSettings()

        self.textEdit.document().contentsChanged.connect(self.documentWasModified)

    def createActions(self):
        self.newAct = QAction(QIcon(':/images/new.png'), "&New", self,
                shortcut=QKeySequence.New, statusTip="Create a new file",
                triggered=self.newFile)

        self.openAct = QAction(QIcon(':/images/open.png'), "&Open...", self,
                shortcut=QKeySequence.Open, statusTip="Open an existing file",
                triggered=self.open)

        self.saveAct = QAction(QIcon(':/images/save.png'), "&Save", self,
                shortcut=QKeySequence.Save,
                statusTip="Save the document to disk", triggered=self.save)

        self.saveAsAct = QAction("Save &As...", self,
                shortcut=QKeySequence.SaveAs,
                statusTip="Save the document under a new name",
                triggered=self.saveAs)

        self.closeAct = QAction("&Close", self, shortcut="Ctrl+W",
                statusTip="Close this window", triggered=self.close)

        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit the application",
                triggered=QApplication.instance().closeAllWindows)

        self.cutAct = QAction(QIcon(':/images/cut.png'), "Cu&t", self,
                enabled=False, shortcut=QKeySequence.Cut,
                statusTip="Cut the current selection's contents to the clipboard",
                triggered=self.textEdit.cut)

        self.copyAct = QAction(QIcon(':/images/copy.png'), "&Copy", self,
                enabled=False, shortcut=QKeySequence.Copy,
                statusTip="Copy the current selection's contents to the clipboard",
                triggered=self.textEdit.copy)

        self.pasteAct = QAction(QIcon(':/images/paste.png'), "&Paste", self,
                shortcut=QKeySequence.Paste,
                statusTip="Paste the clipboard's contents into the current selection",
                triggered=self.textEdit.paste)

        self.aboutAct = QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

        self.aboutQtAct = QAction("About &Qt", self,
                statusTip="Show the Qt library's About box",
                triggered=QApplication.instance().aboutQt)

        self.textEdit.copyAvailable.connect(self.cutAct.setEnabled)
        self.textEdit.copyAvailable.connect(self.copyAct.setEnabled)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.closeAct)
        self.fileMenu.addAction(self.exitAct)

        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.cutAct)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.pasteAct)

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

    def createToolBars(self):
        self.fileToolBar = self.addToolBar("File")
        self.fileToolBar.addAction(self.newAct)
        self.fileToolBar.addAction(self.openAct)
        self.fileToolBar.addAction(self.saveAct)

        self.editToolBar = self.addToolBar("Edit")
        self.editToolBar.addAction(self.cutAct)
        self.editToolBar.addAction(self.copyAct)
        self.editToolBar.addAction(self.pasteAct)

    def createStatusBar(self):
        self.statusBar().showMessage("Ready")

    def readSettings(self):
        settings = QSettings()
        pos = settings.value('pos', QPoint(200, 200))
        size = settings.value('size', QSize(400, 400))
        self.move(pos)
        self.resize(size)

    def writeSettings(self):
        settings = QSettings()
        settings.setValue('pos', self.pos())
        settings.setValue('size', self.size())

    def maybeSave(self):
        if self.textEdit.document().isModified():
            ret = QMessageBox.warning(self, "SDI",
                    "The document has been modified.\nDo you want to save "
                    "your changes?",
                    QMessageBox.Save | QMessageBox.Discard |
                    QMessageBox.Cancel)

            if ret == QMessageBox.Save:
                return self.save()

            if ret == QMessageBox.Cancel:
                return False

        return True

    def loadFile(self, fileName):
        file = QFile(fileName)
        if not file.open(QFile.ReadOnly | QFile.Text):
            QMessageBox.warning(self, "SDI",
                    "Cannot read file %s:\n%s." % (fileName, file.errorString()))
            return

        instr = QTextStream(file)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.textEdit.setPlainText(instr.readAll())
        QApplication.restoreOverrideCursor()

        self.setCurrentFile(fileName)
        self.statusBar().showMessage("File loaded", 2000)

    def saveFile(self, fileName):
        file = QFile(fileName)
        if not file.open(QFile.WriteOnly | QFile.Text):
            QMessageBox.warning(self, "SDI",
                    "Cannot write file %s:\n%s." % (fileName, file.errorString()))
            return False

        outstr = QTextStream(file)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        outstr << self.textEdit.toPlainText()
        QApplication.restoreOverrideCursor()

        self.setCurrentFile(fileName)
        self.statusBar().showMessage("File saved", 2000)
        return True

    def setCurrentFile(self, fileName):
        self.isUntitled = not fileName
        if self.isUntitled:
            self.curFile = "document%d.txt" % MainWindow.sequenceNumber
            MainWindow.sequenceNumber += 1
        else:
            self.curFile = QFileInfo(fileName).canonicalFilePath()

        self.textEdit.document().setModified(False)
        self.setWindowModified(False)

        self.setWindowTitle("%s[*] - SDI" % self.strippedName(self.curFile))

    def strippedName(self, fullFileName):
        return QFileInfo(fullFileName).fileName()

    def findMainWindow(self, fileName):
        canonicalFilePath = QFileInfo(fileName).canonicalFilePath()

        for widget in QApplication.instance().topLevelWidgets():
            if isinstance(widget, MainWindow) and widget.curFile == canonicalFilePath:
                return widget

        return None





class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        tabs = FancyTabWidget()
        self.setCentralWidget(tabs)

        icon = self.style().standardIcon

        welcome_page = WelcomePage()
        tabs.addTab(welcome_page,
                    icon(QStyle.SP_DialogHelpButton),
                    "Welcome",
                    "Select active course")

        config_page = ConfigPage()
        tabs.addTab(config_page,
                    icon(QStyle.SP_FileDialogDetailedView),
                    "Configure",
                    "Configure active course")

        self.compile_page = compile_page = CompilePage()
        compile_page.set_tabs(4)
        tabs.addTab(compile_page,
                    icon(QStyle.SP_ComputerIcon),
                    "Compile",
                    "Compile and validate active course")

        compile_page.tabs.process_started.connect(lambda: tabs.setTabsEnabled(False))
        compile_page.tabs.process_completed.connect(tabs.setTabsEnabled)
        compile_page.tabs.process_stopped.connect(tabs.setTabsEnabled)

        tabs.setBarVisible(False)
        welcome_page.courseSelected.connect(tabs.setBarVisible)

from PyQt5.QtCore import QTimer
import random
class TestData:
    def __init__(self, log):
        self.log = log
        self.lines = [
            ("Jotain sinistä", TextLogWidget.PALETTE.BLUE),
            ("Started preparing phase", None),
            ("\tPreparing step 1", None),
            ("\tStarted building phase", None),
            ("\tBuilding step 1", None),
            ("\tRunning container apluslms/compile-rst:latest:", None),
            ("find . -name ''*.rst' -exec touch {} \;", None),
            ("sphinx-build -b html -d _build/doctrees   . _build/html", None),
            ("Running Sphinx v1.6.5", None),
            ("loading translations [en]... done", None),
            ("loading pickled environment... done", None),
            ("building [mo]: targets for 0 po files that are out of date", None),
            ("building [html]: targets for 21 source files that are out of date", None),
            ("updating environment: 0 added, 21 changed, 0 removed", None),
            ("reading sources... [  4%] index", None),
            ("reading sources... [  9%] module01/chapter01", None),
            ("reading sources... [ 14%] module01/chapter02", None),
            ("reading sources... [ 19%] module01/index", None),
            ("reading sources... [ 23%] module02/01", None),
            ("reading sources... [ 28%] module02/index", None),
            ("Jotain punaista", TextLogWidget.PALETTE.RED),
        ]
        self.count = 0
        self.write()

    def write(self):
        self.count += 1
        line, color = random.choice(self.lines)
        self.log.write(line, color)
        if self.count < 50:
            QTimer.singleShot(random.randint(200, 1200), self.write)


def main():
    import sys
    app = createApplication(sys.argv)
    main = MainWindow()
    #generators = []
    #for step in ('eka', 'toka'):
    #    log = main.compile_page.add_step(step)
    #    generators.append(TestData(log))
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
