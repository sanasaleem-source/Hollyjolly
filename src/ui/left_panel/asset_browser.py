"""
Asset Browser Widget
Displays characters, props, and environments version files in a collapsible tree.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt

class AssetBrowserWidget(QWidget):
    """
    Asset Browser Widget
    Displays characters, props, and environments version files in a collapsible tree.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        title_label = QLabel("Asset Register")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        layout.addWidget(title_label)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 4px;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #383838;
            }
            QTreeWidget::item:selected {
                background-color: #1a4f7c;
            }
        """)
        layout.addWidget(self.tree)
        
        # Populate initial empty structure
        self.characters_root = QTreeWidgetItem(self.tree, ["Characters"])
        self.objects_root = QTreeWidgetItem(self.tree, ["Objects & Props"])
        self.environments_root = QTreeWidgetItem(self.tree, ["Environments"])
        
        self.tree.expandAll()
        
    def refresh_assets(self, world_state) -> None:
        """Queries world_state and updates the asset tree."""
        # Clear existing children
        self.characters_root.takeChildren()
        self.objects_root.takeChildren()
        self.environments_root.takeChildren()
        
        # Load characters
        characters = world_state.get_all_characters()
        for char in characters:
            char_item = QTreeWidgetItem(self.characters_root, [char.name])
            if char.appearance:
                QTreeWidgetItem(char_item, [f"Appearance: {char.appearance}"])
            if char.clothing:
                QTreeWidgetItem(char_item, [f"Clothing: {char.clothing}"])
            if char.injuries:
                QTreeWidgetItem(char_item, [f"Injuries: {char.injuries}"])
            QTreeWidgetItem(char_item, [f"Last Seen: {char.last_seen_shot_id or 'Never'}"])
            
        # Load objects
        objects = world_state.get_all_objects()
        for obj in objects:
            obj_item = QTreeWidgetItem(self.objects_root, [obj.name])
            QTreeWidgetItem(obj_item, [f"Location: {obj.location or 'N/A'}"])
            QTreeWidgetItem(obj_item, [f"Condition: {obj.condition}"])
            if obj.owner:
                QTreeWidgetItem(obj_item, [f"Owner: {obj.owner}"])
            QTreeWidgetItem(obj_item, [f"Version: {obj.version}"])
            
        # Load environments from world events
        events = world_state.get_world_events()
        environments_added = set()
        for ev in events:
            env_name = f"{ev.weather} {ev.time_of_day}"
            if env_name not in environments_added:
                env_item = QTreeWidgetItem(self.environments_root, [env_name])
                QTreeWidgetItem(env_item, [f"Lighting: {ev.lighting}"])
                QTreeWidgetItem(env_item, [f"Weather: {ev.weather}"])
                QTreeWidgetItem(env_item, [f"Time: {ev.time_of_day}"])
                environments_added.add(env_name)
                
        self.tree.expandAll()

