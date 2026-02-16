import cv2
import numpy as np


# Template Matching / Document Registration
class ImageAligner:
    MAX_FEATURES = 2000
    GOOD_MATCH_PERCENT = 0.15

    @staticmethod
    def align_images(target_img, template_img):
        """
        target_img : 정렬 대상 이미지 (스캔본)
        template_img : 기준 이미지 (서식 원본)
        반환값 : 정렬된 이미지, 변환 행렬
        """

        try:
            # 1. 흑백 변환
            target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)

            # 2. 특징점 감지기(ORB) 생성
            orb = cv2.ORB_create(ImageAligner.MAX_FEATURES)

            # 3. 특징점(Keypoints)과 기술자(Descriptors) 검출
            keypoints1, descriptors1 = orb.detectAndCompute(target_gray, None)
            keypoints2, descriptors2 = orb.detectAndCompute(template_gray, None)

            # 4. 특징점 매칭 (Hamming 거리 사용)
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = matcher.match(descriptors1, descriptors2, None)

            # 5. 매칭 결과를 거리 순으로 정렬 (상위 N%만 사용)
            matches = sorted(matches, key=lambda x: x.distance)
            num_good_matches = int(len(matches) * ImageAligner.GOOD_MATCH_PERCENT)
            matches = matches[:num_good_matches]

            if len(matches) < 4:
                print("[WARNING] 특징점이 부족하여 정렬을 수행할 수 없습니다.")
                return target_img, None

            # 6. 매칭된 점들의 좌표 추출
            points1 = np.zeros((len(matches), 2), dtype=np.float32)
            points2 = np.zeros((len(matches), 2), dtype=np.float32)

            for i, match in enumerate(matches):
                points1[i, :] = keypoints1[match.queryIdx].pt
                points2[i, :] = keypoints2[match.trainIdx].pt

            # 7. 호모그래피(Homography) 행렬 계산
            # RANSAC 알고리즘을 사용하여 이상치(Outlier) 제거
            h, mask = cv2.findHomography(points1, points2, cv2.RANSAC)

            if h is None:
                print("[WARNING] 정렬 실패: 호모그래피 행렬을 찾을 수 없음")
                return target_img, None

            # 8. 원근 변환 적용 (이미지 펴기)
            height, width = template_img.shape[:2]
            im1Reg = cv2.warpPerspective(target_img, h, (width, height))

            return im1Reg, h

        except Exception as e:
            print(f"[ERROR] 이미지 정렬 중 오류: {e}")
            return target_img, None
