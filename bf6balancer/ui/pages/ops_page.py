"""BF6 Team Balancer - Action page: re-import / re-allocate / exit + resets."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QStackedWidget, QComboBox, QHeaderView,
    QMessageBox, QFrame, QGridLayout, QSizePolicy, QAbstractItemView, QProgressBar,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor
from ..constants import PAGE_IMPORT, PAGE_ALLOC


class OpsPageMixin:
    def _build_page_ops(self):
        """Build the operations page (re-import, re-allocate, exit)."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)

        title = QLabel("操作")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("选择下一步操作")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Action buttons
        btn_reimport = QPushButton("📄 重新导入")
        btn_reimport.setMinimumHeight(60)
        btn_reimport.setFont(QFont("Microsoft YaHei UI", 18))
        btn_reimport.clicked.connect(self._reset_to_import)

        btn_realloc = QPushButton("🔀 重新分配")
        btn_realloc.setMinimumHeight(60)
        btn_realloc.setFont(QFont("Microsoft YaHei UI", 18))
        btn_realloc.clicked.connect(self._reset_to_alloc)

        btn_exit = QPushButton("❌ 退出")
        btn_exit.setObjectName("exit_btn")
        btn_exit.setMinimumHeight(60)
        btn_exit.setFont(QFont("Microsoft YaHei UI", 18))
        btn_exit.clicked.connect(self.close)

        layout.addStretch()
        layout.addWidget(btn_reimport)
        layout.addSpacing(12)
        layout.addWidget(btn_realloc)
        layout.addSpacing(12)
        layout.addWidget(btn_exit)
        layout.addStretch()

        return page

    def _reset_to_import(self):
        """Reset to import page, clear all data."""
        # Stop API worker if running
        if hasattr(self, '_api_worker') and self._api_worker.isRunning():
            self._api_worker.terminate()
            self._api_worker.wait()
        self._api_query_done = False
        self.players_data = None
        self.players = None
        self.report = None
        self.alloc_mode = "balanced"
        self._visited_history = False
        self.file_name_label.setText("未选择文件")
        self.file_hint_label.setText("支持 .xlsx / .xls 格式")
        self.player_count_label.setText("")
        self.player_table.setRowCount(0)
        self.balance_label.setText("请先完成分队")
        self.team_a_table.setRowCount(0)
        self.team_b_table.setRowCount(0)
        self.reserve_table.setRowCount(0)
        self.warning_label.setText("")
        # Clear bindings
        for row in getattr(self, "binding_rows", []):
            row["widget"].deleteLater()
        self.binding_rows = []
        # Reset alloc mode cards
        self.card_balanced.setChecked(True)
        self.card_random.setChecked(False)
        self.current_page = PAGE_IMPORT
        self.stack.setCurrentIndex(PAGE_IMPORT)
        self._update_nav()

    def _reset_to_alloc(self):
        """Reset to alloc mode page, keep player data."""
        self.report = None
        self._visited_history = False
        self.balance_label.setText("请先完成分队")
        self.team_a_table.setRowCount(0)
        self.team_b_table.setRowCount(0)
        self.reserve_table.setRowCount(0)
        self.warning_label.setText("")
        self.current_page = PAGE_ALLOC
        self.stack.setCurrentIndex(PAGE_ALLOC)
        self._update_nav()

