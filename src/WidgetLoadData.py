from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class WidgetLoadData(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.load_db_button = QPushButton('Select source folder', self)
        self.load_db_button.setMaximumWidth(400)
        self.load_db_button.setShortcut('Ctrl+L')

        main_layout = QVBoxLayout()        
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.load_db_button)
        main_layout.addStretch()
        self.setLayout(main_layout)