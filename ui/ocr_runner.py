import os
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QComboBox,
    QListWidget,
    QSplitter,
    QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QShortcut, QKeySequence
from core.batch_processor import BatchProcessor
from core.profile_manager import ProfileManager
from ui.components import ActionButton, LogView, SmoothProgressBar


class OCRRunner(QWidget):
    ocr_finished_with_data = Signal(dict)

    SUPPORTED_EXTENSIONS = (".png", ".jpg", "jpeg", ".pdf")
    FILE_FILTER = "Images (*.png *.jpg *.jpeg *.pdf)"

    def __init__(self):
        super().__init__()
        self.processor = None
        self.profile_manager = ProfileManager()
        self.target_files = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Horizontal)

        # [좌측 패널] OCR 대상 파일 추가
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(self._create_profile_group())
        left_layout.addWidget(self._create_input_group())

        # [우측 패널] 버튼, 로그
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(self._create_control_group())
        right_layout.addWidget(self._create_log_group())

        # [패널 조립]
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)

        main_layout.addWidget(splitter)

        # Shortcut
        self.shortcut_del_file = QShortcut(QKeySequence("Delete"), self)
        self.shortcut_del_file.activated.connect(self.delete_selected_files)

    def _create_profile_group(self):
        group = QGroupBox("서식 매칭 방법")
        layout = QVBoxLayout()

        # 라디오 버튼
        radio_layout = QHBoxLayout()
        self.radio_auto = QRadioButton("자동 (키워드)")
        self.radio_manual = QRadioButton("수동 (강제지정)")
        self.radio_manual.setChecked(True)

        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.radio_auto)
        self.mode_group.addButton(self.radio_manual)
        self.mode_group.buttonClicked.connect(self.toggle_profile_combo)

        radio_layout.addWidget(self.radio_auto)
        radio_layout.addWidget(self.radio_manual)
        radio_layout.addStretch()

        layout.addLayout(radio_layout)

        # 콤보박스
        self.combo_profile = QComboBox()
        self.refresh_profile_list()
        layout.addWidget(self.combo_profile)

        lbl_guide = QLabel("※ 목록에 서식이 없다면 서식 설정 먼저 진행해주세요")
        lbl_guide.setStyleSheet("margin-top: 5px; color: #ff7f00;")
        layout.addWidget(lbl_guide)

        group.setLayout(layout)
        return group

    def _create_input_group(self):
        group = QGroupBox("대상 파일")
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        self.btn_add_files = ActionButton("파일 추가", self.add_files)
        self.btn_add_folder = ActionButton("폴더 추가", self.add_folder)
        self.btn_clear = ActionButton("초기화", self.clear_files)

        btn_layout.addWidget(self.btn_add_files)
        btn_layout.addWidget(self.btn_add_folder)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.file_list_widget)

        group.setLayout(layout)
        return group

    def _create_control_group(self):
        group = QGroupBox("실행 제어")
        layout = QHBoxLayout()

        self.btn_start = ActionButton(
            "▶ 추출 시작", self.start_processing, preset="blue"
        )
        self.btn_stop = ActionButton(
            "■ 작업 중지", self.stop_processing, preset="red", enabled=False
        )

        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)
        group.setLayout(layout)
        return group

    def _create_log_group(self):
        group = QGroupBox("처리 로그 및 결과")
        layout = QVBoxLayout()

        self.progress_bar = SmoothProgressBar()
        self.log_view = LogView()

        layout.addWidget(QLabel("진행률:"))
        layout.addWidget(self.progress_bar)
        layout.addWidget(QLabel("상세 로그:"))
        layout.addWidget(self.log_view)

        group.setLayout(layout)
        return group

    # Logic

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_profile_list()

    def refresh_profile_list(self):
        current_text = self.combo_profile.currentText()
        self.combo_profile.clear()

        self.profile_manager.load_profiles()
        names = self.profile_manager.get_all_profile_names()

        self.combo_profile.addItems(names)
        if current_text in names:
            self.combo_profile.setCurrentText(current_text)

    def toggle_profile_combo(self):
        self.combo_profile.setEnabled(self.radio_manual.isChecked())

    def _add_file_item(self, file_path):
        if file_path not in self.target_files:
            self.target_files.append(file_path)

            display_text = os.path.basename(file_path)

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, file_path)
            self.file_list_widget.addItem(item)
            return True
        return False

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "파일 선택", "", "Images (*.png *.jpg *.jpeg *.pdf)"
        )
        if files:
            count = 0
            for f in files:
                if self._add_file_item(f):
                    count += 1
            if count > 0:
                self.update_log_count()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if folder:
            cnt = 0
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(self.SUPPORTED_EXTENSIONS):
                        full_path = os.path.join(root, f)
                        if self._add_file_item(full_path):
                            cnt += 1

            self.log_view.append_log(f"📂 폴더에서 {cnt}개 파일 추가됨.")
            self.update_log_count()

    def delete_selected_files(self):
        if not self.file_list_widget.hasFocus():
            return

        items = self.file_list_widget.selectedItems()
        if not items:
            return

        deleted_count = 0
        for item in items:
            full_path = item.data(Qt.UserRole)

            if full_path in self.target_files:
                self.target_files.remove(full_path)

            row = self.file_list_widget.row(item)
            self.file_list_widget.takeItem(row)
            deleted_count += 1

        if deleted_count > 0:
            self.log_view.append_log(f"{deleted_count}개 파일이 제외되었습니다.")
            self.update_log_count()

    def clear_files(self):
        self.target_files = []
        self.file_list_widget.clear()
        self.log_view.append("목록이 초기화되었습니다.")
        self.update_log_count()

    def update_log_count(self):
        self.log_view.append(f"현재 대기 중인 파일: {len(self.target_files)}개")

    # OCR Processing

    def _set_processing_state(self, is_running):
        self.btn_start.setEnabled(not is_running)
        self.btn_stop.setEnabled(is_running)
        self.btn_add_files.setEnabled(not is_running)
        self.btn_add_folder.setEnabled(not is_running)
        self.btn_clear.setEnabled(not is_running)

        self.combo_profile.setEnabled(not is_running and self.radio_manual.isChecked())
        self.radio_auto.setEnabled(not is_running)
        self.radio_manual.setEnabled(not is_running)

    def start_processing(self):
        if not self.target_files:
            QMessageBox.warning(self, "알림", "처리할 파일이 없습니다.")
            return

        self.refresh_profile_list()

        forced_profile = None
        if self.radio_manual.isChecked():
            forced_profile = self.combo_profile.currentText()
            if not forced_profile:
                QMessageBox.warning(self, "알림", "선택된 프로파일이 없습니다.")
                return

        self._set_processing_state(True)

        # self.log_view.clear()
        self.progress_bar.setValue(0)
        self.log_view.append_log("--- 작업 시작 ---")

        self.processor = BatchProcessor(self.target_files, forced_profile)
        self.processor.log_signal.connect(self.log_view.append_log)
        self.processor.progress_signal.connect(self.update_progress)
        self.processor.finished_signal.connect(self.on_finished)
        self.processor.results_ready_signal.connect(self.emit_results)
        self.processor.start()

    def stop_processing(self):
        if self.processor and self.processor.isRunning():
            self.processor.stop()
            self.log_view.append_log("🛑 중단 요청됨...")

    def update_progress(self, val):
        self.progress_bar.setValueSmooth(val)

    def emit_results(self, results):
        self.ocr_finished_with_data.emit(results)

    def on_finished(self, msg):
        self._set_processing_state(False)

        self.log_view.append_log(f"--- {msg} ---")
        QMessageBox.information(self, "완료", msg)
