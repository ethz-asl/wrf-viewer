import datetime
from netCDF4 import Dataset
from wrf import getvar

from PyQt5.QtWidgets import QMessageBox

def get_datetime_from_filename(filename):
    splitted_filename = filename.split('_')
    datestring = splitted_filename[-2] + '_' + splitted_filename[-1]
    return datetime.datetime.strptime(datestring, '%Y-%m-%d_%H:%M:%S')

def get_timestring_from_datetime(datetime):
    return datetime.strftime("%Y-%m-%d %H:%M:%S")

def get_times_from_filenamelist(files_list):
    times = []
    for file in files_list:
        times.append(get_timestring_from_datetime(get_datetime_from_filename(file)))

    return times

def get_layer_data(filename, property, layer):
    ncfile = Dataset(filename)
    data = getvar(ncfile, property, meta=False)

    if len(data.shape) == 3:
        slice_data = data[int(layer)]
    elif len(data.shape) == 2:
        slice_data = data
    else:
        error_box = QMessageBox()
        error_box.setWindowTitle("Invalid Property")
        error_box.setText(str('Only plotting 2D or 3D properties is currently supported'))
        error_box.setIcon(QMessageBox.Critical)
        error_box.show()
        slice_data = None
    return slice_data