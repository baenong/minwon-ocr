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

    def load_image(self, image_path):
        img_array = np.fromfile(image_path, np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if image is None:
            raise FileNotFoundError(f"이미지를 불러올 수 없습니다: {image_path}")

        # binary = self._apply_processing(image)
        return image
        # return image, binary

    def pdf_to_images(self, pdf_path):
        doc = fitz.open(pdf_path)
        processed_images = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)  # 고화질 변환

            # PyMuPDF 이미지를 OpenCV 포맷으로 변환
            img_data = np.frombuffer(pix.samples, dtype=np.uint8)

            # RGB to BGR (OpenCV는 BGR 사용)
            if pix.n >= 3:
                img_data = img_data.reshape(pix.h, pix.w, pix.n)
                img_cv = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
            else:
                img_data = img_data.reshape(pix.h, pix.w)
                img_cv = cv2.cvtColor(img_data, cv2.COLOR_GRAY2BGR)

            # binary = self._apply_processing(img_cv)
            processed_images.append(img_cv)

        return processed_images

    def get_display_image(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            try:
                doc = fitz.open(file_path)
                if len(doc) > 0:
                    page = doc.load_page(0)
                    pix = page.get_pixmap(dpi=200)
                    img_data = np.frombuffer(pix.samples, dtype=np.uint8)

                    if pix.n >= 3:
                        img_data = img_data.reshape(pix.h, pix.w, pix.n)
                        return cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
                    else:
                        img_data = img_data.reshape(pix.h, pix.w)
                        return cv2.cvtColor(img_data, cv2.COLOR_GRAY2BGR)
            except Exception as e:
                print(f"PDF Display Error: {e}")
                return None

        else:
            try:
                img_array = np.fromfile(file_path, np.uint8)
                return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            except Exception:
                return None

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
