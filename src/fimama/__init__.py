import numpy as np
import matplotlib
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d

matplotlib.use('qtagg')

def main() -> None:
    # make up data points
    np.random.seed(1234)
    grid_shape = (200,200)

    # make up data points
    base_points = np.mgrid[
        0:(grid_shape[0]):(grid_shape[0]+1)*1j, 
        0:(grid_shape[1]):(grid_shape[1]+1)*1j
    ]
    base_points = base_points.reshape(2,-1).T
    points = base_points + np.random.random_sample(base_points.shape) - .5

    # TODO 0.2: better dummy points or better yet exclude outermost ring of
    # points while keeping them saved as the basis of extending the map.
    # add 4 distant dummy points
    points = np.append(points, [[999,999], [-999,999], [999,-999], [-999,-999]], axis = 0)

    # compute Voronoi tessellation
    voronoi = Voronoi(points)

    # plot
    fig, ax = plt.subplots()
    # voronoi_plot_2d(vor=voronoi, ax=ax, show_vertices=False, show_points=False)

    # colorize
    polygons = []
    for region in voronoi.regions:
        if not -1 in region and len(region) > 0:
            polygon = Polygon([voronoi.vertices[i] for i in region], closed=True)
            polygons.append(polygon)
    poly_collection = PatchCollection(polygons)
    colors = 100 * np.random.rand(len(polygons))
    poly_collection.set_array(colors)
    ax.add_collection(poly_collection)
    fig.colorbar(poly_collection, ax=ax)

    # fix the range of axes
    plt.xlim([-1,grid_shape[0]+1])
    plt.ylim([-1,grid_shape[1]+1])

    plt.show()
