from PyQt5.QtWidgets import *

class ButtonComboBox(QWidget):
    def __init__(self, parent = None):
        super(QWidget, self).__init__(parent)

        self.combo_box = QComboBox()
        self.combo_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.forward_button = QPushButton()
        self.forward_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowForward))
        self.back_button = QPushButton()
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