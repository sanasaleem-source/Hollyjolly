"""
Asset Browser — shows all assets organised by type and version.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel
from PyQt6.QtCore import Qt

STYLE = """
QWidget { background: #13161e; border-bottom: 1px solid #1e2330; }
QLabel { color: #6b7280; font-size: 11px; font-weight: bold;
         letter-spacing: 0.08em; padding: 10px 12px 4px; }
QTreeWidget {
    background: #0d0f14; color: #d4d8e8; border: none;
    font-size: 12px;
}
QTreeWidget::item:hover { background: #13161e; }
QTreeWidget::item:selected { background: #1e2330; color: #5b6af5; }
"""


class AssetBrowser(QWidget):
    """Tree view of all project assets by category and version."""

    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 12)
        layout.setSpacing(4)

        layout.addWidget(QLabel("ASSETS"))

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        layout.addWidget(self.tree)

        self._add_placeholder()

    def _add_placeholder(self) -> None:
        for category in ["Characters", "Objects", "Environments"]:
            item = QTreeWidgetItem([category])
            item.setForeground(0, __import__("PyQt6.QtGui", fromlist=["QColor"]).QColor("#6b7280"))
            self.tree.addTopLevelItem(item)

    def refresh(self, assets: dict) -> None:
        """
        Reload tree from assets dict:
        { "characters": {"john": ["v1","v2"]}, "objects": {...}, ... }
        """
        self.tree.clear()
        for category, items in assets.items():
            cat_item = QTreeWidgetItem([category.title()])
            for name, versions in items.items():
                name_item = QTreeWidgetItem([name])
                for v in versions:
                    name_item.addChild(QTreeWidgetItem([v]))
                cat_item.addChild(name_item)
            self.tree.addTopLevelItem(cat_item)
            cat_item.setExpanded(True)
