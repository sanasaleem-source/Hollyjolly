"""
World State Viewer Widget
A spreadsheet list mapping current character states, inventories, and scene events.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

class WorldViewerWidget(QWidget):
    """
    World State Viewer Widget
    A spreadsheet list mapping current character states, inventories, and scene events.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        title_label = QLabel("Continuity Spreadsheet")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        layout.addWidget(title_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Category", "Entity / Event", "Details / Value", "Timestamp"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #444444;
                border: 1px solid #444444;
                border-radius: 4px;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #333333;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #1a4f7c;
            }
        """)
        layout.addWidget(self.table)
        
    def refresh_state(self, world_state) -> None:
        """Queries world_state and rebuilds the spreadsheet table."""
        self.table.setRowCount(0)
        rows = []
        
        # 1. Gather character rows
        characters = world_state.get_all_characters()
        for c in characters:
            rows.append(("Character", c.name, f"Clothing: {c.clothing or 'N/A'}, Injuries: {c.injuries or 'None'}", c.updated_at))
            
        # 2. Gather object rows
        objects = world_state.get_all_objects()
        for o in objects:
            rows.append(("Object/Prop", o.name, f"Condition: {o.condition}, Location: {o.location or 'N/A'}, Owner: {o.owner or 'N/A'}", o.updated_at))
            
        # 3. Gather event rows
        events = world_state.get_world_events()
        for e in events:
            rows.append(("World Event", f"Shot {e.shot_id}", f"Weather: {e.weather}, Time: {e.time_of_day}, Lighting: {e.lighting}", e.updated_at))
            
        self.table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable) # Read-only
                self.table.setItem(r_idx, c_idx, item)
                
        self.table.resizeColumnsToContents()

