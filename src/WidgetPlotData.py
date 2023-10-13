from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, Qt, QDate
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QColor

import os

from .LayerPlotWidget import LayerPlotWidget

class WidgetPlotData(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()

        self.layer_plot_widget = LayerPlotWidget(self)

        self.tab_widget.addTab(self.layer_plot_widget, "Layer Plot")

        self.layout.addWidget(self.tab_widget)


    def onDataFolderSet(self, folder_name):
        self.layer_plot_widget.setFolderName(folder_name)
