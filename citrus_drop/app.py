"""앱 시작·트레이·작업 스레드·입력 감지의 연결 지점."""
import argparse
from pathlib import Path
import sys
import tempfile
import threading

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QLockFile, QThread, QTimer, Signal, Slot, Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from . import __version__
from .jobs import BatchResult, run_batch
from .models import available_operations
from .native import GestureState, WindowsInput
from .storage import Settings, app_directory
from .typography import configure_typography
from .ui import MainWindow, WheelWindow, STYLESHEET


def application_icon() -> QIcon:
    """EXE·창·트레이에 같은 프로젝트 로고를 사용합니다."""
    roots = [app_directory() / "assets", Path(getattr(sys, "_MEIPASS", app_directory())) / "assets"]
    for root in roots:
        for name in ("icon.ico", "logo.png", "citrus-drop.svg"):
            if (root / name).is_file():
                icon = QIcon(str(root / name))
                if not icon.isNull():
                    return icon
    # 외부 이미지 없이 표시할 수 있는 임시 기본 아이콘입니다.
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#FFAA5C"))
    painter.drawEllipse(5, 5, 54, 54)
    painter.setPen(QColor("#10151E"))
    font = QFont()
    font.setPixelSize(38)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "C")
    painter.end()
    return QIcon(pixmap)


class ConversionWorker(QObject):
    progress = Signal(str)
    entry = Signal(str, bool)
    finished = Signal(object)

    def __init__(self, files, operation_id, ffmpeg, cancel):
        super().__init__()
        self.files, self.operation_id, self.ffmpeg, self.cancel = files, operation_id, ffmpeg, cancel

    @Slot()
    def run(self):
        try:
            result = run_batch(self.files, self.operation_id, self.ffmpeg, self.cancel,
                               self.progress.emit, self.entry.emit)
        except Exception as error:
            self.entry.emit(str(error), True)
            result = BatchResult(failed=1)
        self.finished.emit(result)


class Controller(QObject):
    def __init__(self, app: QApplication, settings: Settings | None = None, show=True, tray=True):
        super().__init__()
        self.app = app
        self.settings = settings or Settings()
        self.window = MainWindow(self.settings)
        self.wheel = WheelWindow(self.settings)
        self.window.requested.connect(self.execute)
        self.wheel.requested.connect(self.execute)
        self.window.cancel_requested.connect(self.cancel_job)
        self.window.close_requested.connect(self.window_closed)
        self.window.quit_requested.connect(self.request_quit)
        self.busy = False
        self.exit_after_job = False
        self.cancel = threading.Event()
        self.thread = None
        self.worker = None
        self.pending_result = None
        icon = application_icon()
        app.setWindowIcon(icon)
        self.window.setWindowIcon(icon)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("Citrus Drop · Shift + 드래그")
        menu = QMenu()
        menu.setStyleSheet(STYLESHEET)
        open_action = QAction("Citrus Drop 열기", menu)
        open_action.triggered.connect(self.window.reveal)
        menu.addAction(open_action)
        quit_action = QAction("종료", menu)
        quit_action.triggered.connect(self.request_quit)
        menu.addAction(quit_action)
        self.tray_menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.tray_activated)
        self.tray_enabled = tray and QSystemTrayIcon.isSystemTrayAvailable()
        if self.tray_enabled:
            self.tray.show()
        else:
            self.window.close_button.setToolTip("트레이를 사용할 수 없어 창을 닫으면 앱도 종료합니다.")
            self.window.close_hint.setText("이 환경에서는 창을 닫으면 앱도 종료합니다. 작업 중에는 취소 여부를 확인합니다.")
        self.input = WindowsInput()
        self.gesture = GestureState()
        if not self.input.supported:
            self.window.gesture_checkbox.setChecked(False)
            self.window.gesture_checkbox.setEnabled(False)
            self.window.gesture_checkbox.setToolTip("전역 Shift 메뉴는 윈도우에서 사용할 수 있습니다.")
        self.timer = QTimer(self)
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.poll_input)
        if self.input.supported:
            self.timer.start()
        if show:
            self.window.show()

    def poll_input(self):
        action = self.gesture.update(self.input.read(), self.wheel.isVisible(), self.window.gesture_checkbox.isChecked())
        if action == "show":
            self.wheel.open_at_cursor()
        elif action == "hide":
            self.wheel.hide()

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.window.reveal()

    def window_closed(self):
        if self.tray_enabled:
            self.window.hide()
        else:
            self.request_quit()

    @Slot(list, str)
    def execute(self, files, operation_id):
        if self.busy:
            self.window.reveal()
            self.window.status.setText("다른 작업이 진행 중입니다. 완료하거나 취소한 뒤 실행해 주세요.")
            return
        allowed = {operation.id for operation in available_operations(files, self.settings.ffmpeg() is not None)}
        if operation_id not in allowed:
            self.window.status.setText("이 파일 조합에서는 선택한 작업을 지원하지 않습니다.")
            return
        if operation_id == "path":
            self.app.clipboard().setText("\n".join(str(path) for path in files))
            self.window.add_history(f"{len(files)}개 파일 경로 복사 완료")
            self.window.status.setText("클립보드에 전체 파일 경로를 복사했습니다.")
            return
        self.busy = True
        self.cancel = threading.Event()
        self.window.set_busy(True)
        self.window.status.setText("작업을 시작합니다. 원본 파일은 유지됩니다.")
        self.thread = QThread(self)
        self.worker = ConversionWorker(list(files), operation_id, self.settings.ffmpeg(), self.cancel)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.window.status.setText)
        self.worker.entry.connect(self.window.add_history)
        self.worker.finished.connect(self.job_completed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread_stopped)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @Slot(object)
    def job_completed(self, result):
        # 작업 스레드가 완전히 끝난 뒤 UI를 해제합니다. 종료 시 QThread 파괴를 방지합니다.
        self.pending_result = result

    @Slot()
    def thread_stopped(self):
        result = self.pending_result or BatchResult(failed=1)
        self.pending_result = None
        self.worker = self.thread = None
        self.busy = False
        self.window.set_busy(False)
        message = ("취소됨" if result.cancelled else "완료") + f" · {result.succeeded}건 성공 / {result.failed}건 실패"
        if result.cancelled:
            message += " · 이미 완료된 결과는 유지됩니다."
        self.window.status.setText(message)
        if self.tray_enabled:
            self.tray.showMessage("Citrus Drop", message, QSystemTrayIcon.MessageIcon.Information, 3000)
        if result.failed:
            self.window.reveal()
        if self.exit_after_job:
            self.shutdown()

    def cancel_job(self):
        self.cancel.set()
        self.window.status.setText("작업을 취소하는 중입니다. 이미지·PDF 처리 중에는 잠시 걸릴 수 있습니다.")

    def request_quit(self):
        if self.busy:
            answer = QMessageBox.question(self.window, "Citrus Drop", "진행 중인 작업을 취소하고 종료하시겠습니까?")
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.exit_after_job = True
            self.timer.stop()
            self.wheel.hide()
            self.cancel_job()
            return
        self.shutdown()

    def shutdown(self, exit_code=0):
        self.timer.stop()
        self.tray.hide()
        self.wheel.hide()
        self.window.allow_close = True
        self.window.close()
        self.app.exit(exit_code)

    def dispose(self):
        """QApplication이 소멸하기 전에 화면·트레이의 Qt 리소스를 정리합니다."""
        self.timer.stop()
        self.cancel.set()
        if self.thread is not None and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.tray.hide()
        self.window.allow_close = True
        self.window.close()
        self.wheel.close()
        for resource in (self.window, self.wheel, self.tray_menu, self.tray):
            resource.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Citrus Drop · 로컬 파일 변환")
    parser.add_argument("--smoke-test", action="store_true", help="화면과 임시 PDF 변환을 검사하고 자동 종료")
    args = parser.parse_args(argv)
    app = QApplication.instance() or QApplication([sys.argv[0]])
    app.setApplicationName("CitrusDrop")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("CitrusDrop")
    app.setQuitOnLastWindowClosed(False)
    font_family = configure_typography(app)
    settings = Settings()
    settings.directory.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(settings.directory / "app.lock"))
    if not lock.tryLock(0):
        QMessageBox.information(None, "Citrus Drop", "이미 실행 중입니다. 트레이 아이콘을 확인해 주세요.")
        return 0
    controller = Controller(app, settings)
    if args.smoke_test:
        def smoke_test():
            from PIL import Image
            from .pdf_tools import images_to_pdf, convert_pdf
            try:
                if not font_family.startswith("Pretendard"):
                    raise RuntimeError("Bundled Pretendard could not be loaded. Run Setup.cmd first.")
                with tempfile.TemporaryDirectory(prefix="CitrusDropSmoke_") as temporary:
                    source = Path(temporary) / "smoke.png"
                    with Image.new("RGB", (32, 24), "orange") as image:
                        image.save(source)
                    pdf = images_to_pdf([source], threading.Event())
                    pages = convert_pdf(pdf, "pdf_png", threading.Event())
                    with Image.open(pages / "page-1.png") as image:
                        image.verify()
            except Exception:
                import traceback
                traceback.print_exc()
                controller.shutdown(1)
            else:
                controller.shutdown()
        QTimer.singleShot(100, smoke_test)
    try:
        return app.exec()
    finally:
        controller.dispose()
        lock.unlock()
