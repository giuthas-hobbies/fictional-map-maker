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
