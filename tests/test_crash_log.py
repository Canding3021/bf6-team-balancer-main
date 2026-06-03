"""
崩溃日志模块单测 - 不触碰真实 Documents 目录。
Run: python -m pytest test_crash_log.py -v
"""

import os
import sys
import pytest
from bf6balancer.core import crash_log


@pytest.fixture
def tmp_logs(tmp_path, monkeypatch):
    """把日志目录重定向到临时目录。"""
    log_dir = tmp_path / "logs"
    monkeypatch.setattr(crash_log, "LOG_DIR", str(log_dir))
    monkeypatch.setattr(crash_log, "CRASH_LOG", str(log_dir / "crash.log"))
    monkeypatch.setattr(crash_log, "FAULT_LOG", str(log_dir / "fault.log"))
    return log_dir


def _raise_and_capture():
    """制造一个真实的 traceback 三元组。"""
    try:
        raise ValueError("boom-test-marker")
    except ValueError:
        return sys.exc_info()


class TestLogException:
    def test_writes_traceback_to_file(self, tmp_logs):
        body = crash_log.log_exception(*_raise_and_capture(), context="unit")

        log_file = tmp_logs / "crash.log"
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "boom-test-marker" in content
        assert "ValueError" in content
        assert "[unit]" in content
        # 返回值即写入正文
        assert "boom-test-marker" in body

    def test_appends_not_overwrites(self, tmp_logs):
        crash_log.log_exception(*_raise_and_capture(), context="first")
        crash_log.log_exception(*_raise_and_capture(), context="second")

        content = (tmp_logs / "crash.log").read_text(encoding="utf-8")
        assert "[first]" in content
        assert "[second]" in content

    def test_write_failure_is_silent(self, monkeypatch):
        """日志目录无法创建时不应抛异常（崩溃处理里不能再崩）。"""
        def boom(*a, **k):
            raise OSError("disk full")
        monkeypatch.setattr(crash_log.os, "makedirs", boom)
        # 不抛异常即通过
        crash_log.log_exception(*_raise_and_capture())


class TestExcepthook:
    def test_hook_logs_and_calls_callback(self, tmp_logs, monkeypatch):
        original = sys.excepthook
        captured = {}

        def on_crash(exc_type, exc_value, tb_text):
            captured["type"] = exc_type
            captured["text"] = tb_text

        try:
            crash_log.install_excepthook(on_crash=on_crash)
            sys.excepthook(*_raise_and_capture())
        finally:
            sys.excepthook = original

        assert captured["type"] is ValueError
        assert "boom-test-marker" in captured["text"]
        assert (tmp_logs / "crash.log").exists()

    def test_callback_exception_is_swallowed(self, tmp_logs):
        original = sys.excepthook

        def bad_callback(*a):
            raise RuntimeError("callback blew up")

        try:
            crash_log.install_excepthook(on_crash=bad_callback)
            # 回调自身崩溃不应向外传播
            sys.excepthook(*_raise_and_capture())
        finally:
            sys.excepthook = original

    def test_keyboard_interrupt_not_logged(self, tmp_logs):
        original = sys.excepthook
        try:
            crash_log.install_excepthook()
            try:
                raise KeyboardInterrupt()
            except KeyboardInterrupt:
                sys.excepthook(*sys.exc_info())
        finally:
            sys.excepthook = original
        # KeyboardInterrupt 不写崩溃日志
        assert not (tmp_logs / "crash.log").exists()
