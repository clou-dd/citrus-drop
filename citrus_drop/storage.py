"""결과 파일 보호, 임시 폴더, 사용자 설정."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


def app_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def config_directory() -> Path:
    base = os.environ.get("LOCALAPPDATA") if sys.platform == "win32" else os.environ.get("XDG_CONFIG_HOME")
    return (Path(base) if base else Path.home() / ".config") / "CitrusDrop"


@contextmanager
def temporary_output(folder: Path):
    """원본과 같은 볼륨에 작업 공간을 만들고, 완료·실패·취소 후 정리합니다."""
    temporary = Path(tempfile.mkdtemp(prefix=".citrus-drop-", dir=folder))
    try:
        yield temporary
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def _move_file_exclusive(source: Path, destination: Path):
    if os.name == "nt":
        # Windows rename은 기존 대상을 덮어쓰지 않습니다.
        os.rename(source, destination)
    else:
        # POSIX rename은 덮어쓸 수 있으므로 같은 볼륨의 원자적 hard link를 사용합니다.
        os.link(source, destination)
        source.unlink()


def publish_file(source: Path, folder: Path, stem: str, suffix: str) -> Path:
    for index in range(1, 10000):
        number = "" if index == 1 else f"_{index}"
        destination = folder / f"{stem}{number}.{suffix}"
        try:
            _move_file_exclusive(source, destination)
            return destination
        except FileExistsError:
            continue
        except PermissionError:
            if destination.exists():
                continue
            raise
    raise OSError("출력 파일 이름이 너무 많이 중복됩니다.")


def publish_directory(prepared: Path, folder: Path, stem: str) -> Path:
    """새 결과 폴더를 배타적으로 확보한 뒤 준비된 페이지 파일을 옮깁니다."""
    for index in range(1, 10000):
        destination = folder / (stem if index == 1 else f"{stem}_{index}")
        try:
            destination.mkdir()
        except FileExistsError:
            continue
        moved = []
        try:
            for source in prepared.iterdir():
                if not source.is_file():
                    raise OSError("예상하지 못한 PDF 결과 폴더 구조입니다.")
                output = destination / source.name
                _move_file_exclusive(source, output)
                moved.append(output)
            return destination
        except BaseException:
            # 이 작업이 만든 파일만 정리합니다. 다른 프로세스가 넣은 파일은 지우지 않습니다.
            for output in moved:
                output.unlink(missing_ok=True)
            try:
                destination.rmdir()
            except OSError:
                pass
            raise
    raise OSError("출력 폴더 이름이 너무 많이 중복됩니다.")


class Settings:
    def __init__(self, directory: Path | None = None):
        self.directory = directory or config_directory()
        self.path = self.directory / "settings.json"
        self.data = {}
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.data = loaded
        except (OSError, ValueError):
            pass
        # 기존 C# 버전에서 선택했던 FFmpeg 경로를 이어서 사용합니다.
        if not self.data.get("ffmpeg"):
            try:
                self.data["ffmpeg"] = (self.directory / "ffmpeg-path.txt").read_text(encoding="utf-8-sig").strip()
            except OSError:
                pass

    def ffmpeg(self) -> Path | None:
        configured = self.data.get("ffmpeg")
        if isinstance(configured, str) and configured and Path(configured).is_file():
            return Path(configured).resolve()
        bundled = app_directory() / "tools" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        return bundled if bundled.is_file() else None

    def save_ffmpeg(self, executable: Path):
        executable = executable.resolve()
        if not executable.is_file():
            raise FileNotFoundError("FFmpeg 실행 파일을 찾을 수 없습니다.")
        self.directory.mkdir(parents=True, exist_ok=True)
        data = dict(self.data, ffmpeg=str(executable))
        handle, temporary = tempfile.mkstemp(prefix="settings-", suffix=".tmp", dir=self.directory)
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
            os.replace(temporary, self.path)
            self.data = data
        finally:
            Path(temporary).unlink(missing_ok=True)
