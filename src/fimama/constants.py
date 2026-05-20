from importlib.metadata import version

from fimama.extended_external_classes import ListablePrintableEnum

# Program setup
RESOURCE_ANCHOR = 'fimama.resources'
LOG_CONFIG = "logging_configuration.json"

# TODO 1.0: Possibly decouple program and file format versions at version 1.0.
VERSION = version('fimama')
FILE_VERSION = VERSION

DEFAULT_ENCODING = 'utf-8'

FIMAMA_CONFIG_DIR = "~/.fimama/"

# Default configuration files
DEFAULT_WORLD_CONFIG = "default.yaml"

# Used to determine the spread falloff of generated hills and pits based
# on the total number of cells in the grid.
BLOB_POWER_MAP: dict[int, float] = {
    1000: 0.93,
    2000: 0.95,
    5000: 0.97,
    10000: 0.98,
    20000: 0.99,
    30000: 0.991,
    40000: 0.993,
    50000: 0.994,
    60000: 0.995,
    70000: 0.9955,
    80000: 0.996,
    90000: 0.9964,
    100000: 0.9973,
}

# Used to determine the spread falloff of generated mountain ranges and
# troughs based on the total number of cells in the grid.
LINE_POWER_MAP: dict[int, float] = {
    1000: 0.75,
    2000: 0.77,
    5000: 0.79,
    10000: 0.81,
    20000: 0.82,
    30000: 0.83,
    40000: 0.84,
    50000: 0.86,
    60000: 0.87,
    70000: 0.88,
    80000: 0.91,
    90000: 0.92,
    100000: 0.93,
}


class ColormapFiles(ListablePrintableEnum):
    """
    FIMAMA's own colormaps.
    """
    DARK_ATLAS = "dark-atlas"
    LIGHT_ATLAS = "light-atlas"


class MapGenerator(ListablePrintableEnum):
    """
    Heightmap generation algorithm names.
    """
    PERLIN = "perlin"


class DistanceUnit(ListablePrintableEnum):
    """
    Heightmap generation algorithm names.
    """
    METER = "m"
    KILOMETRES = "km"
    FEET = "feet"
    MILE = "miles"
    LEAGUE = "leagues"


class MapTool(ListablePrintableEnum):
    """Enumeration of available topographical tools."""
    HILL = "Hill"
    PIT = "Pit"
    RIDGE = "Ridge"
    VALLEY = "Valley"
    STRAIT = "Strait"
    MASK = "Mask"
    SMOOTH = "Smooth"
    INVERT = "Invert"
    MULTIPLY = "Multiply"
    ADD = "Add"


class ToolMode(ListablePrintableEnum):
    """Enumeration of tool interaction modes."""
    POINT = "Point"
    LINE = "Line"
