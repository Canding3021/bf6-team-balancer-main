"""
BF6 Team Balancer - 程序入口。

运行: python main.py
"""

import sys

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

from bf6balancer.core.crash_log import install_excepthook, install_faulthandler, get_log_dir
from bf6balancer.ui.main_window import MainWindow


def main():
    # High DPI adaptation
    # Windows DPI awareness: let the process handle scaling itself to avoid blurry upscaling
    if sys.platform == "win32":
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Per-Monitor DPI Aware
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    # Qt high DPI scaling: auto-scale all widgets, fonts, and spacing
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Crash logging: windowed builds (console=False) swallow uncaught errors silently.
    # Install global hooks so a crash leaves a log + tells the user where it is.
    install_faulthandler()

    app = QApplication(sys.argv)

    def _on_crash(exc_type, exc_value, tb_text):
        try:
            QMessageBox.critical(
                None, "程序遇到错误",
                f"发生未预期的错误，程序可能需要关闭。\n\n"
                f"错误信息: {exc_type.__name__}: {exc_value}\n\n"
                f"详细日志已保存到:\n{get_log_dir()}\n\n"
                f"反馈问题时请附上 crash.log 文件。"
            )
        except Exception:
            pass

    install_excepthook(on_crash=_on_crash)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
