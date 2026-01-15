import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d

matplotlib.use('qtagg')

def main() -> None:
    # make up data points
    np.random.seed(1234)
    grid_shape = (100,100)
    # Source - https://stackoverflow.com/a
    # Posted by Arrows
    # Retrieved 2026-01-14, License - CC BY-SA 4.0

    # make up data points
    base_points = np.mgrid[
        0:(grid_shape[0]):(grid_shape[0]+1)*1j, 
        0:(grid_shape[1]):(grid_shape[1]+1)*1j
    ]
    base_points = base_points.reshape(2,-1).T
    points = base_points + np.random.random_sample(base_points.shape) - .5

    # points = np.random.rand(25,2)

    # add 4 distant dummy points
    points = np.append(points, [[999,999], [-999,999], [999,-999], [-999,-999]], axis = 0)

    # compute Voronoi tessellation
    base_voronoi = Voronoi(base_points)
    voronoi = Voronoi(points)

    # plot
    fig = voronoi_plot_2d(vor=voronoi, show_vertices=False, show_points=False)
    axes = fig.axes
    # voronoi_plot_2d(vor=base_voronoi, ax=axes[0], show_vertices=False)

    # colorize
    for region in voronoi.regions:
        if not -1 in region:
            polygon = [voronoi.vertices[i] for i in region]
            plt.fill(*zip(*polygon), "b")

    # fix the range of axes
    plt.xlim([-1,grid_shape[0]+1])
    plt.ylim([-1,grid_shape[1]+1])

    plt.show()
