from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import QTimer

import numpy as np
import os
import sip

from .NcFileInterface import NcFileInterface
from .LayerImageViewWidget import LayerImageViewWidget
from .WrfoutFolderInterface import WrfoutFolderInterface
from .custom_widgets import CustomComboBox, CustomLineEdit

class LayerPlotWidget(QWidget):
    def __init__(self, parent = None):
        super(QWidget, self).__init__(parent)

        self.default_property = 'U'
        self.files_dict = None
        self.folder_name = None

        self.plotting_widget = LayerImageViewWidget(self)

        self.cbar_box = CustomComboBox(['jet', 'viridis', 'turbo', 'rainbow', 'gray', 'ocean', 'terrain'])
        self.scalingmode_box = CustomComboBox(['Auto (image)', 'Auto (timestep)', 'Auto (layer)', 'Auto (all data)', 'Custom'])
        self.minlimit_box = CustomLineEdit('0.0', True, self)
        self.maxlimit_box = CustomLineEdit('1.0', True, self)

        self.animation_mode_box = CustomComboBox(['Time', 'Layer'])
        self.animation_dt_box = CustomLineEdit('0.1', False, self)
        self.animation_play_button = QPushButton()
        self.animation_play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.animation_stop_button = QPushButton()
        self.animation_stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.animation_save_button = QCheckBox()

        # data options
        bar_layout = QVBoxLayout()
        data_selection_box = QGroupBox("Data Options")
        self.data_selection_box_layout = QVBoxLayout()
        self.data_interface = QWidget()
        self.data_selection_box_layout.addWidget(self.data_interface)
        data_selection_box.setLayout(self.data_selection_box_layout)
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

        # animation
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animationStep)

        # connect signals
        self.cbar_box.currentTextChanged.connect(self.onCbarChanged)
        self.scalingmode_box.currentTextChanged.connect(self.onScalingmodeChanged)
        self.minlimit_box.editingFinished.connect(self.onCustomLimitsChanged)
        self.maxlimit_box.editingFinished.connect(self.onCustomLimitsChanged)
        self.animation_play_button.clicked.connect(self.onAnimationPlayPressed)
        self.animation_stop_button.clicked.connect(self.onAnimationStopPressed)
        self.animation_dt_box.editingFinished.connect(self.onAnimationDtChanged)

    def onAnimationDtChanged(self):
        dt = self.animation_dt_box.text()
        if dt:
            if self.animation_timer.isActive():
                self.animation_timer.stop()
                self.animation_timer.start(float(dt) * 1000)

    def onAnimationPlayPressed(self):
        dt = self.animation_dt_box.text()
        if dt:
            self.animation_timer.start(float(dt) * 1000)

    def onAnimationStopPressed(self):
        self.animation_timer.stop()

    def onAutoLimitsChanged(self, limits):
        self.minlimit_box.setText(str(limits[0]))
        self.maxlimit_box.setText(str(limits[1]))
        self.plotting_widget.updateLimits(float(limits[0]), float(limits[1]))

    def onCbarChanged(self, cbar):
        if cbar:
            self.plotting_widget.setCbar(cbar)

    def onCustomLimitsChanged(self):
        mode = self.scalingmode_box.currentText()
        if mode == 'Custom':
            val_min = self.minlimit_box.text()
            val_max = self.maxlimit_box.text()
            if val_min and val_max:
                self.plotting_widget.updateLimits(float(val_min), float(val_max))

    def onScalingmodeChanged(self, mode):
        if mode == 'Custom':
            self.minlimit_box.setReadOnly(False)
            self.maxlimit_box.setReadOnly(False)

            val_min = self.minlimit_box.text()
            val_max = self.maxlimit_box.text()
            if val_min and val_max:
                self.plotting_widget.updateLimits(float(val_min), float(val_max))

        else:
            self.data_interface.setScalingMode(mode)
            self.minlimit_box.setReadOnly(True)
            self.maxlimit_box.setReadOnly(True)
            self.data_interface.updateLimits()

    def updatePlot(self, data_tuple):
        self.plotting_widget.plot(data_tuple[0], data_tuple[1])

    def setFolderName(self, folder_name):
        if not isinstance(self.data_interface, WrfoutFolderInterface):
            self.data_selection_box_layout.removeWidget(self.data_interface)
            sip.delete(self.data_interface)
            scaling_mode = self.scalingmode_box.currentText()
            self.data_interface = WrfoutFolderInterface(scaling_mode, self)
            self.data_selection_box_layout.addWidget(self.data_interface)
            self.data_interface.limits_changed.connect(self.onAutoLimitsChanged)
            self.data_interface.data_changed.connect(self.updatePlot)

        self.data_interface.setFolderName(folder_name)

    def setFileName(self, folder_name):
        if not isinstance(self.data_interface, NcFileInterface):
            self.data_selection_box_layout.removeWidget(self.data_interface)
            sip.delete(self.data_interface)
            scaling_mode = self.scalingmode_box.currentText()
            self.data_interface = NcFileInterface(scaling_mode, self)
            self.data_selection_box_layout.addWidget(self.data_interface)
            self.data_interface.limits_changed.connect(self.onAutoLimitsChanged)
            self.data_interface.data_changed.connect(self.updatePlot)

        self.data_interface.setFileName(folder_name)

    def animationStep(self):
        animation_mode = self.animation_mode_box.currentText()
        scaling_mode = self.scalingmode_box.currentText()

        if animation_mode == 'Time':
            if scaling_mode != 'Auto (layer)' or scaling_mode == 'Auto (all data)' or scaling_mode == 'Custom':
                index = self.scalingmode_box.findText('Auto (layer)')
                self.scalingmode_box.setCurrentIndex(index)

            self.data_interface.time_box.onForwardPressed()
            index_animation = self.data_interface.time_box.combo_box.currentIndex()

        elif animation_mode == 'Layer':
            if scaling_mode != 'Auto (timestep)' or scaling_mode == 'Auto (all data)' or scaling_mode == 'Custom':
                index = self.scalingmode_box.findText('Auto (timestep)')
                self.scalingmode_box.setCurrentIndex(index)

            self.data_interface.layer_box.onForwardPressed()
            index_animation = self.data_interface.layer_box.combo_box.currentIndex()

        if self.animation_save_button.isChecked():
            property = self.data_interface.property_box.combo_box.currentText()
            filename = property + '_' + animation_mode + str(index_animation).zfill(6) + '.png'
            self.plotting_widget.saveImage(os.path.join(self.folder_name, filename))
