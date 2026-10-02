"""The editor's look: a dark Deep Rock palette with amber accents, applied to the whole application."""
import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import QApplication

COLORS = {
    "bg": "#14161a",
    "sidebar": "#101215",
    "card": "#1b1e24",
    "card_border": "#2a2e37",
    "input": "#14161a",
    "input_border": "#323743",
    "button": "#262a33",
    "button_hover": "#2f343f",
    "button_border": "#383e4b",
    "text": "#e9e7e2",
    "muted": "#8d93a0",
    "disabled": "#5a606c",
    "accent": "#f5a524",
    "accent_hover": "#ffb83d",
    "accent_pressed": "#d98f12",
    "on_accent": "#1a1204",
    "selection": "#3a2f17",
    "danger": "#ef6a60",
    "success": "#63c68c",
    "row_alt": "#171a1f",
}

# the four classes, as the game colours them
CLASS_COLORS = {
    "Driller": "#D19724",
    "Engineer": "#C2494A",
    "Gunner": "#6A9B68",
    "Scout": "#2F8FCB",
}

# status of an overclock or cosmetic in the Overclocks & Cosmetics tree
STATUS_COLORS = {
    "Forged": COLORS["success"],
    "Unforged": COLORS["accent"],
    "Unacquired": COLORS["muted"],
}


def images_dir():
    """the class images sit in an images folder next to the exe when frozen, in src/main/images otherwise"""
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "images")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images")


_pixmaps = {}


def class_pixmap(class_name, size):
    """the class's portrait scaled to size x size, or None if the image is missing"""
    key = (class_name, size)
    if key not in _pixmaps:
        pixmap = QPixmap(os.path.join(images_dir(), class_name.lower() + ".png"))
        _pixmaps[key] = (
            pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation) if not pixmap.isNull() else None
        )
    return _pixmaps[key]


def class_icon(class_name, size=32):
    pixmap = class_pixmap(class_name, size)
    return QIcon(pixmap) if pixmap is not None else None


def stylesheet():
    c = COLORS
    return f"""
* {{
    font-family: "Segoe UI Variable Text", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
    color: {c["text"]};
}}
QMainWindow, QDialog {{ background: {c["bg"]}; }}
QWidget#pages, QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollArea {{ border: none; }}

/* ---- sidebar */
QFrame#sidebar {{ background: {c["sidebar"]}; border: none; border-right: 1px solid {c["card_border"]}; }}
QLabel#brand {{ color: {c["accent"]}; font-size: 15pt; font-weight: 800; letter-spacing: 1px; }}
QLabel#brandSub {{ color: {c["muted"]}; font-size: 9pt; }}
QPushButton#nav {{
    text-align: left; padding: 11px 16px; border: none; border-radius: 8px;
    background: transparent; color: {c["muted"]}; font-weight: 600;
}}
QPushButton#nav:hover {{ background: #191c22; color: {c["text"]}; }}
QPushButton#nav:disabled {{ color: {c["disabled"]}; background: transparent; }}
QLabel#welcomeTitle {{ font-size: 20pt; font-weight: 700; background: transparent; }}
QPushButton#nav:checked {{ background: #22262e; color: {c["text"]}; border-left: 3px solid {c["accent"]}; }}
QToolButton#sidebarAction {{
    text-align: left; padding: 10px 16px; border: 1px solid {c["button_border"]}; border-radius: 8px;
    background: transparent; color: {c["text"]}; font-weight: 600;
}}
QToolButton#sidebarAction:hover {{ background: #191c22; border-color: {c["accent"]}; }}
QToolButton#sidebarAction:disabled {{ color: {c["disabled"]}; border-color: {c["card_border"]}; }}

/* ---- top bar */
QFrame#topbar {{ background: transparent; border: none; }}
QLabel#pageTitle {{ font-size: 18pt; font-weight: 700; }}
QLabel#fileLabel {{ color: {c["muted"]}; font-size: 9pt; }}

/* ---- cards */
QFrame#card {{ background: {c["card"]}; border: 1px solid {c["card_border"]}; border-radius: 12px; }}
QLabel#cardTitle {{ font-size: 11pt; font-weight: 700; background: transparent; }}
QLabel#rowLabel {{ color: {c["muted"]}; background: transparent; }}
QLabel#muted, QLabel#hint {{ color: {c["muted"]}; background: transparent; }}
QLabel#banner {{ font-size: 13pt; font-weight: 600; color: {c["accent"]}; background: transparent; }}
QLabel#counts {{ color: {c["muted"]}; background: transparent; }}
QLabel#dirty {{ color: {c["accent"]}; font-weight: 600; background: transparent; }}

/* ---- inputs */
QLineEdit, QComboBox, QSpinBox {{
    background: {c["input"]}; border: 1px solid {c["input_border"]}; border-radius: 6px;
    padding: 6px 10px; min-height: 20px; selection-background-color: {c["accent"]}; selection-color: {c["on_accent"]};
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover {{ border-color: #454c5c; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border-color: {c["accent"]}; }}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{ color: {c["disabled"]}; background: #111317; border-color: #22262d; }}
QComboBox QAbstractItemView {{
    background: {c["card"]}; border: 1px solid {c["input_border"]}; outline: none;
    selection-background-color: {c["selection"]}; selection-color: {c["text"]};
}}

/* ---- buttons */
QPushButton, QToolButton {{
    background: {c["button"]}; border: 1px solid {c["button_border"]}; border-radius: 8px;
    padding: 8px 16px; font-weight: 600;
}}
QPushButton:hover, QToolButton:hover {{ background: {c["button_hover"]}; border-color: #4a5264; }}
QPushButton:pressed, QToolButton:pressed {{ background: #20242c; }}
QPushButton:disabled, QToolButton:disabled {{ color: {c["disabled"]}; background: #16181d; border-color: #22262d; }}
QPushButton#primary, QToolButton#primary {{ background: {c["accent"]}; color: {c["on_accent"]}; border: none; font-weight: 700; }}
QPushButton#primary:hover, QToolButton#primary:hover {{ background: {c["accent_hover"]}; }}
QPushButton#primary:pressed, QToolButton#primary:pressed {{ background: {c["accent_pressed"]}; }}
QPushButton#primary:disabled, QToolButton#primary:disabled {{ background: #3a3322; color: #7d7458; }}
QPushButton#danger {{ color: {c["danger"]}; }}
QPushButton#danger:hover {{ border-color: {c["danger"]}; }}
QPushButton#danger:disabled {{ color: {c["disabled"]}; }}
QPushButton#small {{ padding: 5px 12px; font-weight: 500; }}

/* ---- trees and lists */
QTreeWidget, QListWidget {{
    background: {c["input"]}; border: 1px solid {c["input_border"]}; border-radius: 8px;
    alternate-background-color: {c["row_alt"]}; outline: none; padding: 2px;
}}
QTreeWidget::item, QListWidget::item {{ padding: 4px 2px; border-radius: 4px; }}
QTreeWidget::item:hover, QListWidget::item:hover {{ background: #1f232a; }}
QTreeWidget::item:selected, QListWidget::item:selected {{ background: {c["selection"]}; color: {c["text"]}; }}
QTreeWidget:disabled, QListWidget:disabled {{ color: {c["disabled"]}; }}
QHeaderView::section {{
    background: {c["card"]}; color: {c["muted"]}; border: none; border-bottom: 1px solid {c["card_border"]};
    padding: 8px 10px; font-weight: 600;
}}

/* ---- scroll bars */
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #343a46; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #454d5c; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #343a46; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: #454d5c; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ---- misc */
QSplitter::handle {{ background: transparent; }}
QStatusBar {{ background: {c["sidebar"]}; color: {c["muted"]}; border-top: 1px solid {c["card_border"]}; }}
QStatusBar::item {{ border: none; }}
QToolTip {{ background: {c["card"]}; color: {c["text"]}; border: 1px solid {c["input_border"]}; padding: 4px 8px; }}
QMenu {{ background: {c["card"]}; border: 1px solid {c["input_border"]}; padding: 4px; }}
QMenu::item {{ padding: 6px 24px; border-radius: 4px; }}
QMenu::item:selected {{ background: {c["selection"]}; }}
QMessageBox {{ background: {c["bg"]}; }}
QGroupBox {{ border: 1px solid {c["card_border"]}; border-radius: 10px; margin-top: 14px; padding-top: 10px; background: {c["card"]}; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; font-weight: 700; }}
QTableWidget {{ background: {c["input"]}; border: 1px solid {c["input_border"]}; border-radius: 8px; gridline-color: {c["card_border"]}; alternate-background-color: {c["row_alt"]}; }}
QTableWidget::item:selected {{ background: {c["selection"]}; color: {c["text"]}; }}
QTableWidget::item {{ padding: 2px 6px; }}
QCheckBox::indicator, QTableView::indicator, QListView::indicator {{
    width: 18px; height: 18px; border: 1px solid {c["input_border"]}; border-radius: 4px; background: {c["input"]};
}}
QCheckBox::indicator:checked, QTableView::indicator:checked, QListView::indicator:checked {{
    background: {c["accent"]}; border-color: {c["accent"]};
}}
QCheckBox::indicator:hover, QTableView::indicator:hover {{ border-color: {c["accent"]}; }}
"""


def apply(app: QApplication):
    """Fusion draws the same everywhere, which is what the stylesheet is written against"""
    app.setStyle("Fusion")
    palette = QPalette()
    for role, key in (
        (QPalette.Window, "bg"),
        (QPalette.Base, "input"),
        (QPalette.AlternateBase, "row_alt"),
        (QPalette.Button, "button"),
        (QPalette.WindowText, "text"),
        (QPalette.Text, "text"),
        (QPalette.ButtonText, "text"),
        (QPalette.ToolTipBase, "card"),
        (QPalette.ToolTipText, "text"),
        (QPalette.Highlight, "accent"),
        (QPalette.HighlightedText, "on_accent"),
        (QPalette.PlaceholderText, "disabled"),
    ):
        palette.setColor(role, QColor(COLORS[key]))
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        palette.setColor(QPalette.Disabled, role, QColor(COLORS["disabled"]))
    app.setPalette(palette)
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
    app.setStyleSheet(stylesheet())
