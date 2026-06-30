"""
Model Setup Dialog — first-launch screen with THREE independent model slots:
Text (story planning), Vision (frame validation), Image (asset generation).
Each slot can use a different provider with a different API key, or a local
HuggingFace model with no key at all. Any combination is valid.
"""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QComboBox,
    QWidget, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)

STYLE = """
QDialog { background: #0d0f14; }
QLabel { color: #d4d8e8; }
QLabel#title { font-size: 16px; font-weight: bold; color: white; }
QLabel#sub   { font-size: 12px; color: #6b7280; }
QLabel#section_title { font-size: 13px; font-weight: bold; color: #5b6af5; }
QLabel#field_label { font-size: 10px; font-weight: bold; color: #6b7280; letter-spacing: 0.06em; }
QLabel#hint { font-size: 10px; color: #6b7280; }
QLineEdit {
    background: #13161e; color: #d4d8e8;
    border: 1px solid #1e2330; border-radius: 6px;
    padding: 8px 10px; font-size: 12px;
}
QLineEdit:focus { border-color: #5b6af5; }
QComboBox {
    background: #13161e; color: #d4d8e8;
    border: 1px solid #1e2330; border-radius: 6px;
    padding: 8px 10px; font-size: 12px;
}
QComboBox QAbstractItemView {
    background: #13161e; color: #d4d8e8;
    selection-background-color: #1e2330;
}
QPushButton {
    background: #5b6af5; color: white; border: none;
    border-radius: 6px; padding: 10px 24px;
    font-weight: bold; font-size: 13px;
}
QPushButton:hover { background: #6b7aff; }
QPushButton#secondary {
    background: transparent; color: #6b7280;
    border: 1px solid #1e2330;
}
QPushButton#secondary:hover { color: #d4d8e8; border-color: #d4d8e8; }
QFrame#card {
    background: #13161e; border: 1px solid #1e2330; border-radius: 8px;
}
QFrame#divider { background: #1e2330; }
"""


class ModelSlotWidget(QFrame):
    """One configurable slot: provider dropdown + matching key/repo field."""

    def __init__(self, title: str, hint: str, providers: list[tuple[str, str]],
                 config: dict, config_provider_key: str,
                 field_configs: dict) -> None:
        """
        providers: list of (value, label) e.g. [("gemini", "Gemini (Cloud)"), ("huggingface", "Local (HuggingFace)")]
        field_configs: {provider_value: (config_key, placeholder, label)}
        """
        super().__init__()
        self.setObjectName("card")
        self.config = config
        self.config_provider_key = config_provider_key
        self.field_configs = field_configs
        self.field_inputs: dict[str, QLineEdit] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("section_title")
        layout.addWidget(title_lbl)

        hint_lbl = QLabel(hint)
        hint_lbl.setObjectName("hint")
        hint_lbl.setWordWrap(True)
        layout.addWidget(hint_lbl)
        layout.addSpacing(4)

        self.provider_combo = QComboBox()
        for value, label in providers:
            self.provider_combo.addItem(label, value)
        current = config.get(config_provider_key, providers[0][0])
        idx = self.provider_combo.findData(current)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        layout.addWidget(self.provider_combo)

        self.field_container = QVBoxLayout()
        layout.addLayout(self.field_container)

        self._build_field_for_current()

    def _on_provider_changed(self) -> None:
        self._build_field_for_current()

    def _build_field_for_current(self) -> None:
        while self.field_container.count():
            item = self.field_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        provider = self.provider_combo.currentData()
        if provider not in self.field_configs:
            return

        config_key, placeholder, label = self.field_configs[provider]

        lbl = QLabel(label)
        lbl.setObjectName("field_label")
        self.field_container.addWidget(lbl)

        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        if "key" in config_key.lower():
            field.setEchoMode(QLineEdit.EchoMode.Password)
        existing = self.config.get(config_key, "")
        if existing and existing != "GEMINI_API_KEY_HERE":
            field.setText(existing)
        self.field_container.addWidget(field)
        self.field_inputs[provider] = field

    def get_values(self) -> dict:
        """Return {provider_config_key: value, field_config_key: value}."""
        provider = self.provider_combo.currentData()
        result = {self.config_provider_key: provider}
        if provider in self.field_inputs:
            config_key, _, _ = self.field_configs[provider]
            result[config_key] = self.field_inputs[provider].text().strip()
        return result


class ModelSetupDialog(QDialog):
    """First-run / settings dialog: configure Text, Vision, and Image models independently."""

    def __init__(self, config: dict) -> None:
        super().__init__()
        self.config = dict(config)
        self.setWindowTitle("AI Production Studio — Model Setup")
        self.setFixedSize(560, 620)
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 20)
        outer.setSpacing(10)

        title = QLabel("AI Production Studio")
        title.setObjectName("title")
        outer.addWidget(title)

        sub = QLabel(
            "Configure three independent models. Mix and match freely — "
            "cloud for one, local for another. No single model is required to do everything."
        )
        sub.setObjectName("sub")
        sub.setWordWrap(True)
        outer.addWidget(sub)
        outer.addSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(12)
        inner_layout.setContentsMargins(0, 0, 4, 0)

        # ── Text slot ──
        self.text_slot = ModelSlotWidget(
            title="Text — Story Planning & Repair",
            hint="Writes shot plans, checks continuity, rewrites broken descriptions.",
            providers=[("gemini", "Gemini (Cloud)"), ("huggingface", "Local (HuggingFace)"),
                       ("ollama", "Local (Ollama)")],
            config=self.config,
            config_provider_key="text_provider",
            field_configs={
                "gemini": ("gemini_api_key", "AIza...", "GEMINI API KEY"),
                "huggingface": ("hf_repo_id", "e.g. Qwen/Qwen2.5-3B-Instruct", "HUGGINGFACE REPO ID"),
                "ollama": ("ollama_model", "e.g. llama3", "OLLAMA MODEL NAME"),
            }
        )
        inner_layout.addWidget(self.text_slot)

        # ── Vision slot ──
        self.vision_slot = ModelSlotWidget(
            title="Vision — Frame Validation",
            hint="Looks at rendered frames and checks them against the script. "
                 "Can use a different key/account than the text model.",
            providers=[("gemini", "Gemini (Cloud)"), ("huggingface", "Local (HuggingFace, limited)"),
                       ("ollama", "Local (Ollama / LLaVA)")],
            config=self.config,
            config_provider_key="vision_provider",
            field_configs={
                "gemini": ("vision_gemini_api_key", "Leave blank to reuse text key", "GEMINI API KEY (OPTIONAL)"),
                "huggingface": ("hf_repo_id", "Uses text model — most can't do vision", "HUGGINGFACE REPO ID"),
                "ollama": ("ollama_model", "e.g. llava", "OLLAMA VISION MODEL"),
            }
        )
        inner_layout.addWidget(self.vision_slot)

        # ── Image slot ──
        self.image_slot = ModelSlotWidget(
            title="Image — Asset Generation",
            hint="Generates character, object, and environment artwork.",
            providers=[("imagen", "Imagen (Cloud)"), ("diffusers", "Local (Stable Diffusion)")],
            config=self.config,
            config_provider_key="image_provider",
            field_configs={
                "imagen": ("image_api_key", "Leave blank to reuse text key", "GEMINI API KEY (OPTIONAL)"),
                "diffusers": ("hf_image_repo_id", "e.g. stabilityai/sdxl-turbo", "HUGGINGFACE IMAGE REPO ID"),
            }
        )
        inner_layout.addWidget(self.image_slot)

        scroll.setWidget(inner)
        outer.addWidget(scroll, stretch=1)

        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        outer.addWidget(divider)
        outer.addSpacing(8)

        btn_row = QHBoxLayout()
        skip_btn = QPushButton("Skip for now")
        skip_btn.setObjectName("secondary")
        skip_btn.clicked.connect(self.reject)
        btn_row.addWidget(skip_btn)
        btn_row.addStretch()

        save_btn = QPushButton("Save & Continue")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        outer.addLayout(btn_row)

    def _on_save(self) -> None:
        text_values   = self.text_slot.get_values()
        vision_values = self.vision_slot.get_values()
        image_values  = self.image_slot.get_values()

        if text_values.get("text_provider") == "gemini" and not text_values.get("gemini_api_key"):
            QMessageBox.warning(self, "Missing key", "Enter a Gemini API key for the text model, or switch to Local.")
            return
        if text_values.get("text_provider") == "huggingface" and not text_values.get("hf_repo_id"):
            QMessageBox.warning(self, "Missing repo", "Enter a HuggingFace repo ID for the text model.")
            return

        self.config.update(text_values)
        self.config.update(vision_values)
        self.config.update(image_values)

        # Keep legacy llm_provider key in sync for any old code paths
        self.config["llm_provider"] = text_values.get("text_provider", "gemini")

        self.accept()

    def get_updated_config(self) -> dict:
        return self.config
