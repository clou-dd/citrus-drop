from concurrent.futures import ThreadPoolExecutor
import threading

from PIL import Image
from pypdf import PdfReader
import pytest
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

from citrus_drop.converters import Cancelled
from citrus_drop.pdf_tools import images_to_pdf, convert_pdf


def test_image_pdf_page_order_orientation_and_render(tmp_path, image_file):
    portrait = tmp_path / "portrait.png"
    with Image.new("RGB", (40, 80), "blue") as image:
        image.save(portrait)
    output = images_to_pdf([image_file, portrait], threading.Event())
    reader = PdfReader(output)
    assert len(reader.pages) == 2
    assert reader.pages[0].mediabox.width > reader.pages[0].mediabox.height
    assert reader.pages[1].mediabox.width < reader.pages[1].mediabox.height
    pages = convert_pdf(output, "pdf_png", threading.Event())
    assert sorted(p.name for p in pages.iterdir()) == ["page-1.png", "page-2.png"]
    with Image.open(pages / "page-1.png") as first, Image.open(pages / "page-2.png") as second:
        assert first.width > first.height and second.width < second.height
        red = first.convert("RGB").getpixel((first.width // 2, first.height // 2))
        blue = second.convert("RGB").getpixel((second.width // 2, second.height // 2))
        assert red[0] > 200 and red[2] < 50
        assert blue[2] > 230 and blue[0] < 20
        assert abs(first.info["dpi"][0] - 150) < 0.1


def test_pdf_jpg_and_output_collision(image_file):
    source = images_to_pdf([image_file], threading.Event())
    original = source.read_bytes()
    first = convert_pdf(source, "pdf_jpg", threading.Event())
    second = convert_pdf(source, "pdf_jpg", threading.Event())
    assert first != second and len(list(first.glob("*.jpg"))) == 1
    assert source.read_bytes() == original
    with Image.open(first / "page-1.jpg") as image:
        image.verify()


def test_pdf_text_and_image_only_pdf(tmp_path, image_file):
    text_pdf = tmp_path / "text.pdf"
    canvas = Canvas(str(text_pdf)); canvas.drawString(40, 750, "Citrus PDF text fixture"); canvas.save()
    text = convert_pdf(text_pdf, "pdf_txt", threading.Event())
    assert "Citrus PDF text fixture" in text.read_text(encoding="utf-8")
    scan = images_to_pdf([image_file], threading.Event())
    no_text = convert_pdf(scan, "pdf_txt", threading.Event())
    assert no_text.read_text(encoding="utf-8") == ""


def test_korean_pdf_text(tmp_path):
    pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
    source = tmp_path / "한글.pdf"
    canvas = Canvas(str(source)); canvas.setFont("HYSMyeongJo-Medium", 14)
    canvas.drawString(40, 750, "시트러스 PDF 한글 추출"); canvas.save()
    output = convert_pdf(source, "pdf_txt", threading.Event())
    assert "시트러스 PDF 한글 추출" in output.read_text(encoding="utf-8")


@pytest.mark.parametrize("encrypted", [False, True])
def test_invalid_or_encrypted_pdf_rolls_back(tmp_path, encrypted):
    source = tmp_path / "blocked.pdf"
    if encrypted:
        canvas = Canvas(str(source), encrypt=StandardEncryption("secret"))
        canvas.drawString(40, 750, "encrypted"); canvas.save()
    else:
        source.write_bytes(b"not a PDF")
    original = source.read_bytes()
    with pytest.raises(ValueError, match="PDF"):
        convert_pdf(source, "pdf_png", threading.Event())
    assert list(tmp_path.iterdir()) == [source]
    assert source.read_bytes() == original


def test_cancel_during_image_pdf(image_file):
    cancel = threading.Event()
    with pytest.raises(Cancelled):
        images_to_pdf([image_file, image_file], cancel, lambda index, count: cancel.set())
    assert list(image_file.parent.glob("*.pdf")) == []
    assert list(image_file.parent.glob(".citrus-drop-*")) == []


def test_cancel_during_pdf_render_rolls_back(image_file):
    pdf = images_to_pdf([image_file, image_file], threading.Event())
    cancel = threading.Event()
    def progress(index, total):
        if index == 2:
            cancel.set()
    with pytest.raises(Cancelled):
        convert_pdf(pdf, "pdf_png", cancel, progress)
    assert list(pdf.parent.glob("*_pages*")) == []
    assert list(pdf.parent.glob(".citrus-drop-*")) == []


def test_pdf_operations_are_serialized_between_threads(image_file):
    source = images_to_pdf([image_file], threading.Event())
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(convert_pdf, source, "pdf_png", threading.Event()) for _ in range(2)]
        outputs = [future.result() for future in futures]
    assert outputs[0] != outputs[1]
    assert all((output / "page-1.png").is_file() for output in outputs)
