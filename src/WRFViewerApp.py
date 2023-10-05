import os
import sys

import PyQt5.QtCore as QtCore
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

from .MainWindow import MainWindow

class WRFViewerApp(QObject):
    data_folder_set = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.app = QApplication(sys.argv)

        self.window = MainWindow()

        self.connectActions()
        self.connectSignals()

    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())

    def connectActions(self):
        self.window.tab_widget.ui_open_widget.load_db_button.clicked.connect(self.initDataset)

    def connectSignals(self):
        self.data_folder_set.connect(self.window.tab_widget.onDataFolderSet)

    def initDataset(self):
        folder_name = QFileDialog.getExistingDirectory(None, "Select data folder", '.')

        if folder_name:
            files_list = os.listdir(folder_name)

            wrfout_files = [f for f in files_list if 'wrfout' in f]

            if len(wrfout_files) > 0:
                self.data_folder_set.emit(folder_name)
            else:
                self.error_box = QMessageBox()
                self.error_box.setWindowTitle("Invalid Folder")
                self.error_box.setText(str('No wrfout files present in the selected folder'))
                self.error_box.setIcon(QMessageBox.Critical)
                self.error_box.show()

