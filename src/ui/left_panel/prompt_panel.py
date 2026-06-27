"""
Prompt Panel Widget
Text entries and targeting selection buttons to trigger or rerun generations.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import pyqtSignal

class PromptPanelWidget(QWidget):
    """
    Prompt Panel Widget
    Text entries and targeting selection buttons to trigger or rerun generations.
    """
    generate_requested = pyqtSignal(str) # Emits the story prompt
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Label
        title_label = QLabel("Creative Story Prompt")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        layout.addWidget(title_label)
        
        desc_label = QLabel("Describe the story or narrative below. The AI pipeline will segment it into shots, generate or reuse assets, assemble scenes in USD, and run quality validations.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        layout.addWidget(desc_label)
        
        # Prompt box
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Enter your story here...")
        self.prompt_edit.setText("John is standing on a rainy city street corner under a dark low-key sky, holding a wet umbrella. He looks around, waiting for a shadow to appear across the road.")
        self.prompt_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 4px;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                padding: 6px;
            }
            QTextEdit:focus {
                border: 1px solid #007acc;
            }
        """)
        layout.addWidget(self.prompt_edit)
        
        # Generate Button
        self.btn_generate = QPushButton("Begin AI Production Pipeline")
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #0098ff;
            }
            QPushButton:pressed {
                background-color: #005999;
            }
        """)
        self.btn_generate.clicked.connect(self._on_generate_clicked)
        layout.addWidget(self.btn_generate)
        
    def _on_generate_clicked(self) -> None:
        prompt = self.prompt_edit.toPlainText().strip()
        if prompt:
            self.generate_requested.emit(prompt)

