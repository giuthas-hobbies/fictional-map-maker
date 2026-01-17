import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d


def voronoi_map(heightmap: np.ndarray = None, config = None):

    np.random.seed(1234)
    if heightmap is not None:
        grid_shape = (heightmap.shape[0] - 1, heightmap.shape[1] - 1, )
    else:
        grid_shape = (200,200)

    # make up data points
    base_points = np.mgrid[
        0:(grid_shape[0]):(grid_shape[0]+1)*1j,
        0:(grid_shape[1]):(grid_shape[1]+1)*1j
    ]
    base_points = base_points.reshape(2,-1).T
    points = base_points + np.random.random_sample(base_points.shape) - .5
    print(base_points)

    # TODO 0.3: better dummy points or better yet exclude outermost ring of
    # points while keeping them saved as the basis of extending the map.
    # add 4 distant dummy points
    # base_points = np.append(base_points, [[999,999], [-999,999], [999,-999], [-999,-999]], axis = 0)
    # points = np.append(points, [[999,999], [-999,999], [999,-999], [-999,-999]], axis = 0)

    # compute Voronoi tessellation
    voronoi = Voronoi(points)

    # plot
    fig, ax = plt.subplots()
    # voronoi_plot_2d(vor=voronoi, ax=ax, show_vertices=False, show_points=False)

    # Polygon patches for the voronoi regions
    polygons = []
    for region in voronoi.regions:
        if len(region) > 0:
            polygon = Polygon([voronoi.vertices[i] for i in region], closed=True)
            polygons.append(polygon)
    poly_collection = PatchCollection(patches=polygons, cmap="terrain")

    # Generate height field and add it to the collection as data
    print(base_points[voronoi.point_region-1])
    print(voronoi.npoints)
    print(len(base_points))
    heights = 100 * (np.random.rand(len(polygons))-.2)
    poly_collection.set_array(heights)
    if heightmap is not None:
        for i in range(voronoi.npoints):
            x, y = np.int64(base_points[voronoi.point_region[i]-1])
            heights[i] = heightmap[x, y]

    ax.add_collection(poly_collection)
    fig.colorbar(poly_collection, ax=ax)

    # fix the range of axes
    plt.xlim([-1,grid_shape[0]+1])
    plt.ylim([-1,grid_shape[1]+1])

    plt.show()
