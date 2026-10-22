"""이미지·FFmpeg·ZIP 처리. Qt 없이도 실행하고 테스트할 수 있습니다."""
from datetime import datetime
from pathlib import Path
import subprocess
import threading
import zipfile

from PIL import Image, ImageOps

from .storage import temporary_output, publish_file

MAX_PIXELS = 100_000_000


class Cancelled(Exception):
    """사용자가 취소한 작업입니다."""


def check_cancel(cancel: threading.Event):
    if cancel.is_set():
        raise Cancelled("작업을 취소했습니다.")


def load_image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        if source.width * source.height > MAX_PIXELS:
            raise ValueError("1억 픽셀을 넘는 이미지는 처리하지 않습니다.")
        source.seek(0)
        upright = ImageOps.exif_transpose(source)
        try:
            result = upright.convert("RGBA")
            result.info.clear()
            return result
        finally:
            if upright is not source:
                upright.close()


def on_white(image: Image.Image) -> Image.Image:
    background = Image.new("RGB", image.size, "white")
    background.paste(image, mask=image.getchannel("A"))
    return background


def convert_image(input_path: Path, target: str, cancel: threading.Event) -> Path:
    formats = {"png": "PNG", "jpg": "JPEG", "bmp": "BMP", "tiff": "TIFF", "gif": "GIF", "webp": "WEBP"}
    if target not in formats:
        raise ValueError("지원하지 않는 이미지 출력 형식입니다.")
    check_cancel(cancel)
    with temporary_output(input_path.parent) as temporary:
        output = temporary / f"output.{target}"
        with load_image(input_path) as source:
            check_cancel(cancel)
            image = on_white(source) if target in {"jpg", "bmp"} else source
            try:
                options = {"exif": b"", "icc_profile": None}
                if target in {"jpg", "webp"}:
                    options["quality"] = 90
                if target == "tiff":
                    options["compression"] = "tiff_deflate"
                image.save(output, formats[target], **options)
            finally:
                if image is not source:
                    image.close()
        check_cancel(cancel)
        return publish_file(output, input_path.parent, input_path.stem + "_converted", target)


MEDIA_ARGUMENTS = {
    "mp4": ["-map", "0:v:0", "-map", "0:a:0?", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-crf", "22", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart"],
    "webm": ["-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0", "-c:a", "libopus"],
    "mp3": ["-vn", "-map", "0:a:0", "-c:a", "libmp3lame", "-q:a", "2"],
    "wav": ["-vn", "-map", "0:a:0", "-c:a", "pcm_s16le"],
    "flac": ["-vn", "-map", "0:a:0", "-c:a", "flac"],
    "ogg": ["-vn", "-map", "0:a:0", "-c:a", "libvorbis", "-q:a", "5"],
}


def run_process(arguments: list[str], log_path: Path, cancel: threading.Event):
    """셸을 거치지 않습니다. 오류 출력은 파일로 받아 PIPE 교착을 방지합니다."""
    check_cancel(cancel)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    with log_path.open("wb") as errors:
        process = subprocess.Popen(arguments, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=errors, shell=False, creationflags=flags)
        try:
            while True:
                check_cancel(cancel)
                try:
                    result = process.wait(timeout=0.1)
                    break
                except subprocess.TimeoutExpired:
                    continue
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    check_cancel(cancel)
    if result:
        with log_path.open("rb") as stream:
            stream.seek(max(0, log_path.stat().st_size - 12000))
            detail = stream.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"FFmpeg 변환 실패 ({result}): {detail}")


def convert_media(input_path: Path, target: str, ffmpeg: Path | None, cancel: threading.Event) -> Path:
    if ffmpeg is None or not ffmpeg.is_file():
        raise FileNotFoundError("설정에서 FFmpeg 실행 파일을 선택해 주세요.")
    if target not in MEDIA_ARGUMENTS:
        raise ValueError("지원하지 않는 영상·음성 형식입니다.")
    check_cancel(cancel)
    with temporary_output(input_path.parent) as temporary:
        output = temporary / f"output.{target}"
        arguments = [str(ffmpeg), "-nostdin", "-hide_banner", "-loglevel", "error", "-n", "-i", str(input_path)]
        run_process(arguments + MEDIA_ARGUMENTS[target] + [str(output)], temporary / "errors.log", cancel)
        if not output.is_file() or output.stat().st_size == 0:
            raise OSError("변환 결과 파일이 비어 있습니다.")
        check_cancel(cancel)
        return publish_file(output, input_path.parent, input_path.stem + "_converted", target)


def create_archive(files: list[Path], cancel: threading.Event) -> Path:
    if not files:
        raise ValueError("압축할 파일이 없습니다.")
    check_cancel(cancel)
    with temporary_output(files[0].parent) as temporary:
        output = temporary / "output.zip"
        names = set()
        with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in files:
                check_cancel(cancel)
                name, index = path.name, 2
                while name.casefold() in names:
                    name = f"{path.stem}_{index}{path.suffix}"
                    index += 1
                names.add(name.casefold())
                with path.open("rb") as source, archive.open(name, "w", force_zip64=True) as destination:
                    while chunk := source.read(65536):
                        check_cancel(cancel)
                        destination.write(chunk)
        check_cancel(cancel)
        return publish_file(output, files[0].parent, "Citrus_" + datetime.now().strftime("%Y%m%d_%H%M%S"), "zip")
