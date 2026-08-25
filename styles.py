# -*- coding: utf-8 -*-
QSS = """
* {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
    color: #d8dde8;
}
QMainWindow, QWidget#central {
    background-color: #0c0f1c;
}
QMenuBar {
    background-color: #0c0f1c;
    border-bottom: 1px solid #1c2240;
    padding: 4px;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 14px;
    border-radius: 6px;
}
QMenuBar::item:selected {
    background-color: #161c3a;
    color: #00e5ff;
}
QMenu {
    background-color: #12152a;
    border: 1px solid #2a3060;
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    padding: 7px 26px;
    border-radius: 6px;
}
QMenu::item:selected {
    background-color: #1a2244;
    color: #00e5ff;
}
QToolBar {
    background-color: #0c0f1c;
    border-bottom: 1px solid #1c2240;
    padding: 6px;
    spacing: 6px;
}
QToolBar QToolButton {
    background-color: #161c3a;
    border: 1px solid #2a3060;
    border-radius: 8px;
    padding: 6px 14px;
    color: #d8dde8;
}
QToolBar QToolButton:hover {
    background-color: #1f2a55;
    border: 1px solid #00e5ff;
    color: #00e5ff;
}
QToolBar QToolButton:pressed {
    background-color: #00e5ff;
    color: #0c0f1c;
}
QPushButton {
    background-color: #161c3a;
    border: 1px solid #2a3060;
    border-radius: 8px;
    padding: 7px 16px;
    color: #d8dde8;
}
QPushButton:hover {
    background-color: #1f2a55;
    border: 1px solid #00e5ff;
    color: #00e5ff;
}
QPushButton:pressed {
    background-color: #00e5ff;
    color: #0c0f1c;
}
QPushButton:disabled {
    background-color: #12152a;
    color: #4a5275;
    border: 1px solid #1c2240;
}
QPushButton#primary {
    background-color: #00bcd4;
    border: none;
    color: #0c0f1c;
    font-weight: bold;
}
QPushButton#primary:hover {
    background-color: #00e5ff;
}
QPushButton#danger {
    background-color: #2a1428;
    border: 1px solid #ff4081;
    color: #ff80ab;
}
QPushButton#danger:hover {
    background-color: #ff4081;
    color: #0c0f1c;
}
QListWidget {
    background-color: #10142a;
    border: 1px solid #1c2240;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 7px 10px;
    border-radius: 6px;
}
QListWidget::item:selected {
    background-color: #16305c;
    color: #00e5ff;
    border: 1px solid #00bcd4;
}
QListWidget::item:hover {
    background-color: #1a2244;
}
QLineEdit, QSpinBox, QComboBox {
    background-color: #10142a;
    border: 1px solid #2a3060;
    border-radius: 8px;
    padding: 6px 10px;
    selection-background-color: #00bcd4;
    selection-color: #0c0f1c;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #00e5ff;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #12152a;
    border: 1px solid #2a3060;
    border-radius: 8px;
    selection-background-color: #16305c;
    selection-color: #00e5ff;
    padding: 4px;
    outline: none;
}
QLabel {
    background: transparent;
}
QLabel#title {
    color: #00e5ff;
    font-size: 15px;
    font-weight: bold;
}
QLabel#hint {
    color: #6a7390;
    font-size: 11px;
}
QLabel#bigcount {
    color: #00bcd4;
    font-size: 22px;
    font-weight: bold;
}
QGroupBox {
    border: 1px solid #1c2240;
    border-radius: 10px;
    margin-top: 16px;
    padding: 10px 8px 8px 8px;
    background-color: #10142a;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 8px;
    color: #00bcd4;
    font-weight: bold;
}
QScrollBar:vertical {
    background: #0c0f1c;
    width: 10px;
    border: none;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #2a3060;
    min-height: 30px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #00bcd4;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #0c0f1c;
    height: 10px;
    border: none;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #2a3060;
    min-width: 30px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background: #00bcd4;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QStatusBar {
    background-color: #0c0f1c;
    border-top: 1px solid #1c2240;
    color: #6a7390;
}
QStatusBar QLabel {
    padding: 2px 8px;
}
QSplitter::handle {
    background-color: #1c2240;
    width: 3px;
}
QSplitter::handle:hover {
    background-color: #00bcd4;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #2a3060;
    background-color: #10142a;
}
QCheckBox::indicator:checked {
    background-color: #00bcd4;
    border: 1px solid #00e5ff;
}
QFrame#panel {
    background-color: #10142a;
    border: 1px solid #1c2240;
    border-radius: 10px;
}
QMessageBox {
    background-color: #eef1f6;
    color: #000000;
}
QMessageBox QLabel {
    color: #000000;
}
QMessageBox QPushButton {
    color: #000000;
    background-color: #dde2ec;
    border: 1px solid #aab2c5;
    border-radius: 6px;
    padding: 6px 18px;
    min-width: 60px;
}
QMessageBox QPushButton:hover {
    background-color: #ccd3e0;
    border: 1px solid #00bcd4;
}
QMessageBox QPushButton:pressed {
    background-color: #00bcd4;
    color: #000000;
}
QInputDialog {
    background-color: #eef1f6;
    color: #000000;
}
QInputDialog QLabel {
    color: #000000;
}
"""