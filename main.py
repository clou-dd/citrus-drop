"""콘솔 또는 창 없는 실행에서도 시작 오류를 확인할 수 있는 진입점."""
from datetime import datetime
import sys
import traceback

from citrus_drop.storage import config_directory


def report_startup_error(details: str):
    message = "Citrus Drop could not start."
    try:
        log_path = config_directory() / "startup-error.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(f"{datetime.now().isoformat()}\n{details}", encoding="utf-8")
        message += f"\n\nError log: {log_path}"
    except OSError:
        message += f"\n\n{details}"
    if sys.stderr is not None:
        sys.stderr.write(details)
    elif sys.platform == "win32" and "--smoke-test" not in sys.argv:
        # Qt 자체를 불러오지 못한 경우에도 pythonw/EXE에서 오류를 알립니다.
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, "Citrus Drop", 0x10)


def main() -> int:
    try:
        from citrus_drop.app import main as run_app
        return run_app()
    except Exception:
        report_startup_error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
