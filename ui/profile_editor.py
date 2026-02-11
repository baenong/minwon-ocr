import os
from pathlib import Path
import copy
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QLabel,
    QLineEdit,
    QSplitter,
    QMessageBox,
    QInputDialog,
    QFileDialog,
    QListWidgetItem,
)
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtCore import Qt, QSize, QEvent

from core.profile_manager import ProfileManager
from core.ocr_engine import OCREngine
from core.constants import AppConfig
from core.image_loader import ImageLoader
from ui.editor_widget import ROISelector
from ui.profile_dialog import KeywordSettingsDialog
from ui.components import ActionButton, LogView, TitleLabel


# [1] 프로파일 목록용 (단순 라벨 + 삭제 버튼)
class ProfileItemWidget(QWidget):
    def __init__(self, text, delete_callback):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        self.label = QLabel(text)
        self.label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.label)

        self.btn_delete = QPushButton("❌")
        self.btn_delete.setFixedSize(28, 24)
        self.btn_delete.setFlat(True)
        self.btn_delete.setToolTip("삭제")
        self.btn_delete.clicked.connect(lambda checked: delete_callback())
        layout.addWidget(self.btn_delete)


# [2] ROI 목록용 (입력창 + 삭제 버튼 + 이벤트 필터)
class ROIItemWidget(QWidget):
    def __init__(self, text, change_callback, delete_callback, select_callback=None):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.select_callback = select_callback

        self.name_edit = QLineEdit(text)
        self.name_edit.setStyleSheet(
            "border: 1px solid transparent; background: transparent;"
        )
        self.name_edit.setPlaceholderText("이름 입력")

        # 클릭 시 선택 처리를 위한 이벤트 필터
        self.name_edit.installEventFilter(self)
        self.name_edit.editingFinished.connect(
            lambda: change_callback(self.name_edit.text())
        )

        layout.addWidget(self.name_edit)

        self.btn_delete = QPushButton("❌")
        self.btn_delete.setFixedSize(28, 24)
        self.btn_delete.setFlat(True)
        self.btn_delete.setToolTip("삭제")
        self.btn_delete.clicked.connect(lambda checked: delete_callback())
        layout.addWidget(self.btn_delete)

    def eventFilter(self, obj, event):
        if obj == self.name_edit and event.type() == QEvent.MouseButtonPress:
            if self.select_callback:
                self.select_callback()
        return super().eventFilter(obj, event)


class ProfileEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.profile_manager = ProfileManager()
        self.ocr_engine = OCREngine()

        self.current_image = None
        self.current_image_path = None

        self.rois = []
        self.undo_stack = []
        self.is_modified = False
        self.last_selected_item = None

        self.init_ui()
        self.load_profile_list()

    def init_ui(self):
        main_layout = QVBoxLayout(self)  # 전체를 수직으로 (상단 바 + 하단 3분할)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        main_layout.addLayout(self._create_top_toolbar())

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self._create_left_panel())
        self.splitter.addWidget(self._create_center_panel())
        self.splitter.addWidget(self._create_right_panel())
        self.splitter.setSizes([220, 580, 300])  # 비율 조정

        main_layout.addWidget(self.splitter)

    # UI Create

    def _create_top_toolbar(self):
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("<h2>서식 설정 관리자</h2>"))  # 타이틀 (선택사항)
        top_bar.addStretch()  # 버튼들을 우측으로 밀기

        # 버튼 스타일 통일
        self.btn_keyword = ActionButton(
            text=" 키워드 설정", callback=self.open_keyword_dialog
        )

        self.btn_backup = ActionButton("백업", self.backup_profiles)
        self.btn_export = ActionButton("내보내기", self.export_current_profile)
        self.btn_import = ActionButton("불러오기", self.import_external_profile)

        self.btn_new = ActionButton(
            text="📄 신규 프로파일", callback=self.create_new_profile, preset="blue"
        )

        self.btn_save = ActionButton(
            text="💾 프로파일 저장", callback=self.save_current_profile, preset="green"
        )

        self.lbl_guide = QLabel(
            "샘플 이미지를 불러온 후 추출할 영역을 드래그하여 설정합니다."
        )
        self.lbl_guide.setStyleSheet("margin-top: 5px; color: #ff7f00;")

        top_bar.addWidget(self.btn_keyword)
        top_bar.addWidget(self.btn_backup)
        top_bar.addWidget(self.btn_export)
        top_bar.addWidget(self.btn_import)

        top_bar.addWidget(self.btn_new)
        top_bar.addWidget(self.btn_save)

        return top_bar

    def _create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(TitleLabel("📂 프로파일 목록"))

        self.profile_list_widget = QListWidget()
        self.profile_list_widget.itemClicked.connect(self.load_selected_profile)
        layout.addWidget(self.profile_list_widget)

        # 순서 조정 버튼 (삭제 버튼은 리스트 내부로 이동했으므로 여기선 제거)
        order_layout = QHBoxLayout()
        self.btn_up = QPushButton("▲")
        self.btn_up.clicked.connect(lambda: self.move_profile_order(-1))
        self.btn_down = QPushButton("▼")
        self.btn_down.clicked.connect(lambda: self.move_profile_order(1))
        order_layout.addWidget(self.btn_up)
        order_layout.addWidget(self.btn_down)
        layout.addLayout(order_layout)

        return panel

    def _create_center_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        img_bar = QHBoxLayout()

        self.btn_load_img = ActionButton("샘플 불러오기", self.load_image_file)
        self.lbl_img_name = QLabel("선택된 이미지 없음")

        img_bar.addWidget(TitleLabel("✏️ 샘플 이미지"))
        img_bar.addStretch()
        img_bar.addWidget(self.lbl_img_name)
        img_bar.addSpacing(10)
        img_bar.addWidget(self.btn_load_img)
        layout.addLayout(img_bar)

        self.editor = ROISelector()
        self.editor.roi_added.connect(self.on_roi_added)
        layout.addWidget(self.editor)

        return panel

    def _create_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # ROI 목록
        layout.addWidget(TitleLabel("🔧 추출 영역(ROI) 목록"))

        self.roi_list_widget = QListWidget()
        self.roi_list_widget.currentRowChanged.connect(self.on_roi_selection_changed)
        layout.addWidget(self.roi_list_widget)

        roi_order_layout = QHBoxLayout()
        self.btn_roi_up = QPushButton("▲")
        self.btn_roi_up.clicked.connect(lambda: self.move_roi_order(-1))
        self.btn_roi_down = QPushButton("▼")
        self.btn_roi_down.clicked.connect(lambda: self.move_roi_order(1))
        roi_order_layout.addWidget(self.btn_roi_up)
        roi_order_layout.addWidget(self.btn_roi_down)
        layout.addLayout(roi_order_layout)

        # OCR 테스트 로그
        layout.addSpacing(10)
        log_header = QHBoxLayout()
        log_header.addWidget(TitleLabel("📝 결과"))
        self.btn_test_all = ActionButton("OCR 테스트", self.test_all_rois, preset="red")

        log_header.addWidget(self.btn_test_all)
        layout.addLayout(log_header)

        self.log_view = LogView()
        layout.addWidget(self.log_view)

        return panel

    def _init_shortcuts(self):
        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_current_profile)

        self.shortcut_del_roi = QShortcut(QKeySequence("Delete"), self)
        self.shortcut_del_roi.activated.connect(self.delete_selected_roi_shortcut)

        self.shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.shortcut_undo.activated.connect(self.undo_last_action)

    # UI Update

    def _create_roi_data(self, name, x, y, w, h, img_w, img_h):
        return {
            "col_name": name,
            "x": x / img_w,
            "y": y / img_h,
            "w": w / img_w,
            "h": h / img_h,
        }

    def clear_editor(self):
        if self.rois:
            self.save_state_for_undo()
            self.mark_as_modified()

        self.rois = []
        self.refresh_roi_list()
        self.log_view.clear()
        if self.current_image is not None:
            self.redraw_all_boxes()
        else:
            self.editor.scene.clear()

    def move_profile_order(self, direction):
        row = self.profile_list_widget.currentRow()
        names = self.profile_manager.get_all_profile_names()
        if 0 <= row + direction < len(names):
            names[row], names[row + direction] = names[row + direction], names[row]
            self.profile_manager.reorder_profiles(names)
            self.load_profile_list()
            self.profile_list_widget.setCurrentRow(row + direction)

    def move_roi_order(self, direction):
        row = self.roi_list_widget.currentRow()
        if 0 <= row + direction < len(self.rois):
            self.save_state_for_undo()
            self.mark_as_modified()

            self.rois[row], self.rois[row + direction] = (
                self.rois[row + direction],
                self.rois[row],
            )

            self.refresh_roi_list()
            self.redraw_all_boxes()

            new_row = row + direction
            self.roi_list_widget.setCurrentRow(new_row)
            self.editor.highlight_roi_by_index(new_row)

    def refresh_roi_list(self):
        self.roi_list_widget.clear()
        self.roi_list_widget.blockSignals(True)

        for idx, roi in enumerate(self.rois):
            item = QListWidgetItem(self.roi_list_widget)
            item.setSizeHint(QSize(0, 32))
            item.setData(Qt.UserRole, roi["col_name"])

            widget = ROIItemWidget(
                roi["col_name"],
                lambda text, i=idx: self.update_roi_name_by_index(i, text),
                lambda i=idx: self.delete_roi_by_index(i),
                select_callback=lambda it=item: self._on_roi_item_clicked(it),
            )
            self.roi_list_widget.setItemWidget(item, widget)

        self.roi_list_widget.blockSignals(False)

    def redraw_all_boxes(self):
        if self.current_image is None:
            return

        self.editor.set_image(self.current_image, reset_view=False)
        curr_h, curr_w = self.current_image.shape[:2]

        for roi in self.rois:
            px, py, pw, ph = ROISelector.to_pixel_rect(roi, curr_w, curr_h)
            self.editor.add_roi_rect(px, py, pw, ph)

    # Create

    def create_new_profile(self):
        name, ok = QInputDialog.getText(self, "신규 서식", "서식 이름:")
        if not ok or not name:
            return

        if name in self.profile_manager.profiles:
            QMessageBox.warning(self, "중복", "이미 존재하는 이름입니다.")
            return

        current_item = self.profile_list_widget.currentItem()

        # 선택된 프로파일이 없고 ROI는 있을 때
        if current_item is None and self.rois:
            ref_w, ref_h = 0, 0
            img_path = ""

            if self.current_image is not None:
                ref_h, ref_w = self.current_image.shape[:2]
                img_path = self.current_image_path if self.current_image_path else ""

            self.profile_manager.add_profile(
                name, [], self.rois, ref_w, ref_h, img_path
            )
            should_clear = False

        else:
            # 선택한 프로파일도 없고 ROI도 없거나 선택한 프로파일은 있는데 ROI가 없는 경우
            # 신규 프로파일을 추가한다.
            self.profile_manager.add_profile(name, [], [], 0, 0, "")
            should_clear = True

        self.load_profile_list()

        for i in range(self.profile_list_widget.count()):
            item = self.profile_list_widget.item(i)
            if item.data(Qt.UserRole) == name:
                self.profile_list_widget.setCurrentItem(item)
                break

        if should_clear:
            self.clear_editor()
            self.log_view.setText(f"새 서식 생성됨: '{name}' (빈 서식)")
        else:
            self.log_view.setText(f"새 서식 생성됨: '{name}' (현재 내용 저장됨)")

    # Read

    def load_profile_list(self):
        self.profile_list_widget.clear()
        names = self.profile_manager.get_all_profile_names()
        for name in names:
            item = QListWidgetItem(self.profile_list_widget)
            item.setSizeHint(QSize(0, 32))
            item.setData(Qt.UserRole, name)

            # 커스텀 위젯 생성 (이름 + 삭제버튼)
            widget = ProfileItemWidget(
                name, lambda n=name: self.delete_profile_by_name(n)
            )

            self.profile_list_widget.setItemWidget(item, widget)

    def load_selected_profile(self, item):
        if self.last_selected_item == item:
            return

        if self.check_unsaved_changes():
            self.profile_list_widget.blockSignals(True)
            self.profile_list_widget.setCurrentItem(self.last_selected_item)
            self.profile_list_widget.blockSignals(False)
            return

        self.last_selected_item = item

        name = item.data(Qt.UserRole)
        data = self.profile_manager.get_profile(name)
        if not data:
            return

        self.rois = copy.deepcopy(data.get("rois", []))
        self.undo_stack.clear()
        self.is_modified = False

        # 샘플 불러오기
        saved_img_path = data.get("sample_image_path", "")
        if saved_img_path and Path(saved_img_path).exists():
            self._load_image_from_path(saved_img_path)
        else:
            self.current_image = None
            self.current_image_path = None
            self.lbl_img_name.setText("선택된 이미지 없음")
            self.editor.scene.clear()

        self.refresh_roi_list()

        if self.current_image is not None:
            self.redraw_all_boxes()

        self.log_view.setText(
            f"서식 선택됨: {name}\n키워드: {', '.join(data.get('keywords', []))}"
        )

    def _load_image_from_path(self, file_path):
        path_obj = Path(file_path)
        if not path_obj.exists():
            return False

        try:
            self.current_image = ImageLoader.load_image(path_obj)

            if self.current_image is None:
                raise Exception("이미지 데이터를 읽을 수 없습니다.")

            self.current_image_path = file_path
            self.lbl_img_name.setText(path_obj.name)
            self.editor.set_image(self.current_image, reset_view=True)

            # 이미지가 바뀌었으니 ROI 박스도 다시 그려야 함
            if self.rois:
                self.redraw_all_boxes()
            return True

        except Exception as e:
            print(f"이미지 로드 실패: {e}")
            return False

    def load_image_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "이미지 열기", "", AppConfig.FILTER_IMAGE
        )
        if file_path:
            self._load_image_from_path(file_path)

    # Update

    def save_current_profile(self):
        item = self.profile_list_widget.currentItem()

        if not item:
            if self.rois:
                answer = QMessageBox.question(
                    self,
                    "서식 생성",
                    "선택된 서식이 없습니다.\n현재 작업 내용으로 '새 서식'을 만드시겠습니까?",
                )
                if answer == QMessageBox.Yes:
                    self.create_new_profile()
                return
            else:
                QMessageBox.warning(self, "경고", "저장할 서식을 선택하세요.")
                return

        name = item.data(Qt.UserRole)
        data = self.profile_manager.get_profile(name)
        keywords = data.get("keywords", [])

        ref_w, ref_h = 0, 0

        if self.current_image is not None:
            ref_h, ref_w = self.current_image.shape[:2]
        elif data:
            ref_w = data.get("ref_w", 0)
            ref_h = data.get("ref_h", 0)

        image_path_to_save = ""
        if self.current_image_path:
            image_path_to_save = self.current_image_path
        elif data:
            image_path_to_save = data.get("sample_image_path", "")

        if self.profile_manager.add_profile(
            name, keywords, self.rois, ref_w, ref_h, image_path_to_save
        ):
            QMessageBox.information(self, "성공", "설정이 저장되었습니다.")
            self.is_modified = False
        else:
            QMessageBox.critical(self, "실패", "저장 실패")

    def update_roi_name_by_index(self, index, new_name):
        if 0 <= index < len(self.rois):
            if self.rois[index]["col_name"] != new_name:
                self.save_state_for_undo()
                self.rois[index]["col_name"] = new_name
                item = self.roi_list_widget.item(index)
                if item:
                    item.setData(Qt.UserRole, new_name)

    # Delete

    def delete_profile_by_name(self, name):
        """리스트 옆 X버튼 클릭 시 호출"""
        if (
            QMessageBox.question(
                self, "삭제", f"'{name}' 서식을 정말 삭제하시겠습니까?"
            )
            == QMessageBox.Yes
        ):
            self.profile_manager.delete_profile(name)
            self.load_profile_list()
            self.clear_editor()

    def delete_roi_by_index(self, index):
        """ROI 리스트 옆 X버튼 클릭 시 호출"""
        if 0 <= index < len(self.rois):
            self.save_state_for_undo()
            self.mark_as_modified()

            del self.rois[index]
            self.refresh_roi_list()
            if self.current_image is not None:
                self.redraw_all_boxes()

            new_row = min(index, self.roi_list_widget.count() - 1)
            if new_row >= 0:
                self.roi_list_widget.setCurrentRow(new_row)

    def delete_selected_roi_shortcut(self):
        if self.roi_list_widget.hasFocus():
            row = self.roi_list_widget.currentRow()
            if row >= 0:
                self.delete_roi_by_index(row)

    # OCR Test

    def test_all_rois(self):
        if self.current_image is None or not self.rois:
            self.log_view.setText("테스트할 이미지나 영역이 없습니다.")
            return

        self.log_view.clear()
        self.log_view.append_log(f"--- OCR 테스트 시작 ({len(self.rois)}개 영역) ---")

        curr_h, curr_w = self.current_image.shape[:2]

        for roi in self.rois:
            # 비율 -> 픽셀
            px, py, pw, ph = ROISelector.to_pixel_rect(roi, curr_w, curr_h)

            try:
                text = self.ocr_engine.extract_text_from_roi(
                    self.current_image, px, py, pw, ph
                )
                self.log_view.append_log(f"<b>[{roi['col_name']}]</b> : {text}")
            except Exception as e:
                self.log_view.append_log(f"[{roi['col_name']}] 오류: {str(e)}")

        self.log_view.append_log("------ 테스트 완료 ------")

    def open_keyword_dialog(self):
        item = self.profile_list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "알림", "설정할 서식을 먼저 선택해주세요.")
            return

        name = item.data(Qt.UserRole)
        data = self.profile_manager.get_profile(name)
        current_keywords = data.get("keywords", [])

        dialog = KeywordSettingsDialog(name, current_keywords, self)
        if dialog.exec():
            new_keywords = dialog.get_keywords()
            # 키워드만 업데이트하고 저장은 add_profile로 덮어쓰기
            ref_w, ref_h = 0, 0
            if self.current_image is not None:
                ref_h, ref_w = self.current_image.shape[:2]
            elif data.get("ref_w"):
                ref_w, ref_h = data.get("ref_w"), data.get("ref_h")

            self.profile_manager.add_profile(
                name, new_keywords, self.rois, ref_w, ref_h, self.current_image_path
            )
            QMessageBox.information(self, "완료", "키워드가 설정되었습니다.")

    # Handler

    def on_roi_added(self, x, y, w, h):
        if self.current_image is None:
            return

        self.save_state_for_undo()
        self.mark_as_modified()

        curr_h, curr_w = self.current_image.shape[:2]
        new_name = f"Column_{len(self.rois)+1}"

        roi_data = self._create_roi_data(new_name, x, y, w, h, curr_w, curr_h)
        self.rois.append(roi_data)
        self.refresh_roi_list()

        last_row = len(self.rois) - 1
        self.roi_list_widget.setCurrentRow(last_row)

        self.redraw_all_boxes()
        self.editor.highlight_roi_by_index(last_row)

        item = self.roi_list_widget.item(last_row)
        widget = self.roi_list_widget.itemWidget(item)

        if widget and isinstance(widget, ROIItemWidget):
            widget.name_edit.setFocus()
            widget.name_edit.selectAll()

    def on_roi_selection_changed(self, current_row):
        if current_row >= 0:
            self.editor.highlight_roi_by_index(current_row)

    def _on_roi_item_clicked(self, item):
        self.roi_list_widget.setCurrentItem(item)
        self.roi_list_widget.setFocus()

    # Save Profile

    def export_current_profile(self):
        item = self.profile_list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "경고", "내보낼 서식을 선택해주세요.")
            return

        name = item.data(Qt.UserRole)
        file_path, _ = QFileDialog.getSaveFileName(
            self, "서식 내보내기", f"{name}.json", AppConfig.FILTER_JSON
        )

        if file_path:
            if self.profile_manager.export_profile(name, file_path):
                QMessageBox.information(self, "성공", f"'{name}' 서식을 내보냈습니다.")
            else:
                QMessageBox.critical(self, "실패", "내보내기 중 오류가 발생했습니다.")

    def import_external_profile(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "서식 불러오기", "", AppConfig.FILTER_JSON
        )

        if file_path:
            # 반환값: (상태, 개수, 부가정보)
            status, count, extra = self.profile_manager.import_profiles(file_path)

            if status == "REPLACED":
                self.load_profile_list()  # 리스트 갱신
                self.clear_editor()  # 편집기 초기화
                QMessageBox.information(
                    self,
                    "복원 완료",
                    f"전체 서식 목록이 교체되었습니다.\n(총 {count}개 로드됨)",
                )

            elif status == "MERGED":
                self.load_profile_list()
                names_str = ", ".join(extra[:5])  # 너무 길면 5개까지만 표시
                if len(extra) > 5:
                    names_str += "..."

                QMessageBox.information(
                    self,
                    "추가 완료",
                    f"{count}개의 서식이 추가되었습니다.\n({names_str})",
                )

            else:  # ERROR
                QMessageBox.warning(
                    self, "오류", "파일을 불러오는 중 문제가 발생했습니다."
                )

    def backup_profiles(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "전체 서식 백업", "MinwonOCR_Backup.json", AppConfig.FILTER_JSON
        )
        if file_path:
            if self.profile_manager.export_all_profiles(file_path):
                QMessageBox.information(
                    self, "성공", "모든 서식이 백업 파일로 저장되었습니다."
                )
            else:
                QMessageBox.critical(self, "실패", "백업 중 오류가 발생했습니다.")

    # Undo Logic

    def save_state_for_undo(self):
        snapshot = copy.deepcopy(self.rois)
        self.undo_stack.append(snapshot)

        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def undo_last_action(self):
        if not self.undo_stack:
            return

        prev_rois = self.undo_stack.pop()
        self.rois = copy.deepcopy(prev_rois)

        self.mark_as_modified()
        self.refresh_roi_list()
        self.redraw_all_boxes()
        self.log_view.append_log("↩ 실행 취소됨")

    def mark_as_modified(self):
        self.is_modified = True

    def check_unsaved_changes(self):
        if self.is_modified:
            answer = QMessageBox.question(
                self,
                "저장되지 않음",
                "현재 서식의 변경사항이 저장되지 않았습니다.\n저장하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )

            if answer == QMessageBox.Cancel:
                return True

            if answer == QMessageBox.Yes:
                self.save_current_profile()

        return False
