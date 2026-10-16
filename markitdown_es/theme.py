STYLE = """
QWidget { color: #172b3a; font-family: 'Segoe UI'; font-size: 14px; }
QMainWindow, QWidget#root { background: #f2f5f7; }
QLabel#brand { background: #16394b; color: white; border-radius: 10px;
  font-size: 20px; font-weight: 700; padding: 12px; }
QLabel#title { font-size: 26px; font-weight: 700; }
QLabel#subtitle, QLabel#muted { color: #526575; }
QLabel#badge { background: #e0f1e9; color: #176044; border-radius: 12px; padding: 6px 12px; }
QFrame#panel { background: white; border: 1px solid #d8e1e7; border-radius: 12px; }
QLabel#section { font-size: 17px; font-weight: 600; }
QPushButton { background: white; border: 1px solid #c3d0d9; border-radius: 6px;
  padding: 9px 14px; font-weight: 600; min-height: 20px; }
QPushButton:hover { background: #edf3f6; border-color: #7c95a5; }
QPushButton:focus { border: 2px solid #087e8b; }
QPushButton:disabled { color: #7b8994; background: #eef1f3; border-color: #dce3e8; }
QPushButton#primary { color: white; background: #087785; border-color: #087785; }
QPushButton#primary:hover { background: #075f6b; }
QPushButton#primary:disabled { background: #d7e2e6; color: #657782; border-color: #d7e2e6; }
QPushButton#drop { border: 2px dashed #9dbac5; background: #f4fafb;
  padding: 20px; font-size: 16px; min-height: 68px; }
QPushButton#drop:hover { background: #e6f4f6; border-color: #087785; }
QTreeWidget { border: none; background: white; outline: none; }
QTreeWidget::item { padding: 12px 4px; border-bottom: 1px solid #edf1f4; }
QTreeWidget::item:selected { color: #123d4c; background: #e6f4f6; }
QHeaderView::section { background: #f5f7f9; border: none; color: #526575;
  padding: 8px; font-size: 12px; font-weight: 600; }
QTabWidget::pane { border: 1px solid #d8e1e7; border-radius: 6px; }
QTabBar::tab { padding: 10px 16px; background: #f2f5f7; border: none; }
QTabBar::tab:selected { background: white; color: #066573; border-bottom: 2px solid #087785; }
QTextEdit, QPlainTextEdit { background: white; border: none; padding: 16px;
  selection-background-color: #b8e2e7; }
QPlainTextEdit { font-family: Consolas; font-size: 13px; }
QLineEdit { border: 1px solid #c3d0d9; background: white; border-radius: 6px; padding: 10px; }
QLineEdit:focus { border: 2px solid #087785; }
QProgressBar { background: #e4ebef; border: none; border-radius: 3px; min-height: 6px; max-height: 6px; }
QProgressBar::chunk { background: #087785; border-radius: 3px; }
QSplitter::handle { background: transparent; width: 16px; }
QStatusBar { background: #f2f5f7; color: #526575; }
"""
