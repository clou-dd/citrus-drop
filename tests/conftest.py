import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import pytest
from PIL import Image


@pytest.fixture
def image_file(tmp_path):
    path = tmp_path / "한글 공백 & $ 이미지.png"
    with Image.new("RGBA", (80, 40), (240, 60, 20, 255)) as image:
        image.paste((0, 0, 0, 0), (0, 0, 16, 16))
        image.save(path)
    return path


@pytest.fixture(scope="session")
def qt_app():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


@pytest.fixture(autouse=True)
def cleanup_qt_widgets(request):
    yield
    if "qt_app" not in request.fixturenames:
        return
    from PySide6.QtCore import QCoreApplication, QEvent
    app = request.getfixturevalue("qt_app")
    for widget in app.topLevelWidgets():
        if widget.parent() is None:
            if hasattr(widget, "allow_close"):
                widget.allow_close = True
            widget.close()
            widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
