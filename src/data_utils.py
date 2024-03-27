import datetime
from netCDF4 import Dataset
import numpy as np
from wrf import getvar, destagger

from PyQt5.QtWidgets import QMessageBox

def destagger_data(variable_data):
    # destagger the data that is available on a different grid
    if variable_data.attrs['stagger'] == 'X':
        data = destagger(variable_data, -1)
    elif variable_data.attrs['stagger'] == 'Y':
        data = destagger(variable_data, -2)
    elif variable_data.attrs['stagger'] == 'Z':
        data = destagger(variable_data, -3)
    elif variable_data.attrs['stagger'] == 'U':
        data = destagger(variable_data, -1)
    elif variable_data.attrs['stagger'] == 'V':
        data = destagger(variable_data, -2)
    elif variable_data.attrs['stagger'] == 'W':
        data = destagger(variable_data, -3)
    else:
        data = variable_data.data
    return data

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

def get_sample_data(filename, property):
    ncfile = Dataset(filename)
    if property == 'S':
        wind_data = None
        for wind_prop in ['U', 'V', 'W']:
            try:
                if wind_data is None:
                    wind_data = destagger_data(getvar(ncfile, wind_prop, meta=True))**2
                else:
                    wind_data += destagger_data(getvar(ncfile, wind_prop, meta=True))**2
            except:
                if wind_data is None:
                    wind_data = destagger_data(getvar(ncfile, wind_prop, meta=True))**2
                else:
                    wind_data += destagger_data(getvar(ncfile, wind_prop, meta=True))**2
                print('exception')
                pass
        data = np.sqrt(wind_data)
    else:
        data = getvar(ncfile, property, meta=False)
    return data

def get_layer_data(filename, property, layer):
    data = get_sample_data(filename, property)

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