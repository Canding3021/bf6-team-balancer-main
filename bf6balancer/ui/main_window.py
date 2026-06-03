"""BF6 Team Balancer - 主窗口：组合各页面 Mixin，负责导航/主题/初始化。"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QStackedWidget, QComboBox, QHeaderView, QMessageBox, QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from .theme import THEMES, DEFAULT_THEME, build_stylesheet
from .constants import (
    FONT_FAMILY, _MAIN_FLOW, NUM_STEPS, PAGE_TO_STEP, SKIPPED_STEP_RANDOM,
    PAGE_IMPORT, PAGE_API, PAGE_ALLOC, PAGE_GAME, PAGE_SQUAD,
    PAGE_RESULT, PAGE_HISTORY, PAGE_ACTION,
)
from .widgets import ModeCard, SpinnerWidget, ApiQueryWorker
from ..core.history import load_config, save_config
from .pages.import_page import ImportPageMixin
from .pages.api_page import ApiPageMixin
from .pages.mode_pages import ModePagesMixin
from .pages.custom_page import CustomPageMixin
from .pages.result_page import ResultPageMixin
from .pages.history_page import HistoryPageMixin
from .pages.ops_page import OpsPageMixin


class MainWindow(
    QMainWindow,
    ImportPageMixin, ApiPageMixin, ModePagesMixin, CustomPageMixin,
    ResultPageMixin, HistoryPageMixin, OpsPageMixin,
):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BF6 Team Balancer")
        self.setMinimumSize(1100, 750)

        # Load saved theme
        config = load_config()
        self.current_theme = config.get("theme", DEFAULT_THEME)
        if self.current_theme not in THEMES:
            self.current_theme = DEFAULT_THEME
        self.setStyleSheet(build_stylesheet(THEMES[self.current_theme]))

        self.players_data = None
        self.players = None
        self.report = None
        self.alloc_mode = "balanced"  # "balanced" | "random"
        self._visited_history = False  # Whether user has visited history page
        self._api_query_done = False   # Whether API query page has completed

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 16, 20, 16)

        # Top navigation bar
        nav = QHBoxLayout()
        nav.setSpacing(8)
        self.btn_prev = QPushButton("< 上一步")
        self.btn_prev.setMinimumWidth(100)
        self.btn_next = QPushButton("下一步 >")
        self.btn_next.setObjectName("primary")
        self.btn_next.setMinimumWidth(120)
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)

        self.step_indicators = []
        self.step_connectors = []
        indicator_row = QHBoxLayout()
        indicator_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        indicator_row.setSpacing(4)
        t = THEMES[self.current_theme]
        for i in range(NUM_STEPS):
            dot = QLabel(f" {i+1} ")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setFixedSize(42, 42)
            dot.setStyleSheet(
                f"background: {t['step_pending']}; border-radius: 21px; font-weight: bold; color: {t['text_disabled']}; font-size: 17px;"
            )
            self.step_indicators.append(dot)
            indicator_row.addWidget(dot)
            if i < NUM_STEPS - 1:
                line = QLabel("---")
                line.setStyleSheet(f"color: {t['step_connector']}; background: transparent;")
                self.step_connectors.append(line)
                indicator_row.addWidget(line)

        nav.addWidget(self.btn_prev)
        nav.addStretch()
        nav.addLayout(indicator_row)
        nav.addStretch()
        nav.addWidget(self.btn_next)
        main_layout.addLayout(nav)

        # Page stack
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, stretch=1)

        self.page_import = self._build_page_import()
        self.page_api_query = self._build_page_api_query()
        self.page_alloc = self._build_page_alloc_mode()
        self.page_mode = self._build_page_mode()
        self.page_custom = self._build_page_custom()
        self.page_result = self._build_page_result()
        self.page_history = self._build_page_history()
        self.page_ops = self._build_page_ops()

        self.stack.addWidget(self.page_import)       # index 0
        self.stack.addWidget(self.page_api_query)    # index 1
        self.stack.addWidget(self.page_alloc)        # index 2
        self.stack.addWidget(self.page_mode)         # index 3
        self.stack.addWidget(self.page_custom)       # index 4
        self.stack.addWidget(self.page_result)       # index 5
        self.stack.addWidget(self.page_history)      # index 6
        self.stack.addWidget(self.page_ops)          # index 7

        self.btn_prev.clicked.connect(self._go_prev)

        self.current_page = PAGE_IMPORT
        self._next_handler = self._go_next
        self.btn_next.clicked.connect(lambda: self._next_handler())
        self._update_nav()
        self._apply_dynamic_styles()

    # -- Navigation ------------------------------------------------

    def _is_skipped(self, page):
        """Game mode page is skipped in random alloc mode."""
        return page == PAGE_GAME and self.alloc_mode == "random"

    def _go_prev(self):
        if self.current_page <= PAGE_IMPORT:
            return
        # HISTORY and ACTION both step back to RESULT.
        if self.current_page in (PAGE_HISTORY, PAGE_ACTION):
            target = PAGE_RESULT
        else:
            # Walk backward through the main flow, skipping disabled pages.
            idx = _MAIN_FLOW.index(self.current_page)
            target = _MAIN_FLOW[idx - 1]
            while self._is_skipped(target) and idx - 1 > 0:
                idx -= 1
                target = _MAIN_FLOW[idx - 1]
        self.current_page = target
        self.stack.setCurrentIndex(self.current_page)
        self._update_nav()

    def _go_next(self):
        # Pages with side effects / guards on the way forward.
        if self.current_page == PAGE_IMPORT:
            if self.players_data is None or len(self.players_data) == 0:
                QMessageBox.warning(self, "提示", "请先选择 Excel 文件")
                return
            self.current_page = PAGE_API
            self.stack.setCurrentIndex(self.current_page)
            self._start_api_query()
            self._update_nav()
            return
        if self.current_page == PAGE_SQUAD:
            self._run_algorithm()
            if self.report is None:
                return
            self.current_page = PAGE_RESULT
            self.stack.setCurrentIndex(self.current_page)
            self._update_nav()
            return
        if self.current_page in (PAGE_RESULT, PAGE_HISTORY):
            target = PAGE_ACTION
        else:
            # Walk forward through the main flow, skipping disabled pages.
            idx = _MAIN_FLOW.index(self.current_page)
            target = _MAIN_FLOW[idx + 1]
            while self._is_skipped(target) and idx + 1 < len(_MAIN_FLOW) - 1:
                idx += 1
                target = _MAIN_FLOW[idx + 1]
        self.current_page = target
        self.stack.setCurrentIndex(self.current_page)
        self._update_nav()

    def _update_nav(self):
        self._next_handler = self._go_next
        self.btn_next.setText("下一步 >")
        self.btn_next.setObjectName("primary")

        if self.current_page == PAGE_ACTION:
            # Action page: prev -> result, no next
            self.btn_prev.setEnabled(True)
            self.btn_next.setEnabled(False)
        elif self.current_page in (PAGE_RESULT, PAGE_HISTORY):
            self.btn_prev.setEnabled(True)
            self.btn_next.setEnabled(True)
        elif self.current_page == PAGE_API:
            # Nav stays disabled until the query finishes.
            self.btn_prev.setEnabled(self._api_query_done)
            self.btn_next.setEnabled(self._api_query_done)
        else:
            self.btn_prev.setEnabled(self.current_page > PAGE_IMPORT)
            self.btn_next.setText("查看结果" if self.current_page == PAGE_SQUAD else "下一步 >")
            self.btn_next.setEnabled(self.current_page != PAGE_IMPORT or self.players_data is not None)

        # Re-apply style
        self.btn_next.style().unpolish(self.btn_next)
        self.btn_next.style().polish(self.btn_next)

        current_step = PAGE_TO_STEP.get(self.current_page, 0)
        t = THEMES[self.current_theme]
        for i, dot in enumerate(self.step_indicators):
            if i == SKIPPED_STEP_RANDOM and self.alloc_mode == "random":
                dot.setStyleSheet(self._dot_style(t["step_skipped"], t["text_disabled"], strike=True))
            elif i == current_step:
                dot.setStyleSheet(self._dot_style(t["step_active"], t["btn_text"]))
            elif i < current_step:
                dot.setStyleSheet(self._dot_style(t["step_done"], t["btn_text"]))
            else:
                dot.setStyleSheet(self._dot_style(t["step_pending"], t["text_disabled"]))

    @staticmethod
    def _dot_style(bg, color, strike=False):
        """Build the stylesheet for a step indicator dot."""
        extra = " text-decoration: line-through;" if strike else ""
        return (f"background: {bg}; border-radius: 21px; font-weight: bold; "
                f"color: {color}; font-size: 17px;{extra}")


    # -- Theme Switch -----------------------------------------------

    def _apply_dynamic_styles(self):
        """Apply theme colors to all widgets with hardcoded stylesheets."""
        t = THEMES[self.current_theme]

        # Import page
        self.file_frame.setStyleSheet(f"QFrame {{ background: {t['card']}; border-radius: 10px; padding: 14px; }}")
        self.file_hint_label.setStyleSheet(f"color: {t['text_hint']}; background: transparent;")
        self.count_frame.setStyleSheet(f"QFrame {{ background: {t['card']}; border-radius: 10px; padding: 12px; }}")
        self.player_count_label.setStyleSheet(f"color: {t['balance']}; font-weight: bold; background: transparent;")
        self.theme_label.setStyleSheet(f"color: {t['text_sub']}; font-size: 14px;")

        # API query page
        self.api_progress_label.setStyleSheet(f"font-size: 18px; color: {t['text_sub']};")
        self.api_stat_found.setStyleSheet(f"font-size: 14px; color: {t['balance']};")
        self.api_stat_not_found.setStyleSheet(f"font-size: 14px; color: {t['exit']};")
        self.api_stat_no_eaid.setStyleSheet(f"font-size: 14px; color: {t['text_sub']};")
        self.api_warning_label.setStyleSheet(f"font-size: 13px; color: {t['warning']}; padding: 8px;")

        # Result page - team frames
        self.result_left_frame.setStyleSheet(f"QFrame {{ background: {t['card']}; border-radius: 10px; }}")
        self.result_right_frame.setStyleSheet(f"QFrame {{ background: {t['card']}; border-radius: 10px; }}")
        self.result_reserve_frame.setStyleSheet(f"QFrame {{ background: {t['card']}; border-radius: 10px; }}")
        self.lbl_a.setStyleSheet(f"color: {t['team_a']}; background: transparent;")
        self.lbl_b.setStyleSheet(f"color: {t['team_b']}; background: transparent;")
        self.lbl_r.setStyleSheet(f"color: {t['reserve']}; background: transparent;")

        # History page - team frames
        self.hist_left_frame.setStyleSheet(f"QFrame {{ background: {t['card']}; border-radius: 10px; }}")
        self.hist_right_frame.setStyleSheet(f"QFrame {{ background: {t['card']}; border-radius: 10px; }}")
        self.hist_lbl_a.setStyleSheet(f"color: {t['team_a']}; background: transparent;")
        self.hist_lbl_b.setStyleSheet(f"color: {t['team_b']}; background: transparent;")
        self.hist_reserve_label.setStyleSheet(f"color: {t['reserve']}; font-size: 15px;")
        self.hist_balance_label.setStyleSheet(f"color: {t['balance']}; font-size: 15px;")

        # Custom squad page - binding rows
        for row in getattr(self, "binding_rows", []):
            row["widget"].setStyleSheet(f"QFrame {{ background: {t['btn']}; border-radius: 8px; padding: 10px; }}")

        # Spinner color
        self.api_spinner._accent_color = QColor(t["accent"])

    def _on_theme_changed(self, index):
        theme_id = self.theme_combo.currentData()
        if theme_id and theme_id in THEMES:
            self.current_theme = theme_id
            t = THEMES[theme_id]
            self.setStyleSheet(build_stylesheet(t))
            # Sync all ModeCard themes
            for card in [self.card_balanced, self.card_random,
                         self.card_conquest, self.card_breakthrough]:
                card.set_theme(t)
            # Refresh step indicator colors
            for line in self.step_connectors:
                line.setStyleSheet(f"color: {t['step_connector']}; background: transparent;")
            self._update_nav()
            # Refresh dynamic styles
            self._apply_dynamic_styles()
            # Save preference
            config = load_config()
            config["theme"] = theme_id
            save_config(config)

