from dataclasses import dataclass
from typing import Final, Tuple


@dataclass(frozen=True)
class AppConfig:
    APP_NAME: Final[str] = "Minwon OCR Automation Tool"

    # ext
    IMG_EXTS: Final[Tuple[str, ...]] = (".png", ".jpg", ".jpeg", ".pdf")
    EXCEL_EXTS: Final[Tuple[str, ...]] = (".xlsx", ".xls")
    JSON_EXTS: Final[Tuple[str, ...]] = (".json",)

    @staticmethod
    def _make_filter(name: str, exts: Tuple[str, ...]):
        # 예: (".png", ".jpg") -> "*.png *.jpg"
        wildcards = " ".join([f"*{ext}" for ext in exts])
        return f"{name} ({wildcards})"

    FILTER_IMAGE: Final[str] = _make_filter.__func__("Images", IMG_EXTS)
    FILTER_EXCEL: Final[str] = _make_filter.__func__("Excel Files", EXCEL_EXTS)
    FILTER_JSON: Final[str] = _make_filter.__func__("JSON Files", JSON_EXTS)
    FILTER_ALL: Final[str] = "All Files (*)"
