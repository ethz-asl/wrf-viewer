import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal

from .TabWidget import CustomTabWidget

class MainWindow(QMainWindow):
    resized = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("WRF OUT Viewer")

        self.resize(1000, 600)

        self.createMainWidget()

        # self.resized.connect(self.tab_widget.draw)

    def resizeEvent(self, event):
        self.resized.emit()
        return super(MainWindow, self).resizeEvent(event)

    def createMainWidget(self):
        self.tab_widget = CustomTabWidget(self)
        self.setCentralWidget(self.tab_widget)
