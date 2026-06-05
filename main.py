import sys
import os
import glob

# Ensure project root is on the path when run directly
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QIcon


def _load_fonts():
    fonts_dir = os.path.join(os.path.dirname(__file__), "assets", "fonts")
    for ttf in sorted(glob.glob(os.path.join(fonts_dir, "*.ttf"))):
        QFontDatabase.addApplicationFont(ttf)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Jamdar")
    app.setOrganizationName("Jamdar")

    _load_fonts()

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
