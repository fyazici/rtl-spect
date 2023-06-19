#!/usr/bin/env python

import sys
from PyQt6.QtWidgets import QApplication

from rtl_spect.MainWindow import MainWindow


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
