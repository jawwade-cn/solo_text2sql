import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from src.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    
    app.setFont(QFont("Microsoft YaHei", 9))
    
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
