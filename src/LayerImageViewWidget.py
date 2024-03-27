import pyqtgraph as pg
import numpy as np

class LayerImageViewWidget(pg.ImageView):
    def __init__(self, parent=None):
        super(LayerImageViewWidget, self).__init__(parent)

        self.setColorMap(pg.colormap.get('jet', source='matplotlib'))
        self.show()

    def setCbar(self, cbar):
        self.setColorMap(pg.colormap.get(cbar, source='matplotlib'))

    def updateLimits(self, val_min, val_max):
        self.setLevels(min=val_min, max=val_max)

    def plot(self, slice_data, title):
        self.setImage(np.fliplr(slice_data.T), autoLevels=False)

    def saveImage(self, filename):
        self.export(filename)
