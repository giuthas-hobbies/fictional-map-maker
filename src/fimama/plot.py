"""
Plotting logic for rendering Fimama maps to Matplotlib figures.
"""

import logging

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt

from fimama.configuration import VoronoiConfiguration
from fimama.voronoi import FimamaMap

_logger = logging.getLogger(__name__)


def plot_map(
    world_map: FimamaMap,
    colormap: LinearSegmentedColormap | str = "terrain",
    config: VoronoiConfiguration | None = None,
) -> tuple[Figure, Axes]:
    """
    Plot a heightmap as a field of Voronoi cells.

    Parameters
    ----------
    world_map : FimamaMap
        The state container storing the map data and heightmap.
    colormap : LinearSegmentedColormap | str, optional
        Colormap for displaying the heightmap, by default 'terrain'.
    config : VoronoiConfiguration, optional
        Configuration for plotting the Voronoi grid.

    Returns
    -------
    tuple[Figure, Axes]
        The containing Figure and the Axes the map was plotted on.
    """
    fig, axes = plt.subplots(nrows=1, ncols=1, layout="constrained")
    axes.set_aspect(aspect='equal', adjustable='box')

    _logger.info("Plotting the Voronoi cells")
    if config is None:
        config = VoronoiConfiguration()

    polygons = []
    heights = []

    # The first N points are our valid grid points, followed by dummy points.
    num_valid_points = len(world_map.points) - len(world_map.dummy_points)
    heightmap_flat = world_map.heightmap.flatten()

    for i in range(num_valid_points):
        # Find the specific region index assigned to this grid point
        region_idx = world_map.point_region[i]
        region = world_map.regions[region_idx]

        # Only draw the polygon if it is fully enclosed (no -1 infinity flags)
        if -1 not in region and len(region) > 0:
            vertices = [world_map.vertices[v] for v in region]
            polygon = Polygon(xy=vertices, closed=True)

            polygons.append(polygon)
            heights.append(heightmap_flat[i])

    # Convert to PatchCollection and apply heights for the colormap
    poly_collection = PatchCollection(patches=polygons, cmap=colormap)
    poly_collection.set_array(np.array(heights))

    axes.add_collection(collection=poly_collection)
    axes.set_xlim(0, world_map.grid_shape[0])
    axes.set_ylim(0, world_map.grid_shape[1])

    return fig, axes
