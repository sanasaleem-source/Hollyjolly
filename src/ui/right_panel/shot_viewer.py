"""
Shot Viewer Widget
Shows detail inspect logs, prompt variables, and active validations for a selected shot.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt6.QtCore import Qt
import json

class ShotViewerWidget(QWidget):
    """
    Shot Viewer Widget
    Shows detail inspect logs, prompt variables, and active validations for a selected shot.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Shot Inspection Logs & Quality Control")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        layout.addWidget(title_label)
        
        # Scrollable log viewer
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333333;
                border-radius: 4px;
                font-family: 'JetBrains Mono', 'Fira Code', monospace;
                font-size: 11px;
                line-height: 1.4;
                padding: 8px;
            }
        """)
        self.log_viewer.setHtml("<span style='color: #666666;'>Select a shot card from the timeline to audit parameters and quality control metrics.</span>")
        layout.addWidget(self.log_viewer)
        
    def load_shot_logs(self, shot_id: str, world_state) -> None:
        """Loads details of a shot and formats nice HTML telemetry report."""
        shot = world_state.get_shot(shot_id)
        if not shot:
            self.log_viewer.setHtml(f"<span style='color: #ff3333;'>Error: Shot {shot_id} not found in database.</span>")
            return
            
        # Compile a gorgeous telemetry audit sheet
        html = f"""
        <h3 style='color: #007acc; margin-top: 0;'>SHOT TELEMETRY: {shot_id.upper()}</h3>
        <table width='100%' style='border-collapse: collapse; margin-bottom: 15px;'>
          <tr>
            <td style='color: #888888; font-weight: bold; width: 120px;'>Scene reference:</td>
            <td style='color: #ffffff;'>{shot.scene_id}</td>
          </tr>
          <tr>
            <td style='color: #888888; font-weight: bold;'>Pipeline status:</td>
            <td style='color: {self._get_status_color(shot.status)}; font-weight: bold;'>{shot.status.upper()}</td>
          </tr>
          <tr>
            <td style='color: #888888; font-weight: bold;'>Repair attempts:</td>
            <td style='color: #ffffff;'>{shot.repair_attempts} / 3</td>
          </tr>
          <tr>
            <td style='color: #888888; font-weight: bold;'>Last updated:</td>
            <td style='color: #aaaaaa; font-size: 10px;'>{shot.updated_at}</td>
          </tr>
        </table>
        """
        
        # 1. Show asset versions
        html += "<h4 style='color: #e5c07b; margin-bottom: 5px;'>RESOLVED ASSET PIPELINE:</h4>"
        if shot.asset_versions:
            html += "<ul>"
            for asset, path in shot.asset_versions.items():
                html += f"<li><b>{asset}</b>: <span style='color: #98c379;'>{path}</span></li>"
            html += "</ul>"
        else:
            html += "<span style='color: #666666; font-style: italic;'>No characters/props active in this shot.</span><br/>"
            
        # 2. Show rendering paths
        html += "<h4 style='color: #e5c07b; margin-top: 15px; margin-bottom: 5px;'>GODOT ENGINE COMPOSE & LAYOUT USDA:</h4>"
        if shot.render_path:
            html += f"<div style='background-color: #2d2d2d; padding: 4px; border-radius: 4px; border-left: 3px solid #61afef;'><code>{shot.render_path}</code></div>"
        else:
            html += "<span style='color: #666666; font-style: italic;'>Rendering layout file not written yet.</span><br/>"
            
        # 3. Quality control validators
        html += "<h4 style='color: #e5c07b; margin-top: 15px; margin-bottom: 5px;'>QUALITY CONTROL REPORT:</h4>"
        valid = shot.validation_result
        if valid:
            passed = valid.get("passed", True)
            failures = valid.get("failures", [])
            severity = valid.get("severity", "none")
            
            p_color = "#2ecc71" if passed else "#e74c3c"
            p_text = "PASSED ALL GUARDRAILS" if passed else "FAILED QC VERIFICATION"
            
            html += f"<div style='font-weight: bold; color: {p_color}; margin-bottom: 5px;'>{p_text} (Severity: {severity.upper()})</div>"
            if failures:
                html += "<ol style='color: #ff6b6b;'>"
                for fail in failures:
                    html += f"<li>{fail}</li>"
                html += "</ol>"
            else:
                html += "<span style='color: #2ecc71;'>✔ All character clothing, narrative plot, aesthetic styles, and physical gravity boundaries satisfied.</span><br/>"
        else:
            html += "<span style='color: #666666; font-style: italic;'>Quality control checks pending render.</span><br/>"
            
        self.log_viewer.setHtml(html)
        
    def _get_status_color(self, status: str) -> str:
        if status == "done": return "#2ecc71"
        if status == "failed": return "#e74c3c"
        if status in ["generating", "running"]: return "#f1c40f"
        return "#888888"

