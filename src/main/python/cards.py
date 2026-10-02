"""Small building blocks shared by the pages."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPolygon
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from theme import COLORS


class Card(QFrame):
    """
    A panel with a small uppercase header strip. Offers setTitle like a group box, which is what the rest of the
    code expects. Its contents go into body, a grid layout.
    """

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("panelHeader")
        self.head = QHBoxLayout(header)
        self.head.setContentsMargins(12, 6, 12, 6)
        self.head.setSpacing(10)
        self._title = QLabel(title)
        self._title.setObjectName("panelTitle")
        font = QFont(self._title.font())
        font.setCapitalization(QFont.AllUppercase)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.1)
        self._title.setFont(font)
        self.head.addWidget(self._title)
        self.head.addStretch(1)
        outer.addWidget(header)

        body = QWidget()
        body.setObjectName("panelBody")
        self.body = QGridLayout(body)
        self.body.setContentsMargins(14, 12, 14, 14)
        self.body.setHorizontalSpacing(12)
        self.body.setVerticalSpacing(8)
        self.body.setColumnStretch(0, 1)
        outer.addWidget(body, 1)
        self._next_row = 0

    def setTitle(self, title):
        self._title.setText(title)

    def title(self):
        return self._title.text()

    def add_row(self, label, control, icon=None):
        text = QLabel(label)
        text.setObjectName("rowLabel")
        if icon is not None:  # a pixmap shown before the label, in a slot of the same size for every row
            holder = QWidget()
            holder_layout = QHBoxLayout(holder)
            holder_layout.setContentsMargins(0, 0, 0, 0)
            holder_layout.setSpacing(8)
            picture = QLabel()
            picture.setPixmap(icon)
            picture.setFixedSize(32, 32)
            picture.setAlignment(Qt.AlignCenter)
            picture.setStyleSheet("background: transparent;")
            holder_layout.addWidget(picture)
            holder_layout.addWidget(text)
            holder_layout.addStretch(1)
            self.body.addWidget(holder, self._next_row, 0)
        else:
            self.body.addWidget(text, self._next_row, 0)
        self.body.addWidget(control, self._next_row, 1)
        self._next_row += 1
        self.body.setRowStretch(self._next_row, 1)


class Banner(QLabel):
    """A line of text that offers setTitle like a group box (the rank summary above the classes)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("banner")

    def setTitle(self, title):
        self.setText(title.replace("Classes - ", "", 1))


class HazardStripe(QWidget):
    """a strip of diagonal amber and black bars, as on the game's hazard markings"""

    def __init__(self, height=6, parent=None):
        super().__init__(parent)
        self.setFixedHeight(height)

    def paintEvent(self, event):
        painter = QPainter(self)
        h = self.height()
        painter.fillRect(self.rect(), QColor("#1a1710"))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(COLORS["accent"]))
        step = h * 2
        x = -h
        while x < self.width():
            painter.drawPolygon(QPolygon([QPoint(x, h), QPoint(x + h, 0), QPoint(x + h + h, 0), QPoint(x + h, h)]))
            x += step
