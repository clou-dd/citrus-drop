"""프로젝트 SVG를 앱 PNG와 여러 해상도의 Windows ICO로 렌더링합니다."""
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


def generate_icons():
    app = QGuiApplication.instance() or QGuiApplication([])
    assets = Path(__file__).resolve().parents[1] / "assets"
    renderer = QSvgRenderer(str(assets / "citrus-drop.svg"))
    if not renderer.isValid():
        raise ValueError("assets/citrus-drop.svg is not a valid SVG")
    image = QImage(512, 512, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    try:
        renderer.render(painter)
    finally:
        painter.end()
    if not image.save(str(assets / "logo.png")):
        raise OSError("Could not save assets/logo.png")
    with Image.open(assets / "logo.png") as logo:
        logo.save(assets / "icon.ico", sizes=[(size, size) for size in (16, 24, 32, 48, 64, 128, 256)])
    print("Generated assets/logo.png and assets/icon.ico from assets/citrus-drop.svg")


if __name__ == "__main__":
    generate_icons()
