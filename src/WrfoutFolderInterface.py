from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal


from netCDF4 import Dataset
import numpy as np
import os
from wrf import getvar

from .data_utils import get_times_from_filenamelist, get_layer_data
from .custom_widgets import ButtonComboBox, ProgressWidget

class WrfoutFolderInterface(QWidget):
    limits_changed = pyqtSignal(list)
    data_changed = pyqtSignal(tuple)

    def __init__(self, scaling_mode, parent = None):
        super(QWidget, self).__init__(parent)

        self.default_property = 'U'
        self.files_dict = None
        self.folder_name = None
        self.scaling_mode = scaling_mode

        self.domain_box = ButtonComboBox(self)
        self.property_box = ButtonComboBox(self)
        self.layer_box = ButtonComboBox(self)
        self.time_box = ButtonComboBox(self)

        # data options
        main_layout = QVBoxLayout()
        form_layout_data = QFormLayout()
        form_layout_data.addRow(QLabel("Domain:"), self.domain_box)  
        form_layout_data.addRow(QLabel("Property:"), self.property_box)
        form_layout_data.addRow(QLabel("Layer:"), self.layer_box)
        form_layout_data.addRow(QLabel("Time:"), self.time_box)
        main_layout.addLayout(form_layout_data)
        self.setLayout(main_layout)

        # connect signals
        self.domain_box.combo_box.currentTextChanged.connect(self.onDomainChanged)
        self.layer_box.combo_box.currentTextChanged.connect(self.onLayerChanged)
        self.property_box.combo_box.currentTextChanged.connect(self.onPropertyChanged)
        self.time_box.combo_box.currentTextChanged.connect(self.onTimeChanged)

    def setDomains(self, domains):
        previous_domain = self.domain_box.combo_box.currentText()
        self.domain_box.combo_box.clear()

        if domains:
            self.domain_box.combo_box.addItems(domains)
            if previous_domain in domains:
                self.domain_box.combo_box.setCurrentText(previous_domain)
            else:
                self.domain_box.combo_box.setCurrentText(domains[0])

    def setLayers(self, layers):
        previous_layer = self.layer_box.combo_box.currentText()
        self.layer_box.combo_box.clear()

        if layers:
            self.layer_box.combo_box.addItems(layers)
            if previous_layer in layers:
                self.layer_box.combo_box.setCurrentText(previous_layer)
            else:
                self.layer_box.combo_box.setCurrentText('0')

    def setProperties(self, properties):
        self.property_box.combo_box.clear()

        if properties:
            self.property_box.combo_box.addItems(properties)
            if self.default_property in properties:
                self.property_box.combo_box.setCurrentText(self.default_property)
            else:
                self.property_box.combo_box.setCurrentText(properties[0])

    def setScalingMode(self, mode):
        self.scaling_mode = mode

    def setTimes(self, times):
        previous_time = self.time_box.combo_box.currentText()
        self.time_box.combo_box.clear()

        if times:
            self.time_box.combo_box.addItems(times)

            if previous_time in times:
                self.time_box.combo_box.setCurrentText(previous_time)
            else:
                self.time_box.combo_box.setCurrentText(times[0])

    def onDomainChanged(self, domain):
        if domain:
            times = get_times_from_filenamelist(self.files_dict[domain])
            times.sort()
            self.setTimes(times)
            self.updateLimits()

    def onLayerChanged(self, layer):
        if layer:
            self.getData()

            if self.scaling_mode == 'Auto (image)' or self.scaling_mode == 'Auto (layer)':
                self.updateLimits()

    def onLimitsChanged(self):
        mode = self.scalingmode_box.currentText()
        if mode == 'Custom':
            val_min = self.minlimit_box.text()
            val_max = self.maxlimit_box.text()
            if val_min and val_max:
                self.plotting_widget.updateLimits(float(val_min), float(val_max))

    def onPropertyChanged(self, property):
        if property:
            domain = self.domain_box.combo_box.currentText()
            time_index = self.time_box.combo_box.currentIndex()
            ncfile = Dataset(os.path.join(self.folder_name, self.files_dict[domain][time_index]))
            data = getvar(ncfile, property, meta=False)

            if len(data.shape) == 3:
                num_layers = data.shape[0]
            elif len(data.shape) == 2:
                num_layers = 1
            else:
                num_layers = None
                self.error_box = QMessageBox()
                self.error_box.setWindowTitle("Invalid Property")
                self.error_box.setText(str('Only plotting 2D or 3D properties is currently supported'))
                self.error_box.setIcon(QMessageBox.Critical)
                self.error_box.show()

            if num_layers:
                layers = range(num_layers)
                layers_str = [str(l) for l in layers]
                self.setLayers(layers_str)
                self.updateLimits()

    def onTimeChanged(self, time):
        if time:
            self.getData()

            if self.scaling_mode == 'Auto (image)' or self.scaling_mode == 'Auto (timestep)':
                self.updateLimits()

    def getData(self):
        domain = self.domain_box.combo_box.currentText()
        time = self.time_box.combo_box.currentText()
        time_index = self.time_box.combo_box.currentIndex()
        layer = self.layer_box.combo_box.currentText()
        property = self.property_box.combo_box.currentText()

        if not domain or not time or not layer or not property:
            return

        slice_data = get_layer_data(os.path.join(self.folder_name, self.files_dict[domain][time_index]), property, int(layer))

        if not (slice_data is None):
            title = property + ' ' + domain + ' L' + layer + ' ' + time
            self.data_changed.emit((slice_data, title))

    def setFolderName(self, folder_name):
        all_files = os.listdir(folder_name)

        wrfout_files = [f for f in all_files if 'wrfout' in f]

        self.files_dict = {}

        for file in wrfout_files:
            splitted = file.split('_')
            if not splitted[1] in self.files_dict.keys():
                self.files_dict[splitted[1]] = []

            self.files_dict[splitted[1]].append(file)

        for key in self.files_dict.keys():
            self.files_dict[key].sort()

        self.folder_name = folder_name

        domains = list(self.files_dict.keys())
        domains.sort()

        ncfile = Dataset(os.path.join(folder_name, self.files_dict[domains[0]][0]))
        all_properties = list(ncfile.variables.keys())

        plot_properties = []
        for prop in all_properties:
            try:
                data = getvar(ncfile, prop, meta=False)
                if len(data.shape) > 1:
                    plot_properties.append(prop)
            except:
                pass

        self.setDomains(domains)
        self.setProperties(plot_properties)

    def updateLimits(self):
        domain = self.domain_box.combo_box.currentText()
        property = self.property_box.combo_box.currentText()
        time = self.time_box.combo_box.currentText()
        time_index = self.time_box.combo_box.currentIndex()
        layer = self.layer_box.combo_box.currentText()

        val_min = val_max = None
        if self.scaling_mode == 'Auto (image)':
            if property and domain and layer and time:
                slice_data = get_layer_data(os.path.join(self.folder_name, self.files_dict[domain][time_index]), property, int(layer))

                if not (slice_data is None):
                    val_min = slice_data.min()
                    val_max = slice_data.max()

        elif self.scaling_mode == 'Auto (timestep)':
            ncfile = Dataset(os.path.join(self.folder_name, self.files_dict[domain][time_index]))
            data = getvar(ncfile, property, meta=False)
            val_max = data.max()
            val_min = data.min()

        elif self.scaling_mode == 'Auto (layer)':
            if property and domain and layer:
                val_min = np.inf
                val_max = -np.inf

                progress_widget = ProgressWidget(len(self.files_dict[domain]))

                for i, file in enumerate(self.files_dict[domain]):
                    slice_data = get_layer_data(os.path.join(self.folder_name, file), property, int(layer))

                    if not (slice_data is None):
                        val_max = max(val_max, slice_data.max())
                        val_min = min(val_min, slice_data.min())

                    progress_widget.progress_bar.setValue(i)
                    QApplication.processEvents()

                progress_widget.close()

        elif self.scaling_mode == 'Auto (all data)':
            if property and domain:
                val_min = np.inf
                val_max = -np.inf

                progress_widget = ProgressWidget(len(self.files_dict[domain]))

                for i, file in enumerate(self.files_dict[domain]):
                    ncfile = Dataset(os.path.join(self.folder_name, file))
                    data = getvar(ncfile, property, meta=False)
                    val_max = max(val_max, data.max())
                    val_min = min(val_min, data.min())

                    progress_widget.progress_bar.setValue(i)
                    QApplication.processEvents()

                progress_widget.close()

        if (not (val_min is None)) and (not (val_max is None)):
            self.limits_changed.emit([val_min, val_max])
