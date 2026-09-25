"""Original QEAPP Studio dark indigo + electric-violet visual language.
Inspired by three-pane editor workflows, not copied from LuaS30-IDE assets/code.
"""
APP_STYLE = '''
QMainWindow,QDialog,QWidget { background:#101322; color:#e3e8ff; font-family:'Segoe UI',Arial; font-size:12px; }
QMenuBar,QMenu,QToolBar { background:#14192a; color:#e6eaff; }
QMenuBar::item:selected,QMenu::item:selected {background:#343559; }
QStatusBar { background:#35316d; color:#e4e8ff; font-size:11px; }
QSplitter::handle { background:#252a42; }
QTreeWidget,QPlainTextEdit,QLineEdit,QComboBox,QSpinBox { background:#15192b; color:#e2e9ff;
  border:1px solid #343d5a; border-radius:4px; selection-background-color:#51489c; }
QTreeWidget {border:0; padding:4px; outline:0;}
QTreeWidget::item {height:23px;}
QTreeWidget::item:selected { background:#31365b; border-left:2px solid #a39aff; }
QTreeWidget::branch { background:#15192b; }
QTabWidget::pane { border:0; background:#121729; }
QTabBar::tab { background:#1b2235; padding:8px 15px; margin-right:2px;
 border-top-left-radius:5px;border-top-right-radius:5px; min-width:76px; }
QTabBar::tab:selected { background:#303451; border-top:2px solid #9688ff; color:#fff; }
QPushButton {background:#272d48; color:#e7e8ff; border:1px solid #3c476c;
 border-radius:6px; padding:6px 10px; min-height:20px;}
QPushButton:hover {background:#3b4069; border-color:#8179e4; }
QPushButton:pressed {background:#5158a2;}
QPushButton:disabled { color:#707a99; background:#1d2236; border-color:#29314c;}
QPushButton#PrimaryButton {background:#675ac8; border-color:#8175eb; font-weight:600;}
QPushButton#PrimaryButton:hover {background:#786be2;}
QPushButton#ActivityButton {background:transparent; border:0; font-size:19px;
 border-left:3px solid transparent; border-radius:0; min-height:38px;}
QPushButton#ActivityButton:checked {background:#252b4b; border-left:3px solid #a18dff;}
QLabel#PanelTitle {font-size:11px; color:#c8d3f8; font-weight:700; letter-spacing:1px;}
QLabel#Subtle {color:#929ebf; font-size:10px;}
QLabel#MetricBadge {background:#18392f; color:#98efc2; padding:4px 7px; border-radius:6px; font-family:Consolas;}
QLabel#PhoneBrand {color:#acbaf4; font-size:11px;font-weight:700;}
QLabel#notice {color:#f4cb7d;}
QFrame#ActivityRail,QFrame#ExplorerDock {background:#161b30; border-right:1px solid #2d3451;}
QFrame#WorkbenchBar {background:#171d31; border-bottom:1px solid #343c55;}
QFrame#BottomPanel {background:#14192d; border-top:1px solid #343a57;}
QFrame#PhoneBezel {background:#222841; border:1px solid #434c70; border-radius:22px;}
QPushButton#DpadButton {background:#394465; font-weight:600; color:#e3ebff;}
QPushButton#SystemButton {background:#2b324f; font-size:10px;}
QGroupBox {border:1px solid #343f61; border-radius:6px; margin-top:6px;
 font-weight:600; padding-top:13px;}
QScrollArea {border:0;}
QScrollBar:vertical {background:#14182a;width:10px;}
QScrollBar::handle:vertical {background:#414969; border-radius:4px;min-height:30px;}
'''
