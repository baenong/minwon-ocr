import json
import os


class ProfileManager:
    def __init__(self, filename="profiles.json"):
        self.filename = filename
        self.profiles = {}
        self.load_profiles()

    def load_profiles(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    self.profiles = json.load(f)
            except Exception as e:
                print(f"프로파일 로드 실패: {e}")
                self.profiles = {}
        else:
            self.profiles = {}

    def save_profiles(self):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"프로파일 저장 실패: {e}")
            return False

    def get_all_profile_names(self):
        return list(self.profiles.keys())

    def add_profile(self, name, keywords, roi_pixels, ref_w=0, ref_h=0, image_path=""):
        rois_ratio = []

        if not roi_pixels:
            rois_ratio = []
        else:
            # ROI가 있는데 기준 해상도가 없으면 계산 불가 (방어 코드)
            if ref_w <= 0 or ref_h <= 0:
                print("Error: 기준 해상도 없이 ROI를 저장할 수 없습니다.")
                return False

            for r in roi_pixels:
                # 이미 비율(1.0 미만)인 경우 그대로 사용 (중복 변환 방지)
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
        }
        return self.save_profiles()

    def delete_profile(self, name):
        if name in self.profiles:
            del self.profiles[name]
            return self.save_profiles()
        return False

    def reorder_profiles(self, new_name_list):
        new_profiles = {}
        for name in new_name_list:
            if name in self.profiles:
                new_profiles[name] = self.profiles[name]

        self.profiles = new_profiles
        self.save_profiles()

    def get_profile(self, name):
        return self.profiles.get(name)

    # 전체 프로파일 백업
    def export_all_profiles(self, file_path):
        export_data = {"version": "1.0", "type": "full", "profiles": self.profiles}
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Export All Error: {e}")
            return False

    # 단일 서식 내보내기
    def export_profile(self, name, file_path):
        if name not in self.profiles:
            return False

        export_data = {
            "version": "1.0",
            "type": "single",
            "profiles": {name: self.profiles[name]},
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Export Error: {e}")
            return False

    def import_profiles(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            imported_profiles = data.get("profiles", {})
            import_type = data.get("type", "single")

            if import_type == "full":
                self.profiles = imported_profiles  # 덮어쓰기
                self.save_profiles()
                return "REPLACED", len(self.profiles), "full"

            else:
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
