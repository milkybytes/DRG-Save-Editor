"""
The editor's window, built in code: a sidebar with one page per area (classes, resources, season, overclocks and
and the overclocks) and a top bar with the file actions.

main.py finds every control by attribute name (widget.bismor_text, widget.overclock_tree, ...), so the names below
are part of its interface; tests/test_ui.py checks that all of them exist.
"""
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIntValidator, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QToolButton,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from campaign_page import CampaignPage
from cards import Banner, Card
import theme
from theme import CLASS_COLORS

CLASSES = ("Driller", "Engineer", "Gunner", "Scout")

# (attribute name, label)
MINERALS = [
    ("bismor_text", "Bismor"),
    ("croppa_text", "Croppa"),
    ("enor_text", "Enor Pearl"),
    ("jadiz_text", "Jadiz"),
    ("magnite_text", "Magnite"),
    ("umanite_text", "Umanite"),
]
BREWING = [
    ("barley_text", "Barley Bulb"),
    ("malt_text", "Malt Star"),
    ("starch_text", "Starch Nut"),
    ("yeast_text", "Yeast Cone"),
]
MISC = [
    ("credits_text", "Credits"),
    ("perk_text", "Perk Points"),
    ("core_text", "Blank Cores"),
    ("error_text", "Error Cubes"),
    ("data_text", "Data Cells"),
    ("phazy_text", "Phazyonite"),
]

NO_FILE = "No save loaded. Open one with Open save…"
ASSIGNMENTS_PAGE = 4
WELCOME_PAGE = 5  # shown instead of the pages while no save is open
BIG_NUMBER = 2147483647


def number_edit(cls, name, width=170):
    edit = cls()
    edit.setObjectName(name)
    edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    edit.setFixedWidth(width)
    edit.setValidator(QIntValidator(0, BIG_NUMBER))
    return edit


def page(content_layout_builder):
    """a page that scrolls instead of squashing its cards when the window is small"""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    inner = QWidget()
    layout = QVBoxLayout(inner)
    layout.setContentsMargins(0, 0, 14, 0)
    layout.setSpacing(18)
    content_layout_builder(layout)
    scroll.setWidget(inner)
    return scroll


class MainWindow(QMainWindow):
    _loaded = False
    _dirty = False

    def set_save_loaded(self, loaded):
        """everything that only makes sense once a save is open"""
        self._loaded = loaded
        self._dirty = False
        for button in self.nav_buttons:
            button.setEnabled(loaded)
        for action in (self.actionSet_All_Classes_to_25, self.actionAdd_overclock_crafting_materials):
            action.setEnabled(loaded)
        self._refresh_save_actions()
        if not loaded:
            self.nav_group.setExclusive(False)  # so that no page is marked as the current one
            for button in self.nav_buttons:
                button.setChecked(False)
            self.nav_group.setExclusive(True)
            self.pages.setCurrentIndex(WELCOME_PAGE)
            self.page_title.setText("Welcome")
        elif self.pages.currentIndex() == WELCOME_PAGE:
            self.show_page(0)

    def set_dirty(self, dirty):
        """Save and Reset only do something while there are unsaved changes"""
        self._dirty = bool(dirty)
        self._refresh_save_actions()

    def _refresh_save_actions(self):
        enabled = self._loaded and self._dirty
        self.actionSave_changes.setEnabled(enabled)
        self.actionReset_to_original_values.setEnabled(enabled)
        self.dirty_label.setVisible(enabled)

    def set_assignments_available(self, available):
        button = self.nav_buttons[ASSIGNMENTS_PAGE]
        button.setEnabled(available and self._loaded)
        if not available and self.pages.currentIndex() == ASSIGNMENTS_PAGE:
            self.show_page(0)

    def setWindowTitle(self, title):
        super().setWindowTitle(title)
        label = getattr(self, "file_label", None)  # not there yet while the window is being built
        if label is not None:
            label.setText(title.replace("DRG Save Editor - ", "", 1) if " - " in title else NO_FILE)

    def show_page(self, index):
        self.pages.setCurrentIndex(index)
        self.nav_buttons[index].setChecked(True)
        self.page_title.setText(self.page_names[index])


def build_main_window(focus_edit=QLineEdit):
    """focus_edit is the line edit class used for the XP boxes, which react to losing focus"""
    win = MainWindow()
    win.setObjectName("MainWindow")
    win.setWindowTitle("DRG Save Editor")
    win.resize(1280, 800)
    win.setMinimumSize(1060, 700)

    # ---- actions (also what the buttons are bound to, so they enable and disable together)
    def action(name, text, shortcut=None, enabled=True):
        a = QAction(text, win)
        a.setObjectName(name)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.setEnabled(enabled)
        win.addAction(a)
        setattr(win, name, a)
        return a

    action("actionOpen_Save_File", "Open save…", "Ctrl+O")
    action("actionSave_changes", "Save changes", "Ctrl+S", enabled=False)
    action("actionReset_to_original_values", "Reset", enabled=False)
    action("actionSet_All_Classes_to_25", "Set all classes to level 25", enabled=False)
    action("actionAdd_overclock_crafting_materials", "Add required materials", enabled=False)
    win.actionAdd_overclock_crafting_materials.setToolTip(
        "Adds the credits and minerals needed to forge everything in the unforged list"
    )

    def tool_button(act, name=None, object_name=None):
        button = QToolButton()
        button.setDefaultAction(act)
        button.setToolButtonStyle(Qt.ToolButtonTextOnly)
        button.setCursor(Qt.PointingHandCursor)
        if object_name:
            button.setObjectName(object_name)
        if name:
            setattr(win, name, button)
        return button

    root = QWidget()
    outer = QHBoxLayout(root)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)
    win.setCentralWidget(root)

    # ---- sidebar
    sidebar = QFrame()
    sidebar.setObjectName("sidebar")
    sidebar.setFixedWidth(230)
    side = QVBoxLayout(sidebar)
    side.setContentsMargins(16, 22, 16, 18)
    side.setSpacing(6)
    brand = QLabel("DRG SAVE EDITOR")
    brand.setObjectName("brand")
    sub = QLabel("Rock and Stone!")
    sub.setObjectName("brandSub")
    side.addWidget(brand)
    side.addWidget(sub)
    side.addSpacing(22)

    win.page_names = ["Classes", "Resources", "Season", "Overclocks", "Assignments"]
    win.nav_buttons = []
    nav_group = win.nav_group = QButtonGroup(win)
    nav_group.setExclusive(True)
    for index, name in enumerate(win.page_names):
        button = QPushButton(name.replace("&", "&&"))
        button.setObjectName("nav")
        button.setCheckable(True)
        button.setCursor(Qt.PointingHandCursor)
        nav_group.addButton(button, index)
        win.nav_buttons.append(button)
        side.addWidget(button)
    side.addStretch(1)

    # ---- right side: top bar over the pages
    right = QWidget()
    right_layout = QVBoxLayout(right)
    right_layout.setContentsMargins(30, 24, 22, 14)
    right_layout.setSpacing(16)

    top = QFrame()
    top.setObjectName("topbar")
    top_layout = QHBoxLayout(top)
    top_layout.setContentsMargins(0, 0, 0, 0)
    titles = QVBoxLayout()
    titles.setSpacing(2)
    win.page_title = QLabel(win.page_names[0])
    win.page_title.setObjectName("pageTitle")
    win.file_label = QLabel(NO_FILE)
    win.file_label.setObjectName("fileLabel")
    title_row = QHBoxLayout()
    title_row.setSpacing(14)
    title_row.addWidget(win.page_title)
    win.dirty_label = QLabel("●  Unsaved changes")
    win.dirty_label.setObjectName("dirty")
    win.dirty_label.setVisible(False)
    title_row.addWidget(win.dirty_label, 0, Qt.AlignBottom)
    title_row.addStretch(1)
    titles.addLayout(title_row)
    titles.addWidget(win.file_label)
    top_layout.addLayout(titles, 1)
    top_layout.addWidget(tool_button(win.actionOpen_Save_File))
    top_layout.addWidget(tool_button(win.actionReset_to_original_values))
    top_layout.addWidget(tool_button(win.actionSave_changes, object_name="primary"))
    right_layout.addWidget(top)

    win.pages = QStackedWidget()
    win.pages.setObjectName("pages")
    right_layout.addWidget(win.pages, 1)

    outer.addWidget(sidebar)
    outer.addWidget(right, 1)

    win.pages.addWidget(page(lambda layout: _classes_page(win, layout, focus_edit)))
    win.pages.addWidget(page(lambda layout: _resources_page(win, layout)))
    win.pages.addWidget(page(lambda layout: _season_page(win, layout, focus_edit)))
    win.pages.addWidget(_items_page(win))
    win.campaign_page = CampaignPage()
    win.pages.addWidget(win.campaign_page)
    win.pages.addWidget(_welcome_page(win))

    # the boxes that hold values to be saved, for noticing edits
    win.data_edits = [e for e in win.pages.findChildren(QLineEdit) if e.validator() is not None]
    win.data_combos = [win.driller_promo_box, win.engineer_promo_box, win.gunner_promo_box, win.scout_promo_box]

    nav_group.idClicked.connect(win.show_page)
    win.nav_buttons[0].setChecked(True)
    win.statusBar().setSizeGripEnabled(False)
    win.set_save_loaded(False)
    return win


# ------------------------------------------------------------------ pages


def _classes_page(win, layout, focus_edit):
    win.classes_group = Banner()
    win.classes_group.setText("Open a save file to see your rank")
    layout.addWidget(win.classes_group)

    grid = QGridLayout()
    grid.setHorizontalSpacing(18)
    grid.setVerticalSpacing(18)
    for i, name in enumerate(CLASSES):
        key = name.lower()
        card = Card(name, accent=CLASS_COLORS[name], pixmap=theme.class_pixmap(name, 44))
        total = number_edit(focus_edit, key + "_xp")
        level = number_edit(focus_edit, key + "_lvl_text", 90)
        progress = number_edit(focus_edit, key + "_xp_2")
        promo = QComboBox()
        promo.setObjectName(key + "_promo_box")
        promo.setFixedWidth(170)
        for control in (total, level, progress, promo):
            setattr(win, control.objectName(), control)
        card.add_row("Total XP", total)
        card.add_row("Level", level)
        card.add_row("Progress to next level", progress)
        card.add_row("Promotion", promo)
        grid.addWidget(card, i // 2, i % 2)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)
    layout.addLayout(grid)

    row = QHBoxLayout()
    row.addWidget(_plain_button(win.actionSet_All_Classes_to_25))
    row.addStretch(1)
    layout.addLayout(row)
    layout.addStretch(1)


def _plain_button(act):
    button = QToolButton()
    button.setDefaultAction(act)
    button.setToolButtonStyle(Qt.ToolButtonTextOnly)
    button.setCursor(Qt.PointingHandCursor)
    return button


def _resource_card(win, title, rows):
    card = Card(title)
    for name, label in rows:
        edit = number_edit(QLineEdit, name)
        setattr(win, name, edit)
        card.add_row(label, edit)
    return card


def _resources_page(win, layout):
    grid = QGridLayout()
    grid.setHorizontalSpacing(18)
    grid.setVerticalSpacing(18)
    grid.addWidget(_resource_card(win, "Minerals", MINERALS), 0, 0)
    grid.addWidget(_resource_card(win, "Miscellaneous", MISC), 0, 1)
    grid.addWidget(_resource_card(win, "Brewing", BREWING), 1, 0)

    note = Card("Before you save")
    text = QLabel(
        "A backup of your save is written next to it (as .old) when you open it.\n\n"
        "Resources you have never owned may not be in the save yet. Collect one in game first."
    )
    text.setObjectName("hint")
    text.setWordWrap(True)
    text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    note.body.addWidget(text, 0, 0, 1, 2)
    note.body.setRowStretch(1, 1)
    grid.addWidget(note, 1, 1)
    for column in (0, 1):
        grid.setColumnStretch(column, 1)
    layout.addLayout(grid)
    layout.addStretch(1)


def _season_page(win, layout, focus_edit):
    win.season_group = Card("Season progress")
    win.season_picker = QComboBox()
    win.season_picker.setObjectName("season_picker")
    win.season_picker.setFixedWidth(170)
    win.season_lvl_text = number_edit(focus_edit, "season_lvl_text", 90)
    win.season_xp = number_edit(focus_edit, "season_xp")
    win.scrip_text = number_edit(QLineEdit, "scrip_text")
    win.season_group.add_row("Season", win.season_picker)
    win.season_group.add_row("Level", win.season_lvl_text)
    win.season_group.add_row("Progress to next level", win.season_xp)
    win.season_group.add_row("Scrip", win.scrip_text)

    hint = QLabel("Each season keeps its own level and scrip. Changes to several seasons are all saved together.")
    hint.setObjectName("hint")
    hint.setWordWrap(True)
    win.season_group.body.addWidget(hint, win.season_group._next_row, 0, 1, 2)

    row = QHBoxLayout()
    row.addWidget(win.season_group, 1)
    row.addStretch(1)
    layout.addLayout(row)
    layout.addStretch(1)


def _welcome_page(win):
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setAlignment(Qt.AlignCenter)
    layout.setSpacing(18)

    portraits = QHBoxLayout()
    portraits.setSpacing(14)
    portraits.addStretch(1)
    for name in CLASSES:
        picture = QLabel()
        pixmap = theme.class_pixmap(name, 72)
        if pixmap is not None:
            picture.setPixmap(pixmap)
        picture.setStyleSheet("background: transparent;")
        portraits.addWidget(picture)
    portraits.addStretch(1)
    layout.addLayout(portraits)

    title = QLabel("Open a save file to get started")
    title.setObjectName("welcomeTitle")
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    hint = QLabel(
        "Your save is the file ending in .sav in the game's SaveGames folder.\n"
        "A backup (.old) is written next to it when you open it."
    )
    hint.setObjectName("hint")
    hint.setAlignment(Qt.AlignCenter)
    layout.addWidget(hint)

    button = QToolButton()
    button.setDefaultAction(win.actionOpen_Save_File)
    button.setToolButtonStyle(Qt.ToolButtonTextOnly)
    button.setObjectName("primary")
    button.setCursor(Qt.PointingHandCursor)
    button.setMinimumWidth(180)
    row = QHBoxLayout()
    row.addStretch(1)
    row.addWidget(button)
    row.addStretch(1)
    layout.addLayout(row)
    return page


def _items_page(win):
    splitter = QSplitter(Qt.Horizontal)
    splitter.setChildrenCollapsible(False)

    # ---- left: filters, tree, actions
    left = QWidget()
    left_layout = QVBoxLayout(left)
    left_layout.setContentsMargins(0, 0, 8, 0)
    left_layout.setSpacing(12)

    filters = QHBoxLayout()
    filters.setSpacing(10)
    win.oc_search = QLineEdit()
    win.oc_search.setObjectName("oc_search")
    win.oc_search.setPlaceholderText("Search name, weapon or GUID…")
    win.oc_search.setMinimumWidth(220)
    win.oc_search.setClearButtonEnabled(True)
    win.oc_class_filter = QComboBox()
    win.oc_class_filter.setObjectName("oc_class_filter")
    win.oc_class_filter.addItems(["All classes", *CLASSES])
    win.oc_kind_filter = QComboBox()
    win.oc_kind_filter.setObjectName("oc_kind_filter")
    win.oc_kind_filter.addItems(["All overclocks", "Weapon overclocks", "Cosmetic overclocks"])
    win.combo_oc_filter = QComboBox()  # status; main.py fills it
    win.combo_oc_filter.setObjectName("combo_oc_filter")
    filters.addWidget(win.oc_search, 1)
    for combo, width in ((win.oc_class_filter, 125), (win.oc_kind_filter, 190), (win.combo_oc_filter, 115)):
        combo.setFixedWidth(width)
        filters.addWidget(combo)
    left_layout.addLayout(filters)

    win.overclock_tree = QTreeWidget()
    win.overclock_tree.setObjectName("overclock_tree")
    win.overclock_tree.setColumnCount(3)
    win.overclock_tree.setAlternatingRowColors(True)
    win.overclock_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
    win.overclock_tree.setSortingEnabled(True)
    win.overclock_tree.setUniformRowHeights(True)
    win.overclock_tree.setIndentation(18)
    header = win.overclock_tree.header()
    header.setStretchLastSection(False)
    header.setSectionResizeMode(0, QHeaderView.Stretch)
    header.setSectionResizeMode(1, QHeaderView.Fixed)
    header.setSectionResizeMode(2, QHeaderView.Fixed)
    header.resizeSection(1, 190)
    header.resizeSection(2, 290)
    left_layout.addWidget(win.overclock_tree, 1)

    win.oc_counts = QLabel("")
    win.oc_counts.setObjectName("counts")
    left_layout.addWidget(win.oc_counts)

    actions = QHBoxLayout()
    actions.setSpacing(10)
    win.expand_all_button = QPushButton("Expand all")
    win.expand_all_button.setObjectName("small")
    win.collapse_all_button = QPushButton("Collapse all")
    win.collapse_all_button.setObjectName("small")
    win.expand_all_button.clicked.connect(win.overclock_tree.expandAll)
    win.collapse_all_button.clicked.connect(win.overclock_tree.collapseAll)
    actions.addWidget(win.expand_all_button)
    actions.addWidget(win.collapse_all_button)
    actions.addStretch(1)
    actions.addWidget(_plain_button(win.actionAdd_overclock_crafting_materials))
    win.add_cores_button = QPushButton("Add selected to inventory")
    win.add_cores_button.setObjectName("primary")
    win.add_cores_button.setCursor(Qt.PointingHandCursor)
    win.add_cores_button.setToolTip(
        "Adds the selected overclocks to the acquired-but-unforged list.\n"
        "Selecting a weapon, a cosmetic group or a class adds everything unacquired under it that is shown."
    )
    actions.addWidget(win.add_cores_button)
    left_layout.addLayout(actions)

    # ---- right: the unforged list
    win.groupBox = Card("Acquired but unforged")
    win.unforged_count = QLabel("0")
    win.unforged_count.setObjectName("muted")
    win.groupBox.head.addWidget(win.unforged_count)
    win.unforged_list = QListWidget()
    win.unforged_list.setObjectName("unforged_list")
    win.unforged_list.setAlternatingRowColors(True)
    win.unforged_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    win.unforged_list.setTextElideMode(Qt.ElideRight)
    win.unforged_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    win.unforged_list.setWordWrap(False)
    win.unforged_list.setIconSize(QSize(24, 24))
    win.unforged_list.setUniformItemSizes(True)
    def update_unforged_count(*_):
        try:
            win.unforged_count.setText(str(win.unforged_list.count()))
        except RuntimeError:  # the window is being torn down
            pass

    model = win.unforged_list.model()
    for signal in (model.rowsInserted, model.rowsRemoved, model.modelReset):
        signal.connect(update_unforged_count)
    win.groupBox.body.addWidget(win.unforged_list, 0, 0, 1, 2)
    win.groupBox.body.setRowStretch(0, 1)
    win.remove_selected_ocs = QPushButton("Remove selected")
    win.remove_selected_ocs.setObjectName("danger")
    win.remove_all_ocs = QPushButton("Remove all")
    win.remove_all_ocs.setObjectName("danger")
    win.groupBox.body.addWidget(win.remove_selected_ocs, 1, 0)
    win.groupBox.body.addWidget(win.remove_all_ocs, 1, 1)
    win.groupBox.setMinimumWidth(280)

    splitter.addWidget(left)
    splitter.addWidget(win.groupBox)
    splitter.setStretchFactor(0, 3)
    splitter.setStretchFactor(1, 2)
    splitter.setSizes([760, 320])
    return splitter
