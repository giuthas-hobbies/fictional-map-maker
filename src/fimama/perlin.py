import numpy as np
from noise import pnoise2

def perlin_map(
    width = 200,
    height = 200,
    scale = 100.0,
    octaves = 6,
    persistence = 0.5,
    lacunarity = 2.0,
) -> np.ndarray:
    terrain = np.zeros((height, width))

    for i in range(height):
        for j in range(width):
            terrain[i][j] = pnoise2(
                i / scale,
                j / scale,
                octaves=octaves,
                persistence=persistence,
                lacunarity=lacunarity,
                repeatx=width,
                repeaty=height,
                base=42
            )

    # # Normalize terrain values to 0–1
    # normalized_terrain = (terrain - terrain.min()) / (terrain.max() - terrain.min())

    return terrain
