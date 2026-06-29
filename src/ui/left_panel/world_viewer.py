"""
World Viewer — shows current World State: characters, objects, world conditions.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QHeaderView
)
from PyQt6.QtCore import Qt

STYLE = """
QWidget { background: #13161e; }
QLabel { color: #6b7280; font-size: 11px; font-weight: bold;
         letter-spacing: 0.08em; padding: 10px 12px 4px; }
QTableWidget {
    background: #0d0f14; color: #d4d8e8;
    border: none; font-size: 12px; gridline-color: #1e2330;
}
QHeaderView::section {
    background: #13161e; color: #6b7280; border: none;
    font-size: 10px; font-weight: bold; letter-spacing: 0.06em;
    padding: 6px;
}
"""


class WorldViewer(QWidget):
    """Tabular view of current World State."""

    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 12)
        layout.setSpacing(4)

        layout.addWidget(QLabel("WORLD STATE"))

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Character", "Clothing", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh(self, characters: list[dict]) -> None:
        """Reload table from list of character dicts."""
        self.table.setRowCount(0)
        for char in characters:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(char.get("name", "")))
            clothing = char.get("clothing", {})
            if isinstance(clothing, dict):
                clothing_str = ", ".join(f"{k}: {v}" for k, v in clothing.items())
            else:
                clothing_str = str(clothing)
            self.table.setItem(row, 1, QTableWidgetItem(clothing_str))
            injuries = char.get("injuries", "none")
            self.table.setItem(row, 2, QTableWidgetItem(str(injuries)))
