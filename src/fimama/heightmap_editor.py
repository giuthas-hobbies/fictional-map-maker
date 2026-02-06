from matplotlib.axes import Axes
from matplotlib.figure import Figure

from fimama.voronoi import FimamaMap


class HeightmapEditor:
    def __init__(self, figure: Figure, axes: Axes, world_map: FimamaMap):
        self.figure = figure
        self.axes = axes
        self.world_map = world_map
        self.x_values = []
        self.y_values = []
        self.x_indeces = []
        self.y_indeces = []
        self.cid = figure.canvas.mpl_connect(
            'button_press_event', self.onclick)

    def onclick(self, event):
        self.x_values.append(event.xdata)
        self.y_values.append(event.ydata)
        x, y = self.world_map.closest_point(event.xdata, event.ydata)
        self.x_indeces.append(x)
        self.y_indeces.append(y)
        # - calculate all euclidean distances between x,y and the voronoi
        # original points
        # - find argmin and you have the index of the original
        # point and therefore the cell as well

        # question is if there is a way of doing this without recalculating the
        # euclidean distances and taking the argmin every time

        if len(self.x_values) == 2:
            self.axes.plot(self.x_values, self.y_values, color="r")
            self.figure.canvas.draw()
            self.figure.canvas.mpl_disconnect(self.cid)
