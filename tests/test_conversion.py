import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import wave
import zipfile

from PIL import Image, features
import pytest

from citrus_drop.converters import (Cancelled, convert_image, convert_media, create_archive, run_process)
from citrus_drop.jobs import run_batch
from citrus_drop.models import available_operations, normalize_files
from citrus_drop.storage import Settings, publish_file, publish_directory


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("target", ["png", "jpg", "bmp", "tiff", "gif", "webp"])
def test_image_formats_preserve_original(image_file, target):
    if target == "webp" and not features.check("webp"):
        pytest.skip("Pillow build has no WebP support")
    original = digest(image_file)
    output = convert_image(image_file, target, threading.Event())
    assert output != image_file and digest(image_file) == original
    with Image.open(output) as image:
        assert image.size == (80, 40)
        if target in {"jpg", "bmp"}:
            assert min(image.convert("RGB").getpixel((0, 0))) > 210
        if target == "png":
            assert image.convert("RGBA").getpixel((0, 0))[3] == 0


def test_output_collision_preserves_existing_file(image_file):
    first = convert_image(image_file, "png", threading.Event())
    before = first.read_bytes()
    second = convert_image(image_file, "png", threading.Event())
    assert first != second and second.stem.endswith("_2")
    assert first.read_bytes() == before


def test_orientation_and_metadata(tmp_path):
    source = tmp_path / "oriented.jpg"
    with Image.new("RGB", (2, 3), "red") as image:
        exif = Image.Exif()
        exif[274] = 6
        exif[315] = "private author"
        image.save(source, exif=exif)
    output = convert_image(source, "png", threading.Event())
    with Image.open(output) as image:
        assert image.size == (3, 2)
        assert not image.getexif()


def test_gif_uses_first_frame(tmp_path):
    source = tmp_path / "animated.gif"
    with Image.new("RGB", (30, 20), "red") as first, Image.new("RGB", (30, 20), "blue") as second:
        first.save(source, save_all=True, append_images=[second], duration=100, loop=0)
    output = convert_image(source, "png", threading.Event())
    with Image.open(output) as image:
        assert image.convert("RGB").getpixel((15, 10)) == (255, 0, 0)


def test_archive_duplicate_names_and_content(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(); b.mkdir()
    first, second = a / "same.txt", b / "same.txt"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")
    result = create_archive([first, second], threading.Event())
    with zipfile.ZipFile(result) as archive:
        assert archive.namelist() == ["same.txt", "same_2.txt"]
        assert archive.read("same.txt") == b"first"
        assert archive.read("same_2.txt") == b"second"
    assert first.read_text() == "first" and second.read_text() == "second"


def test_invalid_image_rolls_back(tmp_path):
    source = tmp_path / "broken.png"
    source.write_bytes(b"not an image")
    with pytest.raises(OSError):
        convert_image(source, "jpg", threading.Event())
    assert sorted(p.name for p in tmp_path.iterdir()) == ["broken.png"]


def test_batch_continues_after_error(tmp_path, image_file):
    source = tmp_path / "broken.png"
    source.write_bytes(b"not an image")
    records = []
    result = run_batch([source, image_file], "png", None, threading.Event(), entry=lambda text, failed: records.append(failed))
    assert (result.succeeded, result.failed, result.cancelled) == (1, 1, False)
    assert records == [True, False]


def test_pre_cancelled_job_creates_nothing(image_file):
    cancel = threading.Event(); cancel.set()
    result = run_batch([image_file], "png", None, cancel)
    assert result.cancelled and result.succeeded == 0
    assert list(image_file.parent.glob("*_converted*")) == []


def test_process_cancel_terminates_child(tmp_path):
    cancel = threading.Event()
    timer = threading.Timer(0.2, cancel.set)
    timer.start()
    start = time.monotonic()
    try:
        with pytest.raises(Cancelled):
            run_process([sys.executable, "-c", "import time; time.sleep(30)"], tmp_path / "errors.log", cancel)
    finally:
        timer.cancel()
    assert time.monotonic() - start < 5


def test_process_error_is_reported(tmp_path):
    with pytest.raises(RuntimeError, match="test error"):
        run_process([sys.executable, "-c", "import sys; sys.stderr.write('test error'); sys.exit(2)"], tmp_path / "errors.log", threading.Event())


def test_menu_capabilities(image_file, tmp_path):
    pdf, video, text = tmp_path / "a.pdf", tmp_path / "a.mp4", tmp_path / "a.txt"
    for path in (pdf, video, text):
        path.touch()
    assert {o.id for o in available_operations([image_file, text], True)} == {"zip", "path"}
    assert {o.id for o in available_operations([pdf])} == {"pdf_png", "pdf_jpg", "pdf_txt", "zip", "path"}
    assert {o.id for o in available_operations([video])} == {"zip", "path"}
    assert "mp4" in {o.id for o in available_operations([video], True)}
    assert "pdf" in {o.id for o in available_operations([image_file])}
    assert normalize_files([image_file, image_file, tmp_path, tmp_path / "missing"]) == [image_file]


def test_publish_collision_with_directory(tmp_path):
    (tmp_path / "out.txt").mkdir()
    temporary = tmp_path / "temporary"
    temporary.write_text("new")
    output = publish_file(temporary, tmp_path, "out", "txt")
    assert output.name == "out_2.txt" and (tmp_path / "out.txt").is_dir()


def test_publish_pages_preserves_existing_empty_folder(tmp_path):
    (tmp_path / "pages").mkdir()
    prepared = tmp_path / "prepared"; prepared.mkdir()
    (prepared / "page-1.png").write_bytes(b"new")
    output = publish_directory(prepared, tmp_path, "pages")
    assert output.name == "pages_2"
    assert list((tmp_path / "pages").iterdir()) == []
    assert (output / "page-1.png").read_bytes() == b"new"


def test_settings_migrate_and_save(tmp_path):
    executable = tmp_path / "ffmpeg.exe"; executable.touch()
    (tmp_path / "ffmpeg-path.txt").write_text(str(executable), encoding="utf-8")
    settings = Settings(tmp_path)
    assert settings.ffmpeg() == executable
    settings.save_ffmpeg(executable)
    assert Settings(tmp_path).ffmpeg() == executable
    assert list(tmp_path.glob("settings-*.tmp")) == []


def test_media_conversion_with_real_ffmpeg(tmp_path):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("FFmpeg optional engine not installed")
    source = tmp_path / "한글 공백 & $ 오디오.wav"
    with wave.open(str(source), "wb") as audio:
        audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 800)
    before = digest(source)
    result = convert_media(source, "flac", Path(ffmpeg), threading.Event())
    assert result.read_bytes().startswith(b"fLaC")
    assert digest(source) == before
