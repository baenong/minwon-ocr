import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from PySide6.QtCore import QThread, Signal

from core.ocr_engine import OCREngine
from core.profile_manager import ProfileManager
from core.image_loader import ImageLoader


class BatchProcessor(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal(str)
    results_ready_signal = Signal(dict)

    def __init__(self, file_list: List[str], forced_profile_name: Optional[str] = None):
        super().__init__()
        self.file_list = [Path(f) for f in file_list]
        self.forced_profile_name = forced_profile_name
        self.is_running = True

        # 엔진과 매니저 인스턴스 생성
        self.ocr_engine = OCREngine()
        self.profile_manager = ProfileManager()

        # 결과 저장용: { "프로파일이름": [ {row_data}, {row_data} ... ] }
        self.results: Dict[str, List[Dict[str, Any]]] = {}

    def run(self):
        total_files = len(self.file_list)
        self.log_signal.emit(f">>> 작업 시작: 총 {total_files}개 파일")

        processed_count = 0

        # 프로파일 이름 목록 미리 로드
        profile_names = self.profile_manager.get_all_profile_names()

        for file_path in self.file_list:
            if not self.is_running:
                break

            filename = file_path.name
            target_profile_name = self._determine_profile(filename, profile_names)

            if not target_profile_name:
                self.log_signal.emit(f"[SKIP] 매칭 실패: {filename}")
                processed_count += 1
                self._emit_progress(processed_count, total_files)
                continue

            self.log_signal.emit(f"[처리 중] {filename} -> {target_profile_name}")

            # 프로파일 데이터 로드
            row_data = self._process_single_file(file_path, target_profile_name)

            if row_data:
                if target_profile_name not in self.results:
                    self.results[target_profile_name] = []
                self.results[target_profile_name].append(row_data)

            processed_count += 1
            self._emit_progress(processed_count, total_files)

            # 너무 빠른 루프 방지 및 UI 반응성 확보
            time.sleep(0.05)

        if self.is_running:
            self.results_ready_signal.emit(self.results)
            self.finished_signal.emit(
                "OCR 추출이 완료되었습니다. 검증 화면으로 이동합니다."
            )
        else:
            self.finished_signal.emit("작업이 사용자에 의해 중단되었습니다.")

    def stop(self):
        self.is_running = False

    def _determine_profile(
        self, filename: str, profile_names: List[str]
    ) -> Optional[str]:
        if self.forced_profile_name:
            return self.forced_profile_name

        for name in profile_names:
            profile_data = self.profile_manager.get_profile(name)
            keywords = profile_data.get("keywords", [])
            if any(k in filename for k in keywords):
                return name
        return None

    def _process_single_file(
        self, file_path: Path, profile_name: str
    ) -> Optional[Dict[str, Any]]:
        try:
            # 프로파일 데이터 로드
            profile_data = self.profile_manager.get_profile(profile_name)
            if not profile_data:
                return None

            rois = profile_data.get("rois", [])

            # 이미지 로드
            img = ImageLoader.load_image(str(file_path))
            if img is None:
                self.log_signal.emit(f"[ERROR] 이미지 로드 실패: {file_path.name}")
                return None

            curr_h, curr_w = img.shape[:2]

            row_data = {
                "파일명": file_path.name,
                "full_path": str(file_path),
            }

            for roi in rois:
                # 중지 요청 시 즉시 중단 (긴 작업 방지)
                if not self.is_running:
                    return None

                # 좌표 계산
                final_x = int(roi["x"] * curr_w)
                final_y = int(roi["y"] * curr_h)
                final_w = int(roi["w"] * curr_w)
                final_h = int(roi["h"] * curr_h)

                col_name = roi["col_name"]

                # OCR 엔진 호출
                text = self.ocr_engine.extract_text_from_roi(
                    img, final_x, final_y, final_w, final_h
                )
                row_data[col_name] = text

            return row_data

        except Exception as e:
            self.log_signal.emit(f"[ERROR] {file_path.name} 처리 중 오류: {e}")
            return None

    def _emit_progress(self, current: int, total: int):
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_signal.emit(percent)
