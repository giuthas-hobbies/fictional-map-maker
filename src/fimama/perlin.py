import numpy as np
from noise import pnoise2

from .configuration import PerlinParameters

def perlin_map(
    width: int,
    height: int,
    params: PerlinParameters
) -> np.ndarray:
    """

    copied from noise.pnoise3:
    octaves -- specifies the number of passes for generating fBm noise,
    defaults to 1 (simple noise).

    persistence -- specifies the amplitude of each successive octave relative
    to the one below it. Defaults to 0.5 (each higher octave's amplitude
    is halved). Note the amplitude of the first pass is always 1.0.

    lacunarity -- specifies the frequency of each successive octave relative
    to the one below it, similar to persistence. Defaults to 2.0.

    repeatx, repeaty, repeatz -- specifies the interval along each axis when
    the noise values repeat. This can be used as the tile size for creating
    tileable textures

    base -- specifies a fixed offset for the input coordinates. Useful for
    generating different noise textures with the same repeat interval

    Parameters
    ----------
    width : int, optional
        _description_, by default 200
    height : int, optional
        _description_, by default 200
    scale : float, optional
        _description_, by default 100.0
    octaves : int, optional
        _description_, by default 6
    persistence : float, optional
        _description_, by default 0.5
    lacunarity : float, optional
        _description_, by default 2.0

    Returns
    -------
    np.ndarray
        _description_
    """
    terrain = np.zeros((height, width))

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
    normalized_terrain = (terrain - terrain.min()) / (terrain.max() - terrain.min())

    return normalized_terrain
