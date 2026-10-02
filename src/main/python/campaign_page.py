"""
The Assignments page. It edits an assignment state ({"active": ..., "completed": [...]}) directly: every change
is applied at once and announced with the changed signal, and ends up in the save when the save is written.
"""
import re
from copy import deepcopy
from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import campaigns
from cards import Card

GUID_RE = re.compile(r"^[0-9A-Fa-f]{32}$")
UNKNOWN = "Unknown assignment"

# table columns
COL_DONE, COL_PREFIX, COL_NAME, COL_GUID, COL_ASSIGN = range(5)


class CampaignPage(QWidget):
    changed = Signal(dict)  # the whole state, after every change

    def __init__(self, parent=None):
        super().__init__(parent)
        self.catalog = {}
        self.original = None  # the state the save had, which decides what is listed
        self.state = None
        self.manual_guids = set()  # guids added by hand that aren't in the catalog or completed yet

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        # ---- active assignment
        self.active_card = Card("Active assignment")
        self.active_label = QLabel()
        self.active_label.setObjectName("rowLabel")
        self.active_label.setWordWrap(True)
        self.active_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.active_card.body.addWidget(self.active_label, 0, 0, 1, 2)
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.complete_button = QPushButton("Complete")
        self.clear_button = QPushButton("Unassign")
        self.complete_button.clicked.connect(self.complete_active)
        self.clear_button.clicked.connect(self.clear_active)
        buttons.addWidget(self.complete_button)
        buttons.addWidget(self.clear_button)
        buttons.addStretch(1)
        self.active_card.body.addLayout(buttons, 1, 0, 1, 2)
        layout.addWidget(self.active_card)

        # ---- every assignment
        self.list_card = Card("All assignments")
        hint = QLabel("Check an assignment to mark it completed. Assign makes it your active assignment.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        self.list_card.body.addWidget(hint, 0, 0, 1, 2)

        self.table = QTableWidget(0, 5)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setHorizontalHeaderLabels(["Done", "Prefix", "Name", "GUID", ""])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_DONE, QHeaderView.Fixed)
        self.table.setColumnWidth(COL_DONE, 60)
        header.setSectionResizeMode(COL_PREFIX, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_GUID, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_ASSIGN, QHeaderView.Fixed)
        self.table.setColumnWidth(COL_ASSIGN, 96)
        self.table.itemChanged.connect(self.on_item_changed)
        self.list_card.body.addWidget(self.table, 1, 0, 1, 2)
        self.list_card.body.setRowStretch(1, 1)

        add_row = QHBoxLayout()
        self.guid_edit = QLineEdit()
        self.guid_edit.setPlaceholderText("Add an assignment by GUID (32 hex characters)")
        self.add_button = QPushButton("Add assignment")
        self.guid_edit.returnPressed.connect(self.add_guid)
        self.add_button.clicked.connect(self.add_guid)
        add_row.addWidget(self.guid_edit, 1)
        add_row.addWidget(self.add_button)
        self.list_card.body.addLayout(add_row, 2, 0, 1, 2)
        self.add_status = QLabel("")
        self.add_status.setObjectName("hint")
        self.list_card.body.addWidget(self.add_status, 3, 0, 1, 2)
        layout.addWidget(self.list_card, 1)

        self.load(None)

    # ---- data
    def set_catalog(self, catalog):
        self.catalog = catalog
        if self.state is not None:
            self.populate_table()
            self.refresh_active()

    def load(self, state):
        """starts over from a save's state; None when the save has no assignments to edit"""
        self.original = deepcopy(state)
        self.state = deepcopy(state)
        self.manual_guids = set()
        self.add_status.setText("")
        available = state is not None
        self.setEnabled(available)
        if not available:
            self.active_label.setText("This save has no assignment data to edit.")
            self.complete_button.setEnabled(False)
            self.clear_button.setEnabled(False)
            self.table.setRowCount(0)
            return
        self.refresh_active()
        self.populate_table()

    def info_of(self, guid):
        return self.catalog.get(guid, {})

    def name_of(self, guid):
        return self.info_of(guid).get("name", UNKNOWN)

    def prefix_of(self, guid):
        return self.info_of(guid).get("prefix", "")

    def _changed(self):
        self.refresh_active()
        self.populate_table()
        self.changed.emit(deepcopy(self.state))

    # ---- active assignment
    def refresh_active(self):
        active = self.state["active"] if self.state else None
        if active is None:
            self.active_label.setText("No assignment is active.")
        else:
            guid, progress = active
            prefix = self.prefix_of(guid)
            title = "{}  ·  {}".format(prefix, self.name_of(guid)) if prefix else self.name_of(guid)
            self.active_label.setText("{}\nGUID: {}\nProgress: {} mission(s) done".format(title, guid, progress))
        self.complete_button.setEnabled(active is not None and active[0] not in campaigns.HIDDEN_GUIDS)
        self.clear_button.setEnabled(active is not None)

    def complete_active(self):
        if campaigns.complete_active_in_state(self.state) is not None:
            self._changed()

    def clear_active(self):
        if self.state["active"] is not None:
            self.state["active"] = None
            self._changed()

    def assign(self, guid):
        campaigns.set_active_in_state(self.state, guid)
        self._changed()

    # ---- all assignments
    def populate_table(self):
        """rows are every assignment we know about except the active one; checked means completed"""
        completed = set(self.state["completed"])
        active = self.state["active"][0] if self.state["active"] else None
        guids = set(self.catalog) | set(self.original["completed"]) | completed | self.manual_guids
        guids.discard(active)
        guids -= campaigns.HIDDEN_GUIDS
        rows = sorted(guids, key=lambda g: (self.name_of(g) == UNKNOWN, self.name_of(g), g))

        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))
        for row, guid in enumerate(rows):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            check.setCheckState(Qt.Checked if guid in completed else Qt.Unchecked)
            self.table.setItem(row, COL_DONE, check)
            for column, text in ((COL_PREFIX, self.prefix_of(guid)), (COL_NAME, self.name_of(guid)), (COL_GUID, guid)):
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.table.setItem(row, column, item)
            assign_button = QPushButton("Assign")
            assign_button.setObjectName("small")
            assign_button.setCursor(Qt.PointingHandCursor)
            assign_button.clicked.connect(partial(self.assign, guid))
            self.table.setCellWidget(row, COL_ASSIGN, assign_button)
        self.table.blockSignals(False)

    def on_item_changed(self, item):
        if item.column() != COL_DONE:
            return
        guid = self.table.item(item.row(), COL_GUID).text()
        completed = self.state["completed"]
        if item.checkState() == Qt.Checked and guid not in completed:
            completed.append(guid)  # newly completed assignments go on the end, like the game does
        elif item.checkState() != Qt.Checked and guid in completed:
            completed.remove(guid)
        else:
            return
        self.changed.emit(deepcopy(self.state))

    def add_guid(self):
        text = self.guid_edit.text().strip().replace("-", "").replace("{", "").replace("}", "")
        if not GUID_RE.match(text):
            self.add_status.setText("A GUID is 32 hexadecimal characters.")
            return
        guid = text.upper()
        active = self.state["active"]
        if active is not None and active[0] == guid:
            self.add_status.setText("That assignment is already active.")
            return
        if guid in campaigns.HIDDEN_GUIDS:
            self.add_status.setText("Weekly assignments are managed by the game and can't be edited here.")
            return
        self.manual_guids.add(guid)
        self.guid_edit.clear()
        self.add_status.setText("Added. Check it to mark it completed, or press Assign.")
        self.populate_table()
