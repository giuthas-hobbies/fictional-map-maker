from importlib.resources import path as resource_path
import logging
from pathlib import Path

from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import sys
import yaml

from fimama.constants import (
    DEFAULT_WORLD_CONFIG, DEFAULT_ENCODING, RESOURCE_ANCHOR, ColormapFiles
)
from fimama.configuration import MapConfiguration
from fimama.perlin import perlin_map

_logger = logging.getLogger(__name__)


def load_map_configuration(
    config_path: Path | None = None,
) -> MapConfiguration:
    # read the config
    if config_path is None:
        config_path = resource_path(RESOURCE_ANCHOR, DEFAULT_WORLD_CONFIG)

    _logger.debug(f"Reading the config file from {config_path}.")
    with open(config_path, 'r', encoding=DEFAULT_ENCODING) as config_file:
        raw_config = yaml.safe_load(config_file)
        config = MapConfiguration(**raw_config)

    return config


def get_heightmap_and_colormap(
    config: MapConfiguration,
) -> tuple[np.ndarray, LinearSegmentedColormap]:
    """
    Build a heightmap and get a colormap.

    Parameters
    ----------
    config : MapConfiguration
        Configuration for building the heightmap and selecting or loading the
        colormap.

    Returns
    -------
    tuple[np.ndarray, LinearSegmentedColormap]
        The heightmap and the colormap.
    """
    heightmap = perlin_map(
        width=config.width,
        height=config.height,
        params=config.perlin_parameters)
    heightmap = heightmap.T
    # terrain = np.arange(width*height).reshape((width,height))

    if config.colormap_name not in ColormapFiles:
        print(
            f"Unrecognised colormap_name '{config.colormap_name}'.\n"
            f"Valid names are {ColormapFiles.values()}."
        )
        sys.exit()

    # Read the colormap
    with resource_path(
        RESOURCE_ANCHOR, f"{config.colormap_name}.gpf"
    ) as colormap_path:
        _logger.debug(f"Reading the colormap from {colormap_path}.")
        tmp = []
        for row in np.loadtxt(colormap_path):
            tmp.append([row[0], row[1:4]])
        colormap = LinearSegmentedColormap.from_list(
            config.colormap_name, tmp)

    return heightmap, colormap
