from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal

from datetime import datetime
from netCDF4 import Dataset
import numpy as np
import os

from .custom_widgets import ButtonComboBox, ProgressWidget

class NcFileInterface(QWidget):
    limits_changed = pyqtSignal(list)
    data_changed = pyqtSignal(tuple)

    def __init__(self, scaling_mode, parent = None):
        super(QWidget, self).__init__(parent)

        self.default_property = 'U'
        self.nc_file = None
        self.scaling_mode = scaling_mode
        self.time_keys_dict = None

        self.case_box = ButtonComboBox(self)
        self.model_box = ButtonComboBox(self)
        self.property_box = ButtonComboBox(self)
        self.layer_box = ButtonComboBox(self)
        self.time_box = ButtonComboBox(self)

        # data options
        main_layout = QVBoxLayout()
        form_layout_data = QFormLayout()
        form_layout_data.addRow(QLabel("Case:"), self.case_box)  
        form_layout_data.addRow(QLabel("Model:"), self.model_box)  
        form_layout_data.addRow(QLabel("Property:"), self.property_box)
        form_layout_data.addRow(QLabel("Layer:"), self.layer_box)
        form_layout_data.addRow(QLabel("Time:"), self.time_box)
        main_layout.addLayout(form_layout_data)
        self.setLayout(main_layout)

        # connect signals
        self.case_box.combo_box.currentTextChanged.connect(self.onCaseChanged)
        self.model_box.combo_box.currentTextChanged.connect(self.onModelChanged)
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

    def setModels(self, models):
        previous_model = self.model_box.combo_box.currentText()
        self.model_box.combo_box.clear()

        if models:
            self.model_box.combo_box.addItems(models)
            if previous_model in models:
                self.model_box.combo_box.setCurrentText(previous_model)
            else:
                self.model_box.combo_box.setCurrentText(models[0])

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
            models = self.getModelsFromCase(case)
            self.setModels(models)

    def onModelChanged(self, model):
        case = self.case_box.combo_box.currentText()
        if model and case:
            times, keys_dict = self.getTimesFromCase(case, model)
            properties = self.getPropertiesFromCase(case, model)
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
        model = self.model_box.combo_box.currentText()
        time = self.time_box.combo_box.currentText()
        if property and case and time and not self.nc_file is None:
            dims = self.getDims(case, model, property)
            has_time = self.propertyHasTimeDim(case, model, property)
            spatial_dims = [d for d in dims if d != 'time']
            if property == 'S' or property == 'S_max':
                # take the dimensions of only the u wind that is available as it was used to compute S and S_max
                property_adj = 'U'
            else:
                property_adj = property
            data_shape = self.nc_file[case][model].variables[property_adj].shape

            if len(spatial_dims) == 3:
                if has_time:
                    num_layers = data_shape[1]
                else:
                    num_layers = data_shape[0]
            elif len(spatial_dims) == 2:
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
            try:
                self.getData()

                if self.scaling_mode == 'Auto (image)' or self.scaling_mode == 'Auto (timestep)':
                    self.updateLimits()
            except:
                # due to the update order in case of a model change the time gets updated before the
                # property this causes an error here that is caught with this exception
                pass

    def getDims(self, case, model, property):
        if property == 'S' or property == 'S_max':
            # take the dimensions of only the u wind that is available as it was used to compute S and S_max
            property_adj = 'U'
        else:
            property_adj = property
        return self.nc_file[case][model].variables[property_adj].dimensions

    def propertyHasTimeDim(self, case, model, property):
        dims = self.getDims(case, model, property)
        return 'time' in dims

    def getData(self):
        case = self.case_box.combo_box.currentText()
        model = self.model_box.combo_box.currentText()
        time = self.time_box.combo_box.currentText()
        layer = self.layer_box.combo_box.currentText()
        property = self.property_box.combo_box.currentText()

        if not case or not time or not layer or not property or not model:
            return

        slice_data = self.getLayerData(case, model, property, time, int(layer))

        if not (slice_data is None):
            title = case + ' ' + model + ' ' + property + ' L' + layer + ' ' + time
            self.data_changed.emit((slice_data, title))

    def setFileName(self, file_name):
        try:
            self.nc_file = Dataset(file_name, "r", format="NETCDF4")
            cases = list(self.nc_file.groups.keys())
            self.setCases(cases)

        except:
            self.nc_file = None

    def getTimeData(self, case, model, property, time):
        has_time = self.propertyHasTimeDim(case, model, property)
        if has_time:
            time_idx = self.time_keys_dict[time]
            data = self.nc_file[case][model].variables[property][time_idx]
        else:
            data = self.nc_file[case][model].variables[property][:]

        return data

    def getLayerData(self, case, model, property, time, layer):
        dims = self.getDims(case, model, property)
        has_time = self.propertyHasTimeDim(case, model, property)
        
        if has_time:
            time_idx = self.time_keys_dict[time]
            if len(dims) == 4:
                if property == 'S':
                    wind_data = None
                    all_properties = AllItems = [self.property_box.combo_box.itemText(i) for i in range(self.property_box.combo_box.count())]
                    for wind_prop in ['U', 'V', 'W']:
                        if wind_prop in all_properties:
                            if wind_data is None:
                                wind_data = self.nc_file[case][model].variables[wind_prop][time_idx, layer] ** 2
                            else:
                                wind_data += self.nc_file[case][model].variables[wind_prop][time_idx, layer] ** 2
                    
                    data = np.sqrt(wind_data)
                elif property == 'S_max':
                    wind_data = None
                    all_properties = AllItems = [self.property_box.combo_box.itemText(i) for i in range(self.property_box.combo_box.count())]
                    for wind_prop in ['U_max', 'V_max', 'W_max']:
                        if wind_prop in all_properties:
                            if wind_data is None:
                                wind_data = self.nc_file[case][model].variables[wind_prop][time_idx, layer] ** 2
                            else:
                                wind_data += self.nc_file[case][model].variables[wind_prop][time_idx, layer] ** 2
                    
                    data = np.sqrt(wind_data)
                else:
                    data = self.nc_file[case][model].variables[property][time_idx, layer]
            elif len(dims) == 3:
                data = self.nc_file[case][model].variables[property][time_idx]
            else:
                data = None
        else:
            if len(dims) == 3:
                data = self.nc_file[case][model].variables[property][layer]
            elif len(dims) == 2:
                data = self.nc_file[case][model].variables[property][:]
            else:
                data = None
        
        return data

    def getModelsFromCase(self, case):
        if not self.nc_file is None:
            models = list(self.nc_file[case].groups.keys())
            return models

    def getTimesFromCase(self, case, model):
        if not self.nc_file is None:
            times = []
            keys_dict = {}

            for i, time in enumerate(self.nc_file[case][model].variables['time'][:]):
                time_str = datetime.utcfromtimestamp(time).strftime("%Y-%m-%d_%H:%M:%S")
                keys_dict[time_str] = i
                times.append(time_str)
            return times, keys_dict
        else:
            return None, {}

    def getPropertiesFromCase(self, case, model):
        properties = []

        for prop in list(self.nc_file[case][model].variables.keys()):
            # check the number of spatial dimensions
            dims = self.nc_file[case][model].variables[prop].dimensions
            dims = [d for d in dims if d != 'time']
            num_dim = len(dims)
            if num_dim == 2 or num_dim == 3:
                properties.append(prop)

        if all(item in properties for item in ['U', 'V']):
            properties.append('S')

        if all(item in properties for item in ['U_max', 'V_max']):
            properties.append('S_max')

        return properties

    def updateLimits(self):
        case = self.case_box.combo_box.currentText()
        model = self.model_box.combo_box.currentText()
        property = self.property_box.combo_box.currentText()
        time = self.time_box.combo_box.currentText()
        time_index = self.time_box.combo_box.currentIndex()
        layer = self.layer_box.combo_box.currentText()

        val_min = val_max = None
        if self.scaling_mode == 'Auto (image)':
            if property and case and layer and time:
                slice_data = self.getLayerData(case, model, property, time, int(layer))

                if not (slice_data is None):
                    val_min = slice_data.min()
                    val_max = slice_data.max()

        elif self.scaling_mode == 'Auto (timestep)':
            if property and case and layer and time:
                data = self.getTimeData(case, model, property, time)
                val_max = data.max()
                val_min = data.min()

        elif self.scaling_mode == 'Auto (layer)':
            if property and case and layer:
                val_min = np.inf
                val_max = -np.inf

                has_time = self.propertyHasTimeDim(case, model, property)
                all_times, _ = self.getTimesFromCase(case, model)
                if has_time:
                    progress_widget = ProgressWidget(len(all_times))

                    for i, time in enumerate(all_times):
                        slice_data = self.getLayerData(case, model, property, time, int(layer))

                        if not (slice_data is None):
                            val_max = max(val_max, slice_data.max())
                            val_min = min(val_min, slice_data.min())

                        progress_widget.progress_bar.setValue(i)
                        QApplication.processEvents()

                    progress_widget.close()
                else:
                    slice_data = self.getLayerData(case, model, property, all_times[0], int(layer))

                    if not (slice_data is None):
                        val_max = max(val_max, slice_data.max())
                        val_min = min(val_min, slice_data.min())

        elif self.scaling_mode == 'Auto (all data)':
            if property and case:
                val_min = np.inf
                val_max = -np.inf

                has_time = self.propertyHasTimeDim(case, model, property)
                if has_time:
                    all_times, _ = self.getTimesFromCase(case, model)
                    progress_widget = ProgressWidget(len(all_times))

                    for i, time in enumerate(all_times):
                        data = self.getTimeData(case, model, property, time)
                        val_max = max(val_max, data.max())
                        val_min = min(val_min, data.min())

                        progress_widget.progress_bar.setValue(i)
                        QApplication.processEvents()

                    progress_widget.close()
                else:
                    data = self.getTimeData(case, model, property, time)
                    val_max = max(val_max, data.max())
                    val_min = min(val_min, data.min())

        if (not (val_min is None)) and (not (val_max is None)):
            self.limits_changed.emit([val_min, val_max])
