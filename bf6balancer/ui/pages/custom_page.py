"""BF6 Team Balancer - Custom squad binding page."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QStackedWidget, QComboBox, QHeaderView,
    QMessageBox, QFrame, QGridLayout, QSizePolicy, QAbstractItemView, QProgressBar,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor


class CustomPageMixin:
    def _build_page_custom(self):
        """Build the custom squad binding page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        title = QLabel("自定义小队（可选）")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("绑定的两人将被分配到同一阵营的同一个小队。每人最多被选一次。")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # Add button
        btn_add = QPushButton("+ 添加绑定")
        btn_add.setFixedWidth(120)
        btn_add.clicked.connect(self._add_binding_row)
        layout.addWidget(btn_add)

        # Binding list area
        self.binding_container = QWidget()
        self.binding_layout = QVBoxLayout(self.binding_container)
        self.binding_layout.setSpacing(8)
        layout.addWidget(self.binding_container, stretch=1)

        # Hint
        hint = QLabel("如果不设绑定，直接点「查看结果」即可")
        hint.setObjectName("hint")
        layout.addWidget(hint)

        return page

    def _add_binding_row(self):
        if self.players is None:
            return

        row_widget = QFrame()
        row_widget.setStyleSheet("QFrame { background: #3d3d50; border-radius: 8px; padding: 10px; }")
        row_layout = QHBoxLayout(row_widget)

        cb1 = QComboBox()
        cb2 = QComboBox()
        names = [p.name for p in self.players]
        cb1.addItems(["-- 选择玩家 --"] + names)
        cb2.addItems(["-- 选择玩家 --"] + names)
        cb1.setMinimumWidth(200)
        cb2.setMinimumWidth(200)

        btn_remove = QPushButton("X")
        btn_remove.setFixedSize(30, 30)

        row_layout.addWidget(QLabel("玩家A:"))
        row_layout.addWidget(cb1, stretch=1)
        row_layout.addWidget(QLabel("+"))
        row_layout.addWidget(QLabel("玩家B:"))
        row_layout.addWidget(cb2, stretch=1)
        row_layout.addWidget(btn_remove)

        row_data = {"widget": row_widget, "cb1": cb1, "cb2": cb2}
        self.binding_rows = getattr(self, "binding_rows", [])
        self.binding_rows.append(row_data)
        self.binding_layout.addWidget(row_widget)

        btn_remove.clicked.connect(lambda: self._remove_binding_row(row_data))

    def _remove_binding_row(self, row_data):
        self.binding_rows.remove(row_data)
        row_data["widget"].deleteLater()

    def _refresh_binding_combos(self):
        names = [p.name for p in self.players]
        for row in getattr(self, "binding_rows", []):
            row["cb1"].clear()
            row["cb2"].clear()
            row["cb1"].addItems(["-- 选择玩家 --"] + names)
            row["cb2"].addItems(["-- 选择玩家 --"] + names)

