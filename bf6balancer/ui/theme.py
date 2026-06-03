"""BF6 Team Balancer - 颜色主题与全局样式表生成。"""

from .constants import FONT_FAMILY


# -- Theme Config -------------------------------------------------

THEMES = {
    "dark_gray": {
        "name": "🌙 暗夜灰",
        "bg": "#2b2b3a", "card": "#333346", "card_alt": "#3a3a50",
        "btn": "#3d3d50", "btn_hover": "#4a4a60", "btn_disabled": "#333344",
        "text": "#e0dfe6", "text_disabled": "#666680", "text_sub": "#9998aa",
        "text_hint": "#777790", "border": "#44445a", "border_header": "#4a4a60",
        "accent": "#7b8db8", "accent_hover": "#8a9cc8",
        "exit": "#b87b7b", "exit_hover": "#c88a8a",
        "balance": "#a8c8a8", "warning": "#d4a574",
        "btn_text": "#ffffff",
        "team_a": "#9aadd4", "team_b": "#d4a0a0", "reserve": "#c8b88a",
        "squads": ["#363648", "#3e3e52", "#363648", "#42425a"],
        "step_active": "#7b8db8", "step_done": "#8aaa8a", "step_pending": "#3d3d50",
        "step_skipped": "#2d2d3a", "step_connector": "#44445a",
    },
    "deep_blue": {
        "name": "🌊 深海蓝",
        "bg": "#1a2332", "card": "#1e2a3a", "card_alt": "#223344",
        "btn": "#253545", "btn_hover": "#2d4050", "btn_disabled": "#1e2830",
        "text": "#d0dfe6", "text_disabled": "#556677", "text_sub": "#8899aa",
        "text_hint": "#667788", "border": "#2a3a4a", "border_header": "#344455",
        "accent": "#5b8db8", "accent_hover": "#6a9cc8",
        "exit": "#b87b5b", "exit_hover": "#c88a6a",
        "balance": "#8ac8a8", "warning": "#d4a574",
        "btn_text": "#ffffff",
        "team_a": "#7aa0c8", "team_b": "#c89090", "reserve": "#b8a878",
        "squads": ["#1e2e3e", "#253545", "#1e2e3e", "#2a3a4a"],
        "step_active": "#5b8db8", "step_done": "#6a9c6a", "step_pending": "#253545",
        "step_skipped": "#1a2830", "step_connector": "#2a3a4a",
    },
    "dark_green": {
        "name": "🌲 墨绿",
        "bg": "#1a2b1a", "card": "#1e331e", "card_alt": "#223a22",
        "btn": "#253d25", "btn_hover": "#2d4a2d", "btn_disabled": "#1e2e1e",
        "text": "#d0e6d0", "text_disabled": "#557755", "text_sub": "#88aa88",
        "text_hint": "#668866", "border": "#2a4a2a", "border_header": "#345534",
        "accent": "#7ba87b", "accent_hover": "#8ab88a",
        "exit": "#b87b7b", "exit_hover": "#c88a8a",
        "balance": "#a8c8a8", "warning": "#d4b874",
        "btn_text": "#ffffff",
        "team_a": "#7bb87b", "team_b": "#c8a0a0", "reserve": "#b8b878",
        "squads": ["#1e2e1e", "#253525", "#1e2e1e", "#2a3a2a"],
        "step_active": "#7ba87b", "step_done": "#6a9c6a", "step_pending": "#253d25",
        "step_skipped": "#1a2e1a", "step_connector": "#2a4a2a",
    },
    "dark_red": {
        "name": "🔥 暗红",
        "bg": "#2b1a1a", "card": "#331e1e", "card_alt": "#3a2222",
        "btn": "#3d2525", "btn_hover": "#4a2d2d", "btn_disabled": "#2e1e1e",
        "text": "#e6d0d0", "text_disabled": "#775555", "text_sub": "#aa8888",
        "text_hint": "#886666", "border": "#4a2a2a", "border_header": "#553434",
        "accent": "#b87b7b", "accent_hover": "#c88a8a",
        "exit": "#b87b5b", "exit_hover": "#c88a6a",
        "balance": "#c8a8a8", "warning": "#d4a574",
        "btn_text": "#ffffff",
        "team_a": "#c89090", "team_b": "#d4a0a0", "reserve": "#c8b888",
        "squads": ["#2e1e1e", "#352525", "#2e1e1e", "#3a2a2a"],
        "step_active": "#b87b7b", "step_done": "#8a6a6a", "step_pending": "#3d2525",
        "step_skipped": "#2e1a1a", "step_connector": "#4a2a2a",
    },
    "mono_bw": {
        "name": "⬛ 黑白纯色",
        "bg": "#0a0a0a", "card": "#141414", "card_alt": "#1a1a1a",
        "btn": "#1e1e1e", "btn_hover": "#2a2a2a", "btn_disabled": "#111111",
        "text": "#f0f0f0", "text_disabled": "#555555", "text_sub": "#999999",
        "text_hint": "#666666", "border": "#2a2a2a", "border_header": "#333333",
        "accent": "#ffffff", "accent_hover": "#cccccc",
        "exit": "#888888", "exit_hover": "#aaaaaa",
        "balance": "#cccccc", "warning": "#dddddd",
        "btn_text": "#111111",
        "team_a": "#bbbbbb", "team_b": "#aaaaaa", "reserve": "#999999",
        "squads": ["#111111", "#1a1a1a", "#111111", "#222222"],
        "step_active": "#ffffff", "step_done": "#999999", "step_pending": "#1e1e1e",
        "step_skipped": "#111111", "step_connector": "#2a2a2a",
    },
}

DEFAULT_THEME = "dark_gray"


def build_stylesheet(t):
    """Generate global stylesheet from theme dict."""
    return f"""
QMainWindow {{
    background: {t["bg"]};
}}
QWidget {{
    color: {t["text"]};
    font-family: {FONT_FAMILY};
    font-size: 16px;
}}
QPushButton {{
    background: {t["btn"]};
    color: {t["text"]};
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    min-height: 22px;
    font-size: 16px;
    font-family: {FONT_FAMILY};
}}
QPushButton:hover {{
    background: {t["btn_hover"]};
}}
QPushButton:disabled {{
    background: {t["btn_disabled"]};
    color: {t["text_disabled"]};
}}
QPushButton#primary {{
    background: {t["accent"]};
    color: {t["btn_text"]};
    font-weight: bold;
    font-size: 17px;
}}
QPushButton#primary:hover {{
    background: {t["accent_hover"]};
}}
QPushButton#exit_btn {{
    background: {t["exit"]};
    color: {t["btn_text"]};
    font-weight: bold;
    font-size: 17px;
}}
QPushButton#exit_btn:hover {{
    background: {t["exit_hover"]};
}}
QTableWidget {{
    background: {t["card"]};
    alternate-background-color: {t["card_alt"]};
    border: none;
    border-radius: 8px;
    gridline-color: {t["border"]};
    font-size: 15px;
    font-family: {FONT_FAMILY};
}}
QTableWidget::item {{
    padding: 8px;
}}
QHeaderView::section {{
    background: {t["btn"]};
    color: {t["text"]};
    border: none;
    border-bottom: 2px solid {t["border_header"]};
    padding: 10px;
    font-size: 15px;
    font-weight: bold;
    font-family: {FONT_FAMILY};
}}
QGroupBox {{
    border: 1px solid {t["border"]};
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: bold;
    font-size: 16px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 10px;
}}
QComboBox {{
    background: {t["btn"]};
    border: 1px solid {t["border"]};
    border-radius: 8px;
    padding: 10px;
    min-width: 160px;
    font-size: 15px;
    font-family: {FONT_FAMILY};
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox QAbstractItemView {{
    background: {t["btn"]};
    border: 1px solid {t["border"]};
    selection-background-color: {t["accent"]};
    selection-color: #ffffff;
    font-size: 15px;
}}
QDoubleSpinBox {{
    background: {t["btn"]};
    border: 1px solid {t["border"]};
    border-radius: 8px;
    padding: 10px;
    font-size: 15px;
}}
QLabel#title {{
    font-size: 26px;
    font-weight: bold;
    color: {t["text"]};
}}
QLabel#subtitle {{
    font-size: 16px;
    color: {t["text_sub"]};
}}
QLabel#balance_summary {{
    font-size: 20px;
    font-weight: bold;
    color: {t["balance"]};
    padding: 16px;
    background: {t["card"]};
    border-radius: 10px;
}}
QLabel#warning {{
    color: {t["warning"]};
    font-weight: bold;
    font-size: 15px;
    padding: 8px;
}}
QLabel#hint {{
    color: {t["text_hint"]};
    font-size: 14px;
}}
QFrame#separator {{
    background: {t["border"]};
    max-height: 1px;
}}
"""


def get_theme_squad_colors(theme_id):
    """Get squad color list for the given theme."""
    return THEMES.get(theme_id, THEMES[DEFAULT_THEME])["squads"]
