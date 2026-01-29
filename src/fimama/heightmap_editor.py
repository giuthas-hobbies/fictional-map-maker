from matplotlib.axes import Axes
from matplotlib.figure import Figure
import numpy as np


class HeightmapEditor:
    def __init__(self, figure: Figure, axes: Axes):
        self.figure = figure
        self.axes = axes
        self.x_values = []
        self.y_values = []
        self.cid = figure.canvas.mpl_connect(
            'button_press_event', self.onclick)

    def onclick(self, event):
        self.x_values.append(event.xdata)
        self.y_values.append(event.ydata)
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
