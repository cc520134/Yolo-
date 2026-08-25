# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import QThread, pyqtSignal
from ai_annotator import image_size


class AutoAnnotateThread(QThread):
    progress = pyqtSignal(int, int, str)
    finished_ok = pyqtSignal(int, int, list, dict)
    error = pyqtSignal(str)

    def __init__(self, model, image_files, save_dir, class_names,
                 conf=0.25, skip_existing=True):
        super().__init__()
        self.model = model
        self.image_files = image_files
        self.save_dir = save_dir
        self.conf = conf
        self.skip_existing = skip_existing
        self._cancel = False
        self.class_map = {}
        self.merged_names = list(class_names)

    def cancel(self):
        self._cancel = True

    def _ensure_class(self, model_id, model_name):
        if model_id in self.class_map:
            return self.class_map[model_id]
        if model_name in self.merged_names:
            pid = self.merged_names.index(model_name)
        else:
            pid = len(self.merged_names)
            self.merged_names.append(model_name)
        self.class_map[model_id] = pid
        return pid

    def run(self):
        processed = 0
        skipped = 0
        total = len(self.image_files)
        results = {}
        for i, img_path in enumerate(self.image_files):
            if self._cancel:
                break
            name = os.path.basename(img_path)
            self.progress.emit(i, total, name)
            txt_path = os.path.join(self.save_dir,
                                    os.path.splitext(name)[0] + ".txt")
            if self.skip_existing and os.path.exists(txt_path) \
                    and os.path.getsize(txt_path) > 0:
                skipped += 1
                continue
            try:
                boxes = self.model.predict(img_path, conf=self.conf)
            except Exception as e:
                self.error.emit(f"{name} 推理失败: {e}")
                continue
            iw, ih = image_size(img_path)
            if iw <= 0 or ih <= 0:
                continue
            mapped = []
            for cid, x, y, w, h in boxes:
                x = max(0, min(x, iw))
                y = max(0, min(y, ih))
                w = max(0, min(w, iw - x))
                h = max(0, min(h, ih - y))
                if w <= 0 or h <= 0:
                    continue
                pid = self._ensure_class(cid, self.model.class_name(cid))
                mapped.append({'class_id': pid, 'x': x, 'y': y, 'w': w, 'h': h})
            results[img_path] = mapped
            processed += 1
        self.finished_ok.emit(processed, skipped, self.merged_names, results)