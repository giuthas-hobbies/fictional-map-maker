
from importlib.resources import path as resource_path
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import yaml

from fimama.configuration import MapConfiguration
from fimama.perlin import perlin_map
from fimama.voronoi import voronoi_map

matplotlib.use('qtagg')


def plot_map(
    heightmap: np.ndarray, colormap: LinearSegmentedColormap,
):
    """
    Plot a heightmap as a field of Voronoi cells.

    Parameters
    ----------
    heightmap : np.ndarray
        Heightmap to plot
    colormap : LinearSegmentedColormap
        Colormap to use in the plotting.

    Returns
    -------
    tuple[matplotlib.figure.Figure, matplotlib.Axes.axes]
        The containing Figure and the Axes the map was plotted on.
    """
    fig, (ax1) = plt.subplots(nrows=1, ncols=1, layout="constrained")
    ax1.set_aspect('equal', 'box')
    # ax2.set_aspect('equal', 'box')

    voronoi_map(fig=fig, axes=ax1, heightmap=heightmap, colormap=colormap)

    # Colored elevation map
    # ax2.imshow(X=terrain, cmap=colormap)
    # plt.tight_layout()
    plt.show()
    return fig, ax1


def build_map(
    config_path: Path | None = None
) -> tuple[np.ndarray, LinearSegmentedColormap]:
    """
    Build a map based on settings in the configuration file.

    Parameters
    ----------
    config_path : Path | None, optional
        Path to the configuration file. If this is None the default parameters
        from the fimama package will be loaded, by default None.

    Returns
    -------
    tuple[np.ndarray, LinearSegmentedColormap]
        The heightmap and the colormap.
    """
    anchor = 'fimama.resources'

    # read the config
    with resource_path(anchor, "default.yaml") as config_path:
        with open(config_path, 'r', encoding='utf-8') as config_file:
            raw_config = yaml.safe_load(config_file)
            config = MapConfiguration(**raw_config)

    heightmap = perlin_map(
        width=config.width,
        height=config.height,
        params=config.perlin_parameters)
    heightmap = heightmap.T
    # terrain = np.arange(width*height).reshape((width,height))

    # Read the colormap
    with resource_path(anchor, f"{config.colormap_name}.gpf") as colormap_path:
        tmp = []
        for row in np.loadtxt(colormap_path):
            tmp.append([row[0], row[1:4]])
        colormap = LinearSegmentedColormap.from_list(
            config.colormap_name, tmp)

    return heightmap, colormap


def main() -> None:
    heightmap, colormap = build_map()
    fig, ax1 = plot_map(heightmap=heightmap, colormap=colormap)
