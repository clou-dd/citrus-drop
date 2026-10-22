"""PDF 생성·페이지 이미지화·문자 추출. 별도 Poppler 설치가 필요하지 않습니다."""
from contextlib import closing
from datetime import datetime
from pathlib import Path
import threading

from PIL import Image
import pypdfium2 as pdfium
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from .converters import MAX_PIXELS, check_cancel, load_image, on_white
from .storage import temporary_output, publish_file, publish_directory

# PDFium은 서로 다른 문서여도 동시 호출하면 안 됩니다.
_pdf_lock = threading.RLock()


def images_to_pdf(files: list[Path], cancel: threading.Event, progress=None) -> Path:
    if not files:
        raise ValueError("PDF에 넣을 이미지가 없습니다.")
    check_cancel(cancel)
    with temporary_output(files[0].parent) as temporary:
        output = temporary / "output.pdf"
        document = Canvas(str(output), pagesize=A4, pageCompression=1)
        document.setTitle("Citrus Drop image PDF")
        for index, path in enumerate(files):
            check_cancel(cancel)
            if progress:
                progress(index + 1, len(files))
            with load_image(path) as source, on_white(source) as image:
                page_width, page_height = landscape(A4) if image.width > image.height else A4
                document.setPageSize((page_width, page_height))
                scale = min((page_width - 48) / image.width, (page_height - 48) / image.height)
                width, height = image.width * scale, image.height * scale
                # Pillow 이미지를 ReportLab에 전달하여 이미지 데이터를 무손실로 삽입합니다.
                document.drawImage(ImageReader(image), (page_width - width) / 2, (page_height - height) / 2,
                                   width, height, preserveAspectRatio=True)
                document.showPage()
        check_cancel(cancel)
        document.save()
        check_cancel(cancel)
        stem = files[0].stem + "_converted" if len(files) == 1 else "Citrus_images_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        return publish_file(output, files[0].parent, stem, "pdf")


def convert_pdf(input_path: Path, target: str, cancel: threading.Event, progress=None) -> Path:
    if target not in {"pdf_png", "pdf_jpg", "pdf_txt"}:
        raise ValueError("지원하지 않는 PDF 출력 형식입니다.")
    check_cancel(cancel)
    with temporary_output(input_path.parent) as temporary, _pdf_lock:
        try:
            document = pdfium.PdfDocument(str(input_path))
        except pdfium.PdfiumError as error:
            raise ValueError("PDF를 열 수 없습니다. 암호가 필요하거나 손상된 파일인지 확인해 주세요.") from error
        with closing(document):
            count = len(document)
            if count == 0:
                raise ValueError("PDF에 페이지가 없습니다.")
            if target == "pdf_txt":
                texts = []
                for index in range(count):
                    check_cancel(cancel)
                    if progress:
                        progress(index + 1, count)
                    with closing(document[index]) as page, closing(page.get_textpage()) as text_page:
                        texts.append(text_page.get_text_bounded().replace("\r\n", "\n").replace("\r", "\n"))
                output = temporary / "output.txt"
                content = "\n\f\n".join(texts) if any(text.strip() for text in texts) else ""
                output.write_text(content, encoding="utf-8")
            else:
                pages = temporary / "pages"
                pages.mkdir()
                suffix = "png" if target == "pdf_png" else "jpg"
                for index in range(count):
                    check_cancel(cancel)
                    if progress:
                        progress(index + 1, count)
                    with closing(document[index]) as page:
                        width, height = page.get_size()
                        scale = 150 / 72
                        if width <= 0 or height <= 0 or width * height * scale * scale > MAX_PIXELS:
                            raise ValueError("PDF 페이지가 너무 크거나 페이지 크기가 올바르지 않습니다.")
                        with closing(page.render(scale=scale, fill_color=(255, 255, 255, 255))) as bitmap:
                            with bitmap.to_pil() as image:
                                destination = pages / f"page-{index + 1:0{len(str(count))}d}.{suffix}"
                                if suffix == "jpg":
                                    with image.convert("RGB") as rgb:
                                        rgb.save(destination, "JPEG", quality=90, dpi=(150, 150))
                                else:
                                    image.save(destination, "PNG", dpi=(150, 150))
        check_cancel(cancel)
        if target == "pdf_txt":
            return publish_file(output, input_path.parent, input_path.stem + "_converted", "txt")
        return publish_directory(pages, input_path.parent, f"{input_path.stem}_{suffix}_pages")
