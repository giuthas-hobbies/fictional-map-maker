"""
Unit tests for Fimama's core computational modules.

This module validates the mathematical and array-based operations
that serve as choke points during map generation and modification.
"""

import numpy as np

from fimama.configuration import MapScaleConfiguration, PerlinParameters
from fimama.heightmap_modifier import HeightmapModifier
from fimama.perlin import perlin_map
from fimama.voronoi import FimamaMap


def test_perlin_map_generation() -> None:
    """
    Test the multiprocessing Perlin noise generator.

    Ensures the map is generated with the correct dimensions and that
    all values are properly normalized within the expected [0.0, 1.0]
    range.
    """
    params = PerlinParameters(
        scale=100.0, octaves=1, persistence=0.5, lacunarity=2.0, base=1
    )
    width = 50
    height = 50

    # Execute the choke point multiprocessing function
    result = perlin_map(width=width, height=height, params=params)

    # Verify physical dimensions match requested width and height
    assert result.shape == (height, width)

    # Verify data normalization falls exactly within 0.0 to 1.0 bounds
    assert np.min(a=result) >= 0.0
    assert np.max(a=result) <= 1.0


def test_closest_point_kdtree_mapping() -> None:
    """
    Test the lazy KDTree implementation for spatial querying.

    Ensures that floating point canvas coordinates map perfectly
    back to integer heightmap array indices.
    """
    # Create a tiny 10x10 mock heightmap to build a quick Voronoi grid
    mock_heightmap = np.zeros(shape=(10, 10))
    world_map = FimamaMap.make_map(
        heightmap=mock_heightmap, random_seed=42
    )

    # Coordinates near the origin should snap to index (0, 0)
    x_idx, y_idx = world_map.closest_point(x=0.1, y=0.1)

    assert isinstance(x_idx, int)
    assert isinstance(y_idx, int)
    # Validate the index is within the heightmap bounds
    assert 0 <= x_idx < 10
    assert 0 <= y_idx < 10


def test_distance_field_ridge_application() -> None:
    """
    Test the distance-field logic of the Ridge tool.

    Ensures that modifications are applied exactly once across the path
    and that compound additions do not exceed physical scale limits.
    """
    scale_config = MapScaleConfiguration(
        min_elevation=-100.0, max_elevation=1000.0
    )
    # Initialise a flat map at elevation 0.0
    mock_heightmap = np.zeros(shape=(20, 20))
    world_map = FimamaMap.make_map(
        heightmap=mock_heightmap, random_seed=42
    )

    modifier = HeightmapModifier(
        world_map=world_map, scale_config=scale_config
    )

    # Create a 3-point stroke path
    path = [(5, 5), (5, 6), (5, 7)]
    power = 500.0
    radius = 2

    modifier.apply_ridge(path=path, power=power, radius=radius)

    # Verify the center of the path received the maximum power
    assert world_map.heightmap[6, 5] == power

    # Verify the limits cannot be exceeded with massive power
    modifier.apply_ridge(path=path, power=2000.0, radius=radius)
    assert world_map.heightmap[6, 5] == scale_config.max_elevation
