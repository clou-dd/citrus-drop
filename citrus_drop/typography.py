"""시스템 설치 없이 앱에 포함된 Pretendard를 사용합니다."""
from pathlib import Path
import sys

from PySide6.QtGui import QFont, QFontDatabase

from .storage import app_directory


def configure_typography(app) -> str:
    roots = [app_directory(), Path(getattr(sys, "_MEIPASS", app_directory()))]
    family = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont).family()
    for root in roots:
        loaded_family = None
        for weight in ("Regular", "SemiBold", "Bold"):
            font_path = root / "assets" / "fonts" / f"Pretendard-{weight}.otf"
            if not font_path.is_file():
                continue
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
            if weight == "Regular" and families:
                loaded_family = families[0]
        if loaded_family:
            family = loaded_family
            break
    font = QFont(family)
    font.setPixelSize(14)
    font.setWeight(QFont.Weight.Normal)
    app.setFont(font)
    return family
