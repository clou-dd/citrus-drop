"""설치·빌드 시 공식 Pretendard 원본을 고정된 버전과 SHA-256으로 준비합니다."""
import hashlib
import os
from pathlib import Path
import tempfile
from urllib.request import urlopen

REVISION = "5c41199ea0024a9e0b2cb31735265056e5472d76"  # Pretendard v1.3.9
BASE_URL = (f"https://raw.githubusercontent.com/orioncactus/pretendard/{REVISION}/"
            "packages/pretendard/dist/public/static/")
FONT_HASHES = {
    "Pretendard-Regular.otf": "3ffbacde6ab8411f1d2db54bb9b1f0b3ee2a738932033722cf0388c06aed1c93",
    "Pretendard-SemiBold.otf": "c89bc43027dc7cde5726e96223376f8eec09302b2fc1f8147fd5b57cfc376118",
    "Pretendard-Bold.otf": "2e91915fab54df71cc9598ebf608b2bdb54c6fe3c066ac61dff0bc44fca71cc7",
}


def fetch_fonts():
    folder = Path(__file__).resolve().parents[1] / "assets" / "fonts"
    folder.mkdir(parents=True, exist_ok=True)
    for name, expected_hash in FONT_HASHES.items():
        target = folder / name
        if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == expected_hash:
            continue
        with urlopen(BASE_URL + name, timeout=30) as response:
            content = response.read(3 * 1024 * 1024 + 1)
        if hashlib.sha256(content).hexdigest() != expected_hash:
            raise ValueError(f"{name} download did not match the expected SHA-256")
        descriptor, temporary = tempfile.mkstemp(prefix="font-", suffix=".tmp", dir=folder)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)
    print("Original Pretendard v1.3.9 Regular/SemiBold/Bold are ready (SHA-256 verified).")


if __name__ == "__main__":
    fetch_fonts()
