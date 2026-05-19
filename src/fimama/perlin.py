"""
Perlin noise generation module.
"""

import concurrent.futures
import logging
import os
import time

import numpy as np
from noise import pnoise2

from fimama.configuration import PerlinParameters

_logger = logging.getLogger(__name__)


def _generate_chunk(
    start_y: int, end_y: int, width: int, height: int, params: PerlinParameters
) -> list[list[float]]:
    """
    Generate a large chunk of rows of Perlin noise.

    This bundles the workload to minimise the Inter-Process Communication (IPC)
    overhead inherent to Python's multiprocessing.

    Parameters
    ----------
    start_y : int
        The starting row index for this chunk (inclusive).
    end_y : int
        The ending row index for this chunk (exclusive).
    width : int
        Width of the heightmap in cells.
    height : int
        Height of the heightmap in cells.
    params : PerlinParameters
        Parameters for generating the Perlin noise.

    Returns
    -------
    list[list[float]]
        A 2D list of generated noise values for the chunk's rows.
    """
    chunk = []
    for i in range(start_y, end_y):
        row = [
            pnoise2(
                x=i / params.scale,
                y=j / params.scale,
                octaves=params.octaves,
                persistence=params.persistence,
                lacunarity=params.lacunarity,
                repeatx=width,
                repeaty=height,
                base=params.base
            )
            for j in range(width)
        ]
        chunk.append(row)
    return chunk


def perlin_map(
    width: int,
    height: int,
    params: PerlinParameters
) -> np.ndarray:
    """
    Generate a heightmap with Perlin noise using all available CPU cores.

    Parameters
    ----------
    width : int
        Width of the heightmap in cells.
    height : int
        Height of the heightmap in cells.
    params : PerlinParameters
        Parameters for generating the Perlin noise.

    Returns
    -------
    np.ndarray
        Normalised heightmap. The values will be in the range [0.0, 1.0].
    """
    cpu_count = os.cpu_count() or 4
    chunk_size = max(1, height // cpu_count)

    futures = []
    terrain_list = []

    _logger.info(
        f"Generating {width}x{height} Perlin map across {cpu_count} cores...")
    start_time = time.perf_counter()

    with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as pool:
        for start_y in range(0, height, chunk_size):
            end_y = min(start_y + chunk_size, height)
            futures.append(
                pool.submit(
                    _generate_chunk, start_y, end_y, width, height, params
                )
            )

        for future in futures:
            terrain_list.extend(future.result())

    end_time = time.perf_counter()
    _logger.info(
        f"Perlin map generated in {end_time - start_time:.4f} seconds.")

    terrain = np.array(terrain_list)

    terrain_min = terrain.min()
    terrain_range = terrain.max() - terrain_min

    normalized_terrain = terrain - terrain_min
    if terrain_range > 0:
        normalized_terrain = normalized_terrain / terrain_range

    return normalized_terrain
