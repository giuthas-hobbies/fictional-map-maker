from importlib.resources import files, as_file
import logging
from pathlib import Path

from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import sys
import yaml

from fimama.constants import (
    DEFAULT_WORLD_CONFIG, DEFAULT_ENCODING, RESOURCE_ANCHOR,
    ColormapFiles, ColormapInternal
)
from fimama.configuration import MapConfiguration

_logger = logging.getLogger(__name__)


def load_map_configuration(
    config_path: Path | None = None,
) -> MapConfiguration:
    # read the config
    if config_path is None:
        # Resolves to a traversable Path-like object
        config_path = files(RESOURCE_ANCHOR).joinpath(DEFAULT_WORLD_CONFIG)

    _logger.debug(f"Reading the config file from {config_path}.")
    with open(config_path, 'r', encoding=DEFAULT_ENCODING) as config_file:
        raw_config = yaml.safe_load(config_file)
        config = MapConfiguration(**raw_config)

    return config


def atlas() -> LinearSegmentedColormap:
    """
    Construct an asymmetric topographic colormap.

    The colormap uses a sharp transition at exactly 0.5 to separate
    water colors from land colors.

    Returns
    -------
    LinearSegmentedColormap
        The generated sea-to-peaks colormap.
    """
    # 0.0 to 0.5 represents the sea, 0.5 to 1.0 represents the land.
    # We use 0.5 and 0.50001 to create a razor-sharp coastline transition.
    colors = [
        (0.00000, '#000033'),  # Very dark blue (deep ocean)
        (0.45000, '#70A8D6'),  # Lighter blue (shallow sea/coast)
        (0.50000, '#90C8E6'),  # Light blue (shallow sea/coast)
        (0.50001, '#004300'),  # Dark green (lowlands)
        (0.60000, '#11A311'),  # light green (lower hills)
        (0.70000, '#D2B48C'),  # Tan (mountains)
        (0.95000, '#8B4513'),  # Saddle brown (tall mountains)
        (1.00000, '#FFFFFF'),  # White (extreme peaks)
    ]
    return LinearSegmentedColormap.from_list(
        name='atlas', colors=colors
    )


def construct_topographic_colormap(
    colormap_name: ColormapInternal | str = ColormapInternal.ATLAS
) -> LinearSegmentedColormap | str:
    if isinstance(colormap_name, str):
        colormap_name = ColormapInternal(colormap_name)

    match colormap_name:
        case ColormapInternal.ATLAS:
            return atlas()
        case _:
            raise ValueError(
                f"Unrecognised procedural colormap requested: {colormap_name}."
                f"Accepted values are: {list(ColormapInternal.values)}"
            )


def get_colormap(
    colormap_name: str,
) -> LinearSegmentedColormap | str:
    """
    Get a colormap.

    If loading a colormap from an internal resource file, the sea level should
    be indicated by a repeated position index. The format of the .gpf file
    rows is:
    `[pos index] [red] [green] [blue]`
    And the position indeces should be in increasing order.

    Parameters
    ----------
    colormap_name : str
        Name of the colormap.

    Returns
    -------
    LinearSegmentedColormap | str
        Either the colormap or its name if a standard matplotlib map is called
        for.
    """
    if colormap_name in ColormapFiles:
        colormap_resource = files(RESOURCE_ANCHOR).joinpath(
            f"{colormap_name}.gpf")
        with as_file(colormap_resource) as colormap_path:
            _logger.debug(f"Reading the colormap from {colormap_path}.")
            # Read the raw floating point space-separated values
        raw_data = np.loadtxt(colormap_path)

        # 1. Find the coastline boundary (indicated by a duplicate
        # position index)
        positions = raw_data[:, 0]
        split_pos = 0.5  # Fallback just in case no duplicate is found
        for i in range(1, len(positions)):
            if positions[i] == positions[i - 1]:
                split_pos = positions[i]
                break

        # 2. Rescale positions to center the coastline exactly at 0.5
        colors = []
        for row in raw_data:
            pos, r, g, b = row[0], row[1], row[2], row[3]

            if pos <= split_pos:
                # Stretch water [0.0 -> split_pos] into [0.0 -> 0.5]
                new_pos = (pos / split_pos) * 0.5 if split_pos > 0 else 0.0
            else:
                # Stretch land [split_pos -> 1.0] into [0.5 -> 1.0]
                new_pos = 0.5 + ((pos - split_pos) / (1.0 - split_pos)) * 0.5

            # Matplotlib requires position values to be strictly increasing.
            # When we hit the duplicate coastline value, push the land side
            # up slightly.
            if colors and new_pos <= colors[-1][0]:
                new_pos = colors[-1][0] + 1e-5

            # Cap at 1.0 to prevent floating point math overshoots
            new_pos = min(1.0, new_pos)

            colors.append((new_pos, (r, g, b)))
        colormap = LinearSegmentedColormap.from_list(
            colormap_name, colors)
    elif colormap_name in ColormapInternal:
        colormap = construct_topographic_colormap(colormap_name=colormap_name)
    else:
        print(
            f"Unrecognised colormap_name '{colormap_name}'.\n"
            f"Valid names are {ColormapFiles.values()} "
            f"and {ColormapInternal.values()}."
        )
        sys.exit()

    return colormap
