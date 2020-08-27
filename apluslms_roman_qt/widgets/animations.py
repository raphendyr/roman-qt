from math import pi, cos

from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
    pyqtSlot,
    QObject,
    QVariant,
    QSize,
    QRect,
    QPoint,
    QVariantAnimation,
)
from PyQt5.QtGui import (
    QPainter,
    QIcon,
)
from PyQt5.QtWidgets import (
    QWidget,
)


class Animation(QVariantAnimation):
    tick = pyqtSignal(float)

    def __init__(self,
                 parent: QObject,
                 fps: int = 16,
                 duration: int = 1000):
        super().__init__(parent)

        self.value = 0.0
        self._frames = frames = int(fps * (duration / 1000.0))
        self._animator = animator = QVariantAnimation(self)
        animator.setStartValue(0)
        animator.setEndValue(frames)
        animator.setDuration(duration)
        animator.valueChanged.connect(self._animation_tick)

    @pyqtSlot(QVariant)
    def _animation_tick(self, animator_value: int):
        self.value = value = animator_value / self._frames
        self.tick.emit(value)

    @pyqtSlot()
    def start(self):
        animator = self._animator
        animator.stop()
        animator.setLoopCount(-1)
        animator.start()

    @pyqtSlot()
    def stop(self):
        animator = self._animator
        animator.setLoopCount(0)
        self._animation_tick(animator.currentValue())


class AnimationRenderer(Animation):
    def __init__(self,
                 target: QObject,
                 fps: int = 16,
                 duration: int = 1000,
                 parent: QObject = None):
        if parent is None:
            parent = target
        super().__init__(parent, fps=fps, duration=duration)
        self._target = target
        self._targetRect = None
        self.tick.connect(self._update_animation)

    @pyqtSlot()
    def _update_animation(self):
        rect = self._targetRect
        if rect:
            self._target.update(rect)
        # skip update request, if we have not been painted ever
        #else:
        #    self._target.update()

    def paint(self, painter: QPainter, rect: QRect):
        # store render region in target coordinates for update request
        self._targetRect = painter.transform().mapRect(rect)


class LoadingDots(AnimationRenderer):
    def __init__(self,
                 target: QObject,
                 size: QSize = None,
                 fps: int = 16,
                 duration: int = 1000,
                 parent: QObject = None):
        super().__init__(target=target, fps=fps, duration=duration, parent=parent)

        self._size = size
        self._dots = 3

    def paint(self, painter: QPainter, rect: QRect):
        super().paint(painter, rect)
        painter.save()
        painter.translate(rect.center())

        size = rect.size() # self._size
        dot_space = min(size.width()/self._dots, size.height()) # self._max_dot_r
        max_dot_r = dot_space/2 * 0.75
        min_dot_r = max_dot_r * 0.6
        state = self._animator.currentValue() / self._frames
        len = self._dots*2-1

        painter.translate(-(size.width()/2-dot_space/2), 0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.black)
        painter.setRenderHint(QPainter.Antialiasing, True)
        for i in range(self._dots):
            dot_s = (state - i/len) % 1
            dot_s = dot_s * len - 0.5
            dot_s = dot_s if dot_s < 0 else min(dot_s / (len-1), 0.5)
            dot_r = min_dot_r + (max_dot_r - min_dot_r) * cos(dot_s*pi)
            painter.drawEllipse(QPoint(0, 0), dot_r, dot_r)
            painter.translate(dot_space, 0)

        painter.restore()


class RotatingIcon(AnimationRenderer):
    def __init__(self,
                 target: QWidget,
                 icon: QIcon,
                 fps: int = 16,
                 duration: int = 2000,
                 parent: QObject = None):
        super().__init__(target=target, fps=fps, duration=duration, parent=parent)

        self.icon = icon

    def paint(self, painter: QPainter, rect: QRect):
        super().paint(painter, rect)
        # edge length of a box rotated 45 degrees and within box with edge of 1
        edge = min(rect.width(), rect.height()) * 0.7
        icon_area = QRect(0, 0, edge, edge)
        painter.save()
        painter.translate(rect.center())
        rotation = self._animator.currentValue() * 360 / self._frames
        painter.rotate(rotation)
        painter.translate(-icon_area.center())
        self.icon.paint(painter, icon_area)
        painter.restore()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QStyle

    class Dots(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)

            self.setFixedSize(128, 128)
            self.l = LoadingDots(self)
            self.l.start()

        def paintEvent(self, event):
            p = QPainter(self)
            self.l.paint(p, QRect(0, 0, self.width(), self.height()))

        def mousePressEvent(self, event):
            if self.l._animator.loopCount() == -1:
                self.l.stop()
            else:
                self.l.start()

    class Icon(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)

            self.setFixedSize(128, 128)
            self.i = RotatingIcon(self, fps=30, icon=self.style().standardIcon(QStyle.SP_BrowserReload))
            self.i.start()

        def paintEvent(self, event):
            p = QPainter(self)
            self.i.paint(p, QRect(0, 0, self.width(), self.height()))

    app = QApplication(sys.argv)

    view = QWidget()
    view.setWindowTitle("Test for LoadingDots")

    layout = QVBoxLayout()
    layout.addWidget(Dots(view))
    layout.addWidget(Icon(view))
    view.setLayout(layout)

    view.show()
    sys.exit(app.exec_())
