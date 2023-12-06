from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class WidgetLoadData(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.load_db_button_folder = QPushButton('Select wrfout folder', self)
        self.load_db_button_folder.setMaximumWidth(400)
        self.load_db_button_folder.setShortcut('Ctrl+W')

        self.load_db_button_file = QPushButton('Select nc dataset file', self)
        self.load_db_button_file.setMaximumWidth(400)
        self.load_db_button_file.setShortcut('Ctrl+L')

        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.load_db_button_folder)
        main_layout.addWidget(self.load_db_button_file)
        self.setLayout(main_layout)