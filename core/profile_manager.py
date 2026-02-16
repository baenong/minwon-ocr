import json
from pathlib import Path
from typing import Dict, List, Any, Optional, TypedDict, Tuple, Union


class RoiData(TypedDict):
    col_name: str
    x: float
    y: float
    w: float
    h: float
    dtype: str


class ProfileData(TypedDict):
    keywords: List[str]
    rois: List[RoiData]
    ref_w: int
    ref_h: int
    sample_image_path: str
    template_path: str


class ProfileManager:
    def __init__(self, filename: str = "profiles.json"):
        self.file_path = Path(filename)
        self.profiles: Dict[str, ProfileData] = {}
        self.load_profiles()

    def load_profiles(self) -> None:
        if not self.file_path.exists():
            self.profiles = {}
            return

        try:
            with self.file_path.open("r", encoding="utf-8") as f:
                self.profiles = json.load(f)
        except Exception as e:
            print(f"프로파일 로드 실패: {e}")
            self.profiles = {}

    def save_profiles(self):
        try:
            with self.file_path.open("w", encoding="utf-8") as f:
                json.dump(self.profiles, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"프로파일 저장 실패: {e}")
            return False

    def get_all_profile_names(self) -> List[str]:
        return list(self.profiles.keys())

    def get_profile(self, name: str) -> Optional[ProfileData]:
        return self.profiles.get(name)

    def add_profile(
        self,
        name: str,
        keywords: List[str],
        roi_pixels: List[Dict[str, Any]],
        ref_w=0,
        ref_h=0,
        image_path: str = "",
        template_path: str = "",
    ) -> bool:
        rois_ratio: List[RoiData] = []

        if not roi_pixels:
            rois_ratio = []
        else:
            if ref_w <= 0 or ref_h <= 0:
                print("Error: 기준 해상도 없이 ROI를 저장할 수 없습니다.")
                return False

            for r in roi_pixels:
                if r["x"] < 1.0 and r["w"] < 1.0:
                    rois_ratio.append(r)
                else:
                    # 픽셀 -> 비율 변환 (소수점 6자리)
                    rois_ratio.append(
                        {
                            "col_name": r["col_name"],
                            "x": round(r["x"], 6),
                            "y": round(r["y"], 6),
                            "w": round(r["w"], 6),
                            "h": round(r["h"], 6),
                        }
                    )

        self.profiles[name] = {
            "keywords": keywords,
            "rois": rois_ratio,  # 비율로 저장됨
            "ref_w": ref_w,
            "ref_h": ref_h,
            "sample_image_path": image_path,
            "template_path": template_path,
        }
        return self.save_profiles()

    def delete_profile(self, name: str) -> bool:
        if name in self.profiles:
            del self.profiles[name]
            return self.save_profiles()
        return False

    def reorder_profiles(self, new_name_list: List[str]) -> None:
        new_profiles = {}
        for name in new_name_list:
            if name in self.profiles:
                new_profiles[name] = self.profiles[name]

        for k, v in self.profiles.items():
            if k not in new_profiles:
                new_profiles[k] = v

        self.profiles = new_profiles
        self.save_profiles()

    # 전체 프로파일 백업
    def export_all_profiles(self, file_path: Union[str, Path]) -> bool:
        export_data = {"version": "1.0", "type": "full", "profiles": self.profiles}
        return self._write_json(str(file_path), export_data)

    # 단일 서식 내보내기
    def export_profile(self, name: str, file_path: Union[str, Path]) -> bool:
        if name not in self.profiles:
            return False

        export_data = {
            "version": "1.0",
            "type": "single",
            "profiles": {name: self.profiles[name]},
        }
        return self._write_json(str(file_path), export_data)

    def _write_json(self, file_path: str, data: Dict) -> bool:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] Export 실패: {e}")
            return False

    def import_profiles(self, file_path: str) -> Tuple[str, int, Any]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            imported_profiles = data.get("profiles", {})
            import_type = data.get("type", "single")

            # 덮어쓰기
            if import_type == "full":
                self.profiles = imported_profiles
                self.save_profiles()
                return "REPLACED", len(self.profiles), "full"

            # 기존 프로파일 목록에 추가
            imported_count = 0
            imported_names = []

            for name, content in imported_profiles.items():
                final_name = name

                while final_name in self.profiles:
                    final_name += "_(Imported)"

                self.profiles[final_name] = content
                imported_names.append(final_name)
                imported_count += 1

            self.save_profiles()
            return "MERGED", imported_count, imported_names

        except Exception as e:
            print(f"Import Error: {e}")
            return 0, []
