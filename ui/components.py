from PySide6.QtWidgets import QPushButton, QTextEdit, QLabel, QProgressBar
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve


class ActionButton(QPushButton):
    PRESETS = {
        "default": {
            "bg": "#333333",
            "hover": "#555555",
            "pressed": "#777777",
            "text": "#f0f0f0",
            "border": "none",
        },
        "light": {
            "bg": "#f0f0f0",
            "hover": "#e0e0e0",
            "pressed": "#cccccc",
            "text": "#333333",
            "border": "1px solid #ccc",
        },
        "blue": {
            "bg": "#0078D7",
            "hover": "#1E88E5",
            "pressed": "#0D47A1",
            "text": "white",
            "border": "none",
        },
        "red": {
            "bg": "#D32F2F",
            "hover": "#E53935",
            "pressed": "#B71C1C",
            "text": "white",
            "border": "none",
        },
        "green": {
            "bg": "#4CAF50",
            "hover": "#66BB6A",
            "pressed": "#388E3C",
            "text": "#333333",
            "border": "none",
        },
    }

    def __init__(
        self, text, callback=None, enabled=True, preset="default", parent=None, **kwargs
    ):
        super().__init__(text, parent)

        self.setCursor(Qt.PointingHandCursor)
        self.setEnabled(enabled)

        if callback:
            self.clicked.connect(callback)

        style_config = self.PRESETS.get(preset, self.PRESETS["default"]).copy()

        if kwargs:
            style_config.update(kwargs)

        self._apply_stylesheet(style_config)

    def _apply_stylesheet(self, config):
        self.setStyleSheet(
            f"""
            QPushButton {{
                font-weight: 500;
                padding: 8px 12px; 
                border-radius: 4px;
                background-color: {config.get('bg')};
                color: {config.get('text')};
                border: {config.get('border', 'none')};
            }}
            QPushButton:hover {{
                background-color: {config.get('hover')};
            }}
            QPushButton:pressed {{
                background-color: {config.get('pressed')};
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
        self.ensureCursorVisible()


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
        self.setMinimumHeight(32)


class SmoothProgressBar(QProgressBar):
    STYLE_SHEET = """
        QProgressBar {
            height: 30px;
            border: 1px solid #bbb;
            border-radius: 6px;
            text-align: center;
            background-color: #e0e0e0;
            color: #333;
            font-weight: bold;
            font-size: 14px;
        }
        QProgressBar::chunk {
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, 
                                              stop:0 #66bb6a, stop:1 #43a047);
            border-radius: 5px;
            margin: 0.5px;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(self.STYLE_SHEET)
        self.animation = None

    def setValueSmooth(self, value):
        if self.animation and self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()

        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(value)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()
