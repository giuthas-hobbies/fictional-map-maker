from importlib.resources import path as resource_path
from pathlib import Path
from warnings import Error

from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import yaml

from fimama.constants import (
    DEFAULT_ENCODING, RESOURCE_ANCHOR, ColormapFiles
)
from fimama.configuration import MapConfiguration
from fimama.perlin import perlin_map


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
    # read the config
    with resource_path(RESOURCE_ANCHOR, ) as config_path:
        with open(config_path, 'r', encoding=DEFAULT_ENCODING) as config_file:
            raw_config = yaml.safe_load(config_file)
            config = MapConfiguration(**raw_config)

    heightmap = perlin_map(
        width=config.width,
        height=config.height,
        params=config.perlin_parameters)
    heightmap = heightmap.T
    # terrain = np.arange(width*height).reshape((width,height))

    # TODO 0.6: Make this more helpful by including a list of recognised names.
    if config.colormap_name not in ColormapFiles:
        raise Error(f"Unrecognised colormap name {config.colormap_name}.")

    # Read the colormap
    with resource_path(
        RESOURCE_ANCHOR, f"{config.colormap_name}.gpf"
    ) as colormap_path:
        tmp = []
        for row in np.loadtxt(colormap_path):
            tmp.append([row[0], row[1:4]])
        colormap = LinearSegmentedColormap.from_list(
            config.colormap_name, tmp)

    return heightmap, colormap
