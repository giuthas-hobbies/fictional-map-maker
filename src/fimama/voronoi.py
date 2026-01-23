# from icecream import ic

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Polygon

from scipy.spatial import Voronoi, voronoi_plot_2d

from .configuration import VoronoiConfiguration


def _generate_voronoi_grid(heightmap: np.ndarray | None = None):
    np.random.seed(1234)
    if heightmap is not None:
        grid_shape = (heightmap.shape[0] - 1, heightmap.shape[1] - 1, )
    else:
        grid_shape = (200, 200)

    # make up data points
    base_points = np.mgrid[
        0:(grid_shape[0]):(grid_shape[0]+1)*1j,
        0:(grid_shape[1]):(grid_shape[1]+1)*1j
    ]
    base_points = base_points.reshape(2, -1).T
    points = base_points + np.random.random_sample(base_points.shape) - .5

    # TODO 0.6: better dummy points or better yet exclude outermost ring of
    # points while keeping them saved as the basis of extending the map.
    # add 4 distant dummy points
    dummy_points = []
    dummy_points = [[999, 999], [-999, 999], [999, -999], [-999, -999]]
    base_points = np.append(base_points, dummy_points, axis=0)
    points = np.append(points, dummy_points, axis=0)

    # compute Voronoi tessellation
    voronoi = Voronoi(points)
    return voronoi, points, dummy_points, grid_shape


def voronoi_map(
    axes: Axes,
    fig: Figure,
    heightmap: np.ndarray = None,
    colormap: LinearSegmentedColormap = None,
    config: VoronoiConfiguration = None,
):
    """
    Plot a voronoi heightmap.

    Parameters
    ----------
    axes : Axes
        axes to plot on
    fig : Figure
        Figure we are plotting into. Used for adding a colorbar.
    heightmap : np.ndarray, optional
        The heightmap, by default None
    colormap : LinearSegmentedColormap, optional
        Colormap for the displaying the heightmap, by default None
    config : `VoronoiConfiguration`, optional
        Configuration for plotting the Voronoi grid, by default None
    """
    if colormap is None:
        colormap = "terrain"
    if config is None:
        config = VoronoiConfiguration()

    voronoi, points, dummy_points, grid_shape = _generate_voronoi_grid(
        heightmap=heightmap)

    if config.plot_voronoi_grid:
        voronoi_plot_2d(
            vor=voronoi,
            ax=axes,
            show_vertices=config.show_vertices,
            show_points=config.show_points
        )

    # map regions to points
    regions_to_points = np.argsort(voronoi.point_region)

    # Polygon patches for the voronoi regions
    polygons = []
    polygon_index = 0
    heights = np.zeros(len(points) - len(dummy_points))
    heightmap = heightmap.flatten()
    for i, region in enumerate(voronoi.regions):
        if -1 not in region and len(region) > 0:
            vertices = [voronoi.vertices[i] for i in region]
            polygon = Polygon(vertices, closed=True)
            polygons.append(polygon)
            # center = np.mean(polygon.get_xy(), axis=0)
            # axes.text(center[0], center[1], f"{i}")
            # index, = np.where(voronoi.point_region == i)
            # index = index[0]
            # ic(index, regions_to_points[i-1])
            heights[polygon_index] = heightmap[regions_to_points[i-1]]
            polygon_index += 1
            # axes.text(
            #     point[0], point[1],
            #     f"{j}, {i}",
            #     horizontalalignment='center',
            #     verticalalignment='center'
            # )
    # ic(points_in_regions[1:])
    # ic(region_to_polygon[1:])
    # ic(voronoi.point_region)
    # ic(regions_to_points)
    poly_collection = PatchCollection(patches=polygons, cmap=colormap)

    poly_collection.set_array(heights)
    axes.add_collection(poly_collection)
    fig.colorbar(poly_collection, ax=axes)

    # fix the range of axes
    axes.set_xlim([-1, grid_shape[0]+1])
    axes.set_ylim([-1, grid_shape[1]+1])
