import cv2
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QBrush
from PySide6.QtCore import Qt, Signal


class ROISelector(QGraphicsView):
    roi_added = Signal(float, float, float, float)

    STYLE_CONFIG = {
        "default_color": QColor(255, 0, 0),
        "highlight_color": QColor(0, 0, 255),
        "default_width": 2,
        "highlight_width": 3,
        "default_alpha": 50,
        "highlight_alpha": 80,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.roi_items = []
        self.start_pos = None
        self.current_rect_item = None
        self.is_drawing = False
        self.pixmap_item = None
        self._image_data_ref = None  # [중요] QImage 데이터 참조 유지용

        self._init_view()
        self._init_scene()
        self._init_styles()

    def _init_view(self):
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    def _init_scene(self):
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

    def _init_styles(self):
        cfg = self.STYLE_CONFIG

        self.default_pen = QPen(cfg["default_color"], cfg["default_width"])
        self.default_pen.setCosmetic(True)

        self.default_brush = QBrush(cfg["default_color"])
        color = self.default_brush.color()
        color.setAlpha(cfg["default_alpha"])
        self.default_brush.setColor(color)

        self.highlight_pen = QPen(cfg["highlight_color"], cfg["highlight_width"])
        self.highlight_pen.setCosmetic(True)

        self.highlight_brush = QBrush(cfg["highlight_color"])
        color = self.highlight_brush.color()
        color.setAlpha(cfg["highlight_alpha"])
        self.highlight_brush.setColor(color)

    def set_image(self, cv_image, reset_view=True):
        self.scene.clear()
        self.current_rect_item = None
        self.roi_items = []

        if cv_image is None:
            return

        if len(cv_image.shape) == 2:
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2BGR)

        height, width, channel = cv_image.shape
        bytes_per_line = 3 * width

        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        self._image_data_ref = rgb_image

        q_img = QImage(
            self._image_data_ref.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888,
        )

        pixmap = QPixmap.fromImage(q_img)
        self.pixmap_item = self.scene.addPixmap(pixmap)
        self.setSceneRect(0, 0, width, height)

        if reset_view:
            self.fit_in_view()

    def add_roi_rect(self, x, y, w, h):
        rect_item = QGraphicsRectItem(x, y, w, h)

        rect_item.setPen(self.default_pen)
        rect_item.setBrush(self.default_brush)

        self.scene.addItem(rect_item)
        self.roi_items.append(rect_item)

    def highlight_roi_by_index(self, index):
        for i, item in enumerate(self.roi_items):
            if i == index:
                item.setPen(self.highlight_pen)
                item.setBrush(self.highlight_brush)
                item.setZValue(1)
            else:
                item.setPen(self.default_pen)
                item.setBrush(self.default_brush)
                item.setZValue(0)

    # Event Handler

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.pixmap_item:
            scene_pos = self.mapToScene(event.pos())

            if not self.sceneRect().contains(scene_pos):
                return

            self.is_drawing = True
            self.start_pos = scene_pos
            self.current_rect_item = QGraphicsRectItem()
            self.current_rect_item.setPen(self.default_pen)
            self.current_rect_item.setBrush(self.default_brush)
            self.scene.addItem(self.current_rect_item)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_drawing and self.current_rect_item:
            scene_pos = self.mapToScene(event.pos())
            img_rect = self.sceneRect()

            curr_x = min(max(scene_pos.x(), 0), img_rect.width())
            curr_y = min(max(scene_pos.y(), 0), img_rect.height())

            width = curr_x - self.start_pos.x()
            height = curr_y - self.start_pos.y()

            top_left_x = self.start_pos.x() if width > 0 else curr_x
            top_left_y = self.start_pos.y() if height > 0 else curr_y

            self.current_rect_item.setRect(
                top_left_x, top_left_y, abs(width), abs(height)
            )
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_drawing and event.button() == Qt.LeftButton:
            self.is_drawing = False
            if self.current_rect_item:
                rect = self.current_rect_item.rect()

                if rect.width() > 5 and rect.height() > 5:
                    self.roi_added.emit(rect.x(), rect.y(), rect.width(), rect.height())
                else:
                    self.scene.removeItem(self.current_rect_item)

                self.current_rect_item = None

        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_in_view()

    def fit_in_view(self):
        if self.pixmap_item:
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
