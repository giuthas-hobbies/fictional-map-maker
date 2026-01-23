import numpy as np
from noise import pnoise2

from .configuration import PerlinParameters


def perlin_map(
    width: int,
    height: int,
    params: PerlinParameters
) -> np.ndarray:
    """
    Generate a heightmap with Perlin noise.

    Parameters
    ----------
    width : int, optional
        Width of the heightmap in cells.
    height : int, optional
        Height of the heightmap in cells.
    params : `PerlinParameters`
        Parameters for generating the Perlin noise.

    Returns
    -------
    np.ndarray
        Normalised heightmap. The values will be in the range [0.0, 1.0].
    """
    terrain = np.zeros((height, width))

    # TODO: run this in parallel
    for i in range(height):
        for j in range(width):
            terrain[i][j] = pnoise2(
                i / params.scale,
                j / params.scale,
                octaves=params.octaves,
                persistence=params.persistence,
                lacunarity=params.lacunarity,
                repeatx=width,
                repeaty=height,
                base=params.base
            )

    # Normalize terrain values to 0–1
    normalized_terrain = terrain - terrain.min()
    normalized_terrain = normalized_terrain / (terrain.max() - terrain.min())

    return normalized_terrain
