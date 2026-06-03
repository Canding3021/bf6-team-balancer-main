"""BF6 Team Balancer - History page: browse and view past allocations."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QStackedWidget, QComboBox, QHeaderView,
    QMessageBox, QFrame, QGridLayout, QSizePolicy, QAbstractItemView, QProgressBar,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor
from ..theme import get_theme_squad_colors
from ..constants import ALLOC_MODE_NAMES, GAME_MODE_NAMES, PAGE_HISTORY
from ...core.history import load_history


class HistoryPageMixin:
    def _build_page_history(self):
        """Build the history page with record list and detail view."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        title = QLabel("历史记录")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("点击记录查看详情，或直接点「下一步」跳过")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # History list
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["#", "时间", "分配模式", "游戏模式", "人数"])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.setColumnWidth(0, 40)
        self.history_table.setMaximumHeight(200)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.clicked.connect(self._on_history_row_clicked)
        layout.addWidget(self.history_table)

        # Detail area (two columns, same structure as result page)
        detail_columns = QHBoxLayout()
        detail_columns.setSpacing(12)

        # Left: Team A
        self.hist_left_frame = QFrame()
        self.hist_left_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        left_layout = QVBoxLayout(self.hist_left_frame)
        left_layout.setSpacing(6)
        self.hist_lbl_a = QLabel("阵营A")
        self.hist_lbl_a.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        self.hist_lbl_a.setStyleSheet("color: #9aadd4; background: transparent;")
        left_layout.addWidget(self.hist_lbl_a)
        self.hist_team_a_table = QTableWidget()
        self.hist_team_a_table.setColumnCount(2)
        self.hist_team_a_table.setHorizontalHeaderLabels(["小队", "昵称"])
        self.hist_team_a_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.hist_team_a_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.hist_team_a_table.setColumnWidth(0, 50)
        self.hist_team_a_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.hist_team_a_table.verticalHeader().setVisible(False)
        left_layout.addWidget(self.hist_team_a_table, stretch=1)
        detail_columns.addWidget(self.hist_left_frame, stretch=1)

        # Right: Team B
        self.hist_right_frame = QFrame()
        self.hist_right_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        right_layout = QVBoxLayout(self.hist_right_frame)
        right_layout.setSpacing(6)
        self.hist_lbl_b = QLabel("阵营B")
        self.hist_lbl_b.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        self.hist_lbl_b.setStyleSheet("color: #d4a0a0; background: transparent;")
        right_layout.addWidget(self.hist_lbl_b)
        self.hist_team_b_table = QTableWidget()
        self.hist_team_b_table.setColumnCount(2)
        self.hist_team_b_table.setHorizontalHeaderLabels(["小队", "昵称"])
        self.hist_team_b_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.hist_team_b_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.hist_team_b_table.setColumnWidth(0, 50)
        self.hist_team_b_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.hist_team_b_table.verticalHeader().setVisible(False)
        right_layout.addWidget(self.hist_team_b_table, stretch=1)
        detail_columns.addWidget(self.hist_right_frame, stretch=1)

        layout.addLayout(detail_columns, stretch=1)

        # Bottom: reserve + balance info
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)
        self.hist_reserve_label = QLabel("")
        self.hist_reserve_label.setStyleSheet("color: #c8b88a; font-size: 15px;")
        self.hist_balance_label = QLabel("")
        self.hist_balance_label.setStyleSheet("color: #a8c8a8; font-size: 15px;")
        bottom_row.addWidget(self.hist_reserve_label, stretch=1)
        bottom_row.addWidget(self.hist_balance_label)
        layout.addLayout(bottom_row)

        return page

    def _on_history_row_clicked(self, index):
        """Handle click on a history row, show detail."""
        row = index.row()
        history = load_history()
        if row >= len(history):
            return
        rec = history[row]
        self._display_history_detail(rec)

    def _display_history_detail(self, rec):
        """Render a history record to the detail area."""
        self.hist_lbl_a.setText(rec["team_a"]["name"])
        self.hist_lbl_b.setText(rec["team_b"]["name"])
        squad_colors = get_theme_squad_colors(self.current_theme)

        for team_key, table in [("team_a", self.hist_team_a_table), ("team_b", self.hist_team_b_table)]:
            t = rec[team_key]
            rows = []
            for sq in t["squads"]:
                for name in sq["members"]:
                    rows.append((sq["id"], name))
            table.setRowCount(len(rows))
            for i, (sid, name) in enumerate(rows):
                item_sid = QTableWidgetItem(str(sid))
                item_name = QTableWidgetItem(name)
                color = QColor(squad_colors[(sid - 1) % len(squad_colors)])
                item_sid.setBackground(color)
                item_name.setBackground(color)
                table.setItem(i, 0, item_sid)
                table.setItem(i, 1, item_name)

        # Reserve
        if rec["reserves"]:
            self.hist_reserve_label.setText(f'候补: {"、".join(rec["reserves"])}')
        else:
            self.hist_reserve_label.setText("无候补")

        # Balance
        bl = rec["balance"]
        self.hist_balance_label.setText(f'KD差{bl["kd_diff"]} | KPM差{bl["kpm_diff"]} | 总分差{bl["score_diff"]}')

    def _refresh_history_table(self):
        """Refresh the history list."""
        history = load_history()

        self.history_table.setRowCount(len(history))
        for i, rec in enumerate(history):
            alloc = ALLOC_MODE_NAMES.get(rec["alloc_mode"], rec["alloc_mode"])
            game = GAME_MODE_NAMES.get(rec["game_mode"], rec["game_mode"])
            total = rec["team_a"]["total_players"] + rec["team_b"]["total_players"]
            self.history_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.history_table.setItem(i, 1, QTableWidgetItem(rec["timestamp"]))
            self.history_table.setItem(i, 2, QTableWidgetItem(alloc))
            self.history_table.setItem(i, 3, QTableWidgetItem(game))
            self.history_table.setItem(i, 4, QTableWidgetItem(f"{total}人"))

    def _show_history(self):
        history = load_history()
        if not history:
            QMessageBox.information(self, "历史记录", "暂无历史记录")
            return
        self._refresh_history_table()
        self._visited_history = True
        self.current_page = PAGE_HISTORY
        self.stack.setCurrentIndex(PAGE_HISTORY)
        self._update_nav()

