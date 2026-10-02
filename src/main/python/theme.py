"""The editor's look: warm charcoal panels, amber for what matters, squared corners, in the manner of the game's terminals."""
import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import QApplication

COLORS = {
    "bg": "#151412",
    "sidebar": "#0f0e0d",
    "card": "#1d1b18",
    "card_header": "#24211d",
    "card_border": "#38342e",
    "input": "#121110",
    "input_border": "#403b34",
    "button": "#2a2723",
    "button_hover": "#35312b",
    "button_border": "#4a453d",
    "text": "#ebe6dc",
    "muted": "#988f80",
    "disabled": "#5d574d",
    "accent": "#f4a20f",
    "accent_hover": "#ffb52e",
    "accent_pressed": "#cc8504",
    "on_accent": "#17110a",
    "selection": "#3b2d12",
    "danger": "#e0604f",
    "success": "#7bc47f",
    "row_alt": "#191714",
}

# the four classes, as the game colours them
CLASS_COLORS = {
    "Driller": "#D19724",
    "Engineer": "#C2494A",
    "Gunner": "#6A9B68",
    "Scout": "#2F8FCB",
}

# status of an overclock in the Overclocks tree
STATUS_COLORS = {
    "Forged": COLORS["success"],
    "Unforged": COLORS["accent"],
    "Unacquired": COLORS["muted"],
}

# Bahnschrift ships with Windows 10 and later and is closest to the game's own lettering
HEADING_FONT = '"Bahnschrift SemiCondensed", "Bahnschrift", "Segoe UI Semibold", "Segoe UI"'
BODY_FONT = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'


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
        pixmap = QPixmap(os.path.join(images_dir(), "characters", class_name.lower() + ".png"))
        _pixmaps[key] = (
            pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation) if not pixmap.isNull() else None
        )
    return _pixmaps[key]


# the box that holds a resource: its file under images/resources
RESOURCE_ICONS = {
    "bismor_text": "minerals/Bismor",
    "croppa_text": "minerals/Croppa",
    "enor_text": "minerals/EnorPearl",
    "jadiz_text": "minerals/Jadiz",
    "magnite_text": "minerals/Magnite",
    "umanite_text": "minerals/Umanite",
    "phazy_text": "minerals/Phazyonite",
    "barley_text": "brewing/BarleyBulb",
    "malt_text": "brewing/MaltStar",
    "starch_text": "brewing/StarchNut",
    "yeast_text": "brewing/YeastCone",
    "credits_text": "misc/Credit",
    "perk_text": "misc/PerkPointStar",
    "core_text": "misc/BlankCore",
    "error_text": "misc/ErrorCube",
}


def resource_pixmap(box_name, limit=28):
    """
    the icon for a resource, or None if there is none. They come in several sizes (20 to 45 pixels), so anything
    bigger than limit is scaled down to it; smaller ones stay as they are rather than being blurred up.
    The files are WebP data with a .png name, which Qt reads fine by their content.
    """
    key = ("resource", box_name, limit)
    if key not in _pixmaps:
        name = RESOURCE_ICONS.get(box_name)
        pixmap = QPixmap(os.path.join(images_dir(), "resources", name + ".png")) if name else QPixmap()
        if pixmap.isNull():
            _pixmaps[key] = None
        else:
            if max(pixmap.width(), pixmap.height()) > limit:
                pixmap = pixmap.scaled(limit, limit, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            _pixmaps[key] = pixmap
    return _pixmaps[key]


def class_icon(class_name, size=32):
    pixmap = class_pixmap(class_name, size)
    return QIcon(pixmap) if pixmap is not None else None


def stylesheet():
    c = COLORS
    return f"""
* {{
    font-family: {BODY_FONT};
    font-size: 10pt;
    color: {c["text"]};
}}
QMainWindow, QDialog {{ background: {c["bg"]}; }}
QWidget#pages, QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollArea {{ border: none; }}

/* ---- sidebar */
QFrame#sidebar {{ background: {c["sidebar"]}; border: none; border-right: 1px solid {c["card_border"]}; }}
QLabel#brand {{ font-family: {HEADING_FONT}; font-size: 14pt; color: {c["text"]}; background: transparent; }}
QPushButton#nav {{
    font-family: {HEADING_FONT}; font-size: 11.5pt;
    text-align: left; padding: 9px 14px; border: none; border-radius: 2px;
    background: transparent; color: {c["muted"]};
}}
QPushButton#nav:hover {{ background: {c["card_header"]}; color: {c["text"]}; }}
QPushButton#nav:checked {{ background: {c["accent"]}; color: {c["on_accent"]}; }}
QPushButton#nav:disabled {{ color: {c["disabled"]}; background: transparent; }}

/* ---- top bar */
QFrame#topbar {{ background: transparent; border: none; }}
QLabel#pageTitle {{ font-family: {HEADING_FONT}; font-size: 20pt; background: transparent; }}
QLabel#fileLabel {{ color: {c["muted"]}; font-size: 9pt; background: transparent; }}
QLabel#dirty {{
    color: {c["accent"]}; border: 1px solid {c["accent"]}; border-radius: 2px;
    padding: 1px 7px; font-size: 8.5pt; background: transparent;
}}

/* ---- panels */
QFrame#panel {{ background: {c["card"]}; border: 1px solid {c["card_border"]}; border-radius: 2px; }}
QFrame#panelHeader {{ background: {c["card_header"]}; border: none; border-bottom: 1px solid {c["card_border"]}; border-radius: 0; }}
QLabel#panelTitle {{ font-family: {HEADING_FONT}; font-size: 9.5pt; color: {c["muted"]}; background: transparent; }}
QWidget#panelBody {{ background: transparent; }}
QLabel#rowLabel {{ color: {c["muted"]}; background: transparent; }}
QLabel#columnHeading {{ color: {c["muted"]}; font-size: 9pt; background: transparent; }}
QLabel#muted, QLabel#hint {{ color: {c["muted"]}; background: transparent; }}
QLabel#banner {{ font-family: {HEADING_FONT}; font-size: 13pt; color: {c["text"]}; background: transparent; }}
QLabel#counts {{ color: {c["muted"]}; background: transparent; }}
QLabel#className {{ font-family: {HEADING_FONT}; font-size: 12pt; background: transparent; }}

/* ---- inputs */
QLineEdit, QComboBox, QSpinBox {{
    background: {c["input"]}; border: 1px solid {c["input_border"]}; border-radius: 2px;
    padding: 4px 7px; min-height: 20px; selection-background-color: {c["accent"]}; selection-color: {c["on_accent"]};
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover {{ border-color: #5a544a; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border-color: {c["accent"]}; }}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{ color: {c["disabled"]}; background: #100f0e; border-color: #2a2824; }}
QComboBox QAbstractItemView {{
    background: {c["card"]}; border: 1px solid {c["input_border"]}; outline: none;
    selection-background-color: {c["selection"]}; selection-color: {c["text"]};
}}

/* ---- buttons */
QPushButton, QToolButton {{
    background: {c["button"]}; border: 1px solid {c["button_border"]}; border-radius: 2px;
    padding: 6px 14px;
}}
QPushButton:hover, QToolButton:hover {{ background: {c["button_hover"]}; border-color: #615b50; }}
QPushButton:pressed, QToolButton:pressed {{ background: #201e1a; }}
QPushButton:disabled, QToolButton:disabled {{ color: {c["disabled"]}; background: #171614; border-color: #2a2824; }}
QPushButton#primary, QToolButton#primary {{ background: {c["accent"]}; color: {c["on_accent"]}; border: 1px solid {c["accent"]}; font-weight: 600; }}
QPushButton#primary:hover, QToolButton#primary:hover {{ background: {c["accent_hover"]}; border-color: {c["accent_hover"]}; }}
QPushButton#primary:pressed, QToolButton#primary:pressed {{ background: {c["accent_pressed"]}; }}
QPushButton#primary:disabled, QToolButton#primary:disabled {{ background: #3a3322; color: #7d7458; border-color: #3a3322; }}
QPushButton#danger {{ color: {c["danger"]}; }}
QPushButton#danger:hover {{ border-color: {c["danger"]}; }}
QPushButton#danger:disabled {{ color: {c["disabled"]}; }}
QPushButton#small {{ padding: 4px 10px; }}

/* ---- trees and lists */
QTreeWidget, QListWidget {{
    background: {c["input"]}; border: 1px solid {c["input_border"]}; border-radius: 2px;
    alternate-background-color: {c["row_alt"]}; outline: none; padding: 0;
}}
QTreeWidget::item, QListWidget::item {{ padding: 3px 2px; }}
QTreeWidget::item:hover, QListWidget::item:hover {{ background: #211f1b; }}
QTreeWidget::item:selected, QListWidget::item:selected {{ background: {c["selection"]}; color: {c["text"]}; }}
QTreeWidget:disabled, QListWidget:disabled {{ color: {c["disabled"]}; }}
QHeaderView::section {{
    background: {c["card_header"]}; color: {c["muted"]}; border: none; border-bottom: 1px solid {c["card_border"]};
    padding: 6px 10px; font-size: 9pt;
}}

/* ---- scroll bars */
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #3c3830; border-radius: 1px; min-height: 30px; margin: 1px; }}
QScrollBar::handle:vertical:hover {{ background: #524c42; }}
QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: #3c3830; border-radius: 1px; min-width: 30px; margin: 1px; }}
QScrollBar::handle:horizontal:hover {{ background: #524c42; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ---- misc */
QSplitter::handle {{ background: transparent; }}
QStatusBar {{ background: {c["sidebar"]}; color: {c["muted"]}; border-top: 1px solid {c["card_border"]}; }}
QStatusBar::item {{ border: none; }}
QToolTip {{ background: {c["card"]}; color: {c["text"]}; border: 1px solid {c["input_border"]}; padding: 3px 6px; }}
QMenu {{ background: {c["card"]}; border: 1px solid {c["input_border"]}; padding: 2px; }}
QMenu::item {{ padding: 5px 22px; }}
QMenu::item:selected {{ background: {c["selection"]}; }}
QMessageBox {{ background: {c["bg"]}; }}
QTableWidget {{ background: {c["input"]}; border: 1px solid {c["input_border"]}; border-radius: 2px; gridline-color: {c["card_border"]}; alternate-background-color: {c["row_alt"]}; }}
QTableWidget::item:selected {{ background: {c["selection"]}; color: {c["text"]}; }}
QTableWidget::item {{ padding: 2px 6px; }}
QCheckBox::indicator, QTableView::indicator, QListView::indicator {{
    width: 16px; height: 16px; border: 1px solid {c["input_border"]}; border-radius: 2px; background: {c["input"]};
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
