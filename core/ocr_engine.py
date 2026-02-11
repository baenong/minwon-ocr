import sys
import os
import pytesseract
import cv2
import numpy as np
import fitz


class OCREngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OCREngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.tesseract_cmd = self._get_tesseract_path()
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        self.default_config = r"--oem 3 --psm 6 -l kor+eng"
        self._initialized = True

    def _get_tesseract_path(self):
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, "tesseract_bin", "tesseract.exe")

    def _preprocess_roi_for_ocr(self, roi_img):
        if len(roi_img.shape) == 3:
            gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi_img

        # 확대
        scale_percent = 300
        width = int(gray.shape[1] * scale_percent / 100)
        height = int(gray.shape[0] * scale_percent / 100)
        dim = (width, height)

        # 보간
        resized = cv2.resize(gray, dim, interpolation=cv2.INTER_CUBIC)

        # 이진화
        binary = cv2.adaptiveThreshold(
            resized,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,  # Block Size
            11,  # C 상수
        )

        # 모폴로지
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
        return closing

    def extract_text_from_roi(self, image, x, y, w, h):
        h_img, w_img = image.shape[:2]
        x = max(0, min(x, w_img - 1))
        y = max(0, min(y, h_img - 1))
        w = max(1, min(w, w_img - x))
        h = max(1, min(h, h_img - y))

        roi = image[y : y + h, x : x + w]
        processed_roi = self._preprocess_roi_for_ocr(roi)
        custom_config = r"--oem 3 --psm 7 -l kor+eng"

        text = pytesseract.image_to_string(processed_roi, config=custom_config)
        return text.strip().replace(" ", "")
