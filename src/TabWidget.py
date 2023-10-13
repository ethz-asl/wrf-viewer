from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator

from .WidgetLoadData import WidgetLoadData
from .WidgetPlotData import WidgetPlotData

class CustomTabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        self.initUi()

        self.tab_widget = QTabWidget()

        self.tabs = [self.ui_open_widget,
                     self.plot_widget
                     ]

        self.tab_names = ['Set Data', 'Plot Data']

        # Add tabs
        self.tab_widget.addTab(self.tabs[0], self.tab_names[0])

        # Add tabs to widget
        self.layout.addWidget(self.tab_widget)

        self.plotting_init = False

    def initUi(self):
        self.ui_open_widget = WidgetLoadData(self)
        self.plot_widget = WidgetPlotData(self)

    def onDataFolderSet(self, value):
        if not self.plotting_init:
            self.tab_widget.addTab(self.tabs[1], self.tab_names[1])
            self.tab_widget.setCurrentIndex(1)
            self.plotting_init = True

        self.plot_widget.onDataFolderSet(value)

    def onDataFileSet(self, value):
        if not self.plotting_init:
            self.tab_widget.addTab(self.tabs[1], self.tab_names[1])
            self.tab_widget.setCurrentIndex(1)
            self.plotting_init = True
        print('TODO', value)
