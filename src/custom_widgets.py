from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QDoubleValidator

class ButtonComboBox(QWidget):
    def __init__(self, parent = None):
        super(QWidget, self).__init__(parent)

        self.combo_box = QComboBox(self)
        self.combo_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.forward_button = QPushButton(self)
        self.forward_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowForward))
        self.back_button = QPushButton(self)
        self.back_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.back_button)
        main_layout.addWidget(self.combo_box, stretch=10)
        main_layout.addWidget(self.forward_button)

        self.setLayout(main_layout)

        self.forward_button.clicked.connect(self.onForwardPressed)
        self.back_button.clicked.connect(self.onBackPressed)

    def onForwardPressed(self):
        idx = self.combo_box.currentIndex() + 1
        if idx >= self.combo_box.count():
            idx = 0
        self.combo_box.setCurrentIndex(idx)

    def onBackPressed(self):
        idx = self.combo_box.currentIndex() - 1
        if idx < 0:
            idx = self.combo_box.count() - 1
        self.combo_box.setCurrentIndex(idx)

class ProgressWidget(QWidget):
    def __init__(self, maximum, parent = None):
        super(QWidget, self).__init__(parent)

        self.setWindowTitle(' ')
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(maximum)
        self.progress_widget_layout = QVBoxLayout(self)
        self.progress_widget_layout.addWidget(QLabel('Computing limits ...'))
        self.progress_widget_layout.addWidget(self.progress_bar)
        self.show()

class ErrorBox(QMessageBox):
    def __init__(self, title, message):
        super(QWidget, self).__init__()
        self.setWindowTitle(str(title))
        self.setText(str(message))
        self.setIcon(QMessageBox.Critical)

class CustomComboBox(QComboBox):
    def __init__(self, items, parent = None):
        super().__init__(parent)

        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.addItems(items)

class CustomLineEdit(QLineEdit):
    def __init__(self, value, read_only = False, parent = None):
        super().__init__(parent)

        self.validator = QDoubleValidator()
        self.validator.setDecimals(2)
        self.validator.setNotation(QDoubleValidator.StandardNotation)

        self.setValidator(self.validator)
        self.setText(str(value))
        self.setReadOnly(read_only)