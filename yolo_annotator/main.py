# -*- coding: utf-8 -*-
import os
import re
import sys
try:
    import torch
except Exception:
    pass
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QKeySequence, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QLineEdit,
    QFileDialog, QMessageBox, QStatusBar, QToolBar, QAction, QSplitter,
    QGroupBox, QShortcut, QFrame, QProgressDialog, QInputDialog
)
from canvas import AnnotationCanvas, color_for_class, make_color_icon
from styles import QSS

IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff')


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO 标注工具")
        self.resize(1440, 880)
        self.setMinimumSize(1000, 650)

        self.image_dir = ""
        self.save_dir = ""
        self.image_files = []
        self.current_index = -1
        self.class_names = []
        self.current_class_id = -1
        self.unsaved = False
        self.ai_model = None
        self.auto_thread = None
        self.progress_dialog = None
        self.auto_results = {}

        self.canvas = AnnotationCanvas()
        self.canvas.boxCreated.connect(self.on_box_created)
        self.canvas.boxSelected.connect(self.on_box_selected)
        self.canvas.boxDeleted.connect(self.on_box_deleted)

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()
        self._build_shortcuts()

        self.setStyleSheet(QSS)
        self._update_class_ui()
        self._update_nav_state()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        left = QFrame()
        left.setObjectName("panel")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(6)
        t1 = QLabel("图片列表")
        t1.setObjectName("title")
        left_layout.addWidget(t1)
        self.image_list = QListWidget()
        self.image_list.setUniformItemSizes(True)
        self.image_list.itemClicked.connect(self.on_image_list_clicked)
        left_layout.addWidget(self.image_list, 1)
        splitter.addWidget(left)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(6)
        info_bar = QHBoxLayout()
        self.lbl_current = QLabel("未打开图片文件夹")
        self.lbl_current.setObjectName("title")
        info_bar.addWidget(self.lbl_current)
        info_bar.addStretch()
        self.lbl_size = QLabel("")
        self.lbl_size.setObjectName("hint")
        info_bar.addWidget(self.lbl_size)
        center_layout.addLayout(info_bar)
        center_layout.addWidget(self.canvas, 1)
        hint = QLabel("左键拖动画框  |  右键删除框  |  滚轮缩放  |  A/D 切换  |  Del 删除  |  S 保存  |  1-9 选类别")
        hint.setObjectName("hint")
        hint.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(hint)
        splitter.addWidget(center)

        right = QFrame()
        right.setObjectName("panel")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(8)

        class_group = QGroupBox("类别管理")
        cg = QVBoxLayout(class_group)
        cg.setSpacing(6)
        row = QHBoxLayout()
        self.edit_class = QLineEdit()
        self.edit_class.setPlaceholderText("输入类别名 回车添加")
        self.edit_class.returnPressed.connect(self.add_class)
        row.addWidget(self.edit_class, 1)
        btn_add = QPushButton("添加")
        btn_add.clicked.connect(self.add_class)
        row.addWidget(btn_add)
        cg.addLayout(row)

        self.class_list = QListWidget()
        self.class_list.itemClicked.connect(self.on_class_list_clicked)
        cg.addWidget(self.class_list, 1)

        self.lbl_cur_class = QLabel("当前类别: 未选择")
        self.lbl_cur_class.setObjectName("hint")
        cg.addWidget(self.lbl_cur_class)

        cb = QHBoxLayout()
        b1 = QPushButton("删除类别")
        b1.setObjectName("danger")
        b1.clicked.connect(self.delete_class)
        cb.addWidget(b1)
        b2 = QPushButton("保存classes")
        b2.clicked.connect(self.save_classes)
        cb.addWidget(b2)
        cg.addLayout(cb)
        right_layout.addWidget(class_group, 1)

        box_group = QGroupBox("当前标注")
        bg = QVBoxLayout(box_group)
        bg.setSpacing(6)
        self.box_list = QListWidget()
        self.box_list.itemClicked.connect(self.on_box_list_clicked)
        bg.addWidget(self.box_list, 1)
        bb = QHBoxLayout()
        b3 = QPushButton("删除选中")
        b3.setObjectName("danger")
        b3.clicked.connect(self.delete_selected_box)
        bb.addWidget(b3)
        b4 = QPushButton("清空当前")
        b4.setObjectName("danger")
        b4.clicked.connect(self.clear_current_boxes)
        bb.addWidget(b4)
        bg.addLayout(bb)
        right_layout.addWidget(box_group, 1)

        splitter.addWidget(right)
        splitter.setSizes([260, 780, 320])

    def _build_menu(self):
        mb = self.menuBar()
        fm = mb.addMenu("文件(&F)")
        a = QAction("打开图片文件夹", self); a.setShortcut("Ctrl+O"); a.triggered.connect(self.open_dir); fm.addAction(a)
        a = QAction("保存标注", self); a.setShortcut("Ctrl+S"); a.triggered.connect(self.save_current); fm.addAction(a)
        a = QAction("设置标注保存目录", self); a.triggered.connect(self.set_save_dir); fm.addAction(a)
        fm.addSeparator()
        a = QAction("导出全部并保存classes", self); a.triggered.connect(self.export_all); fm.addAction(a)
        fm.addSeparator()
        a = QAction("退出", self); a.setShortcut("Ctrl+Q"); a.triggered.connect(self.close); fm.addAction(a)

        vm = mb.addMenu("视图(&V)")
        a = QAction("适应窗口", self); a.setShortcut("F"); a.triggered.connect(self.canvas.fit_to_window); vm.addAction(a)

        hm = mb.addMenu("帮助(&H)")
        a = QAction("关于", self); a.triggered.connect(self.show_about); hm.addAction(a)

    def _build_toolbar(self):
        tb = QToolBar("主工具栏")
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        self.addToolBar(tb)
        a = QAction("打开图片文件夹", self); a.triggered.connect(self.open_dir); tb.addAction(a)
        tb.addSeparator()
        a = QAction("上一张", self); a.triggered.connect(self.prev_image); tb.addAction(a)
        a = QAction("下一张", self); a.triggered.connect(self.next_image); tb.addAction(a)
        tb.addSeparator()
        a = QAction("单个保存", self); a.triggered.connect(self.save_current); tb.addAction(a)
        a = QAction("全部保存", self); a.triggered.connect(self.export_all); tb.addAction(a)
        a = QAction("自动标注", self); a.triggered.connect(self.auto_annotate); tb.addAction(a)
        tb.addSeparator()
        a = QAction("适应窗口", self); a.triggered.connect(self.canvas.fit_to_window); tb.addAction(a)

    def _build_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.lbl_status = QLabel("就绪")
        sb.addWidget(self.lbl_status, 1)
        self.lbl_save_dir = QLabel("保存目录: 未设置")
        self.lbl_save_dir.setObjectName("hint")
        sb.addPermanentWidget(self.lbl_save_dir)

    def _build_shortcuts(self):
        QShortcut(QKeySequence("A"), self, self.prev_image)
        QShortcut(QKeySequence("D"), self, self.next_image)
        QShortcut(QKeySequence("Left"), self, self.prev_image)
        QShortcut(QKeySequence("Right"), self, self.next_image)
        QShortcut(QKeySequence("S"), self, self.save_current)
        QShortcut(QKeySequence("Delete"), self, self.delete_selected_box)
        QShortcut(QKeySequence("F"), self, self.canvas.fit_to_window)
        for i in range(9):
            QShortcut(QKeySequence(str(i + 1)), self,
                      lambda idx=i: self.select_class_by_index(idx))

    def open_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择图片文件夹", "")
        if not d:
            return
        self.image_dir = d
        self.image_files = []
        self.auto_results = {}
        self.unsaved = False
        self.current_index = -1
        for name in sorted(os.listdir(d), key=natural_key):
            if name.lower().endswith(IMAGE_EXTS):
                self.image_files.append(os.path.join(d, name))
        if not self.image_files:
            self.image_list.clear()

            self.canvas.image = None
            self.canvas.boxes = []
            self.canvas.update()
            QMessageBox.information(self, "提示", "该目录下没有图片文件")
            return
        self.image_list.clear()
        for p in self.image_files:
            it = QListWidgetItem(os.path.basename(p))
            it.setToolTip(p)
            self.image_list.addItem(it)
        self.load_classes()
        self.goto_image(0)
        self.lbl_status.setText(f"已加载 {len(self.image_files)} 张图片    目录: {d}")
        self._update_save_dir_label()

    def goto_image(self, idx):
        if idx < 0 or idx >= len(self.image_files):
            return
        if 0 <= self.current_index < len(self.image_files):
            cur_path = self.image_files[self.current_index]
            if cur_path in self.auto_results:
                self.auto_results[cur_path] = [dict(b) for b in self.canvas.boxes]
            elif self.unsaved:
                self.save_current(silent=True)
        self.current_index = idx
        path = self.image_files[idx]
        self.canvas.load_image(path)
        self.canvas.set_class_names(self.class_names)
        self._load_boxes(path)
        self.image_list.setCurrentRow(idx)
        self.lbl_current.setText(f"[{idx + 1}/{len(self.image_files)}]  {os.path.basename(path)}")
        if not self.canvas.image.isNull():
            self.lbl_size.setText(f"{self.canvas.image.width()} x {self.canvas.image.height()}")
        self.refresh_box_list()
        self._update_nav_state()
        self.unsaved = False

    def _load_boxes(self, path):
        if path in self.auto_results:
            self.canvas.set_boxes([dict(b) for b in self.auto_results[path]])
        else:
            self.load_annotation(path)

    def _write_txt_for(self, image_path, boxes):
        pm = QPixmap(image_path)
        iw, ih = pm.width(), pm.height()
        if iw <= 0 or ih <= 0:
            return
        ap = self.annotation_path(image_path)
        with open(ap, 'w', encoding='utf-8') as f:
            for b in boxes:
                xc = (b['x'] + b['w'] / 2) / iw
                yc = (b['y'] + b['h'] / 2) / ih
                f.write(f"{b['class_id']} {xc:.6f} {yc:.6f} {b['w'] / iw:.6f} {b['h'] / ih:.6f}\n")

    def prev_image(self):
        if self.current_index > 0:
            self.goto_image(self.current_index - 1)

    def next_image(self):
        if self.current_index < len(self.image_files) - 1:
            self.goto_image(self.current_index + 1)

    def on_image_list_clicked(self, item):
        self.goto_image(self.image_list.row(item))

    def _update_nav_state(self):
        if len(self.image_files) == 0:
            self.lbl_current.setText("未打开图片文件夹")

    def ensure_save_dir(self):
        if self.save_dir:
            return True
        d = QFileDialog.getExistingDirectory(self, "选择标注保存目录",
                                             self.image_dir or "")
        if d:
            self.save_dir = d
            self._update_save_dir_label()
            return True
        return False

    def set_save_dir(self):
        d = QFileDialog.getExistingDirectory(self, "设置标注保存目录",
                                             self.save_dir or self.image_dir or "")
        if d:
            self.save_dir = d
            self._update_save_dir_label()
            self.lbl_status.setText(f"标注保存目录: {d}")
            self.load_classes()
            if 0 <= self.current_index < len(self.image_files):
                self.load_annotation(self.image_files[self.current_index])
                self.refresh_box_list()

    def _update_save_dir_label(self):
        if self.save_dir:
            self.lbl_save_dir.setText(f"保存目录: {self.save_dir}")
        else:
            self.lbl_save_dir.setText("保存目录: 未设置")

    def load_classes(self):
        self.class_names = []
        for base_dir in (self.save_dir, self.image_dir):
            if not base_dir:
                continue
            path = os.path.join(base_dir, "classes.txt")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        name = line.strip()
                        if name:
                            self.class_names.append(name)
                break
        self._update_class_ui()
        self.canvas.set_class_names(self.class_names)

    def save_classes(self):
        if not self.ensure_save_dir():
            return
        path = os.path.join(self.save_dir, "classes.txt")
        with open(path, 'w', encoding='utf-8') as f:
            for name in self.class_names:
                f.write(name + "\n")
        self.lbl_status.setText(f"类别已保存: {path}")

    def add_class(self):
        name = self.edit_class.text().strip()
        if not name:
            return
        if name in self.class_names:
            QMessageBox.information(self, "提示", f"类别 '{name}' 已存在")
            return
        self.class_names.append(name)
        self.edit_class.clear()
        self._update_class_ui()
        self.canvas.set_class_names(self.class_names)
        if self.image_dir or self.save_dir:
            self.save_classes()
        self.current_class_id = len(self.class_names) - 1
        self.canvas.set_current_class(self.current_class_id)
        self.class_list.setCurrentRow(self.current_class_id)
        self._update_cur_class_label()

    def delete_class(self):
        r = self.class_list.currentRow()
        if r < 0:
            return
        name = self.class_names[r]
        ret = QMessageBox.question(self, "确认",
                                   f"删除类别 '{name}'？\n相关标注的 class_id 可能失效")
        if ret != QMessageBox.Yes:
            return
        del self.class_names[r]
        self._update_class_ui()
        self.canvas.set_class_names(self.class_names)
        if self.image_dir or self.save_dir:
            self.save_classes()
        if self.current_class_id == r:
            self.current_class_id = -1
        elif self.current_class_id > r:
            self.current_class_id -= 1
        self._update_cur_class_label()

    def _update_class_ui(self):
        self.class_list.clear()
        for i, name in enumerate(self.class_names):
            it = QListWidgetItem(f"[{i}]  {name}")
            it.setIcon(make_color_icon(color_for_class(i)))
            self.class_list.addItem(it)

    def _update_cur_class_label(self):
        if 0 <= self.current_class_id < len(self.class_names):
            self.lbl_cur_class.setText(
                f"当前类别: [{self.current_class_id}] {self.class_names[self.current_class_id]}")
        else:
            self.lbl_cur_class.setText("当前类别: 未选择")

    def on_class_list_clicked(self, item):
        self.current_class_id = self.class_list.row(item)
        self.canvas.set_current_class(self.current_class_id)
        self._update_cur_class_label()
        self.lbl_status.setText(f"已选择类别: [{self.current_class_id}] {self.class_names[self.current_class_id]}")

    def select_class_by_index(self, idx):
        if 0 <= idx < len(self.class_names):
            self.current_class_id = idx
            self.canvas.set_current_class(idx)
            self.class_list.setCurrentRow(idx)
            self._update_cur_class_label()
            self.lbl_status.setText(f"已选择类别: [{idx}] {self.class_names[idx]}")

    def on_box_created(self, x, y, w, h):
        if not self.save_dir:
            QMessageBox.information(self, "提示", "开始标注，请选择保存标签位置")
            if not self.ensure_save_dir():
                return
        if self.current_class_id < 0:
            if not self.class_names:
                QMessageBox.warning(self, "提示", "请先添加类别")
                return
            self.current_class_id = 0
            self.canvas.set_current_class(0)
            self.class_list.setCurrentRow(0)
            self._update_cur_class_label()
        cid = self.current_class_id
        self.canvas.add_box(cid, x, y, w, h)
        self.refresh_box_list()
        self.unsaved = True
        self.lbl_status.setText(f"新增标注: [{cid}] {self.class_names[cid]}  ({w}x{h})")

    def on_box_selected(self, idx):
        if 0 <= idx < self.box_list.count():
            self.box_list.setCurrentRow(idx)

    def on_box_deleted(self, idx):
        self.refresh_box_list()
        self.unsaved = True

    def on_box_list_clicked(self, item):
        self.canvas.selected_index = self.box_list.row(item)
        self.canvas.update()

    def delete_selected_box(self):
        if self.canvas.selected_index >= 0:
            self.canvas.delete_selected()
            self.unsaved = True

    def clear_current_boxes(self):
        if not self.canvas.boxes:
            return
        ret = QMessageBox.question(self, "确认", "清空当前图片所有标注？")
        if ret == QMessageBox.Yes:
            self.canvas.boxes = []
            self.canvas.selected_index = -1
            self.canvas.update()
            if 0 <= self.current_index < len(self.image_files):
                cur = self.image_files[self.current_index]
                if cur in self.auto_results:
                    self.auto_results[cur] = []
            self.refresh_box_list()
            self.unsaved = True

    def refresh_box_list(self):
        self.box_list.clear()
        for i, b in enumerate(self.canvas.boxes):
            cid = b['class_id']
            name = self.class_names[cid] if cid < len(self.class_names) else f"#{cid}"
            it = QListWidgetItem(f"[{i}] {name}  ({b['w']}x{b['h']})  @({b['x']},{b['y']})")
            it.setIcon(make_color_icon(color_for_class(cid), 14))
            self.box_list.addItem(it)
        if 0 <= self.canvas.selected_index < self.box_list.count():
            self.box_list.setCurrentRow(self.canvas.selected_index)

    def annotation_path(self, image_path):
        name = os.path.splitext(os.path.basename(image_path))[0] + ".txt"
        target_dir = self.save_dir if self.save_dir else os.path.dirname(image_path)
        return os.path.join(target_dir, name)

    def load_annotation(self, image_path):
        boxes = []
        ap = self.annotation_path(image_path)
        if os.path.exists(ap):
            iw = self.canvas.image.width()
            ih = self.canvas.image.height()
            if iw <= 0 or ih <= 0:
                return
            with open(ap, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) != 5:
                        continue
                    try:
                        cid = int(parts[0])
                        xc, yc, w, h = map(float, parts[1:])
                    except ValueError:
                        continue
                    x = int((xc - w / 2) * iw)
                    y = int((yc - h / 2) * ih)
                    bw = int(w * iw)
                    bh = int(h * ih)
                    boxes.append({'class_id': cid, 'x': x, 'y': y, 'w': bw, 'h': bh})
        self.canvas.set_boxes(boxes)

    def save_current(self, silent=False):
        if (self.current_index < 0 or self.current_index >= len(self.image_files)
                or self.canvas.image is None or self.canvas.image.isNull()):
            if not silent:
                QMessageBox.warning(self, "警告", "没有可保存的图片")
            return
        if not self.save_dir:
            if silent:
                return
            if not self.ensure_save_dir():
                return
        if self.canvas.image.width() <= 0 or self.canvas.image.height() <= 0:
            return
        cur_path = self.image_files[self.current_index]
        self._write_txt_for(cur_path, self.canvas.boxes)
        self.auto_results.pop(cur_path, None)
        self.unsaved = bool(self.auto_results)
        if not silent:
            self.lbl_status.setText(f"已保存: {os.path.basename(self.annotation_path(cur_path))}")

    def export_all(self):
        if not self.image_files:
            QMessageBox.warning(self, "警告", "请先打开图片文件夹")
            return
        if not self.ensure_save_dir():
            return
        for path, boxes in self.auto_results.items():
            self._write_txt_for(path, boxes)
        self.auto_results = {}
        self.save_current(silent=True)
        self.save_classes()
        self.unsaved = False
        QMessageBox.information(self, "完成",
                                 f"全部保存完成\n所有标注与 classes.txt 已保存至:\n{self.save_dir}")

    def auto_annotate(self):
        if not self.image_files or not self.save_dir:
            QMessageBox.warning(self, "提示", "请先打开图片文件夹和保存标签位置")
            return
        model_path, _ = QFileDialog.getOpenFileName(
            self, "选择YOLO模型文件", "", "模型文件 (*.pt *.onnx);;所有文件 (*.*)")
        if not model_path:
            return
        self.lbl_status.setText("正在加载AI模型...")
        QApplication.processEvents()
        from ai_annotator import AIModel
        self.ai_model = AIModel()
        ok, err = self.ai_model.load(model_path)
        if not ok:
            QMessageBox.warning(self, "模型加载失败", err)
            self.lbl_status.setText("模型加载失败")
            return
        self.lbl_status.setText(
            f"模型已加载: {os.path.basename(model_path)}  类别数: {len(self.ai_model.names)}")
        conf, ok2 = QInputDialog.getDouble(
            self, "置信度阈值", "输入置信度阈值 (0-1):", 0.25, 0.0, 1.0, 2)
        if not ok2:
            return
        from auto_thread import AutoAnnotateThread
        self.auto_thread = AutoAnnotateThread(
            self.ai_model, self.image_files, self.save_dir,
            self.class_names, conf=conf, skip_existing=True)
        total = len(self.image_files)
        self.progress_dialog = QProgressDialog("自动标注中...", "取消", 0, total, self)
        self.progress_dialog.setWindowTitle("AI 自动标注")
        self.progress_dialog.setWindowModality(Qt.ApplicationModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.auto_thread.progress.connect(self.on_auto_progress)
        self.auto_thread.finished_ok.connect(self.on_auto_finished)
        self.auto_thread.error.connect(self.on_auto_error)
        self.progress_dialog.canceled.connect(self.auto_thread.cancel)
        self.lbl_status.setText("AI自动标注进行中...")
        self.auto_thread.start()

    def on_auto_progress(self, cur, total, name):
        if self.progress_dialog:
            self.progress_dialog.setMaximum(total)
            self.progress_dialog.setValue(cur)
            self.progress_dialog.setLabelText(f"处理中 ({cur + 1}/{total}): {name}")

    def on_auto_error(self, msg):
        self.lbl_status.setText(msg)

    def on_auto_finished(self, processed, skipped, merged_names, results):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        if merged_names != self.class_names:
            self.class_names = merged_names
            self._update_class_ui()
            self.canvas.set_class_names(self.class_names)
        self.auto_results = results
        if 0 <= self.current_index < len(self.image_files):
            self._load_boxes(self.image_files[self.current_index])
            self.refresh_box_list()
        self.unsaved = bool(self.auto_results)
        QMessageBox.information(
            self, "完成",
            f"AI自动标注完成\n处理: {processed} 张\n跳过(已有标注): {skipped} 张\n\n"
            f"结果已加载到界面预览，请检查后手动保存")
        self.lbl_status.setText(f"自动标注完成: 处理 {processed}  跳过 {skipped}  (请手动保存)")

    def show_about(self):
        QMessageBox.about(self, "关于",
            "YOLO 标注工具\n\n"
            "基于 PyQt5，生成 YOLO 目标检测格式:\n"
            "  class x_center y_center width height (归一化)\n\n"
            "快捷键:\n"
            "  A / ←     上一张\n"
            "  D / →     下一张\n"
            "  S         保存当前\n"
            "  Del       删除选中框\n"
            "  F         适应窗口\n"
            "  1-9       选择类别\n"
            "  右键      删除所指框")

    def closeEvent(self, event):
        if self.unsaved:
            ret = QMessageBox.question(self, "确认", "有未保存的标注，是否保存？")
            if ret == QMessageBox.Yes:
                self.save_current(silent=True)
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()