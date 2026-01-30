import logging

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
from scipy.spatial import voronoi_plot_2d

from fimama.configuration import VoronoiConfiguration
from fimama.voronoi import FimamaMap

_logger = logging.getLogger(__name__)


def plot_map(
    world_map: FimamaMap,
    colormap: LinearSegmentedColormap = None,
    config: VoronoiConfiguration = None,
) -> tuple[Figure, Axes]:
    """
    Plot a heightmap as a field of Voronoi cells.

    Parameters
    ----------
    heightmap : np.ndarray, optional
        The heightmap, by default None
    colormap : LinearSegmentedColormap, optional
        Colormap for the displaying the heightmap, by default None
    config : `VoronoiConfiguration`, optional
        Configuration for plotting the Voronoi grid, by default None

    Returns
    -------
    tuple[matplotlib.figure.Figure, matplotlib.Axes.axes]
        The containing Figure and the Axes the map was plotted on.
    """
    fig, (axes) = plt.subplots(nrows=1, ncols=1, layout="constrained")
    axes.set_aspect('equal', 'box')
    # ax2.set_aspect('equal', 'box')

    _logger.info("Plotting the Voronoi cells")
    if colormap is None:
        colormap = "terrain"
    if config is None:
        config = VoronoiConfiguration()

    # map, points, dummy_points, grid_shape = _generate_voronoi_grid(
    #     heightmap=heightmap)

    if config.plot_voronoi_grid:
        voronoi_plot_2d(
            vor=world_map,
            ax=axes,
            show_vertices=config.show_vertices,
            show_points=config.show_points
        )

    # map regions to points
    regions_to_points = np.argsort(world_map.point_region)

    # Polygon patches for the voronoi regions
    polygons = []
    polygon_index = 0
    heights = np.zeros(len(world_map.points) - len(world_map.dummy_points))
    heightmap = world_map.heightmap.flatten()
    for i, region in enumerate(world_map.regions):
        if -1 not in region and len(region) > 0:
            vertices = [world_map.vertices[i] for i in region]
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
    axes.set_xlim([-1, world_map.grid_shape[0]+1])
    axes.set_ylim([-1, world_map.grid_shape[1]+1])

    return fig, axes
