"""실제 Qt 화면과 이미지→PDF 작업을 README용으로 캡처합니다."""
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication
import pypdfium2 as pdfium

from citrus_drop.app import Controller
from citrus_drop.models import available_operations
from citrus_drop.storage import Settings
from citrus_drop.typography import configure_typography


def main():
    output = project_root / "docs" / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([sys.argv[0]])
    app.setQuitOnLastWindowClosed(False)
    assert "Pretendard" in configure_typography(app)
    with tempfile.TemporaryDirectory(prefix="CitrusDropCapture-") as temporary:
        folder = Path(temporary)
        files = [folder / f"샘플 이미지 {number:02}.png" for number in (1, 2)]
        for path in files:
            shutil.copyfile(project_root / "assets" / "logo.png", path)
        controller = Controller(app, Settings(folder / "settings.json"), tray=False)
        try:
            controller.timer.stop()
            window = controller.window
            window.resize(840, 1040)
            window.add_files(files)
            window.formats.setCurrentIndex(window.formats.findData("pdf"))
            app.processEvents()
            assert window.grab().save(str(output / "main-window.png"))

            # Windows 탐색기 대신 실제 로컬 파일 URL을 담은 Qt 드롭 이벤트를 전달합니다.
            wheel = controller.wheel
            operations = available_operations(files, controller.settings.ffmpeg() is not None)
            index = next(i for i, operation in enumerate(operations) if operation.id == "pdf")
            angle = -math.pi / 2 + index * math.tau / len(operations)
            point = QPoint(round(190 + 121 * math.cos(angle)), round(190 + 121 * math.sin(angle)))
            mime = QMimeData()
            mime.setUrls([QUrl.fromLocalFile(str(path)) for path in files])
            wheel.show()
            enter = QDragEnterEvent(point, Qt.DropAction.CopyAction, mime,
                                   Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
            QApplication.sendEvent(wheel, enter)
            app.processEvents()
            assert enter.isAccepted() and wheel.operations[wheel.hover].id == "pdf"
            assert wheel.grab().save(str(output / "radial-menu.png"))
            drop = QDropEvent(QPointF(point), Qt.DropAction.CopyAction, mime,
                              Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
            QApplication.sendEvent(wheel, drop)
            assert drop.isAccepted()
            deadline = time.monotonic() + 30
            while controller.busy and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.005)
            assert not controller.busy, "PDF conversion timed out"
            assert "1건 성공 / 0건 실패" in window.status.text(), window.status.text()
            result = next(folder.glob("*.pdf"))
            with pdfium.PdfDocument(str(result)) as document:
                assert len(document) == 2
                page = document[0]
                bitmap = page.render(scale=1)
                assert bitmap.to_pil().width > 0
                bitmap.close()
                page.close()
            app.processEvents()
            assert window.grab().save(str(output / "conversion-complete.png"))
            print(f"Saved 3 actual Qt captures; image → PDF: 2 pages, {window.status.text()}")
        finally:
            controller.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
