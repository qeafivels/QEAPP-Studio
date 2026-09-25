"""Entry point: python -m studio.main (from kit root), or python run_studio.py."""
from __future__ import annotations
import os
import sys

def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print('PySide6 not installed. Run: python -m pip install -r requirements-studio.txt', file=sys.stderr)
        return 2
    from studio.core.diagnostics import install_exception_hook
    from studio.gui.window import StudioWindow
    install_exception_hook()
    app = QApplication(sys.argv)
    app.setApplicationName('QEAPP Studio')
    window = StudioWindow()
    window.show()
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())
