from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QDialogButtonBox,
)


class KeywordSettingsDialog(QDialog):
    def __init__(self, current_name="", current_keywords=[], parent=None):
        super().__init__(parent)
        self.setWindowTitle("프로파일 설정")
        self.resize(400, 180)

        layout = QVBoxLayout(self)

        # 프로파일 이름 (수정 불가능하게 보여주기만 함, 혹은 수정 가능하게 할 수도 있음)
        layout.addWidget(QLabel("프로파일 이름:"))
        self.name_edit = QLineEdit(current_name)
        self.name_edit.setReadOnly(True)  # 이름은 키값이라 변경 막음 (필요시 해제)
        self.name_edit.setStyleSheet("background-color: #f0f0f0; color: #555;")
        layout.addWidget(self.name_edit)

        # 키워드 입력
        layout.addWidget(QLabel("매칭 키워드 (쉼표 ','로 구분):"))
        self.keywords_edit = QLineEdit(", ".join(current_keywords))
        self.keywords_edit.setPlaceholderText("예: 가족관계, 증명서")
        layout.addWidget(self.keywords_edit)

        # 버튼
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_keywords(self):
        text = self.keywords_edit.text()
        return [k.strip() for k in text.split(",") if k.strip()]
