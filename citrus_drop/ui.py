"""PySide6 화면. 변환 로직은 converters/pdf_tools/jobs에 있습니다."""
from datetime import datetime
import math
import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal, Slot, QPointF, QRectF
from PySide6.QtGui import QColor, QCursor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
                               QListWidget, QListWidgetItem, QMainWindow, QProgressBar, QPushButton,
                               QPlainTextEdit, QScrollArea, QVBoxLayout, QWidget)

from . import __version__
from .models import available_operations, normalize_files
from .storage import Settings, bundled_directory

ORANGE = "#FFAA5C"
STYLESHEET = """
QWidget { background: #10151E; color: #F2F4F8; font-size: 14px; }
QLabel { background: transparent; }
QPushButton { background: #2A3547; border: 1px solid #3D495D; border-radius: 7px; padding: 8px 13px; }
QPushButton:hover { background: #3A4961; }
QPushButton:disabled { color: #758094; background: #202938; border-color: #293345; }
QPushButton#quit:hover { background: #61323A; border-color: #8B4551; }
QPushButton#run { background: #FFAA5C; color: #171D26; font-weight: 600; font-size: 15px; padding: 12px; }
QPushButton#run:hover { background: #FFBB7E; }
QPushButton#run:disabled { background: #66513D; color: #B5A18D; }
QListWidget { background: #151C28; border: 1px solid #2D3747; border-radius: 7px; padding: 6px; }
QListWidget::item { padding: 5px; border-radius: 4px; }
QListWidget::item:selected { background: #344764; }
QComboBox { background: #202B3C; border: 1px solid #46536A; border-radius: 6px; padding: 9px; }
QComboBox QAbstractItemView { background: #202B3C; selection-background-color: #3B4D69; }
QProgressBar { background: #263145; border: none; border-radius: 2px; height: 5px; }
QProgressBar::chunk { background: #FFAA5C; }
QCheckBox { spacing: 8px; }
QToolTip { background: #28364B; color: white; border: 1px solid #52627A; padding: 4px; }
QMenu { background: #202B3C; }
QMenu::item { padding: 7px 20px; }
QMenu::item:selected { background: #3A4961; }
"""


def local_files(event) -> list[Path]:
    if not event.possibleActions() & Qt.DropAction.CopyAction:
        return []
    urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
    try:
        return normalize_files(url.toLocalFile() for url in urls if url.isLocalFile())
    except (OSError, ValueError):
        return []


class DropArea(QFrame):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setStyleSheet("DropArea { background: #1B2432; border: 1px dashed #63738C; border-radius: 14px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        heading = QLabel("여기로 파일을 끌어 놓으셔도 됩니다")
        heading.setStyleSheet("font-size: 17px; font-weight: 600;")
        layout.addWidget(heading)
        hint = QLabel("이미지 · PDF · 영상 · 음성 · ZIP 압축")
        hint.setStyleSheet("color: #A9B3C4;")
        layout.addWidget(hint)

    def dragEnterEvent(self, event):
        if local_files(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        files = local_files(event)
        if files:
            self.files_dropped.emit(files)
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()


class MainWindow(QMainWindow):
    requested = Signal(list, str)
    cancel_requested = Signal()
    close_requested = Signal()
    quit_requested = Signal()

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.files: list[Path] = []
        self.busy = False
        self.allow_close = False
        self.setWindowTitle("Citrus Drop")
        self.resize(800, 900)
        self.setMinimumSize(650, 660)
        self.setStyleSheet(STYLESHEET)
        central = QWidget()
        self.setCentralWidget(central)
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        header = QHBoxLayout()
        header.setContentsMargins(28, 18, 28, 12)
        header.setSpacing(8)
        brand = QLabel("CITRUS DROP")
        brand.setStyleSheet(f"color: {ORANGE}; font-weight: bold; letter-spacing: 2px;")
        header.addWidget(brand, 1)
        self.about_button = QPushButton("정보·라이선스")
        self.about_button.clicked.connect(self.show_about)
        header.addWidget(self.about_button)
        self.close_button = QPushButton("창 닫기")
        self.close_button.setToolTip("창을 닫습니다. 트레이를 사용할 수 있으면 백그라운드에서 계속 실행합니다.")
        self.close_button.clicked.connect(self.close)
        header.addWidget(self.close_button)
        self.quit_button = QPushButton("프로그램 종료")
        self.quit_button.setObjectName("quit")
        self.quit_button.setToolTip("앱을 완전히 종료합니다. 진행 중인 작업이 있으면 취소 여부를 확인합니다.")
        self.quit_button.clicked.connect(self.quit_requested.emit)
        header.addWidget(self.quit_button)
        outer_layout.addLayout(header)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll, 1)
        body = QWidget()
        scroll.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(28, 8, 28, 24)
        layout.setSpacing(12)
        heading = QLabel("파일을 놓으면, 변환됩니다.")
        heading.setStyleSheet("font-size: 28px; font-weight: 600;")
        layout.addWidget(heading)
        layout.addWidget(self.label("탐색기에서 파일을 끌다가 Shift를 누르고, 원형 메뉴의 형식 위에 놓으세요."))
        self.gesture_checkbox = QCheckBox("Shift 원형 메뉴 사용")
        self.gesture_checkbox.setChecked(True)
        layout.addWidget(self.gesture_checkbox)
        drop_area = DropArea()
        drop_area.files_dropped.connect(self.add_files)
        layout.addWidget(drop_area)
        toolbar = QHBoxLayout()
        self.file_count = self.label("0개 파일 선택")
        toolbar.addWidget(self.file_count, 1)
        for text, callback in [("파일 추가", self.pick_files), ("위로", lambda: self.move_selected(-1)),
                               ("아래로", lambda: self.move_selected(1)), ("비우기", self.clear_files)]:
            button = QPushButton(text)
            button.clicked.connect(callback)
            toolbar.addWidget(button)
        layout.addLayout(toolbar)
        self.file_list = QListWidget()
        self.file_list.setFixedHeight(110)
        layout.addWidget(self.file_list)
        layout.addWidget(self.label("출력 형식 / 작업"))
        self.formats = QComboBox()
        layout.addWidget(self.formats)
        layout.addWidget(self.label("원본 폴더에 새 결과를 저장합니다. 기존 파일과 이름이 겹치면 번호를 붙입니다."))
        layout.addWidget(self.label("PDF 만들기: 목록 순서대로 A4 페이지에 배치합니다. GIF·TIFF는 첫 프레임만 사용합니다.", small=True))
        actions = QHBoxLayout()
        self.run_button = QPushButton("변환 실행")
        self.run_button.setObjectName("run")
        self.run_button.clicked.connect(self.submit)
        actions.addWidget(self.run_button, 1)
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        actions.addWidget(self.cancel_button)
        layout.addLayout(actions)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        layout.addWidget(self.progress)
        self.status = self.label("준비되었습니다. 파일은 서버로 업로드되지 않습니다.")
        layout.addWidget(self.status)
        settings_row = QHBoxLayout()
        self.ffmpeg_status = self.label("")
        settings_row.addWidget(self.ffmpeg_status, 1)
        ffmpeg_button = QPushButton("FFmpeg 선택")
        ffmpeg_button.clicked.connect(self.pick_ffmpeg)
        settings_row.addWidget(ffmpeg_button)
        layout.addLayout(settings_row)
        layout.addWidget(self.label("PDF·WebP 기본 지원 · TXT 추출은 OCR을 사용하지 않습니다.", small=True))
        layout.addWidget(self.label("작업 기록 · 이번 실행"))
        self.history = QListWidget()
        self.history.setFixedHeight(135)
        layout.addWidget(self.history)
        self.close_hint = self.label("창 닫기: 트레이에서 계속 실행 · 프로그램 종료: 앱 완전 종료", small=True)
        layout.addWidget(self.close_hint)
        layout.addStretch(1)
        self.refresh_files()
        self.refresh_ffmpeg()

    @staticmethod
    def label(text, small=False):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("color: #A9B3C4;" + ("font-size: 12px;" if small else ""))
        return label

    def show_about(self):
        dialog = QDialog(self)
        dialog.setObjectName("about_dialog")
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.setWindowTitle("Citrus Drop · 정보 및 라이선스")
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.resize(720, 600)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Citrus Drop {__version__}"))
        notices = QPlainTextEdit()
        notices.setReadOnly(True)
        parts = []
        for name in ("LICENSE", "AUTHORS.md", "THIRD_PARTY_NOTICES.md", "assets/fonts/OFL.txt"):
            try:
                content = (bundled_directory() / name).read_text(encoding="utf-8")
            except OSError:
                content = "문서를 읽을 수 없습니다. 공식 저장소의 라이선스 안내를 확인해 주세요."
            parts.append(f"===== {name} =====\n\n{content}")
        notices.setPlainText("\n\n".join(parts))
        layout.addWidget(notices)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("닫기")
        buttons.rejected.connect(dialog.close)
        layout.addWidget(buttons)
        dialog.show()

    def add_files(self, files):
        try:
            self.files = normalize_files(self.files + list(files))
            self.refresh_files()
        except (OSError, ValueError) as error:
            self.status.setText(f"파일 목록을 읽지 못했습니다: {error}")

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "변환할 파일 선택", "", "모든 파일 (*)")
        self.add_files(files)

    def clear_files(self):
        self.files.clear()
        self.refresh_files()

    def move_selected(self, direction):
        index = self.file_list.currentRow()
        destination = index + direction
        if index < 0 or not 0 <= destination < len(self.files):
            return
        self.files.insert(destination, self.files.pop(index))
        self.refresh_files()
        self.file_list.setCurrentRow(destination)

    def refresh_files(self):
        previous = self.formats.currentData()
        self.file_list.clear()
        for path in self.files:
            item = QListWidgetItem(path.name)
            item.setToolTip(str(path))
            self.file_list.addItem(item)
        self.file_count.setText(f"{len(self.files)}개 파일 선택")
        self.formats.clear()
        for operation in available_operations(self.files, self.settings.ffmpeg() is not None):
            self.formats.addItem(f"{operation.label}  ·  {operation.description}", operation.id)
        selected = self.formats.findData(previous)
        self.formats.setCurrentIndex(selected if selected >= 0 else 0)
        self.run_button.setEnabled(bool(self.files) and not self.busy)

    def submit(self):
        operation_id = self.formats.currentData()
        if self.files and operation_id:
            self.requested.emit(list(self.files), operation_id)

    def pick_ffmpeg(self):
        filter_text = "FFmpeg (ffmpeg.exe)" if os.name == "nt" else "모든 파일 (*)"
        filename, _ = QFileDialog.getOpenFileName(self, "사용할 FFmpeg 실행 파일 선택", "", filter_text)
        if not filename:
            return
        try:
            self.settings.save_ffmpeg(Path(filename))
            self.refresh_ffmpeg()
            self.refresh_files()
        except OSError as error:
            self.status.setText(f"설정을 저장하지 못했습니다: {error}")

    def refresh_ffmpeg(self):
        executable = self.settings.ffmpeg()
        self.ffmpeg_status.setText("FFmpeg 연결됨 · 영상 / 음성 사용 가능" if executable else "FFmpeg 미연결 · 이미지 / PDF / ZIP 사용 가능")
        self.ffmpeg_status.setToolTip(str(executable or ""))

    def set_busy(self, busy):
        self.busy = busy
        self.cancel_button.setEnabled(busy)
        self.run_button.setEnabled(bool(self.files) and not busy)
        self.progress.setRange(0, 0 if busy else 1)
        if not busy:
            self.progress.setValue(0)

    @Slot(str, bool)
    def add_history(self, message, failed=False):
        item = QListWidgetItem(datetime.now().strftime("%H:%M:%S") + "  " + message)
        item.setToolTip(message)
        if failed:
            item.setForeground(QColor("#FF9B95"))
        self.history.insertItem(0, item)
        if self.history.count() > 100:
            self.history.takeItem(100)

    def reveal(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        if self.allow_close:
            event.accept()
        else:
            event.ignore()
            self.close_requested.emit()


class WheelWindow(QWidget):
    requested = Signal(list, str)
    center = 190
    inner = 72
    outer = 174

    def __init__(self, settings: Settings):
        flags = Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowDoesNotAcceptFocus
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAcceptDrops(True)
        self.setFixedSize(380, 390)
        self.settings = settings
        self.files = []
        self.operations = []
        self.hover = -1
        self.hint = "파일을 이동해 주세요"

    def open_at_cursor(self):
        self.files, self.operations, self.hover = [], [], -1
        self.hint = "파일을 메뉴 안으로 이동해 주세요"
        position = QCursor.pos()
        screen = self.screen() if self.isVisible() else None
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.screenAt(position) or screen or QGuiApplication.primaryScreen()
        rect = screen.availableGeometry()
        x = max(rect.left(), min(position.x() - self.width() // 2, rect.right() + 1 - self.width()))
        y = max(rect.top(), min(position.y() - self.height() // 2, rect.bottom() + 1 - self.height()))
        self.move(x, y)
        self.show()
        self.update()

    def hit(self, position: QPointF) -> int:
        if not self.operations:
            return -1
        x, y = position.x() - self.center, position.y() - self.center
        if not self.inner <= math.hypot(x, y) <= self.outer:
            return -1
        step = math.tau / len(self.operations)
        angle = (math.atan2(y, x) + math.pi / 2 + step / 2) % math.tau
        index = int(angle / step)
        within = angle - index * step
        return -1 if within < 0.018 or within > step - 0.018 else index

    def _read_drag(self, event):
        files = local_files(event)
        if files != self.files:
            self.files = files
            self.operations = available_operations(files, self.settings.ffmpeg() is not None)
        self.hover = self.hit(event.position())
        self.hint = "원하는 형식에 놓으세요" if files else "로컬 파일만 지원합니다"
        self.update()
        return bool(files)

    def dragEnterEvent(self, event):
        if self._read_drag(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if self._read_drag(event) and self.hover >= 0:
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.hover = -1
        self.update()
        event.accept()

    def dropEvent(self, event):
        if self._read_drag(event) and self.hover >= 0:
            operation_id = self.operations[self.hover].id
            files = list(self.files)
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            self.hide()
            self.requested.emit(files, operation_id)
        else:
            event.ignore()
            self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 투명 창은 이전 프레임을 명시적으로 지워야 안내 글자가 겹치지 않습니다.
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setPen(QPen(QColor("#343C4A"), 1))
        painter.setBrush(QColor("#161B25"))
        painter.drawEllipse(QPointF(self.center, self.center), self.outer + 4, self.outer + 4)
        if self.operations:
            step = math.tau / len(self.operations)
            for index, operation in enumerate(self.operations):
                angle = -math.pi / 2 + index * step
                start, end = angle - step / 2 + 0.018, angle + step / 2 - 0.018
                path = QPainterPath()
                points = []
                for radius, angles in [(self.outer, [start + (end - start) * j / 40 for j in range(41)]),
                                       (self.inner, [end - (end - start) * j / 40 for j in range(41)])]:
                    for point_angle in angles:
                        points.append(QPointF(self.center + radius * math.cos(point_angle), self.center + radius * math.sin(point_angle)))
                path.moveTo(points[0])
                for point in points[1:]:
                    path.lineTo(point)
                path.closeSubpath()
                active = index == self.hover
                painter.fillPath(path, QColor(ORANGE if active else "#232B39"))
                x, y = self.center + 121 * math.cos(angle), self.center + 121 * math.sin(angle)
                self._text(painter, operation.label, x, y - 8, 13, "#171D26" if active else "#FFFFFF", True)
                self._text(painter, "놓아서 실행" if active else "변환 / 작업", x, y + 16, 11, "#57402A" if active else "#9BA6B8")
        self._text(painter, f"{len(self.files)}개 파일" if self.files else "CITRUS", self.center, self.center - 16, 13, ORANGE, True)
        label = self.operations[self.hover].label if self.hover >= 0 else "SHIFT + DROP"
        self._text(painter, label, self.center, self.center + 11, 10, "#FFFFFF")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#161B25"))
        painter.drawRoundedRect(QRectF(34, 364, 312, 25), 8, 8)
        self._text(painter, self.hint, self.center, 376, 11, "#CCD3DE")

    @staticmethod
    def _text(painter, text, x, y, size, color, bold=False):
        painter.setPen(QColor(color))
        font = QFont(painter.font())
        font.setPixelSize(size)
        font.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Normal)
        painter.setFont(font)
        painter.drawText(QRectF(x - 92, y - 15, 184, 30), Qt.AlignmentFlag.AlignCenter, text)
