import os
import sys
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QTextBrowser,
    QSplitter,
    QLabel,
    QListWidgetItem,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve


class InfoContent:
    @staticmethod
    def get_resource_path(file_name):
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, "resources/imgs", file_name).replace("\\", "/")

    @staticmethod
    def get_sections():
        """도움말 섹션 데이터 반환"""
        # 이미지 경로 미리 로드
        img_btn = InfoContent.get_resource_path("setting_menu_btn.png")
        img_menu01 = InfoContent.get_resource_path("setting_menu01.png")
        img_menu02 = InfoContent.get_resource_path("setting_menu02.png")
        img_ocr = InfoContent.get_resource_path("ocr_menu.png")
        img_verify = InfoContent.get_resource_path("verification_menu.png")

        return [
            {
                "title": "1. 프로그램 소개",
                "anchor": "intro",
                "html": f"""
                    <h2>1. 프로그램 소개</h2>
                    <p>이 프로그램은 민원 서류 이미지에서 원하는 데이터를 자동으로 추출(OCR)하고,<br>
                    엑셀 파일로 정리해주는 업무 자동화 도구입니다.</p>
                    <ul>
                        <li><b>서식 설정:</b> 어떤 위치의 글자를 읽을지 지정합니다.</li>
                        <li><b>일괄 처리:</b> 수백 장의 문서를 한 번에 처리합니다.</li>
                        <li><b>검증 및 저장:</b> 결과를 눈으로 확인하고 엑셀로 저장합니다.</li>
                    </ul>
                    <span>버전 이력</span>
                    <ul>
                        <li>v1.0 : 2026. 2. 6. 행정지원과 안민수</li>
                    </ul>
                    <hr>
                """,
            },
            {
                "title": "2. 사용 흐름 요약",
                "anchor": "process",
                "html": """
                    <h2>2. 프로그램 사용 흐름</h2>
                    <p>1. 스캔한 서류들에서 원하는 데이터를 추출하기 위해서 추출할 구역을 먼저 정해줘야 합니다.</p>
                    <ul>
                        <li>서식 설정 메뉴에서 샘플 서류를 불러온 후 추출하고자 하는 구역을 설정합니다.</li>
                        <li>각 구역의 이름을 지정합니다. (나중에 엑셀 헤더로 사용합니다.)</li>
                    </ul>
                    <p>2. 서식을 설정했다면 실제로 데이터를 추출해야합니다.</p>
                    <ul>
                        <li>OCR 메뉴에서 파일 또는 폴더로 추출 대상 서류를 선택합니다.</li>
                        <li>설정한 서식이 맞는지 확인한 후 추출을 실행합니다.</li>
                    </ul>
                    <p>3. OCR이 완료되면 추출결과를 표로 확인한 후 이상이 없다면 엑셀로 저장합니다.</p>
                    <ul>
                        <li>실제 추출한 이미지를 오른쪽에서 확인하며 잘못 추출된 데이터가 있다면 보정합니다.</li>
                        <li>한자 등의 데이터는 인식하지 못합니다.</li>
                        <li>확인이 끝나면 엑셀 파일로 저장합니다.</li>
                    </ul>
                    <br><hr>
                """,
            },
            {
                "title": "3. 서식 설정 방법",
                "anchor": "profile",
                "html": f"""
                    <h2>3. 서식 설정 방법</h2>
                    <p>OCR을 수행하기 전, 어디를 읽어야 할지 '서식 설정(프로파일)'을 만들어야 합니다.</p>
                    <ul>
                        <li><img src="{img_btn}"> 버튼을 눌러 설정화면으로 진입하세요.</li>
                        <li>상단의 <b>[신규 프로파일]</b> 버튼을 눌러 이름을 입력합니다.</li>
                        <br>
                        <img src="{img_menu01}" width="900">
                        <li><b>[이미지 불러오기]</b>로 샘플 서류 이미지를 엽니다.</li>
                        <li>마우스로 읽고 싶은 영역(ROI)을 드래그하여 박스를 그립니다.</li>
                        <li>우측 목록에서 영역의 이름을 알기 쉽게 수정합니다.</li>
                        <br>
                        <img src="{img_menu02}" width="900">
                        <i>※ 샘플 이미지입니다.</i>
                        <br>
                        <li><b>[프로파일 저장]</b>을 눌러 설정을 완료합니다.</li>
                        <li>키워드 설정을 통해 파일 제목에 따라 자동 분류도 가능합니다.</li>
                    </ul>
                    <br>
                    <p><i>Tip: 'OCR 테스트' 버튼을 눌러 잘 읽히는지 바로 확인해보세요!</i></p>
                    <hr>
                """,
            },
            {
                "title": "4. OCR 실행하기",
                "anchor": "run",
                "html": f"""
                    <h2>4. OCR 실행하기</h2>
                    <p>설정된 서식을 이용해 실제 파일들을 처리하는 단계입니다.</p>
                    <ul>
                        <li><b>[파일 추가]</b> 또는 <b>[폴더 추가]</b>로 이미지를 등록합니다.</li>
                        <li>서식 매칭 방법을 선택합니다. (보통 '수동' 사용)</li>
                        <li><b>[▶ 추출 시작]</b> 버튼을 누르면 작업이 시작됩니다.</li>
                        <br>
                        <img src="{img_ocr}" width="900">
                    </ul>
                    <br><hr>
                """,
            },
            {
                "title": "5. 결과 검증 및 저장",
                "anchor": "verify",
                "html": f"""
                    <h2>5. 결과 검증 및 저장</h2>
                    <p>추출한 내용에 오타가 없는지 확인하고 수정합니다.</p>
                    <ul>
                        <li>표의 셀을 클릭하면, 해당 내용의 <b>원본 이미지 위치</b>를 보여줍니다.</li>
                        <li>내용이 틀렸다면 표에서 직접 수정할 수 있습니다.</li>
                        <li>확인이 끝나면 상단의 <b>[💾 엑셀로 저장]</b> 버튼을 누르세요.</li>
                        <br>
                        <img src="{img_verify}" width="900">
                    </ul>
                """,
            },
        ]

    @staticmethod
    def get_css():
        return """
        <style>
            li { margin: 8px 0; }
            ul { margin-bottom: 10px; }
            img { image-rendering: -webkit-optimize-contrast; }
            h2 { border-bottom: 2px solid #0078D7; padding-bottom: 5px; }
        </style>
        """

    @staticmethod
    def get_footer():
        return """
        <br><hr>
        <div style='text-align: center; color: #888; font-size: 11px; margin-top: 20px;'>
            <p><b>Minwon OCR Automation Tool v1.0</b></p>
            <p>Copyright © 2026 Minsoo Ahn. All rights reserved.</p>
        </div>
        <br>
        """


TOC_LIST_STYLE = """
    QListWidget {
        background-color: #333333;
        border: 1px solid #ccc;
        border-radius: 8px;
        font-size: 14px;
        outline: 0;
    }
    QListWidget::item {
        padding: 8px;
        color: #ddd;
    }
    QListWidget::item:selected {
        background-color: #e0e0e0;
        color: #333;
        border-left: 3px solid #0078D7;
    }
    QListWidget::item:hover {
        background-color: #505050;
    }
"""

BROWSER_STYLE = """
    QTextBrowser {
        background: transparent;
        border-radius: 8px;
        padding: 10px 10px 10px 20px;
        line-height: 1.6;
    }
"""


class InfoPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_content()
        self._init_animation()

    def _init_animation(self):
        self._scroll_anim = QPropertyAnimation(
            self.content_browser.verticalScrollBar(), b"value"
        )
        self._scroll_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._scroll_anim.setDuration(500)

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Horizontal)

        left_widget = self._create_toc_panel()

        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)
        self.content_browser.setStyleSheet(BROWSER_STYLE)

        splitter.addWidget(left_widget)
        splitter.addWidget(self.content_browser)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 8)

        layout.addWidget(splitter)

    def _create_toc_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        lbl_toc = QLabel("📑 목차")
        lbl_toc.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        layout.addWidget(lbl_toc)

        self.toc_list = QListWidget()
        self.toc_list.setStyleSheet(TOC_LIST_STYLE)
        self.toc_list.itemClicked.connect(self.on_toc_clicked)
        layout.addWidget(self.toc_list)

        return panel

    def load_content(self):
        sections = InfoContent.get_sections()
        full_html = InfoContent.get_css() + "<h1>📖 사용 설명서</h1><br>"
        self.toc_list.clear()

        for section in sections:
            # 1. 목차 리스트 추가
            item = QListWidgetItem(section["title"])
            item.setData(Qt.UserRole, section["anchor"])
            self.toc_list.addItem(item)

            # 2. HTML 본문 추가 (앵커 포함)
            full_html += f"<a name='{section['anchor']}'></a>"
            full_html += section["html"]
            full_html += "<br><br>"

        full_html += InfoContent.get_footer()
        self.content_browser.setHtml(full_html)

    def on_toc_clicked(self, item):
        anchor_name = item.data(Qt.UserRole)
        if anchor_name:
            self.smooth_scroll_to_anchor(anchor_name)

    def smooth_scroll_to_anchor(self, anchor_name):
        v_bar = self.content_browser.verticalScrollBar()
        start_val = v_bar.value()

        # 목표 위치 계산을 위해 강제 이동 후 복귀
        self.content_browser.scrollToAnchor(anchor_name)
        end_val = v_bar.value()
        v_bar.setValue(start_val)

        if start_val != end_val:
            self._scroll_anim.stop()
            self._scroll_anim.setStartValue(start_val)
            self._scroll_anim.setEndValue(end_val)
            self._scroll_anim.start()
