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
    _logger.info("Plotting the Voronoi cells")
    if config is None:
        config = VoronoiConfiguration()

    # Create figure independently from pyplot to avoid state conflicts
    fig = Figure(layout="constrained")
    axes = fig.add_subplot(111)
    axes.set_aspect(aspect='equal', adjustable='box')

    polygons = []
    heights = []

    # Calculate the number of valid base grid points
    num_valid_points = len(world_map.points) - len(
        world_map.dummy_points
    )
    heightmap_flat = world_map.heightmap.flatten()

    for i in range(num_valid_points):
        region_idx = world_map.point_region[i]
        region = world_map.regions[region_idx]

        # Only process closed polygons without infinity flags (-1)
        if -1 not in region and len(region) > 0:
            vertices = [world_map.vertices[v] for v in region]
            polygon = Polygon(xy=vertices, closed=True)

            polygons.append(polygon)
            heights.append(heightmap_flat[i])

    # Generate a collection of patches to easily apply colormaps
    poly_collection = PatchCollection(patches=polygons, cmap=colormap)
    poly_collection.set_array(np.array(heights))

    axes.add_collection(collection=poly_collection)

    # Clamp the view exactly to the bounds of the valid grid generation.
    # This keeps the extreme dummy cells completely out of sight.
    axes.set_xlim(left=0, right=world_map.grid_shape[0])
    axes.set_ylim(bottom=0, top=world_map.grid_shape[1])

    return fig, axes