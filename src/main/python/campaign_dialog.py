import re
from copy import deepcopy
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

import campaigns

GUID_RE = re.compile(r"^[0-9A-Fa-f]{32}$")
UNKNOWN = "Unknown assignment"

# table columns
COL_DONE, COL_PREFIX, COL_NAME, COL_GUID, COL_ASSIGN = range(5)


class CampaignDialog(QDialog):
    """
    Edits an assignment state ({"active": ..., "completed": [...]}) without touching the save.
    The caller reads the outcome from result_state() after exec() returns accepted.
    """

    def __init__(self, state, catalog, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assignments")
        self.resize(760, 560)
        self.catalog = catalog
        self.original = deepcopy(state)
        self.state = deepcopy(state)
        self.manual_guids = set()  # guids added by hand that aren't in the catalog or completed yet

        layout = QVBoxLayout(self)

        # active assignment
        self.active_group = QGroupBox("Active assignment")
        active_layout = QVBoxLayout(self.active_group)
        self.active_label = QLabel()
        self.active_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        active_layout.addWidget(self.active_label)
        buttons = QHBoxLayout()
        self.complete_button = QPushButton("Complete")
        self.clear_button = QPushButton("Unassign")
        self.complete_button.clicked.connect(self.complete_active)
        self.clear_button.clicked.connect(self.clear_active)
        buttons.addWidget(self.complete_button)
        buttons.addWidget(self.clear_button)
        buttons.addStretch(1)
        active_layout.addLayout(buttons)
        layout.addWidget(self.active_group)

        # all assignments
        all_group = QGroupBox("Assignments")
        all_layout = QVBoxLayout(all_group)
        all_layout.addWidget(
            QLabel(
                "Check an assignment to mark it completed. Use Assign to make it your active assignment."
            )
        )
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Done", "Prefix", "Name", "GUID", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_DONE, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_PREFIX, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_GUID, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_ASSIGN, QHeaderView.ResizeToContents)
        all_layout.addWidget(self.table)

        add_row = QHBoxLayout()
        self.guid_edit = QLineEdit()
        self.guid_edit.setPlaceholderText("Add an assignment by GUID (32 hex characters)")
        self.add_button = QPushButton("Add assignment")
        self.guid_edit.returnPressed.connect(self.add_guid)
        self.add_button.clicked.connect(self.add_guid)
        add_row.addWidget(self.guid_edit)
        add_row.addWidget(self.add_button)
        all_layout.addLayout(add_row)
        layout.addWidget(all_group)

        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        layout.addWidget(box)

        self.refresh_active()
        self.populate_table(set(self.state["completed"]))

    def info_of(self, guid):
        return self.catalog.get(guid, {})

    def name_of(self, guid):
        return self.info_of(guid).get("name", UNKNOWN)

    def prefix_of(self, guid):
        return self.info_of(guid).get("prefix", "")

    # ---- active assignment
    def refresh_active(self):
        active = self.state["active"]
        if active is None:
            self.active_label.setText("No assignment is active.")
        else:
            guid, progress = active
            prefix = self.prefix_of(guid)
            header = "{}\n{}".format(prefix, self.name_of(guid)) if prefix else self.name_of(guid)
            self.active_label.setText(
                "{}\nGUID: {}\nProgress: {} mission(s) done".format(header, guid, progress)
            )
        self.complete_button.setEnabled(active is not None and active[0] not in campaigns.HIDDEN_GUIDS)
        self.clear_button.setEnabled(active is not None)

    def complete_active(self):
        checked = self.checked_guids()  # keep any checkbox edits made so far
        guid = campaigns.complete_active_in_state(self.state)
        if guid is not None:
            self.refresh_active()
            self.populate_table(checked | {guid})

    def clear_active(self):
        self.state["active"] = None
        self.refresh_active()
        self.populate_table(self.checked_guids())

    def assign(self, guid):
        checked = self.checked_guids()
        checked.discard(guid)
        campaigns.set_active_in_state(self.state, guid)
        self.refresh_active()
        self.populate_table(checked)

    # ---- all assignments
    def populate_table(self, checked):
        """rows are every assignment we know about (except the active one), checked = completed"""
        active = self.state["active"][0] if self.state["active"] else None
        guids = set(self.catalog) | set(self.original["completed"]) | checked | self.manual_guids
        guids.discard(active)
        guids -= campaigns.HIDDEN_GUIDS
        rows = sorted(guids, key=lambda g: (self.name_of(g) == UNKNOWN, self.name_of(g), g))

        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))
        for row, guid in enumerate(rows):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            check.setCheckState(Qt.Checked if guid in checked else Qt.Unchecked)
            prefix = QTableWidgetItem(self.prefix_of(guid))
            prefix.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            name = QTableWidgetItem(self.name_of(guid))
            name.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            guid_item = QTableWidgetItem(guid)
            guid_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, COL_DONE, check)
            self.table.setItem(row, COL_PREFIX, prefix)
            self.table.setItem(row, COL_NAME, name)
            self.table.setItem(row, COL_GUID, guid_item)
            assign_button = QPushButton("Assign")
            assign_button.clicked.connect(partial(self.assign, guid))
            self.table.setCellWidget(row, COL_ASSIGN, assign_button)
        self.table.blockSignals(False)

    def checked_guids(self):
        return {
            self.table.item(r, COL_GUID).text()
            for r in range(self.table.rowCount())
            if self.table.item(r, COL_DONE).checkState() == Qt.Checked
        }

    def add_guid(self):
        text = self.guid_edit.text().strip().replace("-", "").replace("{", "").replace("}", "")
        if not GUID_RE.match(text):
            QMessageBox.warning(self, "Assignments", "A GUID is 32 hexadecimal characters.")
            return
        guid = text.upper()
        active = self.state["active"]
        if active is not None and active[0] == guid:
            QMessageBox.information(self, "Assignments", "That assignment is already active.")
            return
        self.manual_guids.add(guid)
        self.populate_table(self.checked_guids())
        self.guid_edit.clear()

    # ---- result
    def result_state(self):
        """completed keeps the save's order; newly checked assignments go on the end"""
        checked = self.checked_guids()
        # hidden assignments aren't shown, so whatever the save had for them is kept
        current = [
            g
            for g in self.original["completed"]
            if g in checked or g in campaigns.HIDDEN_GUIDS
        ]
        added = [
            self.table.item(r, COL_GUID).text()
            for r in range(self.table.rowCount())
            if self.table.item(r, COL_GUID).text() in checked
            and self.table.item(r, COL_GUID).text() not in current
        ]
        return {"active": self.state["active"], "completed": current + added}
