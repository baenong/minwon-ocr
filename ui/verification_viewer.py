import os
import pandas as pd
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QLabel,
    QSplitter,
    QMessageBox,
    QFileDialog,
    QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPen

# Custom Modules
from core.profile_manager import ProfileManager
from core.ocr_engine import OCREngine
from core.constants import AppConfig
from core.image_loader import ImageLoader
from ui.editor_widget import ROISelector
from ui.components import ActionButton


class VerificationViewer(QWidget):
    TABLE_STYLE = "QTableWidget::item { padding: 4px 10px; }"
    GUIDE_STYLE = "margin-right: 5px; color: #ff7f00;"

    def __init__(self):
        super().__init__()
        self.current_results = {}
        self.current_df = None
        self.profile_manager = ProfileManager()
        self.ocr_engine = OCREngine()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. 상단 툴바
        layout.addLayout(self._create_top_toolbar())

        # 2. 메인 스플리터 (테이블 + 이미지 뷰어)
        self.splitter = QSplitter(Qt.Horizontal)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(self.TABLE_STYLE)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.splitter.addWidget(self.table)

        self.image_viewer = ROISelector()
        self.splitter.addWidget(self.image_viewer)

        self.splitter.setSizes([600, 400])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        layout.addWidget(self.splitter)

    def _create_top_toolbar(self):
        toolbar = QHBoxLayout()

        self.lbl_status = QLabel("대기 중...")
        self.combo_sheet = QComboBox()
        self.combo_sheet.currentIndexChanged.connect(self.on_sheet_changed)

        self.btn_open_folder = ActionButton("📂 엑셀 불러오기", self.load_excel_file)
        self.btn_save = ActionButton(
            "💾 엑셀파일 저장", self.save_data_to_file, preset="green"
        )

        lbl_guide = QLabel("OCR 실행결과나 기존 엑셀 파일을 검증합니다.")
        lbl_guide.setStyleSheet(self.GUIDE_STYLE)

        toolbar.addWidget(QLabel("결과 서식: "))
        toolbar.addWidget(self.combo_sheet)
        toolbar.addWidget(self.lbl_status)
        toolbar.addStretch()
        toolbar.addWidget(lbl_guide)
        toolbar.addWidget(self.btn_open_folder)
        toolbar.addWidget(self.btn_save)

        return toolbar

    def display_profile_data(self, profile_name):
        if profile_name not in self.current_results:
            return

        rows_data = self.current_results[profile_name]
        if not rows_data:
            return

        df = pd.DataFrame(rows_data)
        df = self._process_dateframe_columns(df, profile_name)

        self.current_df = df
        self._update_table_view()

    def _update_table_view(self):
        if self.current_df is None:
            return

        self.table.clear()
        rows, cols = self.current_df.shape
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)

        headers = self.current_df.columns.astype(str).tolist()
        self.table.setHorizontalHeaderLabels(headers)

        full_path_idx = headers.index("full_path") if "full_path" in headers else -1

        for r in range(rows):
            for c in range(cols):
                val = str(self.current_df.iat[r, c])
                item = QTableWidgetItem(val)

                if c == full_path_idx:
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)

                # 정렬
                if headers[c] == "파일명":
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignCenter)

                self.table.setItem(r, c, item)

        self.table.resizeColumnsToContents()

        if full_path_idx != -1:
            self.table.setColumnHidden(full_path_idx, True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)

    # --- 메모리 데이터 로드 함수 ---

    def load_data_from_memory(self, results):
        self.current_results = results

        self.combo_sheet.blockSignals(True)
        self.combo_sheet.clear()

        if not results:
            self.lbl_status.setText("결과 데이터가 없습니다.")
            self.combo_sheet.blockSignals(False)
            return

        profile_names = list(results.keys())
        self.combo_sheet.addItems(profile_names)
        self.combo_sheet.blockSignals(False)

        self.lbl_status.setText(f"데이터 로드됨 ({len(profile_names)}개 서식)")
        if profile_names:
            self.display_profile_data(profile_names[0])

    def load_excel_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "엑셀 파일 열기", "", AppConfig.FILTER_EXCEL
        )
        if not file_path:
            return

        try:
            df = pd.read_excel(file_path).fillna("")

            # 필수 컬럼 체크 (full_path가 없으면 이미지 로드 불가하므로 경고)
            if "full_path" not in df.columns:
                QMessageBox.warning(
                    self,
                    "주의",
                    "이 엑셀 파일에는 이미지 경로 정보(full_path)가 없습니다.\n이미지 뷰어가 작동하지 않을 수 있습니다.",
                )

            filename = os.path.basename(file_path)
            profile_name = filename.split("_", 1)[1] if "_" in filename else filename
            profile_name = profile_name.replace(".xlsx", "")

            # UI 초기화 및 데이터 로드
            self.current_results = {}  # 기존 메모리 데이터 초기화
            self.combo_sheet.blockSignals(True)
            self.combo_sheet.clear()
            self.combo_sheet.addItem(profile_name)
            self.combo_sheet.setCurrentIndex(0)
            self.combo_sheet.blockSignals(False)

            self.current_df = df
            self.image_viewer.scene.clear()
            self._update_table_view()

            self.lbl_status.setText(f"파일 로드됨: {filename}")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 로드 실패: {str(e)}")

    def _process_dateframe_columns(self, df, profile_name):
        if "full_path" in df.columns:
            df["파일명"] = df["full_path"].apply(lambda x: os.path.basename(str(x)))
        else:
            df["파일명"] = "-"

        profile_data = self.profile_manager.get_profile(profile_name)
        roi_order = (
            [roi["col_name"] for roi in profile_data.get("rois", [])]
            if profile_data
            else []
        )

        final_columns = ["파일명"] + roi_order

        if "full_path" in df.columns:
            final_columns.append("full_path")

        for col in df.columns:
            if col not in final_columns:
                final_columns.append(col)

        df = df.reindex(columns=final_columns)
        display_cols = [c for c in df.columns if c != "full_path"]
        df[display_cols] = df[display_cols].fillna("-").replace("", "-")

        return df

    # Event Handlers

    def on_sheet_changed(self):
        profile_name = self.combo_sheet.currentText()
        if profile_name in self.current_results:
            self.display_profile_data(profile_name)

    def on_cell_clicked(self, row, col):
        if self.current_df is None:
            return

        try:
            # full_path가 없다면 중단
            headers = [
                self.table.horizontalHeaderItem(c).text()
                for c in range(self.table.columnCount())
            ]
            if "full_path" not in headers:
                return

            full_path_idx = headers.index("full_path")
            path_item = self.table.item(row, full_path_idx)
            if not path_item:
                return

            full_path = path_item.text()

            if not os.path.exists(full_path):
                self._show_image_error("이미지 파일이 없습니다.")
                return

            # 이미지 로드 및 표시
            img = ImageLoader.load_image(full_path)

            if img is not None:
                self.image_viewer.set_image(img, reset_view=True)
                self._draw_roi_boxes(img, col, headers)

        except Exception as e:
            print(f"이미지 로드 에러: {e}")

    def _show_image_error(self, message):
        self.image_viewer.scene.clear()
        text_item = self.image_viewer.scene.addText(message)
        text_item.setDefaultTextColor(Qt.red)
        text_item.setFont(QFont("Malgun Gothic", 20, QFont.Bold))
        text_item.setPos(50, 50)

    def _draw_roi_boxes(self, img, clicked_col_idx, headers):
        current_profile_name = self.combo_sheet.currentText()
        profile_data = self.profile_manager.get_profile(current_profile_name)

        if not profile_data:
            return

        rois = profile_data.get("rois", [])
        curr_h, curr_w = img.shape[:2]
        clicked_col_name = headers[clicked_col_idx]

        for roi in rois:
            px, py, pw, ph = ROISelector.to_pixel_rect(roi, curr_w, curr_h)

            is_selected = roi["col_name"] == clicked_col_name
            rect_item = self.image_viewer.scene.addRect(px, py, pw, ph)

            color = QColor("red") if is_selected else QColor("blue")
            width = 3 if is_selected else 2
            z_value = 10 if is_selected else 0

            pen = QPen(color)
            pen.setWidth(width)
            rect_item.setPen(pen)
            rect_item.setZValue(z_value)

    def save_data_to_file(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "알림", "저장할 데이터가 없습니다.")
            return

        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        current_profile = self.combo_sheet.currentText()
        default_name = f"{timestamp}_{current_profile}.xlsx"

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "엑셀 저장",
            default_name,
            AppConfig.FILTER_EXCEL,
        )

        if save_path:
            rows = self.table.rowCount()
            cols = self.table.columnCount()
            headers = [self.table.horizontalHeaderItem(c).text() for c in range(cols)]

            new_data = []
            for r in range(rows):
                row_vals = {}
                for c in range(cols):
                    item = self.table.item(r, c)
                    row_vals[headers[c]] = item.text() if item else ""
                new_data.append(row_vals)

            try:
                pd.DataFrame(new_data).to_excel(save_path, index=False)
                QMessageBox.information(
                    self, "성공", f"저장되었습니다:\n{os.path.basename(save_path)}"
                )
            except Exception as e:
                QMessageBox.critical(self, "실패", str(e))
