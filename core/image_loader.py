import os
import cv2
import numpy as np
import fitz


class ImageLoader:
    @staticmethod
    def load_image(file_path):
        if not os.path.exists(file_path):
            return None

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            return ImageLoader._pdf_to_image(file_path)

        try:
            img_array = np.fromfile(file_path, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return img

        except Exception as e:
            print(f"이미지를 불러올 수 없습니다: {e}")
            return None

    @staticmethod
    def _pdf_to_image(pdf_path):
        doc = fitz.open(pdf_path)

        try:
            if len(doc) > 0:
                page = doc.load_page(0)
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

                return img_cv
        except Exception as e:
            print(f"PDF 변환 오류: {e}")
            return None
