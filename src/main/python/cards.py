"""Small building blocks shared by the pages."""
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout


class Card(QFrame):
    """A titled panel. Offers setTitle like a group box, which is what the rest of the code expects."""

    def __init__(self, title="", accent=None, parent=None, pixmap=None):
        super().__init__(parent)
        self.setObjectName("card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 20)
        outer.setSpacing(14)

        head = QHBoxLayout()
        head.setSpacing(10)
        if pixmap is not None:
            picture = QLabel()
            picture.setPixmap(pixmap)
            picture.setFixedSize(pixmap.size())
            picture.setStyleSheet("background: transparent; border: none;")
            head.addWidget(picture)
        elif accent:
            dot = QLabel()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background: {accent}; border-radius: 5px; border: none;")
            head.addWidget(dot)
        self._title = QLabel(title)
        self._title.setObjectName("cardTitle")
        head.addWidget(self._title)
        head.addStretch(1)
        self.head = head
        outer.addLayout(head)

        self.body = QGridLayout()
        self.body.setHorizontalSpacing(14)
        self.body.setVerticalSpacing(10)
        self.body.setColumnStretch(0, 1)
        outer.addLayout(self.body, 1)
        self._next_row = 0

    def setTitle(self, title):
        self._title.setText(title)

    def title(self):
        return self._title.text()

    def add_row(self, label, control):
        text = QLabel(label)
        text.setObjectName("rowLabel")
        self.body.addWidget(text, self._next_row, 0)
        self.body.addWidget(control, self._next_row, 1)
        self._next_row += 1
        self.body.setRowStretch(self._next_row, 1)


class Banner(QLabel):
    """A line of text that offers setTitle like a group box (the rank summary above the class cards)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("banner")

    def setTitle(self, title):
        self.setText(title.replace("Classes - ", "", 1))
