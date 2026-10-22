from PySide6.QtGui import QFont, QFontInfo, QRawFont

from citrus_drop.typography import configure_typography


def test_bundled_font_supports_korean_without_system_install(qt_app):
    family = configure_typography(qt_app)
    assert family.startswith("Pretendard")
    assert QFontInfo(qt_app.font()).family().startswith("Pretendard")
    raw_font = QRawFont.fromFont(qt_app.font())
    for character in "한글변환Citrus0123456789":
        assert raw_font.supportsCharacter(ord(character))
    semibold = QFont(qt_app.font())
    semibold.setWeight(QFont.Weight.DemiBold)
    assert QFontInfo(semibold).family().startswith("Pretendard")
    assert QFontInfo(semibold).styleName() == "SemiBold"
