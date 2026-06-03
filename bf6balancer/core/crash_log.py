"""
BF6 Team Balancer - 崩溃日志模块

为打包后的 windowed 应用（console=False）提供崩溃追踪能力。
windowed 模式下未捕获异常会让窗口直接消失、无任何提示，本模块解决这一黑洞。

三层防护:
1. install_excepthook() - 捕获主线程/Qt 槽函数里的 Python 异常
2. install_faulthandler() - 捕获 Qt C++ 层的硬崩溃（段错误等 Python 抓不到的）
3. log_exception() - 供后台线程（QThread）手动调用，记录线程内异常

日志位置: %USERPROFILE%/Documents/BF6TeamBalancer/logs/ （与 history/config 同目录，用户好找）
"""

import os
import sys
import traceback
from datetime import datetime

LOG_DIR = os.path.join(
    os.path.expanduser("~"), "Documents", "BF6TeamBalancer", "logs"
)
CRASH_LOG = os.path.join(LOG_DIR, "crash.log")
FAULT_LOG = os.path.join(LOG_DIR, "fault.log")

# 保留 faulthandler 的文件句柄，避免被 GC 关闭
_fault_file = None


def get_log_dir() -> str:
    return LOG_DIR


def _ensure_dir() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)


def _write(header: str, body: str) -> None:
    """追加一条带时间戳与版本信息的日志。写盘本身失败时静默（不能在崩溃处理里再崩）。"""
    try:
        _ensure_dir()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(CRASH_LOG, "a", encoding="utf-8") as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"[{ts}] {header}\n")
            f.write(f"Python: {sys.version.split()[0]} | Platform: {sys.platform}\n")
            f.write(f"{'-' * 60}\n")
            f.write(body)
            if not body.endswith("\n"):
                f.write("\n")
    except OSError:
        pass


def log_exception(exc_type, exc_value, exc_tb, context: str = "") -> str:
    """
    格式化并写入一个异常。返回写入的日志正文（便于 UI 展示或测试断言）。

    context: 额外说明（如 "API query thread"），标明异常来源。
    """
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    header = f"UNCAUGHT EXCEPTION{f' [{context}]' if context else ''}"
    _write(header, tb_text)
    return tb_text


def install_excepthook(on_crash=None) -> None:
    """
    安装全局 sys.excepthook，捕获主线程（含 Qt 槽函数）里所有未捕获异常。

    on_crash: 可选回调 (exc_type, exc_value, tb_text)，用于弹窗提示用户。
              回调自身异常会被吞掉，保证不会二次崩溃。
    """
    previous = sys.excepthook

    def hook(exc_type, exc_value, exc_tb):
        # KeyboardInterrupt 走默认行为，不当作崩溃记录
        if issubclass(exc_type, KeyboardInterrupt):
            previous(exc_type, exc_value, exc_tb)
            return
        tb_text = log_exception(exc_type, exc_value, exc_tb, context="main thread")
        if on_crash is not None:
            try:
                on_crash(exc_type, exc_value, tb_text)
            except Exception:
                pass
        # 仍调用原 hook（开发时控制台可见）
        previous(exc_type, exc_value, exc_tb)

    sys.excepthook = hook


def install_faulthandler() -> None:
    """
    启用 faulthandler，把 Qt C++ 层的致命信号（段错误等）dump 到 fault.log。
    这类崩溃 Python 的 excepthook 抓不到，DPI/渲染相关崩溃常在此层。
    """
    global _fault_file
    try:
        import faulthandler
        _ensure_dir()
        _fault_file = open(FAULT_LOG, "a", encoding="utf-8")
        _fault_file.write(
            f"\n=== session start {datetime.now():%Y-%m-%d %H:%M:%S} ===\n"
        )
        _fault_file.flush()
        faulthandler.enable(file=_fault_file, all_threads=True)
    except (OSError, RuntimeError, ImportError):
        # faulthandler 在某些受限环境下可能不可用，失败不影响主程序
        pass
