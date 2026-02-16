import sys
import os
import time
import ctypes
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QFontDatabase, QFont, QPainter, QColor, QIcon
from PySide6.QtCore import Qt, QRect
from ui.main_window import MainWindow

## build
# uv remove opencv-python
# uv add opencv-python-headless
# uv add pyinstaller
# uv sync
# uv run pyinstaller --windowed --icon=resources/imgs/brightness-stand.ico --name="MinwonOCR_v1.0" main.py

# .spec file modifying
# ('tesseract_bin', 'tesseract_bin'),
# ('resources', 'resources'),
# ('core', 'core'),
# ('ui', 'ui'),

# uv run pyinstaller --clean --noconfirm MinwonOCR_v1.0.spec


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class CustomSplashScreen(QSplashScreen):
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.setFont(QFont("Malgun Gothic", 10, QFont.Bold))

    def drawContents(self, painter):
        pixmap = self.pixmap()
        painter.drawPixmap(0, 0, pixmap)

        text = self.message()
        if not text:
            return

        rect = self.rect()  # 전체 크기
        text_rect = QRect(0, rect.height() - 50, rect.width(), 30)
        painter.fillRect(text_rect, QColor(0, 0, 0, 180))
        painter.setPen(Qt.white)  # 글씨 색상
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.drawText(text_rect, Qt.AlignCenter, text)

        # copyright part
        copyright_font = QFont("Arial", 8)
        painter.setFont(copyright_font)
        rect = self.rect()
        copyright_rect = QRect(0, rect.height() - 20, rect.width(), 20)
        painter.fillRect(copyright_rect, QColor(0, 0, 0, 180))
        painter.setPen(QColor(200, 200, 200))
        copyright_text = "Copyright © 2026 Minsoo Ahn. All rights reserved."
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.drawText(copyright_rect, Qt.AlignCenter, copyright_text)


def main():
    if sys.platform == "win32":
        myappid = "ahnminsoo.minwon_ocr.v1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)

    icon_path = resource_path("resources/imgs/brightness-stand.ico")
    app.setWindowIcon(QIcon(icon_path))

    splash_path = resource_path("resources/imgs/G-OCR-logo.png")
    splash_pix = QPixmap(splash_path)

    if splash_pix.isNull():
        splash_pix = QPixmap(500, 300)
        splash_pix.fill(Qt.white)

    splash = CustomSplashScreen(splash_pix)
    splash.showMessage(
        "프로그램 초기화 중...", Qt.AlignBottom | Qt.AlignCenter, Qt.black
    )
    splash.show()
    app.processEvents()

    font_filename = "resources/fonts/PretendardVariable.ttf"
    font_path = resource_path(font_filename)
    font_id = QFontDatabase.addApplicationFont(font_path)

    splash.showMessage(
        "폰트 리소스 로드 중...", Qt.AlignBottom | Qt.AlignCenter, Qt.black
    )
    app.processEvents()
    time.sleep(0.5)

    if font_id >= 0:
        font_families = QFontDatabase.applicationFontFamilies(font_id)

        if font_families:
            base_font_name = font_families[0]
            font = QFont(base_font_name, 10)
            font.setPointSizeF(10.5)
            font.setStyleStrategy(QFont.PreferQuality)
            font.setHintingPreference(QFont.PreferFullHinting)
            app.setFont(font)

    splash.showMessage(
        "사용자 인터페이스 구성 중...", Qt.AlignBottom | Qt.AlignCenter, Qt.black
    )
    app.processEvents()

    # 우리가 정의한 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
