from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QDialogButtonBox,
    QFormLayout,
)
from PySide6.QtCore import Qt


class KeywordSettingsDialog(QDialog):
    READONLY_STYLE = "background-color: #f0f0f0; color: #555; padding: 5px; border: 1px solid #ccc; border-radius: 4px;"
    INPUT_STYLE = "padding: 5px; border: 1px solid #ccc; border-radius: 4px;"

    def __init__(self, current_name="", current_keywords=[], parent=None):
        super().__init__(parent)
        self.setWindowTitle("프로파일 키워드 설정")

        self.current_name = current_name
        self.current_keywords = current_keywords if current_keywords else []

        self.init_ui()

    def init_ui(self):
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.name_edit = QLineEdit(self.current_name)
        self.name_edit.setReadOnly(True)
        self.name_edit.setStyleSheet(self.READONLY_STYLE)
        form_layout.addRow("프로파일 이름:", self.name_edit)

        self.keywords_edit = QLineEdit(", ".join(self.current_keywords))
        self.keywords_edit.setPlaceholderText("예: 가족관계, 증명서, 등본")
        self.keywords_edit.setStyleSheet(self.INPUT_STYLE)
        form_layout.addRow("매칭 키워드:", self.keywords_edit)

        layout.addLayout(form_layout)

        lbl_tip = QLabel(
            "※ 파일명에 해당 키워드가 포함되어 있으면 자동으로 이 서식이 적용됩니다.\n(여러 개일 경우 쉼표로 구분)"
        )
        lbl_tip.setStyleSheet("color: #666; font-size: 12px; margin-left: 5px;")
        layout.addWidget(lbl_tip)

        layout.addStretch()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.buttons.setCenterButtons(True)
        layout.addWidget(self.buttons)

    def get_keywords(self):
        text = self.keywords_edit.text()
        raw_list = [k.strip() for k in text.split(",") if k.strip()]
        unique_list = list(dict.fromkeys(raw_list))

        return unique_list
