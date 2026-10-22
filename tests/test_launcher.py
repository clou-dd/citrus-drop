import sys
from types import SimpleNamespace

import main as launcher


def test_missing_gui_dependency_writes_error_without_console(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "config_directory", lambda: tmp_path)
    monkeypatch.setitem(sys.modules, "citrus_drop.app", None)
    monkeypatch.setattr(sys, "stderr", None)
    monkeypatch.setattr(sys, "argv", ["CitrusDrop.exe", "--smoke-test"])
    assert launcher.main() == 1
    assert "ModuleNotFoundError" in (tmp_path / "startup-error.log").read_text(encoding="utf-8")


def test_launcher_preserves_app_exit_code(monkeypatch):
    monkeypatch.setitem(sys.modules, "citrus_drop.app", SimpleNamespace(main=lambda: 7))
    assert launcher.main() == 7


def test_error_still_reaches_console_if_log_cannot_be_saved(monkeypatch, tmp_path, capsys):
    blocked = tmp_path / "blocked"
    blocked.write_text("file instead of directory")
    monkeypatch.setattr(launcher, "config_directory", lambda: blocked)
    launcher.report_startup_error("test startup error")
    assert "test startup error" in capsys.readouterr().err
