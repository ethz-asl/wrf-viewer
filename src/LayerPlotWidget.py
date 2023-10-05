from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDoubleValidator

from netCDF4 import Dataset
import numpy as np
import os
from wrf import getvar

from .LayerImageViewWidget import LayerImageViewWidget
from .data_utils import get_times_from_filenamelist, get_layer_data

class LayerPlotWidget(QWidget):
    def __init__(self, parent = None):
        super(QWidget, self).__init__(parent)

        self.default_property = 'U'
        self.files_dict = None
        self.folder_name = None

        self.onlyDouble = QDoubleValidator()
        self.onlyDouble.setDecimals(2)
        self.onlyDouble.setNotation(QDoubleValidator.StandardNotation)

        self.plotting_widget = LayerImageViewWidget(self)

        self.domain_box = QComboBox()
        self.domain_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.property_box = QComboBox()
        self.property_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.layer_box = QComboBox()
        self.layer_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.time_box = QComboBox()
        self.time_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.cbar_box = QComboBox()
        self.cbar_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cbar_box.addItems(['jet', 'viridis', 'turbo', 'rainbow', 'gray', 'ocean'])
        self.scalingmode_box = QComboBox()
        self.scalingmode_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.scalingmode_box.addItems(['Auto (single)', 'Auto (layer)', 'Auto (domain)', 'Custom'])
        self.minlimit_box = QLineEdit(self)
        self.minlimit_box.setValidator(self.onlyDouble)
        self.minlimit_box.setText('0.0')
        self.minlimit_box.setReadOnly(True)
        self.maxlimit_box = QLineEdit(self)
        self.maxlimit_box.setValidator(self.onlyDouble)
        self.maxlimit_box.setText('1.0')
        self.maxlimit_box.setReadOnly(True)

        self.animation_mode_box = QComboBox()
        self.animation_mode_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.animation_mode_box.addItems(['Time', 'Layer'])
        self.animation_dt_box = QLineEdit(self)
        self.animation_dt_box.setValidator(self.onlyDouble)
        self.animation_dt_box.setText('1.0')
        self.animation_play_button = QPushButton()
        self.animation_play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.animation_stop_button = QPushButton()
        self.animation_stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.animation_save_button = QCheckBox()

        # plotting options
        bar_layout = QVBoxLayout()
        data_selection_box = QGroupBox("Data Options")
        data_selection_box_layout = QVBoxLayout()
        form_layout_data = QFormLayout()
        form_layout_data.addRow(QLabel("Domain:"), self.domain_box)  
        form_layout_data.addRow(QLabel("Property:"), self.property_box)
        form_layout_data.addRow(QLabel("Layer:"), self.layer_box)
        form_layout_data.addRow(QLabel("Time:"), self.time_box)
        data_selection_box_layout.addLayout(form_layout_data)
        data_selection_box.setLayout(data_selection_box_layout)
        bar_layout.addWidget(data_selection_box)

        animation_box = QGroupBox("Animation Options")
        animation_box_layout = QVBoxLayout()

        play_layout = QHBoxLayout()
        play_layout.addWidget(self.animation_play_button)
        play_layout.addWidget(self.animation_stop_button)
        animation_box_layout.addLayout(play_layout)

        form_layout_animation = QFormLayout()
        form_layout_animation.addRow(QLabel("Save:"), self.animation_save_button)  
        form_layout_animation.addRow(QLabel("Mode:"), self.animation_mode_box)  
        form_layout_animation.addRow(QLabel("dt [s]:"), self.animation_dt_box)  
        animation_box_layout.addLayout(form_layout_animation)

        animation_box.setLayout(animation_box_layout)
        bar_layout.addWidget(animation_box)

        # plotting
        plot_layout = QVBoxLayout()
        plot_box = QGroupBox("Layer Plot")
        plot_box_layout = QVBoxLayout()
        plot_box_layout.addWidget(self.plotting_widget)
        plot_box.setLayout(plot_box_layout)
        plot_layout.addWidget(plot_box, stretch=10)

        # display options
        display_layout = QVBoxLayout()
        display_box = QGroupBox("Display options")
        display_box_layout = QVBoxLayout()
        form_layout_display = QFormLayout()
        form_layout_display.addRow(QLabel("C-bar:"), self.cbar_box)  
        display_box_layout.addLayout(form_layout_display)
        display_box.setLayout(display_box_layout)

        display_layout.addWidget(display_box)

        limits_box = QGroupBox("Scaling options")
        limits_box_layout = QVBoxLayout()
        form_layout_limits = QFormLayout()
        form_layout_limits.addRow(QLabel("Mode:"), self.scalingmode_box)
        form_layout_limits.addRow(QLabel("Min:"), self.minlimit_box)
        form_layout_limits.addRow(QLabel("Max:"), self.maxlimit_box)
        limits_box_layout.addLayout(form_layout_limits)
        limits_box.setLayout(limits_box_layout)

        display_layout.addWidget(limits_box)

        # layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(bar_layout)
        main_layout.addLayout(plot_layout, stretch=10)
        main_layout.addLayout(display_layout)
        self.setLayout(main_layout)

        # connect signals
        self.domain_box.currentTextChanged.connect(self.onDomainChanged)
        self.layer_box.currentTextChanged.connect(self.onLayerChanged)
        self.property_box.currentTextChanged.connect(self.onPropertyChanged)
        self.time_box.currentTextChanged.connect(self.onTimeChanged)
        self.cbar_box.currentTextChanged.connect(self.onCbarChanged)
        self.scalingmode_box.currentTextChanged.connect(self.onScalingmodeChanged)
        self.minlimit_box.editingFinished.connect(self.onLimitsChanged)
        self.maxlimit_box.editingFinished.connect(self.onLimitsChanged)

    def setDomains(self, domains):
        self.domain_box.clear()

        if domains:
            self.domain_box.addItems(domains)
            self.domain_box.setCurrentText(domains[0])

    def setLayers(self, layers):
        self.layer_box.clear()

        if layers:
            self.layer_box.addItems(layers)
            self.layer_box.setCurrentText('0') # TODO check if previous value would be still valid and then reset it.

    def setProperties(self, properties):
        self.property_box.clear()

        if properties:
            self.property_box.addItems(properties)
            if self.default_property in properties:
                self.property_box.setCurrentText(self.default_property)

    def setTimes(self, times):
        self.time_box.clear()

        if times:
            self.time_box.addItems(times)
            self.time_box.setCurrentText(times[0])

    def onCbarChanged(self, cbar):
        if cbar:
            self.plotting_widget.setCbar(cbar)

    def onDomainChanged(self, domain):
        if domain:
            times = get_times_from_filenamelist(self.files_dict[domain])
            times.sort()
            self.setTimes(times)
            self.updateLimits()

    def onLayerChanged(self, layer):
        if layer:
            self.updatePlot()

            mode = self.scalingmode_box.currentText()
            if mode == 'Auto (single)' or mode == 'Auto (layer)':
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
            domain = self.domain_box.currentText()
            time_index = self.time_box.currentIndex()
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

    def onScalingmodeChanged(self, mode):
        if mode == 'Custom':
            self.minlimit_box.setReadOnly(False)
            self.maxlimit_box.setReadOnly(False)

            val_min = self.minlimit_box.text()
            val_max = self.maxlimit_box.text()
            if val_min and val_max:
                self.plotting_widget.updateLimits(float(val_min), float(val_max))

        else:
            self.minlimit_box.setReadOnly(True)
            self.maxlimit_box.setReadOnly(True)
            self.updateLimits()


    def onTimeChanged(self, time):
        if time:
            self.updatePlot()

            mode = self.scalingmode_box.currentText()
            if mode == 'Auto (single)':
                self.updateLimits()

    def setFilesDict(self, folder_name, files_dict):
        self.files_dict = files_dict
        self.folder_name = folder_name

        domains = list(files_dict.keys())
        domains.sort()

        ncfile = Dataset(os.path.join(folder_name, files_dict[domains[0]][0]))
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

    def updatePlot(self):
        domain = self.domain_box.currentText()
        time = self.time_box.currentText()
        time_index = self.time_box.currentIndex()
        layer = self.layer_box.currentText()
        property = self.property_box.currentText()

        if not domain or not time or not layer or not property:
            return

        slice_data = get_layer_data(os.path.join(self.folder_name, self.files_dict[domain][time_index]), property, int(layer))

        if not (slice_data is None):
            title = property + ' ' + domain + ' L' + layer + ' ' + time
            self.plotting_widget.plot(slice_data, title)

    def draw(self):
        self.plotting_widget.redraw()

    def updateLimits(self):
        domain = self.domain_box.currentText()
        property = self.property_box.currentText()
        time = self.time_box.currentText()
        time_index = self.time_box.currentIndex()
        layer = self.layer_box.currentText()
        mode = self.scalingmode_box.currentText()

        val_min = val_max = None
        if mode == 'Auto (single)':
            if property and domain and layer and time:
                slice_data = get_layer_data(os.path.join(self.folder_name, self.files_dict[domain][time_index]), property, int(layer))

                if not (slice_data is None):
                    val_min = slice_data.min()
                    val_max = slice_data.max()

        elif mode == 'Auto (layer)':
            if property and domain and layer:
                val_min = np.inf
                val_max = -np.inf

                for file in self.files_dict[domain]:
                    slice_data = get_layer_data(os.path.join(self.folder_name, file), property, int(layer))

                    if not (slice_data is None):
                        val_max = max(val_max, slice_data.max())
                        val_min = min(val_min, slice_data.min())

        elif mode == 'Auto (domain)':
            if property and domain:
                val_min = np.inf
                val_max = -np.inf

                for file in self.files_dict[domain]:
                    ncfile = Dataset(os.path.join(self.folder_name, file))
                    data = getvar(ncfile, property, meta=False)
                    val_max = max(val_max, data.max())
                    val_min = min(val_min, data.min())

        if val_min and val_max:
            self.minlimit_box.setText("{:.2f}".format(val_min))
            self.maxlimit_box.setText("{:.2f}".format(val_max))
            self.plotting_widget.updateLimits(val_min, val_max)
