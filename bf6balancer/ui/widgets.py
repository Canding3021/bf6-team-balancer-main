"""BF6 Team Balancer - 自定义控件：ModeCard / SpinnerWidget / ApiQueryWorker。"""

from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QPainter, QPen, QFont

from .theme import THEMES, DEFAULT_THEME
from ..core.api_query import query_all
from ..core.crash_log import log_exception
import sys


class ModeCard(QPushButton):
    """Game mode selection card."""
    def __init__(self, title, desc, mode_id):
        super().__init__()
        self.mode_id = mode_id
        self.setCheckable(True)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._theme = THEMES[DEFAULT_THEME]
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Microsoft YaHei UI", 22, QFont.Weight.Bold))
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("background: transparent; border: none;")

        lbl_desc = QLabel(desc)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setWordWrap(True)
        self._desc_label = lbl_desc

        layout.addWidget(lbl_title)
        layout.addSpacing(10)
        layout.addWidget(lbl_desc)

        self._update_desc_style()

    def _update_desc_style(self):
        if hasattr(self, '_desc_label') and hasattr(self, '_theme'):
            self._desc_label.setStyleSheet(
                f"background: transparent; border: none; color: {self._theme['text_sub']}; font-size: 15px;"
            )

    def set_theme(self, theme):
        self._theme = theme
        self._update_style()
        self._update_desc_style()

    def _update_style(self):
        t = self._theme
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {t["card_alt"]};
                    color: {t["text"]};
                    border: 2px solid {t["accent"]};
                    border-radius: 14px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {t["card"]};
                    color: {t["text"]};
                    border: 2px solid {t["border"]};
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    border-color: {t["accent"]};
                    background: {t["btn"]};
                }}
            """)

    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_style()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._update_style()


class SpinnerWidget(QWidget):
    """A simple rotating spinner animation widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 64)
        self._angle = 0
        self._accent_color = QColor("#7b8db8")  # Updated by theme
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        # Timer started externally via _start_api_query (80ms ≈ 12fps)

    def _rotate(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self._accent_color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)
        painter.drawArc(-24, -24, 48, 48, 0, 270 * 16)


class ApiQueryWorker(QThread):
    """Background thread for querying player stats from gametools.network."""

    progress = pyqtSignal(int, int, dict)   # completed, total, stats
    finished = pyqtSignal(dict)             # full result dict
    failed = pyqtSignal(str)                # error message (thread-side exception)

    def __init__(self, players_data, platform="pc", batch_size=8, timeout=10):
        super().__init__()
        self.players_data = players_data
        self.platform = platform
        self.batch_size = batch_size
        self.timeout = timeout

    def run(self):
        def on_progress(done, total, stats):
            self.progress.emit(done, total, stats)

        try:
            result = query_all(
                self.players_data,
                platform=self.platform,
                batch_size=self.batch_size,
                timeout=self.timeout,
                progress_callback=on_progress,
            )
            self.finished.emit(result)
        except Exception:
            # excepthook can't catch QThread exceptions; log here and signal the UI
            # so the spinner doesn't hang forever on an unexpected query failure.
            log_exception(*sys.exc_info(), context="API query thread")
            self.failed.emit("查询过程中发生错误，请检查网络后重试。详细信息已记录到日志。")
