from enum import IntEnum
from PySide6.QtWidgets import (
    QMainWindow,
    QToolBar,
    QWidget,
    QStackedWidget,
    QSizePolicy,
)
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QIcon,
    QPixmap,
    QPainter,
    QPainterPath,
    QColor,
    QPen,
    QFont,
)
from PySide6.QtCore import Qt

# Widgets
from ui.profile_editor import ProfileEditor
from ui.ocr_runner import OCRRunner
from ui.verification_viewer import VerificationViewer
from ui.info_page import InfoPage


class PageIndex(IntEnum):
    OCR_RUN = 0
    VERIFY = 1
    SETTINGS = 2
    INFO = 3


TOOLBAR_STYLESHEET = """
    QToolBar {
        spacing: 10px;
        padding: 3px;
        background-color: #333333;
        color: white;
    }
    QToolButton {
        min-width: 60px;
        padding: 8px;
        border-radius: 4px;
    }
    QToolButton:hover {
        background-color: #808080; 
    }
    QToolButton:checked {
        background-color: #666666;
        border: 1px solid #999999;
    }
"""


class IconFactory:
    @staticmethod
    def _base_pixmap(size=24):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        return pixmap, painter

    @staticmethod
    def list_icon(color="black"):
        pixmap, painter = IconFactory._base_pixmap()

        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)

        start_y, row_height, gap = 4, 4, 3
        for i in range(3):
            y = start_y + (i * (row_height + gap))
            painter.drawRoundedRect(2, y, 4, row_height, 1, 1)
            painter.drawRoundedRect(8, y, 14, row_height, 1, 1)

        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def play_icon(color="white"):
        pixmap, painter = IconFactory._base_pixmap()

        path = QPainterPath()
        path.moveTo(6, 4)
        path.lineTo(20, 12)
        path.lineTo(6, 20)
        path.closeSubpath()

        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def gear_icon(color="black"):
        pixmap, painter = IconFactory._base_pixmap()

        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)

        center = 12
        painter.save()
        painter.translate(center, center)
        for _ in range(8):
            painter.drawRect(-2, -11, 4, 5)
            painter.rotate(45)
        painter.restore()

        painter.drawEllipse(4, 4, 16, 16)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.setBrush(Qt.transparent)
        painter.drawEllipse(9, 9, 6, 6)

        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def help_icon(color="white"):
        pixmap, painter = IconFactory._base_pixmap()

        pen = QPen(QColor(color), 2)
        painter.setPen(pen)
        painter.drawEllipse(2, 2, 20, 20)

        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "?")
        painter.end()
        return QIcon(pixmap)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("G-OCR")
        self.resize(1280, 800)

        self._init_central_widget()
        self._init_pages()
        self._init_toolbar()
        self._init_connections()
        self._check_startup_state()

    def _init_central_widget(self):
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

    def _init_pages(self):
        # 페이지 인스턴스 생성
        self.page_ocr_run = OCRRunner()
        self.page_verify = VerificationViewer()
        self.page_settings = ProfileEditor()
        self.page_info = InfoPage()

        # 스택에 순서대로 추가 (PageIndex Enum 순서와 일치해야 함)
        self.stacked_widget.addWidget(self.page_ocr_run)  # 0
        self.stacked_widget.addWidget(self.page_verify)  # 1
        self.stacked_widget.addWidget(self.page_settings)  # 2
        self.stacked_widget.addWidget(self.page_info)  # 3

    def _init_toolbar(self):
        toolbar = QToolBar("Main Navigation")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.setStyleSheet(TOOLBAR_STYLESHEET)

        self.addToolBar(toolbar)

        # 액션 그룹 (Radio 동작)
        self.nav_group = QActionGroup(self)
        self.nav_group.setExclusive(True)

        # 1. OCR 실행
        self.act_run = self._add_nav_action(
            toolbar, "OCR", IconFactory.play_icon("white"), PageIndex.OCR_RUN
        )

        # 2. 결과 검증
        self.act_verify = self._add_nav_action(
            toolbar, "결과 검증", IconFactory.list_icon("white"), PageIndex.VERIFY
        )

        # 3. 설정
        self.act_settings = self._add_nav_action(
            toolbar, "서식 설정", IconFactory.gear_icon("white"), PageIndex.SETTINGS
        )

        # Spacer (우측 정렬용)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        # 4. 도움말
        self.act_help = self._add_nav_action(
            toolbar, "도움말", IconFactory.help_icon("white"), PageIndex.INFO
        )

    def _add_nav_action(self, toolbar, text, icon, page_idx):
        action = QAction(text, self)
        action.setIcon(icon)
        action.setCheckable(True)
        # lambda의 변수 포획 문제 방지를 위해 page_idx=page_idx 사용 권장
        action.triggered.connect(
            lambda checked=False, idx=page_idx: self.switch_page(idx)
        )

        self.nav_group.addAction(action)
        toolbar.addAction(action)
        return action

    def _init_connections(self):
        self.page_ocr_run.ocr_finished_with_data.connect(self.on_ocr_finished)

    def _check_startup_state(self):
        # ProfileEditor가 가진 Manager를 통해 데이터 확인
        has_profiles = bool(self.page_settings.profile_manager.get_all_profile_names())

        if has_profiles:
            self.switch_page(PageIndex.OCR_RUN)
        else:
            self.switch_page(PageIndex.SETTINGS)

    # --- Slots & Logic ---

    def switch_page(self, page_idx):
        self.stacked_widget.setCurrentIndex(page_idx)

        # 코드로 페이지 전환 시 툴바 버튼 상태도 맞춰줌
        if page_idx == PageIndex.OCR_RUN:
            self.act_run.setChecked(True)
        elif page_idx == PageIndex.VERIFY:
            self.act_verify.setChecked(True)
        elif page_idx == PageIndex.SETTINGS:
            self.act_settings.setChecked(True)
        elif page_idx == PageIndex.INFO:
            self.act_help.setChecked(True)

    def on_ocr_finished(self, results):
        # 1. 데이터 전달
        self.page_verify.load_data_from_memory(results)

        # 2. 검증 페이지로 이동
        self.switch_page(PageIndex.VERIFY)
