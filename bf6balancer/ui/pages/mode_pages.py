"""BF6 Team Balancer - Alloc-mode and game-mode selection pages."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QStackedWidget, QComboBox, QHeaderView,
    QMessageBox, QFrame, QGridLayout, QSizePolicy, QAbstractItemView, QProgressBar,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor
from ..widgets import ModeCard


class ModePagesMixin:
    def _build_page_alloc_mode(self):
        """Build the allocation mode selection page (balanced vs random)."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        title = QLabel("选择分配方式")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("均衡模式按实力分配，随机模式纯随机打乱")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        self.card_balanced = ModeCard(
            "⚖️ 均衡分配",
            "根据 KD / KPM 加权得分\n贪心算法平衡双方实力\n适合正式内战",
            "balanced"
        )
        self.card_random = ModeCard(
            "🎲 随机分配",
            "完全随机打乱玩家\n不考虑实力数据\n适合娱乐局 / 测试",
            "random"
        )
        self.card_balanced.setChecked(True)

        self.card_balanced.clicked.connect(lambda: self._select_alloc_mode("balanced"))
        self.card_random.clicked.connect(lambda: self._select_alloc_mode("random"))

        cards_layout.addWidget(self.card_balanced)
        cards_layout.addWidget(self.card_random)
        layout.addLayout(cards_layout, stretch=1)

        return page

    def _select_alloc_mode(self, mode):
        self.alloc_mode = mode
        self.card_balanced.setChecked(mode == "balanced")
        self.card_random.setChecked(mode == "random")

    def _build_page_mode(self):
        """Build the game mode selection page (conquest vs breakthrough)."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        title = QLabel("选择游戏模式")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("不同模式会影响 KD 和 KPM 的权重分配")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # Mode cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        self.card_conquest = ModeCard(
            "征服 Conquest",
            "更看重 KD（生存能力）\n权重: KD 70% / KPM 30%\n最多 64 人 (16 队)",
            0
        )
        self.card_breakthrough = ModeCard(
            "突破 Breakthrough",
            "更看重 KPM（击杀效率）\n权重: KPM 70% / KD 30%\n最多 48 人 (12 队)",
            1
        )
        self.card_conquest.setChecked(True)

        self.card_conquest.clicked.connect(lambda: self._select_mode(0))
        self.card_breakthrough.clicked.connect(lambda: self._select_mode(1))

        cards_layout.addWidget(self.card_conquest)
        cards_layout.addWidget(self.card_breakthrough)
        layout.addLayout(cards_layout, stretch=1)

        return page

    def _select_mode(self, mode_id):
        self.card_conquest.setChecked(mode_id == 0)
        self.card_breakthrough.setChecked(mode_id == 1)

