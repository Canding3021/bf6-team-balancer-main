"""BF6 Team Balancer - Result page: run algorithm, render report, copy text."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QStackedWidget, QComboBox, QHeaderView,
    QMessageBox, QFrame, QGridLayout, QSizePolicy, QAbstractItemView, QProgressBar,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor
from ..theme import get_theme_squad_colors
from ..constants import ALLOC_MODE_NAMES, GAME_MODE_NAMES
from ...core.algorithm import (
    allocate_teams, random_allocate, compute_balance_report, GAME_MODES,
)
from ...core.history import save_record


class ResultPageMixin:
    def _build_page_result(self):
        """Build the result page with team tables, reserves, and balance summary."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        # Summary bar
        self.balance_label = QLabel("请先完成分队")
        self.balance_label.setObjectName("balance_summary")
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.balance_label)

        # Three columns: NATO | PAC | Reserves
        columns = QHBoxLayout()
        columns.setSpacing(12)

        # NATO
        self.result_left_frame = QFrame()
        self.result_left_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        left_layout = QVBoxLayout(self.result_left_frame)
        left_layout.setSpacing(6)
        self.lbl_a = QLabel("北约")
        self.lbl_a.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        self.lbl_a.setStyleSheet("color: #9aadd4; background: transparent;")
        left_layout.addWidget(self.lbl_a)

        self.team_a_table = QTableWidget()
        self.team_a_table.setColumnCount(5)
        self.team_a_table.setHorizontalHeaderLabels(["小队", "昵称", "KD", "KPM", "得分"])
        self.team_a_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.team_a_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.team_a_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.team_a_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.team_a_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.team_a_table.setColumnWidth(0, 50)
        self.team_a_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.team_a_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.team_a_table.verticalHeader().setVisible(False)
        left_layout.addWidget(self.team_a_table, stretch=1)
        columns.addWidget(self.result_left_frame, stretch=3)

        # PAC
        self.result_right_frame = QFrame()
        self.result_right_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        right_layout = QVBoxLayout(self.result_right_frame)
        right_layout.setSpacing(6)
        self.lbl_b = QLabel("和平军团")
        self.lbl_b.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        self.lbl_b.setStyleSheet("color: #d4a0a0; background: transparent;")
        right_layout.addWidget(self.lbl_b)

        self.team_b_table = QTableWidget()
        self.team_b_table.setColumnCount(5)
        self.team_b_table.setHorizontalHeaderLabels(["小队", "昵称", "KD", "KPM", "得分"])
        self.team_b_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.team_b_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.team_b_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.team_b_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.team_b_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.team_b_table.setColumnWidth(0, 50)
        self.team_b_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.team_b_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.team_b_table.verticalHeader().setVisible(False)
        right_layout.addWidget(self.team_b_table, stretch=1)
        columns.addWidget(self.result_right_frame, stretch=3)

        # Reserves (side by side with teams)
        self.result_reserve_frame = QFrame()
        self.result_reserve_frame.setStyleSheet("QFrame { background: #333346; border-radius: 10px; }")
        reserve_layout_inner = QVBoxLayout(self.result_reserve_frame)
        reserve_layout_inner.setSpacing(6)
        self.lbl_r = QLabel("候补")
        self.lbl_r.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        self.lbl_r.setStyleSheet("color: #c8b88a; background: transparent;")
        reserve_layout_inner.addWidget(self.lbl_r)

        self.reserve_table = QTableWidget()
        self.reserve_table.setColumnCount(3)
        self.reserve_table.setHorizontalHeaderLabels(["昵称", "KD", "KPM"])
        self.reserve_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.reserve_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.reserve_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.reserve_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.reserve_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.reserve_table.verticalHeader().setVisible(False)
        reserve_layout_inner.addWidget(self.reserve_table, stretch=1)
        columns.addWidget(self.result_reserve_frame, stretch=2)

        layout.addLayout(columns, stretch=1)

        # Warning label
        self.warning_label = QLabel("")
        self.warning_label.setObjectName("warning")
        self.warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.warning_label.setWordWrap(True)
        layout.addWidget(self.warning_label)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_copy = QPushButton("📋 复制结果")
        btn_copy.setFixedWidth(140)
        btn_copy.clicked.connect(self._copy_result)
        btn_history = QPushButton("📜 历史记录")
        btn_history.setFixedWidth(140)
        btn_history.clicked.connect(self._show_history)
        btn_row.addStretch()
        btn_row.addWidget(btn_copy)
        btn_row.addWidget(btn_history)
        layout.addLayout(btn_row)

        return page

    def _run_algorithm(self):
        if not self.players:
            QMessageBox.warning(self, "提示", "没有玩家数据，请先导入 Excel 文件")
            return

        bindings = []
        used_names = set()
        for row in getattr(self, "binding_rows", []):
            a = row["cb1"].currentText()
            b = row["cb2"].currentText()
            if a.startswith("--") or b.startswith("--"):
                continue
            if a == b:
                QMessageBox.warning(self, "提示", f"不能绑定同一个玩家: {a}")
                return
            if a in used_names or b in used_names:
                QMessageBox.warning(self, "提示", f"玩家已被绑定: {a} 或 {b}")
                return
            used_names.add(a)
            used_names.add(b)
            bindings.append({"player_a": a, "player_b": b})

        # Random mode defaults to conquest cap (64 players), game mode page is skipped
        if self.alloc_mode == "random":
            game_mode = "conquest"
        else:
            game_mode = "conquest" if self.card_conquest.isChecked() else "breakthrough"

        try:
            if self.alloc_mode == "random":
                ta, tb, rv = random_allocate(self.players, bindings, game_mode)
            else:
                ta, tb, rv = allocate_teams(self.players, bindings, game_mode)
            self.report = compute_balance_report(ta, tb, rv, game_mode)
            save_record(self.report, self.alloc_mode)
            self._display_report()
        except (ValueError, KeyError) as e:
            QMessageBox.critical(self, "错误", f"分队失败:\n{e}")
            self.report = None

    def _display_report(self):
        """Render the allocation report to the result page."""
        r = self.report
        bl = r["balance"]
        mode_name = GAME_MODE_NAMES.get(r["game_mode"], r["game_mode"])

        if self.alloc_mode == "random":
            self.balance_label.setText(
                f"[{mode_name} · 随机分配]  "
                f"KD差距: {bl['kd_diff']}  |  "
                f"KPM差距: {bl['kpm_diff']}  |  "
                f"总分差距: {bl['score_diff']}"
            )
        else:
            self.balance_label.setText(
                f"[{mode_name}]  "
                f"KD差距: {bl['kd_diff']}  |  "
                f"KPM差距: {bl['kpm_diff']}  |  "
                f"总分差距: {bl['score_diff']}"
            )

        self._fill_team_table(self.team_a_table, r["team_a"], r["game_mode"])
        self._fill_team_table(self.team_b_table, r["team_b"], r["game_mode"])

        # Reserve table
        rv = r["reserves"]
        self.reserve_table.setRowCount(len(rv["members"]))
        for i, m in enumerate(rv["members"]):
            self.reserve_table.setItem(i, 0, QTableWidgetItem(m["name"]))
            self.reserve_table.setItem(i, 1, QTableWidgetItem(str(m["kd"])))
            self.reserve_table.setItem(i, 2, QTableWidgetItem(str(m["kpm"])))
        if not rv["members"]:
            self.reserve_table.setRowCount(1)
            self.reserve_table.setItem(0, 0, QTableWidgetItem("无候补"))
            self.reserve_table.setItem(0, 1, QTableWidgetItem(""))
            self.reserve_table.setItem(0, 2, QTableWidgetItem(""))

        if self.alloc_mode == "random":
            self.warning_label.setText("🎲 随机分配，均衡性仅供参考")
        elif r["warnings"]:
            self.warning_label.setText("⚠ " + "\n".join(r["warnings"]))
        else:
            self.warning_label.setText("")

    def _fill_team_table(self, table, team_data, game_mode):
        cfg = GAME_MODES[game_mode]
        squad_colors = get_theme_squad_colors(self.current_theme)
        rows = []
        for sq in team_data["squads"]:
            for p in sq["members"]:
                kd = p["kd"]
                kpm = p["kpm"]
                score = round(kd * cfg["kd_weight"] + kpm * cfg["kpm_weight"], 2)
                rows.append((sq["squad_id"], p["name"], str(kd), str(kpm), str(score)))

        table.setRowCount(len(rows))
        for i, (sid, name, kd, kpm, score) in enumerate(rows):
            item_sid = QTableWidgetItem(str(sid))
            item_name = QTableWidgetItem(name)
            item_kd = QTableWidgetItem(kd)
            item_kpm = QTableWidgetItem(kpm)
            item_score = QTableWidgetItem(score)

            # Different squad -> different background color
            color = QColor(squad_colors[(sid - 1) % len(squad_colors)])
            for item in [item_sid, item_name, item_kd, item_kpm, item_score]:
                item.setBackground(color)

            table.setItem(i, 0, item_sid)
            table.setItem(i, 1, item_name)
            table.setItem(i, 2, item_kd)
            table.setItem(i, 3, item_kpm)
            table.setItem(i, 4, item_score)

    def _copy_result(self):
        """Copy formatted result text to clipboard."""
        if not self.report:
            return
        r = self.report
        bl = r["balance"]
        mode_name = GAME_MODE_NAMES.get(r["game_mode"], r["game_mode"])
        alloc_name = ALLOC_MODE_NAMES.get(self.alloc_mode, self.alloc_mode)
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = [
            f"=== BF6 分队结果 ({ts}) ===",
            f"模式: {alloc_name} · {mode_name}",
            "",
        ]

        for team_key in ["team_a", "team_b"]:
            t = r[team_key]
            lines.append(f'【{t["name"]}】({t["total_players"]}人, {t["num_squads"]}小队)')
            for sq in t["squads"]:
                members = "、".join(p["name"] for p in sq["members"])
                lines.append(f'  小队{sq["squad_id"]}: {members}')
            lines.append("")

        if r["reserves"]["members"]:
            names = "、".join(m["name"] for m in r["reserves"]["members"])
            lines.append(f"【候补】{names}")
            lines.append("")

        lines.append(f'均衡: KD差{bl["kd_diff"]} | KPM差{bl["kpm_diff"]} | 总分差{bl["score_diff"]}')

        text = "\n".join(lines)
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "已复制", "分队结果已复制到剪贴板")

