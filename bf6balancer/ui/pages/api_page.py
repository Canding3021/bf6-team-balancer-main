"""BF6 Team Balancer - API query page: spinner, progress, offset application."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QStackedWidget, QComboBox, QHeaderView,
    QMessageBox, QFrame, QGridLayout, QSizePolicy, QAbstractItemView, QProgressBar,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor
from ..widgets import SpinnerWidget, ApiQueryWorker
from ...core.algorithm import load_players
from ...core.api_query import apply_results_to_players


class ApiPageMixin:
    def _build_page_api_query(self):
        """Build the API query loading page with spinner and progress."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Spinner (hidden after query completes)
        self.api_spinner = SpinnerWidget()
        layout.addWidget(self.api_spinner, alignment=Qt.AlignmentFlag.AlignCenter)

        # Checkmark (hidden during query, shown after completion)
        self.api_checkmark = QLabel("✅")
        self.api_checkmark.setStyleSheet("font-size: 48px; background: transparent;")
        self.api_checkmark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.api_checkmark.setVisible(False)
        layout.addWidget(self.api_checkmark, alignment=Qt.AlignmentFlag.AlignCenter)

        # Status text
        self.api_status_label = QLabel("准备查询...")
        self.api_status_label.setObjectName("title")
        self.api_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.api_status_label)

        # Progress text
        self.api_progress_label = QLabel("")
        self.api_progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.api_progress_label.setStyleSheet("font-size: 18px; color: #9998aa;")
        layout.addWidget(self.api_progress_label)

        # Progress bar
        self.api_progress_bar = QProgressBar()
        self.api_progress_bar.setRange(0, 100)
        self.api_progress_bar.setValue(0)
        self.api_progress_bar.setFixedWidth(400)
        self.api_progress_bar.setFixedHeight(12)
        self.api_progress_bar.setTextVisible(False)
        layout.addWidget(self.api_progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_row.setSpacing(20)
        self.api_stat_found = QLabel("✅ 查到: 0")
        self.api_stat_found.setStyleSheet("font-size: 14px; color: #8aaa8a;")
        self.api_stat_not_found = QLabel("❌ 未找到: 0")
        self.api_stat_not_found.setStyleSheet("font-size: 14px; color: #b87b7b;")
        self.api_stat_no_eaid = QLabel("⏭ 无EAID: 0")
        self.api_stat_no_eaid.setStyleSheet("font-size: 14px; color: #9998aa;")
        stats_row.addWidget(self.api_stat_found)
        stats_row.addWidget(self.api_stat_not_found)
        stats_row.addWidget(self.api_stat_no_eaid)
        layout.addLayout(stats_row)

        # Warning label (hidden by default)
        self.api_warning_label = QLabel("")
        self.api_warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.api_warning_label.setStyleSheet("font-size: 13px; color: #d4a574; padding: 8px;")
        self.api_warning_label.setWordWrap(True)
        self.api_warning_label.setVisible(False)
        layout.addWidget(self.api_warning_label)

        return page
    def _start_api_query(self):
        """Start the API query process on a background thread."""
        self._api_query_done = False

        # Disconnect old worker signals to avoid stale connections
        if hasattr(self, '_api_worker') and self._api_worker is not None:
            try:
                self._api_worker.progress.disconnect()
                self._api_worker.finished.disconnect()
                self._api_worker.failed.disconnect()
            except TypeError:
                pass  # Already disconnected

        # Reset UI
        self.api_status_label.setText("正在查询玩家数据 (gametools)...")
        self.api_progress_label.setText(f"0 / {len(self.players_data)}")
        self.api_progress_bar.setValue(0)
        self.api_stat_found.setText("✅ 查到: 0")
        self.api_stat_not_found.setText("❌ 未找到: 0")
        self.api_stat_no_eaid.setText("⏭ 无EAID: 0")
        self.api_warning_label.setVisible(False)
        self.api_spinner.setVisible(True)
        self.api_checkmark.setVisible(False)
        self.api_spinner._timer.start(80)  # ~12fps, slower rotation

        # Disable navigation during query
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)

        # Create and start worker
        self._api_worker = ApiQueryWorker(self.players_data)
        self._api_worker.progress.connect(self._on_api_progress)
        self._api_worker.finished.connect(self._on_api_finished)
        self._api_worker.failed.connect(self._on_api_failed)
        self._api_worker.start()
    def _on_api_progress(self, completed, total, stats):
        """Update progress UI during API query."""
        phase = stats.get("phase", "")
        if phase == "joarchy_id":
            self.api_status_label.setText("正在查询修正数据 (joarchy)...")
        elif phase == "joarchy_fb":
            self.api_status_label.setText("正在兜底查询 (joarchy)...")

        self.api_progress_label.setText(f"{completed} / {total}")
        pct = int(completed / total * 100) if total > 0 else 0
        self.api_progress_bar.setValue(pct)
        self.api_stat_found.setText(f"✅ 查到: {stats['found']}")
        self.api_stat_not_found.setText(f"❌ 未找到: {stats['not_found']}")
        self.api_stat_no_eaid.setText(f"⏭ 无EAID: {stats['no_eaid']}")

    def _on_api_finished(self, result):
        """Handle API query completion."""
        self._api_query_done = True
        self.api_spinner._timer.stop()
        self.api_spinner.setVisible(False)
        self.api_checkmark.setVisible(True)
        self.api_status_label.setText("查询完成！")

        # Show warning if any
        if result.get("warning"):
            self.api_warning_label.setText(f"⚠️ {result['warning']}")
            self.api_warning_label.setVisible(True)

        # Write API results back to player data (offset / freeze logic lives in api_query)
        apply_results_to_players(self.players_data, result)

        # Rebuild Player objects with updated data
        self.players = load_players({"players": self.players_data})

        # Refresh the import page table to show updated values
        self._refresh_player_table()

        # Enable navigation to next page
        self.btn_next.setEnabled(True)
        self.btn_next.setText("下一步 >")
        self._next_handler = self._go_next

    def _on_api_failed(self, message):
        """Handle a thread-side query failure: stop spinner, let the user retry."""
        self._api_query_done = False
        self.api_spinner._timer.stop()
        self.api_spinner.setVisible(False)
        self.api_checkmark.setVisible(False)
        self.api_status_label.setText("查询失败")
        self.api_warning_label.setText(f"⚠️ {message}")
        self.api_warning_label.setVisible(True)
        # Re-enable back/retry: prev returns to import, next re-runs the query.
        self.btn_prev.setEnabled(True)
        self.btn_next.setEnabled(True)
        self.btn_next.setText("重试查询")
        self._next_handler = self._start_api_query

