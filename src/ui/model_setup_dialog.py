"""
Model Setup Dialog — first-launch screen. User picks Cloud (Gemini API key)
or Local (HuggingFace repo ID, downloaded and run on their machine).
Replaces the older single-purpose api_key_dialog.py.
"""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QStackedWidget,
    QWidget, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject

logger = logging.getLogger(__name__)

STYLE = """
QDialog { background: #0d0f14; }
QLabel { color: #d4d8e8; }
QLabel#title { font-size: 16px; font-weight: bold; color: white; }
QLabel#sub   { font-size: 12px; color: #6b7280; }
QLabel#link  { font-size: 11px; color: #5b6af5; }
QLabel#section { font-size: 11px; font-weight: bold; color: #6b7280; letter-spacing: 0.08em; }
QLabel#size_hint { font-size: 11px; color: #f0c060; }
QLineEdit {
    background: #13161e; color: #d4d8e8;
    border: 1px solid #1e2330; border-radius: 6px;
    padding: 10px 12px; font-size: 13px;
}
QLineEdit:focus { border-color: #5b6af5; }
QPushButton {
    background: #5b6af5; color: white; border: none;
    border-radius: 6px; padding: 10px 24px;
    font-weight: bold; font-size: 13px;
}
QPushButton:hover { background: #6b7aff; }
QPushButton:disabled { background: #2a2e3e; color: #6b7280; }
QPushButton#secondary {
    background: transparent; color: #6b7280;
    border: 1px solid #1e2330;
}
QPushButton#secondary:hover { color: #d4d8e8; border-color: #d4d8e8; }
QPushButton#tab_btn {
    background: #13161e; color: #6b7280; border: 1px solid #1e2330;
    border-radius: 6px; padding: 10px; font-weight: bold; font-size: 12px;
}
QPushButton#tab_btn:checked {
    background: #1a1e40; color: #5b6af5; border-color: #5b6af5;
}
QFrame#divider { background: #1e2330; }
QProgressBar {
    background: #13161e; border: 1px solid #1e2330; border-radius: 4px;
    text-align: center; color: #d4d8e8; font-size: 11px; height: 18px;
}
QProgressBar::chunk { background: #5b6af5; border-radius: 3px; }
"""


class DownloadWorker(QObject):
    """Runs HuggingFace model download on a background thread."""
    progress = pyqtSignal(float, str)
    finished = pyqtSignal(bool)

    def __init__(self, repo_id: str, config: dict):
        super().__init__()
        self.repo_id = repo_id
        self.config = config

    def run(self):
        from src.providers.huggingface_provider import HuggingFaceProvider
        provider = HuggingFaceProvider({**self.config, "hf_repo_id": self.repo_id})
        ok = provider.download(progress_callback=lambda pct, msg: self.progress.emit(pct, msg))
        self.finished.emit(ok)


class ModelSetupDialog(QDialog):
    """First-run dialog: choose Cloud (Gemini) or Local (HuggingFace) model."""

    def __init__(self, config: dict) -> None:
        super().__init__()
        self.config = dict(config)
        self.setWindowTitle("AI Production Studio — Model Setup")
        self.setFixedSize(520, 460)
        self.setStyleSheet(STYLE)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        self._thread = None
        self._worker = None
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(36, 28, 36, 24)
        outer.setSpacing(0)

        title = QLabel("AI Production Studio")
        title.setObjectName("title")
        outer.addWidget(title)
        outer.addSpacing(4)

        sub = QLabel("Choose how the Director and validators will think.")
        sub.setObjectName("sub")
        outer.addWidget(sub)
        outer.addSpacing(18)

        # ── Tab buttons ──
        tab_row = QHBoxLayout()
        tab_row.setSpacing(8)
        self.cloud_tab = QPushButton("☁  Cloud (Gemini)")
        self.local_tab = QPushButton("💻  Local (HuggingFace)")
        for btn in (self.cloud_tab, self.local_tab):
            btn.setObjectName("tab_btn")
            btn.setCheckable(True)
            btn.setMinimumHeight(40)
        self.cloud_tab.setChecked(True)
        self.cloud_tab.clicked.connect(lambda: self._switch_tab(0))
        self.local_tab.clicked.connect(lambda: self._switch_tab(1))
        tab_row.addWidget(self.cloud_tab)
        tab_row.addWidget(self.local_tab)
        outer.addLayout(tab_row)
        outer.addSpacing(20)

        # ── Stacked content ──
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_cloud_page())
        self.stack.addWidget(self._build_local_page())
        outer.addWidget(self.stack)

        outer.addStretch()

        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        outer.addWidget(divider)
        outer.addSpacing(14)

        # ── Bottom buttons ──
        btn_row = QHBoxLayout()
        skip_btn = QPushButton("Skip for now")
        skip_btn.setObjectName("secondary")
        skip_btn.clicked.connect(self.reject)
        btn_row.addWidget(skip_btn)
        btn_row.addStretch()

        self.continue_btn = QPushButton("Save & Continue")
        self.continue_btn.clicked.connect(self._on_continue)
        btn_row.addWidget(self.continue_btn)
        outer.addLayout(btn_row)

    def _switch_tab(self, index: int) -> None:
        self.cloud_tab.setChecked(index == 0)
        self.local_tab.setChecked(index == 1)
        self.stack.setCurrentIndex(index)

    def _build_cloud_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        layout.addWidget(self._section_label("GEMINI API KEY"))
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("AIza...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        existing_key = self.config.get("gemini_api_key", "")
        if existing_key and existing_key != "GEMINI_API_KEY_HERE":
            self.key_input.setText(existing_key)
        layout.addWidget(self.key_input)
        layout.addSpacing(4)

        link = QLabel("Get a free key at aistudio.google.com/app/apikey")
        link.setObjectName("link")
        layout.addWidget(link)
        layout.addSpacing(10)

        note = QLabel(
            "Fastest option. Handles text, image generation, and vision validation\n"
            "all from one provider. Requires internet."
        )
        note.setObjectName("sub")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()
        return page

    def _build_local_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        layout.addWidget(self._section_label("HUGGINGFACE REPO ID"))
        self.hf_input = QLineEdit()
        self.hf_input.setPlaceholderText("e.g. Qwen/Qwen2.5-3B-Instruct")
        existing_repo = self.config.get("hf_repo_id", "")
        if existing_repo:
            self.hf_input.setText(existing_repo)
        layout.addWidget(self.hf_input)
        layout.addSpacing(4)

        link = QLabel("Browse models at huggingface.co/models?pipeline_tag=text-generation")
        link.setObjectName("link")
        layout.addWidget(link)
        layout.addSpacing(10)

        self.size_label = QLabel("")
        self.size_label.setObjectName("size_hint")
        layout.addWidget(self.size_label)

        check_btn = QPushButton("Check model size")
        check_btn.setObjectName("secondary")
        check_btn.clicked.connect(self._check_model_size)
        layout.addWidget(check_btn)
        layout.addSpacing(10)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        note = QLabel(
            "Runs entirely on your machine — no internet needed after download,\n"
            "no API costs. Vision validation will use Gemini if also configured,\n"
            "otherwise vision checks are skipped safely. Larger models need more RAM/VRAM."
        )
        note.setObjectName("sub")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()
        return page

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("section")
        return lbl

    def _check_model_size(self) -> None:
        repo_id = self.hf_input.text().strip()
        if not repo_id:
            return
        self.size_label.setText("Checking...")
        try:
            from src.providers.huggingface_provider import HuggingFaceProvider
            provider = HuggingFaceProvider({"hf_repo_id": repo_id, "storage_path": "./storage"})
            size = provider.estimate_size_gb()
            if size:
                self.size_label.setText(f"≈ {size} GB download — make sure you have enough disk space and RAM")
            else:
                self.size_label.setText("Could not estimate size — repo may be private or invalid")
        except Exception as e:
            self.size_label.setText(f"Error checking model: {e}")

    def _on_continue(self) -> None:
        if self.cloud_tab.isChecked():
            key = self.key_input.text().strip()
            if not key:
                QMessageBox.warning(self, "Missing key", "Enter a Gemini API key or switch to Local.")
                return
            self.config["llm_provider"]   = "gemini"
            self.config["image_provider"] = "imagen"
            self.config["gemini_api_key"] = key
            self.accept()
        else:
            repo_id = self.hf_input.text().strip()
            if not repo_id:
                QMessageBox.warning(self, "Missing repo", "Enter a HuggingFace repo ID or switch to Cloud.")
                return
            self.config["llm_provider"] = "huggingface"
            self.config["hf_repo_id"]   = repo_id
            self._start_download(repo_id)

    def _start_download(self, repo_id: str) -> None:
        self.continue_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # indeterminate while downloading

        self._thread = QThread()
        self._worker = DownloadWorker(repo_id, self.config)
        self._worker.moveToThread(self._thread)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_download_finished)
        self._thread.started.connect(self._worker.run)
        self._thread.start()

    def _on_progress(self, pct: float, message: str) -> None:
        self.size_label.setText(message)

    def _on_download_finished(self, success: bool) -> None:
        self.progress.setVisible(False)
        self.continue_btn.setEnabled(True)
        self._thread.quit()
        self._thread.wait()

        if success:
            self.accept()
        else:
            QMessageBox.critical(
                self, "Download failed",
                "Could not download the model. Check the repo ID and your internet connection,\n"
                "or switch to Cloud (Gemini) instead."
            )

    def get_updated_config(self) -> dict:
        return self.config
