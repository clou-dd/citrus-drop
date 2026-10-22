import math
from pathlib import Path
import time

from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from citrus_drop.app import Controller
from citrus_drop.models import available_operations
from citrus_drop.native import GestureState, InputState, WindowsInput
from citrus_drop.storage import Settings
from citrus_drop.ui import MainWindow, WheelWindow, DropArea


def test_window_order_and_operation_selection(qt_app, tmp_path, image_file):
    window = MainWindow(Settings(tmp_path / "settings"))
    try:
        second = tmp_path / "second.png"; second.write_bytes(image_file.read_bytes())
        window.add_files([image_file, second])
        window.file_list.setCurrentRow(1)
        window.move_selected(-1)
        assert window.files == [second, image_file]
        index = window.formats.findData("pdf")
        assert index >= 0
        window.formats.setCurrentIndex(index)
        requested = []
        window.requested.connect(lambda files, op: requested.append((files, op)))
        window.submit()
        assert requested == [([second, image_file], "pdf")]
    finally:
        window.allow_close = True; window.close()


def test_drop_area_accepts_real_files_only(qt_app, image_file):
    area = DropArea()
    mime = QMimeData(); mime.setUrls([QUrl.fromLocalFile(str(image_file))])
    entered = QDragEnterEvent(QPoint(20, 20), Qt.DropAction.CopyAction, mime,
                             Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    qt_app.sendEvent(area, entered)
    assert entered.isAccepted() and entered.dropAction() == Qt.DropAction.CopyAction
    received = []
    area.files_dropped.connect(received.append)
    dropped = QDropEvent(QPointF(20, 20), Qt.DropAction.CopyAction, mime,
                         Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    qt_app.sendEvent(area, dropped)
    assert dropped.isAccepted() and received == [[image_file]]
    remote = QMimeData(); remote.setUrls([QUrl("https://example.com/private.png")])
    rejected = QDragEnterEvent(QPoint(20, 20), Qt.DropAction.CopyAction, remote,
                              Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    qt_app.sendEvent(area, rejected)
    assert not rejected.isAccepted()
    area.close()


def test_wheel_geometry_render_and_drop(qt_app, tmp_path, image_file):
    wheel = WheelWindow(Settings(tmp_path / "settings"))
    wheel.files = [image_file]
    wheel.operations = available_operations(wheel.files)
    assert wheel.hit(QPointF(190, 190)) == -1
    assert wheel.hit(QPointF(190, 69)) == 0
    assert wheel.hit(QPointF(0, 0)) == -1
    step = math.tau / len(wheel.operations)
    angle = -math.pi / 2 + step / 2
    assert wheel.hit(QPointF(190 + 121 * math.cos(angle), 190 + 121 * math.sin(angle))) == -1
    first_frame = wheel.grab().toImage()
    assert not first_frame.isNull()
    assert wheel.grab().toImage() == first_frame
    mime = QMimeData(); mime.setUrls([QUrl.fromLocalFile(str(image_file))])
    enter = QDragEnterEvent(QPoint(190, 69), Qt.DropAction.CopyAction, mime,
                           Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    qt_app.sendEvent(wheel, enter)
    received = []
    wheel.requested.connect(lambda paths, op: received.append((paths, op)))
    drop = QDropEvent(QPointF(190, 69), Qt.DropAction.CopyAction, mime,
                     Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    qt_app.sendEvent(wheel, drop)
    assert drop.isAccepted() and received == [([image_file], "png")]
    wheel.close()


def test_gesture_state_requires_drag_then_shift():
    gesture = GestureState()
    assert gesture.update(InputState(True, False, False, (0, 0)), False, True, 0) == ""
    assert gesture.update(InputState(True, False, False, (20, 0)), False, True, 0.1) == ""
    assert gesture.update(InputState(True, True, False, (20, 0)), False, True, 0.2) == "show"
    assert gesture.update(InputState(True, False, False, (20, 0)), True, True, 0.3) == ""
    assert gesture.update(InputState(False, False, False, (20, 0)), True, True, 0.4) == ""
    assert gesture.update(InputState(False, False, False, (20, 0)), True, True, 0.71) == "hide"


def test_preheld_shift_and_escape():
    gesture = GestureState()
    gesture.update(InputState(True, True, False, (0, 0)), False, True, 0)
    assert gesture.update(InputState(True, True, False, (20, 0)), False, True, 0.1) == ""
    assert gesture.update(InputState(True, True, True, (20, 0)), True, True, 0.2) == "hide"
    assert gesture.update(InputState(True, True, False, (20, 0)), True, False, 0.3) == "hide"


def test_controller_worker_finishes_without_destroying_running_thread(qt_app, tmp_path, image_file):
    controller = Controller(qt_app, Settings(tmp_path / "settings"), show=False, tray=False)
    try:
        controller.execute([image_file], "pdf")
        deadline = time.monotonic() + 10
        while controller.busy and time.monotonic() < deadline:
            qt_app.processEvents()
            time.sleep(0.005)
        assert not controller.busy and controller.thread is None
        assert "1건 성공 / 0건 실패" in controller.window.status.text()
        assert (image_file.parent / (image_file.stem + "_converted.pdf")).is_file()
        controller.execute([image_file], "path")
        assert qt_app.clipboard().text() == str(image_file)
    finally:
        controller.dispose()
        qt_app.processEvents()
