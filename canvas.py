# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt, QPoint, QRect, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QIcon
from PyQt5.QtWidgets import QWidget, QSizePolicy


CLASS_COLORS = [
    QColor(0, 200, 0),
    QColor(255, 0, 0),
    QColor(0, 255, 120),
    QColor(255, 180, 0),
    QColor(80, 180, 255),
    QColor(255, 80, 80),
    QColor(200, 100, 255),
    QColor(255, 255, 100),
    QColor(120, 255, 200),
    QColor(255, 120, 180),
]


def color_for_class(class_id):
    return CLASS_COLORS[class_id % len(CLASS_COLORS)]


def make_color_icon(color, size=16):
    pm = QPixmap(size, size)
    pm.fill(color)
    return QIcon(pm)


class AnnotationCanvas(QWidget):
    boxCreated = pyqtSignal(int, int, int, int)
    boxSelected = pyqtSignal(int)
    boxDeleted = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(400, 300)

        self.image = None
        self.image_path = None
        self.boxes = []
        self.class_names = []
        self.current_class_id = -1

        self.scale = 1.0
        self.offset = QPoint(0, 0)

        self.drawing = False
        self.start_point = QPoint()
        self.current_point = QPoint()

        self.selected_index = -1
        self.hover_index = -1

    def load_image(self, path):
        self.image_path = path
        self.image = QPixmap(path)
        self.boxes = []
        self.selected_index = -1
        self.hover_index = -1
        self.fit_to_window()
        self.update()

    def set_boxes(self, boxes):
        self.boxes = boxes
        self.selected_index = -1
        self.update()

    def set_class_names(self, names):
        self.class_names = names
        self.update()

    def set_current_class(self, class_id):
        self.current_class_id = class_id
        self.update()

    def add_box(self, class_id, x, y, w, h):
        self.boxes.append({'class_id': class_id, 'x': x, 'y': y, 'w': w, 'h': h})
        self.selected_index = len(self.boxes) - 1
        self.update()

    def delete_selected(self):
        if 0 <= self.selected_index < len(self.boxes):
            idx = self.selected_index
            del self.boxes[idx]
            self.selected_index = -1
            self.boxDeleted.emit(idx)
            self.update()

    def clear_selection(self):
        self.selected_index = -1
        self.update()

    def fit_to_window(self):
        if self.image is None or self.image.isNull():
            return
        cw = max(self.width() - 20, 1)
        ch = max(self.height() - 20, 1)
        iw = self.image.width()
        ih = self.image.height()
        sx = cw / iw
        sy = ch / ih
        self.scale = min(sx, sy)
        dw = iw * self.scale
        dh = ih * self.scale
        self.offset = QPoint(int((self.width() - dw) / 2), int((self.height() - dh) / 2))
        self.update()

    def resizeEvent(self, event):
        self.fit_to_window()
        super().resizeEvent(event)

    def to_image_coord(self, pt):
        x = (pt.x() - self.offset.x()) / self.scale
        y = (pt.y() - self.offset.y()) / self.scale
        return QPoint(int(x), int(y))

    def to_widget_coord(self, x, y):
        return QPoint(int(x * self.scale + self.offset.x()), int(y * self.scale + self.offset.y()))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(12, 15, 26))

        if self.image is None or self.image.isNull():
            painter.setPen(QColor(110, 125, 160))
            painter.setFont(QFont("Microsoft YaHei", 14))
            painter.drawText(self.rect(), Qt.AlignCenter,
                             "请打开图片目录\n支持 jpg / png / bmp / tif")
            painter.end()
            return

        target = QRect(self.offset,
                       QSize(int(self.image.width() * self.scale),
                             int(self.image.height() * self.scale)))
        painter.drawPixmap(target, self.image)

        painter.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        for i, box in enumerate(self.boxes):
            color = color_for_class(box['class_id'])
            tl = self.to_widget_coord(box['x'], box['y'])
            br = self.to_widget_coord(box['x'] + box['w'], box['y'] + box['h'])
            rect = QRect(tl, br).normalized()

            if i == self.selected_index:
                painter.setPen(QPen(color, 3))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect)
                painter.setBrush(color)
                for corner in [rect.topLeft(), rect.topRight(),
                               rect.bottomLeft(), rect.bottomRight()]:
                    painter.drawRect(QRect(corner.x() - 4, corner.y() - 4, 8, 8))
            elif i == self.hover_index:
                painter.setPen(QPen(color, 3))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect)
            else:
                painter.setPen(QPen(color, 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect)

            label = self.class_names[box['class_id']] if box['class_id'] < len(self.class_names) else str(box['class_id'])
            fm = painter.fontMetrics()
            tw = fm.width(label) + 10
            th = fm.height() + 4
            label_rect = QRect(rect.x(), rect.y() - th, tw, th)
            if label_rect.y() < 0:
                label_rect.moveTop(rect.y())
            painter.fillRect(label_rect, color)
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(label_rect, Qt.AlignCenter, label)

        if self.drawing:
            draw_color = color_for_class(self.current_class_id) if self.current_class_id >= 0 else QColor(0, 255, 255)
            tl = self.to_widget_coord(self.start_point.x(), self.start_point.y())
            br = self.to_widget_coord(self.current_point.x(), self.current_point.y())
            rect = QRect(tl, br).normalized()
            painter.setPen(QPen(draw_color, 2, Qt.DashLine))
            painter.setBrush(QColor(draw_color.red(), draw_color.green(), draw_color.blue(), 40))
            painter.drawRect(rect)
            painter.setPen(draw_color)
            painter.setFont(QFont("Microsoft YaHei", 9))
            info = f"{abs(rect.width())} x {abs(rect.height())}"
            painter.drawText(rect.x() + 4, rect.y() + 14, info)

        painter.end()

    def mousePressEvent(self, event):
        if self.image is None or self.image.isNull():
            return
        if event.button() == Qt.LeftButton:
            img_pt = self.to_image_coord(event.pos())
            hit = self.hit_test(img_pt)
            if hit >= 0:
                self.selected_index = hit
                self.boxSelected.emit(hit)
                self.update()
                return
            self.drawing = True
            self.start_point = img_pt
            self.current_point = img_pt
            self.selected_index = -1
            self.boxSelected.emit(-1)
            self.update()
        elif event.button() == Qt.RightButton:
            img_pt = self.to_image_coord(event.pos())
            if self.selected_index >= 0 and self._inside_box(self.boxes[self.selected_index], img_pt):
                self.delete_selected()
            else:
                hit = self.hit_test(img_pt)
                if hit >= 0:
                    self.selected_index = hit
                    self.delete_selected()

    def _inside_box(self, b, pt):
        return b['x'] <= pt.x() <= b['x'] + b['w'] and b['y'] <= pt.y() <= b['y'] + b['h']

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.current_point = self.to_image_coord(event.pos())
            self.current_point.setX(max(0, min(self.image.width(), self.current_point.x())))
            self.current_point.setY(max(0, min(self.image.height(), self.current_point.y())))
            self.update()
        else:
            img_pt = self.to_image_coord(event.pos())
            new_hover = self.hit_test(img_pt)
            if new_hover != self.hover_index:
                self.hover_index = new_hover
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            x1, y1 = self.start_point.x(), self.start_point.y()
            x2, y2 = self.current_point.x(), self.current_point.y()
            x, y = min(x1, x2), min(y1, y2)
            w, h = abs(x2 - x1), abs(y2 - y1)
            if w > 3 and h > 3:
                x = max(0, x)
                y = max(0, y)
                if x + w > self.image.width():
                    w = self.image.width() - x
                if y + h > self.image.height():
                    h = self.image.height() - y
                self.boxCreated.emit(x, y, w, h)
            self.update()

    def hit_test(self, img_pt):
        for i in range(len(self.boxes) - 1, -1, -1):
            if self._inside_box(self.boxes[i], img_pt):
                return i
        return -1

    def wheelEvent(self, event):
        if self.image is None or self.image.isNull():
            return
        delta = event.angleDelta().y() / 120
        factor = 1.15 if delta > 0 else 1 / 1.15
        new_scale = max(0.05, min(15.0, self.scale * factor))
        mouse_pos = event.pos()
        img_x = (mouse_pos.x() - self.offset.x()) / self.scale
        img_y = (mouse_pos.y() - self.offset.y()) / self.scale
        self.scale = new_scale
        self.offset = QPoint(int(mouse_pos.x() - img_x * self.scale),
                             int(mouse_pos.y() - img_y * self.scale))
        self.update()