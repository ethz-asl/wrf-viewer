from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal

import numpy as np
import h5py
import os

from .custom_widgets import ButtonComboBox, ProgressWidget

class HDF5FileInterface(QWidget):
    limits_changed = pyqtSignal(list)
    data_changed = pyqtSignal(tuple)

    def __init__(self, scaling_mode, parent = None):
        super(QWidget, self).__init__(parent)

        self.default_property = 'U'
        self.hdf5_file = None
        self.scaling_mode = scaling_mode
        self.time_keys_dict = None

        self.case_box = ButtonComboBox(self)
        self.property_box = ButtonComboBox(self)
        self.layer_box = ButtonComboBox(self)
        self.time_box = ButtonComboBox(self)

        # data options
        main_layout = QVBoxLayout()
        form_layout_data = QFormLayout()
        form_layout_data.addRow(QLabel("Case:"), self.case_box)  
        form_layout_data.addRow(QLabel("Property:"), self.property_box)
        form_layout_data.addRow(QLabel("Layer:"), self.layer_box)
        form_layout_data.addRow(QLabel("Time:"), self.time_box)
        main_layout.addLayout(form_layout_data)
        self.setLayout(main_layout)

        # connect signals
        self.case_box.combo_box.currentTextChanged.connect(self.onCaseChanged)
        self.layer_box.combo_box.currentTextChanged.connect(self.onLayerChanged)
        self.property_box.combo_box.currentTextChanged.connect(self.onPropertyChanged)
        self.time_box.combo_box.currentTextChanged.connect(self.onTimeChanged)

    def setCases(self, cases):
        previous_case = self.case_box.combo_box.currentText()
        self.case_box.combo_box.clear()

        if cases:
            self.case_box.combo_box.addItems(cases)
            if previous_case in cases:
                self.case_box.combo_box.setCurrentText(previous_case)
            else:
                self.case_box.combo_box.setCurrentText(cases[0])

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

    def setTimes(self, times, keys_dict):
        previous_time = self.time_box.combo_box.currentText()
        self.time_box.combo_box.clear()

        if times:
            self.time_box.combo_box.addItems(times)
            self.time_keys_dict = keys_dict

            if previous_time in times:
                self.time_box.combo_box.setCurrentText(previous_time)
            else:
                self.time_box.combo_box.setCurrentText(times[0])

    def onCaseChanged(self, case):
        if case:
            times, keys_dict = self.getTimesFromCase(case)
            properties = self.getPropertiesFromCase(case)
            times.sort()
            properties.sort()
            self.setTimes(times, keys_dict)
            self.setProperties(properties)
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
        case = self.case_box.combo_box.currentText()
        time = self.time_box.combo_box.currentText()
        if property and case and time and not self.hdf5_file is None:
            data = self.hdf5_file[case][self.time_keys_dict[time]][property][...]

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
        case = self.case_box.combo_box.currentText()
        time = self.time_box.combo_box.currentText()
        layer = self.layer_box.combo_box.currentText()
        property = self.property_box.combo_box.currentText()

        if not case or not time or not layer or not property:
            return

        slice_data = self.getLayerData(case, property, time, int(layer))

        if not (slice_data is None):
            title = case + ' ' + property + ' L' + layer + ' ' + time
            self.data_changed.emit((slice_data, title))

    def setFileName(self, file_name):
        try:
            self.hdf5_file = h5py.File(file_name, 'r')
            cases = list(self.hdf5_file.keys())
            self.setCases(cases)

        except:
            self.hdf5_file = None

    def getLayerData(self, case, property, time, layer):
        data = self.hdf5_file[case][self.time_keys_dict[time]][property][...]
        if len(data.shape) == 3:
            return data[int(layer)]
        elif len(data.shape) == 2:
            return data
        else:
            return None

    def getTimesFromCase(self, case):
        if not self.hdf5_file is None:
            times = []
            keys_dict = {}

            for key in self.hdf5_file[case].keys():
                time_str = str(self.hdf5_file[case][key]['timestamp'][...].item().decode('ascii'))
                keys_dict[time_str] = key
                times.append(time_str)
            return times, keys_dict
        else:
            return None, keys_dict

    def getPropertiesFromCase(self, case):
        time_keys = list(self.hdf5_file[case].keys())

        properties = []
        for prop in list(self.hdf5_file[case][time_keys[0]].keys()):
            num_dim = len(self.hdf5_file[case][time_keys[0]][prop][...].shape)
            if num_dim == 2 or num_dim == 3:
                properties.append(prop)

        return properties

    def updateLimits(self):
        case = self.case_box.combo_box.currentText()
        property = self.property_box.combo_box.currentText()
        time = self.time_box.combo_box.currentText()
        time_index = self.time_box.combo_box.currentIndex()
        layer = self.layer_box.combo_box.currentText()

        val_min = val_max = None
        if self.scaling_mode == 'Auto (image)':
            if property and case and layer and time:
                slice_data = self.getLayerData(case, property, time, int(layer))

                if not (slice_data is None):
                    val_min = slice_data.min()
                    val_max = slice_data.max()

        elif self.scaling_mode == 'Auto (timestep)':
            if property and case and layer and time:
                data = self.hdf5_file[case][self.time_keys_dict[time]][property][...]
                val_max = data.max()
                val_min = data.min()

        elif self.scaling_mode == 'Auto (layer)':
            if property and case and layer:
                val_min = np.inf
                val_max = -np.inf

                all_times, _ = self.getTimesFromCase(case)
                progress_widget = ProgressWidget(len(all_times))

                for i, time in enumerate(all_times):
                    slice_data = self.getLayerData(case, property, time, int(layer))

                    if not (slice_data is None):
                        val_max = max(val_max, slice_data.max())
                        val_min = min(val_min, slice_data.min())

                    progress_widget.progress_bar.setValue(i)
                    QApplication.processEvents()

                progress_widget.close()

        elif self.scaling_mode == 'Auto (all data)':
            if property and case:
                val_min = np.inf
                val_max = -np.inf

                all_times, _ = self.getTimesFromCase(case)
                progress_widget = ProgressWidget(len(all_times))

                for i, time in enumerate(all_times):
                    data = self.hdf5_file[case][self.time_keys_dict[time]][property][...]
                    val_max = max(val_max, data.max())
                    val_min = min(val_min, data.min())

                    progress_widget.progress_bar.setValue(i)
                    QApplication.processEvents()

                progress_widget.close()

        if (not (val_min is None)) and (not (val_max is None)):
            self.limits_changed.emit([val_min, val_max])
