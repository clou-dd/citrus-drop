"""지원 형식과 메뉴 규칙. 화면 코드와 독립적으로 사용할 수 있습니다."""
from dataclasses import dataclass
from pathlib import Path
import os

from PIL import features


@dataclass(frozen=True)
class Operation:
    id: str
    label: str
    description: str


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".gif", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".wmv", ".m4v"}
AUDIO_SUFFIXES = {".mp3", ".m4a", ".wav", ".flac", ".ogg", ".opus", ".aiff", ".aif", ".wma"}


def file_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    if suffix in AUDIO_SUFFIXES:
        return "audio"
    return "pdf" if suffix == ".pdf" else "other"


def normalize_files(paths) -> list[Path]:
    """로컬 일반 파일만 선택 순서대로 반환합니다. 폴더는 제외합니다."""
    result, seen = [], set()
    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        key = os.path.normcase(str(path))
        if path.is_file() and key not in seen:
            result.append(path)
            seen.add(key)
    return result


def available_operations(files: list[Path], has_ffmpeg: bool = False) -> list[Operation]:
    if not files:
        return []
    kinds = {file_kind(path) for path in files}
    operations = []
    webp_supported = features.check("webp")
    if kinds == {"image"} and (webp_supported or all(p.suffix.lower() != ".webp" for p in files)):
        operations.extend([
            Operation("png", "PNG", "투명 배경 유지"),
            Operation("jpg", "JPG", "품질 90 · 흰 배경"),
            Operation("bmp", "BMP", "흰 배경"),
            Operation("tiff", "TIFF", "정지 이미지"),
            Operation("gif", "GIF", "첫 프레임 · 색상 축소"),
        ])
        if webp_supported:
            operations.append(Operation("webp", "WebP", "품질 90"))
        operations.append(Operation("pdf", "PDF 만들기", "목록 순서대로 하나의 PDF"))
    elif kinds == {"pdf"}:
        operations.extend([
            Operation("pdf_png", "PNG", "PDF 모든 페이지 · 150 DPI"),
            Operation("pdf_jpg", "JPG", "PDF 모든 페이지 · 150 DPI"),
            Operation("pdf_txt", "TXT", "텍스트 추출 · OCR 제외"),
        ])
    elif has_ffmpeg and (kinds == {"video"} or kinds == {"audio"}):
        if kinds == {"video"}:
            operations.extend([
                Operation("mp4", "MP4", "H.264 / AAC"),
                Operation("webm", "WebM", "VP9 / Opus"),
            ])
        operations.extend([
            Operation("mp3", "MP3", "오디오 변환 / 추출"),
            Operation("wav", "WAV", "PCM 오디오"),
            Operation("flac", "FLAC", "무손실 오디오"),
            Operation("ogg", "OGG", "Vorbis 오디오"),
        ])
    operations.extend([
        Operation("zip", "ZIP", "선택 파일을 하나로 압축"),
        Operation("path", "경로 복사", "파일 전체 경로 복사"),
    ])
    return operations
