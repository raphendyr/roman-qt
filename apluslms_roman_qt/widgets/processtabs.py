from enum import Enum
from time import perf_counter

from PyQt5.QtCore import (
    Qt,
    QSize,
    pyqtSignal,
    pyqtSlot,

    QRect,
    QPointF,
    QVariantAnimation,
)
from PyQt5.QtGui import (
    QStandardItem,
    QStandardItemModel,

    QPainter,
    QPainterPath,
    QBrush,
    QColor,
    QLinearGradient,
    QPen,
    QRegion,

    QPaintEvent,
)
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QListView,
    QStackedWidget,
    QWidget,
    QStyle,
    QSizePolicy,
)

try:
    from .fancytabbar import FancyTab
    from .animations import Animation, RotatingIcon, LoadingDots
except ImportError:
    from fancytabbar import FancyTab
    from animations import Animation, RotatingIcon, LoadingDots


def create_gradient(color, darker=300):
    gradient = QLinearGradient(0, 0, 0, 100)
    gradient.setColorAt(0.0, color)
    gradient.setColorAt(1.0, color.darker(darker))
    return gradient

def create_gradient_colors(color, color_active):
    return (create_gradient(QColor(color)),
            create_gradient(QColor(color_active)))


COLORS = (
    # Unknown
    create_gradient_colors(Qt.gray, Qt.lightGray),
    # Success
    create_gradient_colors(Qt.darkGreen, Qt.green),
    # Failure
    create_gradient_colors(Qt.darkRed, Qt.red),
    # Active
    create_gradient_colors(Qt.darkCyan, Qt.cyan),
)


class State(Enum):
    UNKNOWN = 0
    SUCCESS = 1
    FAILURE = 2
    ACTIVE = 3

    def get_color(self, active):
        pair = COLORS[self.value]
        return pair[1 if active else 0]


class ProcessTab(FancyTab):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = State.UNKNOWN

    def update(self, *args):
        self._tabbar.update(*args)

    def setState(self, state):
        if state == State.ACTIVE:
            self.icon = LoadingDots(self._tabbar, duration=1000, parent=self)
            self.icon.start()
        elif self.icon:
            self.icon.stop()
            del self.icon
            self.icon = None
        self.state = state

    def get_color(self, active):
        return self.state.get_color(active)

class ProcessTabBar(QWidget):
    ANIMATION_FRAMES = 30

    process_started = pyqtSignal()
    step_started = pyqtSignal(int) # index
    step_completed = pyqtSignal(int, bool) # index, success
    process_completed = pyqtSignal(bool) # success
    process_stopped = pyqtSignal()
    tab_selected = pyqtSignal(int) # index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.num_tabs = 0
        self.states = []
        self.selected = None
        self._icon = RotatingIcon(self, self.style().standardIcon(QStyle.SP_BrowserReload))
        self._working_anim = anim = Animation(self, fps=15, duration=1400)
        self.process_completed.connect(anim.stop)
        self.process_started.connect(anim.start)
        anim.tick.connect(self._update_active)
        self._active_box = None

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
        self.setMinimumSize(64, 32)
        self.setMaximumHeight(64)

    def _update_active(self):
        if self._active_box:
            self.update(self._active_box)

    def set_tab_count(self, num):
        self.num_tabs = num
        names = ("Prepare", "apluslms/compile-ariel", "apluslms/compile-jsvee", "Validate", None, None, None)
        self.states = [ProcessTab(self, text=names[i]) for i in range(num+1)]

    def item_at(self, position):
        arrow_width = self._arrow_width
        x = position.x() - self._first_button_width

        #if x <= arrow_width and self._first_button_path.contains(position):
        #    return -1

        # make relative to index
        width = self._button_width
        i = int(x / width)
        x -= i * width

        if x <= arrow_width and self._button_path.contains(QPointF(x+width, position.y())):
            return i - 1
        return i

    @pyqtSlot()
    @pyqtSlot(QRect)
    def _update(self, *args):
        super().update(*args)
        print("update request for:", *args)

    def resizeEvent(self, event):
        height = self.height()
        self._arrow_width = arrow_width = height / 2
        self._first_button_width = first_width = height
        self._button_width = width = (self.width() - first_width) / (self.num_tabs + 1)

        self._first_button_path = fbutton = QPainterPath()
        fbutton.lineTo(first_width, 0)
        fbutton.lineTo(first_width + arrow_width, height / 2)
        fbutton.lineTo(first_width, height)
        fbutton.lineTo(0, height)
        fbutton.closeSubpath()

        self._button_path = button = QPainterPath()
        button.lineTo(width, 0)
        button.lineTo(width + arrow_width, height / 2)
        button.lineTo(width, height)
        button.lineTo(0, height)
        fbutton.closeSubpath()

        self._last_button_path = lbutton = QPainterPath()
        lbutton.lineTo(width, 0)
        lbutton.lineTo(width, height)
        lbutton.lineTo(0, height)
        fbutton.closeSubpath()

    _paint_times = None
    def paintEvent(self, event: QPaintEvent):
        _start = perf_counter()
        num = self.num_tabs
        selected = self.selected
        arrow_width = self._arrow_width
        height = self.height()
        width = self._button_width
        first_width = self._first_button_width
        button = self._button_path
        button_box = QRect(0, 0, width + arrow_width, height)
        first_box = QRect(0, 0, first_width + arrow_width, height)
        icon_area = QRect(arrow_width + 10, 0, max(48, width/2), height)
        text_box = QRect(arrow_width, 0, width-arrow_width, height)
        text_flags = Qt.AlignCenter | Qt.AlignVCenter
        states = self.states

        painter = QPainter(self)
        region = event.region()
        painter.setClipRegion(region)
        #torender = self._tabs_within(event.region())
        #print("regions:")
        #for rect in event.region().rects():
        #    print(" -  ", rect)
        #painter.setPen(Qt.NoPen)
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        titleFont = painter.font()
        titleFont.setPointSizeF(14)
        titleFont.setBold(True)
        painter.setFont(titleFont)

        painter.translate(num * width + first_width, 0)

        if region.intersects(painter.transform().mapRect(button_box)):
            painter.setBrush(states[num].get_color(num == selected))
            painter.drawPath(self._last_button_path)

        for i in reversed(range(num)):
            painter.translate(-width, 0)
            if not region.intersects(painter.transform().mapRect(button_box)):
                continue

            painter.setBrush(states[i].get_color(i == selected))
            painter.drawPath(button)

            if states[i].state == State.ACTIVE:
                painter.save()
                painter.setPen(Qt.NoPen)
                gw = (width+self._arrow_width) * 2
                gradient = QLinearGradient(0, 0, gw, 0)
                value = self._working_anim.value
                gradient.setColorAt(max(0.0, value-0.2), QColor(255, 255, 255, 0))
                gradient.setColorAt(value, QColor(255, 255, 255, 180))
                gradient.setColorAt(min(1.0, value+0.2), QColor(255, 255, 255, 0))
                brush = QBrush(gradient)
                brush.setTransform(brush.transform().translate(-gw/4, 0))
                gradient_height = int(height*0.2)
                painter.setBrush(brush)
                #painter.setClipRect(0, 0, width+self._arrow_width, gradient_height)
                #painter.drawPath(button)
                #painter.setClipRect(0, height-gradient_height, width+self._arrow_width, gradient_height)
                painter.drawPath(button)
                self._active_box = painter.transform().mapRect(button_box)
                painter.restore()

            #if states[i].icon:
            #    states[i].icon.paint(painter, icon_area)

            text = states[i].text
            if text:
                _, _, short = text.rpartition('-')
                painter.drawText(text_box, text_flags, short.capitalize())

        if region.intersects(first_box):
            painter.resetTransform()
            painter.setBrush(State.UNKNOWN.get_color(-1 == selected))
            painter.drawPath(self._first_button_path)

            if self.is_running:
                icon = self.style().standardIcon(QStyle.SP_MediaStop)
            else:
                icon = self.style().standardIcon(QStyle.SP_MediaPlay)

            size = min(self._first_button_width, self.height())*0.8
            painter.translate(5, (self.height()-size)/2)
            icon.paint(painter, QRect(0, 0, size, size))

        _end = perf_counter()
        if not self._paint_times:
            self._paint_times = times = []
        else:
            times = self._paint_times
        times.append(_end - _start)
        if len(times) > 60:
            avg = sum(times) / len(times) * 1000000
            print("Average render time %.2fns" % (avg,))
            self._paint_times = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            index = self.item_at(event.pos())
            if index is not None:
                self.select_tab(index)
                self.setFocus()
            if index == -1:
                if self.is_running:
                    self.stop()
                else:
                    self.start()

    def select_tab(self, index):
        self.selected = index
        self.update()
        self.tab_selected.emit(index)

    @property
    def is_running(self):
        return self._icon._animator.loopCount() == -1

    def complete(self, stopped=False):
        self._icon.stop()
        unknown = any(s.state == State.UNKNOWN for s in self.states[:-1])
        success = not stopped and all(s == State.SUCCESS for s in self.states[:-1])
        self.states[-1].setState(State.UNKNOWN if unknown else State.SUCCESS if success else State.FAILURE)
        self.update()
        self.process_completed.emit(success)

    def stop(self):
        self.complete(stopped=True)
        self.process_stopped.emit()
        for i, state in enumerate(self.states):
            if state.state == State.ACTIVE:
                self.states[i].setState(State.FAILURE)

    def start(self):
        self._icon.start()

        # reset states
        for state in self.states:
            state.setState(State.UNKNOWN)
        self.update()

        # global
        self.process_started.emit()

    def start_step(self, num):
        if 0 <= num < self.num_tabs:
            self.states[num].setState(State.ACTIVE)
            self.update()
            self.step_started.emit(num)
        elif num == self.num_tabs:
            self.complete()

    def complete_step(self, num, success=True):
        if 0 <= num < self.num_tabs:
            self.states[num].setState(State.SUCCESS if success else State.FAILURE)
            self.update()
            #if num == self.num_tabs - 1:
            #    self.complete()
            self.step_completed.emit(num, success)


if __name__ == '__main__':
    import sys, random
    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    view = ProcessTabBar()
    view.setWindowTitle("Test for ProgressTabWidget")
    view.setFixedSize(700, 48)
    view.set_tab_count(4)

    running = False

    def begin():
        global running
        running = True
        view.start_step(0)

    def stopped():
        global running
        running = False

    def done(success):
        if success and view.selected == view.num_tabs - 1:
            view.select_tab(view.num_tabs)
        print("Progress is completed with", "success" if success else "failure")

    def selected(num):
        print("tab: ", num)

    def started(num):
        if view.selected == num-1:
            view.select_tab(num)
        QTimer.singleShot(5000, lambda: complete(num))

    def complete(num):
        if running:
            view.complete_step(num, random.random() > 0.3)

    def completed(num, success):
        if success:
            view.start_step(num+1)
        else:
            view.stop()

    view.process_started.connect(begin)
    view.process_stopped.connect(stopped)
    view.process_completed.connect(done)
    view.tab_selected.connect(selected)
    view.step_started.connect(started)
    view.step_completed.connect(completed)

    view.show()
    sys.exit(app.exec_())
