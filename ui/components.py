from PySide6.QtWidgets import QPushButton, QTextEdit, QLabel, QProgressBar
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve


class ActionButton(QPushButton):
    def __init__(
        self,
        text,
        callback=None,
        bg_color="#333333",
        hover_color="#555555",
        pressed_color="#777777",
        text_color="#f0f0f0",
        enabled=True,
        preset=None,
        parent=None,
    ):
        super().__init__(text, parent)

        self.setCursor(Qt.PointingHandCursor)
        self.setEnabled(enabled)

        if callback:
            self.clicked.connect(callback)

        border_style = (
            "border: 1px solid #ccc;" if bg_color == "#f0f0f0" else "border: none;"
        )

        if preset:
            if preset == "blue":
                bg_color = "#0078D7"
                hover_color = "#1E88E5"
                pressed_color = "#0D47A1"
                text_color = "white"
            elif preset == "red":
                bg_color = "#D32F2F"
                hover_color = "#E53935"
                pressed_color = "#B71C1C"
                text_color = "white"
            elif preset == "green":
                bg_color = "#4CAF50"
                hover_color = "#66BB6A"
                pressed_color = "#388E3C"
                text_color = "#333333"

        self.setStyleSheet(
            f"""
            QPushButton {{
                font-weight: 500;
                padding: 8px 12px; 
                border-radius: 4px;
                background-color: {bg_color};
                color: {text_color};
                {border_style}
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}

            QPushButton:disabled {{
                background-color: #cccccc;  
                color: #888888;             
                border: 1px solid #aaaaaa; 
            }}
        """
        )


class LogView(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setReadOnly(True)
        self.setStyleSheet(
            """
            QTextEdit {
                background-color: #333333; 
                color: #81c147; 
                font-family: Consolas, 'Malgun Gothic';
                font-size: 12px;
                line-height: 1.4;
                padding: 8px 16px;
                border: 1px solid #555;
                border-radius: 4px;
            }
        """
        )

    def append_log(self, text):
        self.append(text)
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())


class TitleLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            """
            QLabel {
                font-weight: 500;
                font-size: 14px;
            }
            """
        )
        self.setFixedHeight(32)


class SmoothProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            """
            QProgressBar {
                height: 30px;              /* 높이 */
                border: 1px solid #bbb;
                border-radius: 6px;
                text-align: center;
                background-color: #e0e0e0; /* 배경색 (연한 회색) */
                color: #333;               /* 글자색 */
                font-weight: bold;
                font-size: 14px;
            }
            QProgressBar::chunk {
                /* 그라데이션으로 광택 효과 내기 */
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, 
                                                  stop:0 #66bb6a, stop:1 #43a047);
                border-radius: 5px;
                margin: 0.5px; /* 약간의 여백으로 둥근 느낌 강조 */
            }
        """
        )

    def setValueSmooth(self, value):
        if hasattr(self, "animation"):
            self.animation.stop()

        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(value)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()
