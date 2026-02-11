class AppConfig:
    APP_NAME = "Minwon OCR Automation Tool"
    SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".pdf", ".bmp")

    _ext_str = " ".join([f"*{ext}" for ext in SUPPORTED_EXTENSIONS])
    FILE_DIALOG_FILTER = f"Images ({_ext_str});;All Files (*)"

    EXCEL_FILTER = "Excel Files (*.xlsx)"
