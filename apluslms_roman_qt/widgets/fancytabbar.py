"""
This module provides vertical nice looking tab bar and widget.

Code is python port of fancytabwidget.h/cpp from qt-creator
https://github.com/qt-creator/qt-creator/blob/84e17dd0f862702c5389c7d9f556141fa2181d2c/src/plugins/coreplugin/fancytabwidget.h
https://github.com/qt-creator/qt-creator/blob/84e17dd0f862702c5389c7d9f556141fa2181d2c/src/plugins/coreplugin/fancytabwidget.cpp

StyleHelper and other theming parts are interated here.
In addition, there are some optimization to shorten evaluation time.
Though, some of the features provided by the original version are not
reimplemented including menu for tab buttons.

Note that as a port this module stays under the same license as the source.
The source, QtCreator, is released under GPLv3 license with an exception.
https://github.com/qt-creator/qt-creator/blob/master/LICENSE.GPL3-EXCEPT
"""

from PyQt5.QtCore import (
    Qt,
    QObject,
    QEvent,
    QSize,
    QRect,
    QRectF,
    QPoint,
    QPropertyAnimation,
    QTimer,
    pyqtSignal,
    pyqtProperty,
    pyqtSlot,
)
from PyQt5.QtGui import (
    QFontMetrics,
    QPaintEvent,
    QMouseEvent,
    QResizeEvent,
    QFont,
    QStandardItem,
    QStandardItemModel,
    qGray,
    qAlpha,
    qRgba,
    QIcon,
    QColor,
    QImage,
    QPixmap,
    QPixmapCache,
    QPainter,
    QBrush,
    QLinearGradient,
)
from PyQt5.QtWidgets import (
    QSizePolicy,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QListView,
    QStackedLayout,
    QWidget,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsBlurEffect,
    QToolTip,
    QStatusBar,
)

def limit_to_255(value: float) -> int:
    return 255 if value > 255 else 0 if value < 0 else int(value)

_isMacHost = True
BASE_COLOR = QColor("#666666")
SIDEBAR_FONT_SIZE = (10 if _isMacHost else 7.5) * 1.2
MODEBAR_ICON_SIZE = 64
TOOLBAR_ICON_SHADOW = True
FLAT_STYLE = False
HIGHLIGHT_COLOR = QColor.fromHsv(
    BASE_COLOR.hue(),
    BASE_COLOR.saturation(),
    limit_to_255(BASE_COLOR.value() * 1.16))
SHADOW_COLOR = QColor.fromHsv(
    BASE_COLOR.hue(),
    limit_to_255(BASE_COLOR.saturation() * 1.1),
    limit_to_255(BASE_COLOR.value() * 0.70))
BORDER_COLOR = QColor.fromHsv(
    BASE_COLOR.hue(),
    BASE_COLOR.saturation(),
    limit_to_255(BASE_COLOR.value() / 2))
FancyToolButtonSelectedColor = QColor("#32000000")
FancyToolButtonHoverColor = QColor("#28ffffff")
FancyTabWidgetDisabledSelectedTextColor = QColor("#ffffffff")
FancyTabWidgetDisabledUnselectedTextColor = QColor("#78ffffff")
FancyTabWidgetEnabledSelectedTextColor = QColor("#ffcccccc")
FancyTabWidgetEnabledUnselectedTextColor = QColor("#ffffffff")


def disabledSideBarIcon(enabledicon: QPixmap) -> QPixmap:
    im = enabledicon.toImage().convertToFormat(QImage.Format_ARGB32)
    for y in range(im.height()):
        for x in range(im.width()):
            pixel = im.pixel(x, y)
            intensity = qGray(pixel)
            im.setPixel(x, y, qRgba(intensity, intensity, intensity, qAlpha(pixel)))
    return QPixmap.fromImage(im)

# Draws a cached pixmap with shadow
def drawIconWithShadow(icon: QIcon,
                       rect: QRect,
                       p: QPainter,
                       iconMode: QIcon.Mode = None,
                       dipRadius: int = None,
                       color: QColor = None,
                       dipOffset: QPoint = None):
    if iconMode is None:
        iconMode = QIcon.Normal
    if color is None:
        color = QColor(0, 0, 0, 130)
    if dipRadius is None:
        dipRadius = 3
    if dipOffset is None:
        dipOffset = QPoint(1, -2)

    devicePixelRatio: int = p.device().devicePixelRatio()
    pixmapName = "icon %s %s %s %s" % (icon.cacheKey(), iconMode, rect.height(), devicePixelRatio)
    cache = QPixmapCache.find(pixmapName)
    if cache is None:
        # High-dpi support: The in parameters (rect, radius, offset) are in
        # device-independent pixels. The call to QIcon::pixmap() below might
        # return a high-dpi pixmap, which will in that case have a devicePixelRatio
        # different than 1. The shadow drawing caluculations are done in device
        # pixels.
        window = p.device().window().windowHandle()
        px = icon.pixmap(window, rect.size(), iconMode)
        radius = dipRadius * devicePixelRatio
        offset = dipOffset * devicePixelRatio
        cache = QPixmap(px.size() + QSize(radius * 2, radius * 2))
        cache.fill(Qt.transparent)
        cachePainter = QPainter(cache)

        if iconMode == QIcon.Disabled:
            hasDisabledState = len(icon.availableSizes()) == len(icon.availableSizes(QIcon.Disabled))
            if not hasDisabledState:
                px = disabledSideBarIcon(icon.pixmap(window, rect.size()))
        elif TOOLBAR_ICON_SHADOW:
            # Draw shadow
            tmp = QImage(px.size() + QSize(radius * 2, radius * 2 + 1), QImage.Format_ARGB32_Premultiplied)
            tmp.fill(Qt.transparent)

            tmpPainter = QPainter(tmp)
            tmpPainter.setCompositionMode(QPainter.CompositionMode_Source)
            tmpPainter.drawPixmap(QRect(radius, radius, px.width(), px.height()), px)
            tmpPainter.end()

            # blur the alpha channel
            blurred = QImage(tmp.size(), QImage.Format_ARGB32_Premultiplied)
            blurred.fill(Qt.transparent)
            blurPainter = QPainter(blurred)
            #qt_blurImage(blurPainter, tmp, radius, False, True)
            # implement qt_blurImage via QLabel with QGraphicsBlurEffect
            # FIXME: alignment is broken
            scene = QGraphicsScene()
            item = QGraphicsPixmapItem(QPixmap.fromImage(tmp))
            effect = QGraphicsBlurEffect()
            effect.setBlurRadius(radius)
            item.setGraphicsEffect(effect)
            scene.addItem(item)
            scene.render(blurPainter)
            blurPainter.end()
            tmp = blurred

            # blacken the image...
            tmpPainter.begin(tmp);
            tmpPainter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            tmpPainter.fillRect(tmp.rect(), color)
            tmpPainter.end()

            tmpPainter.begin(tmp)
            tmpPainter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            tmpPainter.fillRect(tmp.rect(), color)
            tmpPainter.end()

            # draw the blurred drop shadow...
            cachePainter.drawImage(QRect(0, 0, cache.rect().width(), cache.rect().height()), tmp)

        # Draw the actual pixmap...
        cachePainter.drawPixmap(QRect(QPoint(radius, radius) + offset, QSize(px.width(), px.height())), px)
        cachePainter.end()
        cache.setDevicePixelRatio(devicePixelRatio)
        QPixmapCache.insert(pixmapName, cache)

    targetRect = cache.rect()
    targetRect.setSize(targetRect.size() / cache.devicePixelRatio())
    targetRect.moveCenter(rect.center() - dipOffset)
    p.drawPixmap(targetRect, cache)


def verticalGradientHelper(p: QPainter, spanRect: QRect, rect: QRect):
    highlight = HIGHLIGHT_COLOR
    shadow = SHADOW_COLOR
    grad = QLinearGradient(spanRect.topRight(), spanRect.topLeft())
    grad.setColorAt(0, highlight.lighter(117))
    grad.setColorAt(1, shadow.darker(109))
    p.fillRect(rect, grad)

    light = QColor(255, 255, 255, 80)
    p.setPen(light);
    p.drawLine(rect.topRight() - QPoint(1, 0), rect.bottomRight() - QPoint(1, 0))
    dark = QColor(0, 0, 0, 90)
    p.setPen(dark)
    p.drawLine(rect.topLeft(), rect.bottomLeft())

def verticalGradient(painter: QPainter, spanRect: QRect, clipRect: QRect):
    keyColor = BASE_COLOR
    key = "verticalGradient %d %d %d %d %d" % (spanRect.width(), spanRect.height(), clipRect.width(), clipRect.height(), keyColor.rgb())

    pixmap = QPixmapCache.find(key)
    if pixmap is None:
        pixmap = QPixmap(clipRect.size())
        p = QPainter(pixmap)
        rect = QRect(0, 0, clipRect.width(), clipRect.height())
        verticalGradientHelper(p, spanRect, rect)
        p.end();
        QPixmapCache.insert(key, pixmap)

    painter.drawPixmap(clipRect.topLeft(), pixmap)


class FancyTab(QObject):
    """State information and animator for single tab"""

    def __init__(self,
                 tabbar,
                 icon: QIcon = None,
                 text: str = None,
                 toolTip: str = None):
        super().__init__()
        self._tabbar = tabbar
        self.icon = icon
        self.text = text
        self.toolTip = toolTip
        self.enabled = True
        self._fader = 0
        self.fadeInDelay = 80
        self.fadeOutDelay = 100
        self._animator = animator = QPropertyAnimation(self)
        animator.setPropertyName(b"fader")
        animator.setTargetObject(self)

    @pyqtProperty(float)
    def fader(self) -> float:
        return self._fader

    @fader.setter
    def fader(self, value: float):
        self._fader = value
        self._tabbar.update()

    def fadeIn(self):
        animator = self._animator
        animator.stop()
        animator.setDuration(self.fadeInDelay)
        animator.setEndValue(1.0)
        animator.start()

    def fadeOut(self):
        animator = self._animator
        animator.stop()
        animator.setDuration(self.fadeOutDelay)
        animator.setEndValue(0.0)
        animator.start()


class FancyTabBar(QWidget):
    """QWidget of the tabbar part"""

    currentChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hoverRect = QRect()
        self._hoverIndex = -1
        self._enabled = True
        self.__minimumTabSizeHint = None
        self.__tabSize = None
        self.__currentIndex = -1
        self._tabs = []

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setMinimumWidth(44)
        self.setAttribute(Qt.WA_Hover, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True) # Needed for hover events

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.ToolTip:
            tt = self.isValidIndex(self._hoverIndex) and self.tabToolTip(self._hoverIndex)
            if tt:
                QToolTip.showText(event.globalPos(), tt, self, self._hoverRect)
            else:
                QToolTip.hideText()
                event.ignore()
            return True
        return super().event(event)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.__tabSize = None

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        if FLAT_STYLE:
            p.fillRect(event.rect(), BASE_COLOR)

        current = self._currentIndex
        paintTab = self.paintTab
        for i, tab in enumerate(self._tabs):
            if i != current:
                paintTab(p, i)

        if current != -1:
            paintTab(p, current)

    def paintTab(self, painter: QPainter, index: int):
        if not self.isValidIndex(index):
            return
        painter.save()

        tab = self._tabs[index]
        rect = self._tabRect(index)
        selected = index == self._currentIndex
        enabled = self._enabled and tab.enabled

        if selected:
            painter.fillRect(rect, FancyToolButtonSelectedColor)

        tabText = tab.text
        tabTextRect = QRect(rect)
        drawIcon = rect.height() > 36
        tabIconRect = QRect(rect)

        tabTextRect.translate(0, -2 if drawIcon else 1)
        boldFont = QFont(painter.font())
        boldFont.setPointSizeF(SIDEBAR_FONT_SIZE)
        boldFont.setBold(True)
        painter.setFont(boldFont)
        #painter.setPen(QColor(255, 255, 255, 160) if selected else QColor(0, 0, 0, 110))
        textFlags = Qt.AlignCenter | (Qt.AlignBottom if drawIcon else Qt.AlignVCenter) | Qt.TextWordWrap

        fader = tab.fader
        if fader > 0 and not selected and enabled:
            painter.save()
            painter.setOpacity(fader)
            painter.fillRect(rect, FancyToolButtonHoverColor)
            painter.restore()

        if not enabled:
            painter.setOpacity(0.7);

        if drawIcon:
            textHeight = (painter
                .fontMetrics()
                .boundingRect(QRect(0, 0, self.width(), self.height()), Qt.TextWordWrap, tabText)
                .height())
            tabIconRect.adjust(0, 4, 0, -textHeight - 4);
            iconMode = (QIcon.Active if selected else QIcon.Normal) if enabled else QIcon.Disabled
            iconRect = QRect(0, 0, MODEBAR_ICON_SIZE, MODEBAR_ICON_SIZE)
            iconRect.moveCenter(tabIconRect.center())
            iconRect = iconRect.intersected(tabIconRect)
            drawIconWithShadow(tab.icon, iconRect, painter, iconMode)

        if enabled:
            penColor = FancyTabWidgetEnabledSelectedTextColor if selected else FancyTabWidgetEnabledUnselectedTextColor
        else:
            penColor = FancyTabWidgetDisabledSelectedTextColor if selected else FancyTabWidgetDisabledUnselectedTextColor
        painter.setPen(penColor)
        painter.translate(0, -1);
        painter.drawText(tabTextRect, textFlags, tabText);

        painter.restore()

    def mousePressEvent(self, event: QMouseEvent):
        event.accept()
        pos = event.pos()
        index = self._hoverIndex
        if not self.isValidIndex(index) or not self._hoverRect.contains(pos):
            index, _ = self._getTabIndexAt(pos)
            if not self.isValidIndex(index):
                return
        if self._enabled and self._tabs[index].enabled:
            self._currentIndex = index # triggers update and signal

    def mouseMoveEvent(self, event: QMouseEvent):
        # Handle hover events for mouse fade ins
        pos = event.pos()

        # still inside current tab
        if self._hoverRect.contains(pos):
            return

        oldHover = self._hoverIndex
        newHover, rect = self._getTabIndexAt(pos)

        # movement on invalid area will hit here
        if newHover == oldHover:
            return

        if self.isValidIndex(oldHover):
            self._tabs[oldHover].fadeOut()
        if self.isValidIndex(newHover):
            self._tabs[newHover].fadeIn()
        self._hoverIndex = newHover
        self._hoverRect = rect
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent):
        self._hoverRect = QRect()
        self._hoverIndex = -1
        for tab in self._tabs:
            tab.fadeOut()
        super().leaveEvent(event)

    @property
    def _currentIndex(self) -> int:
        return self.__currentIndex

    @_currentIndex.setter
    def _currentIndex(self, index: int):
        if self.__currentIndex != index:
            self.__currentIndex = index
            self.update()
            # update tabbar before emiting the signal
            QTimer.singleShot(0, lambda: self.currentChanged.emit(index))

    def currentIndex(self) -> int:
        return self._currentIndex

    @pyqtSlot(int)
    def setCurrentIndex(self, index: int):
        if self.isTabEnabled(index) and index != self._currentIndex:
            self._currentIndex = index

    def isValidIndex(self, index: int):
        return index >= 0 and index < len(self._tabs)

    @pyqtSlot()
    def updateGeometry(self):
        # Reset cached size variables on geometry change
        self.__minimumTabSizeHint = None
        self.__tabSize = None
        super().updateGeometry()

    def sizeHint(self) -> QSize:
        ts = self._tabSizeHint()
        return QSize(ts.width(), ts.height() * len(self._tabs))

    def minimumSizeHint(self) -> QSize:
        ts = self._minimumTabSizeHint()
        return QSize(ts.width(), ts.height() * len(self._tabs))

    def _tabSizeHint(self) -> QSize:
        ts = self._minimumTabSizeHint()
        return ts + QSize(0, MODEBAR_ICON_SIZE)

    def _minimumTabSizeHint(self) -> QSize:
        cached = self.__minimumTabSizeHint
        if cached:
            return cached

        boldFont = self.font()
        boldFont.setPointSizeF(SIDEBAR_FONT_SIZE)
        boldFont.setBold(True)
        fm = QFontMetrics(boldFont)
        spacing = 8
        tabs = self._tabs
        maxLabelwidth = max(fm.width(tab.text) for tab in tabs) if tabs else 0
        ts = QSize(
            max(MODEBAR_ICON_SIZE*1.2 + spacing, maxLabelwidth) + 4,
            spacing + fm.height()
        )
        self.__minimumTabSizeHint = ts
        return ts

    @property
    def _tabSize(self) -> QSize:
        cached = self.__tabSize
        if cached:
            return cached

        ts = self._tabSizeHint()
        tabs = len(self._tabs)
        height = self.height()
        if ts.height() * tabs > height:
            ts.setHeight(height / tabs)
        self.__tabSize = ts
        return ts


    def _tabRect(self, index: int) -> QRect:
        ts = self._tabSize
        th = ts.height()
        return QRect(0, index * th, ts.width(), th)

    def _getTabIndexAt(self, pos: QPoint) -> (int, QRect):
        ts = self._tabSize
        tw, th = ts.width(), ts.height()
        for index in range(len(self._tabs)):
            rect = QRect(0, index*th, tw, th)
            if rect.contains(pos):
                return (index, rect)
        return (-1, QRect())

    @pyqtSlot()
    @pyqtSlot(bool)
    def setEnabled(self, enable: bool = True):
        self._enabled = enable
        self.update()

    def isEnabled(self) -> bool:
        return self._enabled

    @pyqtSlot(int)
    @pyqtSlot(int, bool)
    def setTabEnabled(self, index: int, enable: bool = True):
        if self.isValidIndex(index):
            self._tabs[index].enabled = enable
            self.update(self._tabRect(index))

    def isTabEnabled(self, index: int) -> bool:
        return self.isValidIndex(index) and self._tabs[index].enabled

    def insertTab(self, index: int, icon: QIcon, label: str, toolTip: str = None):
        tab = FancyTab(self, icon, label, toolTip=toolTip)
        self._tabs.insert(index, tab)
        if (self._currentIndex >= index):
            self._currentIndex += 1
        self.updateGeometry()

    def removeTab(self, index: int):
        tabs = self._tabs
        tab = tabs.pop(index)
        del tab
        self.updateGeometry()
        if not tabs:
            self._currentIndex = -1

    @pyqtSlot(int, str)
    def setTabToolTip(self, index: int, tooltip: str):
        self._tabs[index].toolTip = tooltip

    def tabToolTip(self, index: int) -> str:
        return self._tabs[index].toolTip

    def __len__(self) -> int:
        return len(self._tabs)
    count = __len__


class FancyTabWidget(QWidget):
    currentAboutToShow = pyqtSignal(int)
    currentChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Bar/Panel area

        self._bar = bar = QWidget(self)
        bar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        bar.setAutoFillBackground(False)
        barLayout = QVBoxLayout()
        barLayout.setSpacing(0)
        barLayout.setContentsMargins(0, 0, 0, 0)
        bar.setLayout(barLayout)

        self._tabbar = tabbar = FancyTabBar(self)
        barLayout.addWidget(tabbar, 1)

        self._corner = corner = QWidget(self)
        corner.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        corner.setAutoFillBackground(False)
        self._cornerLayout = cornerLayout = QVBoxLayout()
        cornerLayout.setSpacing(0)
        cornerLayout.setContentsMargins(0, 0, 0, 0)
        cornerLayout.addStretch()
        corner.setLayout(cornerLayout)
        barLayout.addWidget(corner, 0)

        # Right half

        contentLayout = QVBoxLayout()
        contentLayout.setSpacing(0)
        contentLayout.setContentsMargins(0, 0, 0, 0)

        self._stack = stack = QStackedLayout()
        contentLayout.addLayout(stack)

        self._statusBar = statusBar = QStatusBar()
        statusBar.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        contentLayout.addWidget(statusBar)

        mainLayout = QHBoxLayout()
        mainLayout.setSpacing(1)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.addWidget(bar)
        mainLayout.addLayout(contentLayout)
        self.setLayout(mainLayout)

        tabbar.currentChanged.connect(self._showWidget)

    def statusBar(self) -> QStatusBar:
        return self._statusBar

    def addTab(self, tab: QWidget, icon: QIcon, label: str, toolTip: str = None) -> int:
        index = len(self._tabbar)
        self.insertTab(index, tab, icon, label, toolTip)
        return index

    def insertTab(self, index: int, tab: QWidget, icon: QIcon, label: str, toolTip: str = None):
        self._stack.insertWidget(index, tab)
        self._tabbar.insertTab(index, icon, label, toolTip)

    def removeTab(self, index: int):
        if self._tabbar.isValidIndex(index):
            self._stack.removeWidget(self._stack.widget(index))
            self._tabbar.removeTab(index)

    def setBackgroundBrush(self, brush: QBrush):
        pal = QPalette()
        pal.setBrush(QPalette.Mid, brush)
        self._tabbar.setPalette(pal)
        self._corner.setPalette(pal)

    def paintEvent(self, event: QPaintEvent):
        bar = self._bar
        if bar.isVisible():
            painter = QPainter(self)

            rect = bar.rect().adjusted(0, 0, 1, 0)
            rect = self.style().visualRect(self.layoutDirection(), self.geometry(), rect)
            boderRect = QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)

            if not FLAT_STYLE:
                verticalGradient(painter, rect, rect)

            painter.setPen(BORDER_COLOR)
            painter.drawLine(boderRect.topRight(), boderRect.bottomRight())

    def cornerWidgetCount(self) -> int:
        return self._cornerLayout.count()

    def addCornerWidget(self, widget: QWidget):
        self._cornerLayout.addWidget(widget)

    def insertCornerWidget(self, index: int, widget: QWidget):
        layout = self._cornerLayout
        layout.insertWidget(index, widget)

    def setTabToolTip(self, index: int, toolTip: str):
        self._tabbar.setTabToolTip(index, toolTip)

    def tabToolTip(self, index: int) -> str:
        return self._tabbar.tabToolTip(index)

    @pyqtSlot(int)
    @pyqtSlot(int, bool)
    def setTabEnabled(self, index: int, enable: bool):
        self._tabbar.setTabEnabled(index, enable)

    def isTabEnabled(self, index: int) -> bool:
        return self._tabbar.isTabEnabled(index)

    @pyqtSlot()
    @pyqtSlot(bool)
    def setTabsEnabled(self, enable: bool = True):
        self._tabbar.setEnabled(enable)

    def isTabsEnabled(self) -> bool:
        return self._tabbar.isEnabled()

    @pyqtSlot()
    @pyqtSlot(bool)
    def setBarVisible(self, visible: bool = True):
        self._bar.setVisible(visible)

    def isBarVisible(self) -> bool:
        return self._bar.isVisible()

    def currentIndex(self) -> int:
        return self.tabbar.currentIndex()

    @pyqtSlot(int)
    def setCurrentIndex(self, index: int):
        self._tabbar.setCurrentIndex(index)

    def _showWidget(self, index: int):
        self.currentAboutToShow.emit(index)
        self._stack.setCurrentIndex(index)
        self.currentChanged.emit(index)

    def add_page(self, label, icon, widget):
        self.insertTab(len(self._tabbar), widget, icon, label)

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QStyle

    class TestPage(QWidget):
        def __init__(self, name, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Page..."))
            layout.addWidget(QLabel("...and the name is..."))
            layout.addWidget(QLabel(name))
            self.setLayout(layout)

    app = QApplication(sys.argv)

    view = FancyTabWidget()
    view.setWindowTitle("Test for FancyTabWidget")
    #view.setFixedSize(500, 300)
    icon = view.style().standardIcon

    view.addTab(TestPage("eka sivu"),
                icon(QStyle.SP_DirIcon),
                "eka", "eka tabi")
    view.addTab(TestPage("toka sivu"),
                icon(QStyle.SP_MediaPlay),
                "toka", "toka tabi")
    view.addTab(TestPage("kolmas sivu"),
                icon(QStyle.SP_MediaStop),
                 "kolmas", "kolmas tabi")
    view.addTab(TestPage("neljas sivu joo joo "),
                icon(QStyle.SP_DriveHDIcon),
                "neljas", "neljas tabi")
    view.addTab(TestPage("viides sivu"),
                icon(QStyle.SP_TitleBarMenuButton),
                "viides", "viides tabi")

    button = QPushButton("hide")
    view.addCornerWidget(button)
    def clicked():
        view.setBarVisible(not view.isBarVisible())
    button.clicked.connect(clicked)

    showButton = QPushButton("show")
    view.statusBar().addWidget(showButton)
    showButton.clicked.connect(clicked)

    def selected(num):
        print("Tab selected:", num)
    view.currentChanged.connect(selected)

    view.show()
    sys.exit(app.exec_())
