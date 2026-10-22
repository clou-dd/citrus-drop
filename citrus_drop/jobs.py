"""화면에서 호출하는 일괄 처리. 진행·기록 콜백은 호출한 작업 스레드에서 실행됩니다."""
from dataclasses import dataclass, field
from pathlib import Path
import threading

from .converters import Cancelled, check_cancel, convert_image, convert_media, create_archive
from .models import available_operations, file_kind
from .pdf_tools import images_to_pdf, convert_pdf


@dataclass
class BatchResult:
    succeeded: int = 0
    failed: int = 0
    cancelled: bool = False
    outputs: list[Path] = field(default_factory=list)


def run_batch(files: list[Path], operation_id: str, ffmpeg: Path | None, cancel: threading.Event,
              progress=lambda message: None, entry=lambda message, failed: None) -> BatchResult:
    result = BatchResult()
    allowed = {operation.id for operation in available_operations(files, ffmpeg is not None and ffmpeg.is_file())}
    if operation_id not in allowed or operation_id == "path":
        raise ValueError("이 파일 조합에서는 선택한 작업을 지원하지 않습니다.")

    def page_progress(index, total):
        check_cancel(cancel)
        progress(f"PDF 페이지 처리 {index} / {total}")

    def completed(output: Path):
        result.succeeded += 1
        result.outputs.append(output)
        note = " · 문자가 없는 PDF입니다 (OCR 미사용)." if operation_id == "pdf_txt" and output.stat().st_size == 0 else ""
        entry(str(output) + note, False)

    try:
        check_cancel(cancel)
        if operation_id == "zip":
            completed(create_archive(files, cancel))
        elif operation_id == "pdf":
            completed(images_to_pdf(files, cancel, page_progress))
        else:
            for index, input_path in enumerate(files):
                check_cancel(cancel)
                progress(f"{index + 1} / {len(files)}  {input_path.name}")
                try:
                    if operation_id.startswith("pdf_"):
                        output = convert_pdf(input_path, operation_id, cancel, page_progress)
                    elif file_kind(input_path) == "image":
                        output = convert_image(input_path, operation_id, cancel)
                    else:
                        output = convert_media(input_path, operation_id, ffmpeg, cancel)
                    completed(output)
                except Cancelled:
                    raise
                except Exception as error:
                    result.failed += 1
                    entry(f"{input_path.name} · {error}", True)
    except Cancelled:
        result.cancelled = True
    except Exception as error:
        result.failed += 1
        entry(str(error), True)
    return result
