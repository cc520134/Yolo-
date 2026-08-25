# -*- coding: utf-8 -*-
import os


class AIModel:
    def __init__(self):
        self.model = None
        self.names = {}
        self.path = ""

    def load(self, path):
        self.path = path
        try:
            from ultralytics import YOLO
        except Exception as e:
            return False, f"加载 ultralytics 失败: {e}\n请检查 ultralytics/torch 安装"
        try:
            self.model = YOLO(path)
            self.names = {int(k): v for k, v in self.model.names.items()}
            return True, ""
        except Exception as e:
            self.model = None
            self.names = {}
            return False, f"模型加载失败: {e}"

    def predict(self, image_path, conf=0.25, iou=0.45):
        if self.model is None:
            return []
        results = self.model(image_path, conf=conf, iou=iou, verbose=False)
        boxes = []
        for r in results:
            for b in r.boxes:
                cid = int(b.cls.item())
                x1, y1, x2, y2 = b.xyxy[0].tolist()
                boxes.append((cid, int(x1), int(y1), int(x2 - x1), int(y2 - y1)))
        return boxes

    def class_name(self, cid):
        return self.names.get(cid, str(cid))


def write_yolo_txt(path, boxes, iw, ih):
    with open(path, 'w', encoding='utf-8') as f:
        for cid, x, y, w, h in boxes:
            xc = (x + w / 2) / iw
            yc = (y + h / 2) / ih
            f.write(f"{cid} {xc:.6f} {yc:.6f} {w / iw:.6f} {h / ih:.6f}\n")


def image_size(path):
    from PyQt5.QtGui import QPixmap
    pm = QPixmap(path)
    return pm.width(), pm.height()