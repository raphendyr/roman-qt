from enum import Enum
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
    QFontMetrics,
    QFontDatabase,
    QColor,
    QPalette,
)
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTextEdit,
    QWidget,
)


class ColorPalette(Enum):
    BLACK = QColor("black")
    WHITE = QColor("white")
    BLUE = QColor("blue")
    RED = QColor("red")


class TextLogWidget(QTextEdit):
    PALETTE = ColorPalette

    def __init__(self, parent=None):
        super().__init__(parent)

        # Lock textedit for readonly mode
        self.setReadOnly(True)
        #self.setAcceptRichText(False)
        #self.setUndoRedoEnabled(False)

        # Add and set font
        font_db = QFontDatabase()
        font_db.addApplicationFont("/users/jkantoja/Develop/apluslms/roman-qt/apluslms_roman_qt/DejaVuSansMono.ttf")
        font = self.currentFont()
        font.setFamily("DejaVu Sans Mono")
        self.setFont(font)

        # Calculate tab stop
        ts = QFontMetrics(font).width('a') * 4
        self.setTabStopWidth(ts);

        # Background color and default font color
        palette = self.palette()
        palette.setColor(QPalette.Base, ColorPalette.BLACK.value)
        palette.setColor(QPalette.Text, ColorPalette.WHITE.value)
        self.setPalette(palette)
        self.setTextColor(ColorPalette.WHITE.value)

    def setSize(self, cols, rows):
        metrics = QFontMetrics(self.currentFont())
        cw, ch = metrics.width('a'), metrics.height()
        self.setFixedSize(cw*cols, ch*rows)

    def write(self, line, tag=None):
        cur_color = None
        if tag:
            cur_color = self.textColor()
            self.setTextColor(tag.value)
        self.append(str(line).rstrip())
        #self.insertPlainText(str(line).rstrip() + '\n')
        if cur_color:
            self.setTextColor(cur_color)


if __name__ == '__main__':
    import sys, time
    from PyQt5.QtCore import QTimer
    app = QApplication(sys.argv)

    class TestData:
        def __init__(self, log):
            self.log = log
            self.lines = [
                ("Jotain sinistä", ColorPalette.BLUE),
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
                ('reading sources... [ 19%] module01/index', None),
                ("reading sources... [ 23%] module02/01", None),
                ("reading sources... [ 28%] module02/index", None),
                ("Jotain punaista", ColorPalette.RED),
            ]
            self.line = 0
            self.write()

        def write(self):
            if self.line >= len(self.lines):
                self.line = 0
            line, color = self.lines[self.line]
            self.line += 1
            self.log.write(line, color)
            QTimer.singleShot(200, self.write)

    view = TextLogWidget()
    view.setWindowTitle("Test for LogView")
    view.setSize(80, 20)

    test = TestData(view)

    #print(view.toHtml())
    #print(view.toPlainText())
    view.show()
    sys.exit(app.exec_())
