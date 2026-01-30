import logging

import numpy as np

from fimama.configuration import MapConfiguration
from fimama.constants import MapGenerator
from fimama.perlin import perlin_map

_logger = logging.getLogger(__name__)


def construct_heightmap(
    config: MapConfiguration,
) -> np.ndarray:
    """
    Get a colormap.

    Parameters
    ----------
    config : MapConfiguration
        Configuration for building the heightmap.

    Returns
    -------
    np.ndarray
        The heightmap.
    """
    match config.generator:
        case MapGenerator.PERLIN:
            heightmap = perlin_map(
                width=config.width,
                height=config.height,
                params=config.perlin_parameters)
            heightmap = heightmap.T
        case _:
            raise ValueError(
                f"Unrecognised map generator name {config.generator}."
            )

    return heightmap
