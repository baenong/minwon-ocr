import os
import time
from PySide6.QtCore import QThread, Signal
from core.ocr_engine import OCREngine
from core.profile_manager import ProfileManager
from core.image_loader import ImageLoader


class BatchProcessor(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal(str)
    results_ready_signal = Signal(dict)

    def __init__(self, file_list, forced_profile_name=None):
        super().__init__()
        self.file_list = file_list
        self.forced_profile_name = forced_profile_name
        self.is_running = True

        # 엔진과 매니저 인스턴스 생성
        self.ocr_engine = OCREngine()
        self.profile_manager = ProfileManager()

        # 결과 저장용: { "프로파일이름": [ {row_data}, {row_data} ... ] }
        self.results = {}

    def run(self):
        total_files = len(self.file_list)
        self.log_signal.emit(f">>> 작업 시작: 총 {total_files}개 파일")

        processed_count = 0

        # 프로파일 이름 목록 미리 로드
        profile_names = self.profile_manager.get_all_profile_names()

        for file_path in self.file_list:
            if not self.is_running:
                break

            filename = os.path.basename(file_path)
            target_profile_name = None

            # [로직 1] 프로파일 결정 (수동 vs 자동)
            if self.forced_profile_name:
                target_profile_name = self.forced_profile_name
            else:
                # 자동 매칭 (키워드 검색)
                for name in profile_names:
                    p_data = self.profile_manager.get_profile(name)
                    keywords = p_data.get("keywords", [])
                    if any(k in filename for k in keywords):
                        target_profile_name = name
                        break

            if not target_profile_name:
                self.log_signal.emit(f"[SKIP] 매칭 실패: {filename}")
                processed_count += 1
                self.progress_signal.emit(int(processed_count / total_files * 100))
                continue

            # [로직 2] 이미지 로드 및 스케일링 적용 OCR
            try:
                self.log_signal.emit(f"[처리 중] {filename} -> {target_profile_name}")

                # 프로파일 데이터 로드
                profile_data = self.profile_manager.get_profile(target_profile_name)
                rois = profile_data["rois"]

                img = ImageLoader.load_image(file_path)

                # 현재 이미지 크기
                curr_h, curr_w = img.shape[:2]
                row_data = {
                    "파일명": filename,
                    "full_path": file_path,
                }

                for roi in rois:
                    # 좌표 보정
                    final_x = int(roi["x"] * curr_w)
                    final_y = int(roi["y"] * curr_h)
                    final_w = int(roi["w"] * curr_w)
                    final_h = int(roi["h"] * curr_h)

                    col_name = roi["col_name"]
                    text = self.ocr_engine.extract_text_from_roi(
                        img, final_x, final_y, final_w, final_h
                    )
                    row_data[col_name] = text

                if target_profile_name not in self.results:
                    self.results[target_profile_name] = []
                self.results[target_profile_name].append(row_data)

            except Exception as e:
                self.log_signal.emit(f"[ERROR] {filename}: {e}")

            processed_count += 1
            self.progress_signal.emit(int(processed_count / total_files * 100))

        time.sleep(1)
        self.results_ready_signal.emit(self.results)
        self.finished_signal.emit(
            "OCR 추출이 완료되었습니다. 검증 화면으로 이동합니다."
        )

    def stop(self):
        self.is_running = False
