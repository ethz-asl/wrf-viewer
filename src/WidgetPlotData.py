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
        all_files = os.listdir(folder_name)

        wrfout_files = [f for f in all_files if 'wrfout' in f]

        files_dict = {}

        for file in wrfout_files:
            splitted = file.split('_')
            if not splitted[1] in files_dict.keys():
                files_dict[splitted[1]] = []

            files_dict[splitted[1]].append(file)

        for key in files_dict.keys():
            files_dict[key].sort()

        self.layer_plot_widget.setFilesDict(folder_name, files_dict)
