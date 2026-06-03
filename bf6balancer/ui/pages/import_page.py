"""BF6 Team Balancer - Import page: file picker, theme selector, player table."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QStackedWidget, QComboBox, QHeaderView,
    QMessageBox, QFrame, QGridLayout, QSizePolicy, QAbstractItemView, QProgressBar,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor
from ..theme import THEMES
from ..constants import FONT_FAMILY
from ...core.extract import extract_players
from ...core.algorithm import load_players


class ImportPageMixin:
    def _build_page_import(self):
        """Build the file import page with theme selector, file picker, and player table."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        # Top: title + theme selector
        top_row = QHBoxLayout()
        title = QLabel("导入玩家数据")
        title.setObjectName("title")
        top_row.addWidget(title)
        top_row.addStretch()

        self.theme_label = QLabel("主题:")
        self.theme_label.setStyleSheet("color: #9998aa; font-size: 14px;")
        top_row.addWidget(self.theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(150)
        for tid, t in THEMES.items():
            self.theme_combo.addItem(t["name"], tid)
        # Set current selection
        idx = list(THEMES.keys()).index(self.current_theme)
        self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        top_row.addWidget(self.theme_combo)

        layout.addLayout(top_row)

        subtitle = QLabel("选择 Excel 文件（列1=昵称, 列2=KD, 列3=KPM, 列4=EAID）")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # File selection area
        self.file_frame = QFrame()
        self.file_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; padding: 14px; }")
        file_layout = QHBoxLayout(self.file_frame)

        self.file_icon = QLabel("📄")
        self.file_icon.setFont(QFont("", 24))
        self.file_icon.setStyleSheet("background: transparent;")
        file_layout.addWidget(self.file_icon)

        file_info = QVBoxLayout()
        self.file_name_label = QLabel("未选择文件")
        self.file_name_label.setStyleSheet("font-weight: bold; background: transparent;")
        self.file_hint_label = QLabel("支持 .xlsx / .xls 格式")
        self.file_hint_label.setStyleSheet("color: #6c7086; background: transparent;")
        file_info.addWidget(self.file_name_label)
        file_info.addWidget(self.file_hint_label)
        file_layout.addLayout(file_info, stretch=1)

        btn_file = QPushButton("选择文件")
        btn_file.setMinimumWidth(100)
        btn_file.clicked.connect(self._select_file)
        file_layout.addWidget(btn_file)
        layout.addWidget(self.file_frame)

        # Player count label
        self.count_frame = QFrame()
        self.count_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; padding: 12px; }")
        count_layout = QHBoxLayout(self.count_frame)
        self.player_count_label = QLabel("")
        self.player_count_label.setStyleSheet("color: #8aaa8a; font-weight: bold; background: transparent;")
        count_layout.addStretch()
        count_layout.addWidget(self.player_count_label)
        layout.addWidget(self.count_frame)

        # Player table (fills remaining space)
        self.player_table = QTableWidget()
        self.player_table.setColumnCount(4)
        self.player_table.setHorizontalHeaderLabels(["昵称", "KD", "KPM", "EAID"])
        self.player_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.player_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.player_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.player_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.player_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.player_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.player_table.setAlternatingRowColors(True)
        self.player_table.verticalHeader().setVisible(False)
        layout.addWidget(self.player_table, stretch=1)

        return page

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Excel 文件", "", "Excel (*.xlsx *.xls)"
        )
        if not path:
            return
        try:
            self.players_data = extract_players(path)
            self.players = load_players({"players": self.players_data})
            self.file_name_label.setText(os.path.basename(path))
            self.file_hint_label.setText(f"已加载 {len(self.players)} 名玩家")
            self.player_count_label.setText(f"共 {len(self.players)} 人")
            self._refresh_player_table()
            self.btn_next.setEnabled(True)
            self._refresh_binding_combos()
        except (OSError, ValueError) as e:
            QMessageBox.critical(self, "错误", f"读取失败:\n{e}")

    def _refresh_player_table(self):
        self.player_table.setRowCount(len(self.players_data))
        for i, p in enumerate(self.players_data):
            self.player_table.setItem(i, 0, QTableWidgetItem(p["name"]))
            kd = p.get("kd")
            self.player_table.setItem(i, 1, QTableWidgetItem(str(kd) if kd is not None else "-"))
            kpm = p.get("kpm_adjusted") or p.get("kpm_raw")
            self.player_table.setItem(i, 2, QTableWidgetItem(str(kpm) if kpm is not None else "-"))
            self.player_table.setItem(i, 3, QTableWidgetItem(p.get("eaid", "")))

