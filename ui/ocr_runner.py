import os
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
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

    def __init__(self):
        super().__init__()
        self.processor = None
        self.profile_manager = ProfileManager()
        self.target_files = []
        self.init_ui()

    def init_ui(self):
        # 메인 레이아웃 (여백 최소화)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 좌우 분할을 위한 Splitter 생성
        splitter = QSplitter(Qt.Horizontal)

        # ==========================================
        # [좌측 패널] 서식 매칭 설정 + 작업 대상 선택
        # ==========================================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # --- 1. 서식 매칭 설정 (상단 배치) ---
        profile_group = QGroupBox("서식 매칭 방법")
        profile_layout = QVBoxLayout()

        # 라디오 버튼 영역
        radio_layout = QHBoxLayout()
        self.radio_auto = QRadioButton("자동 (키워드)")
        self.radio_manual = QRadioButton("수동 (강제지정)")
        self.radio_manual.setChecked(True)  # 기본값 수동

        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.radio_auto)
        self.mode_group.addButton(self.radio_manual)
        self.mode_group.buttonClicked.connect(self.toggle_profile_combo)

        radio_layout.addWidget(self.radio_auto)
        radio_layout.addWidget(self.radio_manual)
        radio_layout.addStretch()

        profile_layout.addLayout(radio_layout)

        # 콤보박스 (수동 선택 시 활성화)
        self.combo_profile = QComboBox()
        self.combo_profile.setEnabled(True)
        self.refresh_profile_list()  # 목록 로드
        profile_layout.addWidget(self.combo_profile)

        self.lbl_guide = QLabel("※ 목록에 서식이 없다면 서식 설정 먼저 진행해주세요")
        self.lbl_guide.setStyleSheet("margin-top: 5px; color: #ff7f00;")
        profile_layout.addWidget(self.lbl_guide)

        profile_group.setLayout(profile_layout)
        left_layout.addWidget(profile_group)

        # --- 2. 작업 대상 선택 (하단 배치 - 확장됨) ---
        input_group = QGroupBox("대상 파일")
        input_layout = QVBoxLayout()

        # 파일 추가 버튼들
        btn_layout = QHBoxLayout()
        self.btn_add_files = ActionButton("파일 추가", self.add_files)
        self.btn_add_folder = ActionButton("폴더 추가", self.add_folder)
        self.btn_clear = ActionButton("초기화", self.clear_files)

        btn_layout.addWidget(self.btn_add_files)
        btn_layout.addWidget(self.btn_add_folder)
        btn_layout.addWidget(self.btn_clear)
        input_layout.addLayout(btn_layout)

        # 파일 리스트 (공간을 많이 차지하도록)
        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        input_layout.addWidget(self.file_list_widget)

        input_group.setLayout(input_layout)
        left_layout.addWidget(input_group)

        # ==========================================
        # [우측 패널] 실행/중지 + 처리 로그
        # ==========================================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # --- 3. 실행 제어 (상단) ---
        control_group = QGroupBox("실행 제어")
        control_layout = QHBoxLayout()

        self.btn_start = ActionButton(
            "▶ 추출 시작", self.start_processing, preset="blue"
        )

        self.btn_stop = ActionButton(
            "■ 작업 중지",
            self.stop_processing,
            preset="red",
            enabled=False,
        )

        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)
        control_group.setLayout(control_layout)
        right_layout.addWidget(control_group)

        # --- 4. 처리 로그 (하단 - 확장됨) ---
        log_group = QGroupBox("처리 로그 및 결과")
        log_layout = QVBoxLayout()

        self.progress_bar = SmoothProgressBar()
        self.log_view = LogView()

        log_layout.addWidget(QLabel("진행률:"))
        log_layout.addWidget(self.progress_bar)
        log_layout.addWidget(QLabel("상세 로그:"))
        log_layout.addWidget(self.log_view)
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)

        # ==========================================
        # [패널 조립]
        # ==========================================
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # 초기 비율 설정 (좌:우 = 4:6 정도)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)

        main_layout.addWidget(splitter)

        # Shortcut
        self.shortcut_del_file = QShortcut(QKeySequence("Delete"), self)
        self.shortcut_del_file.activated.connect(self.delete_selected_files)

    # --- 기존 기능 메서드들 (변경 없음) ---
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
        is_manual = self.radio_manual.isChecked()
        self.combo_profile.setEnabled(is_manual)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "파일 선택", "", "Images (*.png *.jpg *.jpeg *.pdf)"
        )
        if files:
            for f in files:
                if f not in self.target_files:
                    self.target_files.append(f)
                    item = QListWidgetItem(os.path.basename(f))
                    item.setData(Qt.UserRole, f)
                    self.file_list_widget.addItem(item)

            self.update_log_count()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if folder:
            cnt = 0
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
                        full_path = os.path.join(root, f)

                        if full_path not in self.target_files:
                            self.target_files.append(full_path)
                            item = QListWidgetItem(f"[폴더] {f}")
                            item.setData(Qt.UserRole, full_path)
                            self.file_list_widget.addItem(item)
                            cnt += 1

            self.log_view.append(f"📂 폴더에서 {cnt}개 파일 추가됨.")
            self.update_log_count()

    def delete_selected_files(self):
        if self.file_list_widget.hasFocus():
            items = self.file_list_widget.selectedItems()
            if not items:
                return

            for item in items:
                full_path = item.data(Qt.UserRole)

                if full_path in self.target_files:
                    self.target_files.remove(full_path)

                row = self.file_list_widget.row(item)
                self.file_list_widget.takeItem(row)

            self.log_view.append_log("선택한 파일이 제외되었습니다.")
            self.update_log_count()

    def clear_files(self):
        self.target_files = []
        self.file_list_widget.clear()
        self.log_view.append("목록이 초기화되었습니다.")
        self.update_log_count()

    def update_log_count(self):
        self.log_view.append(f"현재 대기 중인 파일: {len(self.target_files)}개")

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

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_add_files.setEnabled(False)
        self.btn_add_folder.setEnabled(False)
        self.btn_clear.setEnabled(False)

        # self.log_view.clear()
        self.progress_bar.setValue(0)

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

    # def append_log(self, text):
    #     self.log_view.append_log(text)

    def update_progress(self, val):
        self.progress_bar.setValueSmooth(val)

    def emit_results(self, results):
        self.ocr_finished_with_data.emit(results)

    def on_finished(self, msg):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_add_files.setEnabled(True)
        self.btn_add_folder.setEnabled(True)
        self.btn_clear.setEnabled(True)

        self.log_view.append_log(f"--- {msg} ---")
        QMessageBox.information(self, "완료", msg)
