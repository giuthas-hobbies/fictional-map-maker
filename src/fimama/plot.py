"""
Plotting logic for rendering Fimama maps to Matplotlib figures.
"""

import logging

# import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
# from matplotlib.patches import Polygon

from fimama.configuration import MapScaleConfiguration, VoronoiConfiguration
from fimama.voronoi import FimamaMap

_logger = logging.getLogger(__name__)


def plot_map(
    world_map: FimamaMap,
    colormap: LinearSegmentedColormap | str = "terrain",
    config: VoronoiConfiguration | None = None,
    scale_config: MapScaleConfiguration | None = None,
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

    fig = Figure(layout='constrained')
    axes = fig.add_subplot(111)
    axes.set_aspect(aspect='equal', adjustable='box')

    # Calculate the number of valid base grid points
    num_valid_points = len(world_map.points) - len(
        world_map.dummy_points
    )
    verts = [
        world_map.vertices[world_map.regions[world_map.point_region[i]]]
        for i in range(num_valid_points)
        if len(world_map.regions[world_map.point_region[i]]) > 0
    ]
    heights = world_map.heightmap.flatten()[:len(verts)]

    poly_collection = PolyCollection(verts, cmap=colormap)
    poly_collection.set_array(heights)

    # Explicitly lock the colormap boundaries to the physical scale.
    poly_collection.set_clim(
        vmin=scale_config.min_elevation,
        vmax=scale_config.max_elevation
    )

    axes.add_collection(collection=poly_collection)

    # Clamp the view exactly to the bounds of the valid grid generation.
    # This keeps the extreme dummy cells completely out of sight.
    axes.set_xlim(left=0, right=world_map.grid_shape[0])
    axes.set_ylim(bottom=0, top=world_map.grid_shape[1])

    # Add a colorbar to display the current scale unit
    colorbar = fig.colorbar(mappable=poly_collection,
                            ax=axes, shrink=0.6, pad=0.05)
    colorbar.set_label(f"Elevation ({scale_config.elevation_unit.value})")

    return fig, axes
