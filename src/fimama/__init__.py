from importlib.resources import path as resource_path
import json
import logging.config

import matplotlib

from fimama.cli import run_cli
from fimama.constants import LOG_CONFIG, RESOURCE_ANCHOR
matplotlib.use('qtagg')


# Load logging config from json file.
with resource_path(RESOURCE_ANCHOR, LOG_CONFIG) as configuration_path:
    with open(configuration_path, 'r', encoding='utf-8') as configuration_file:
        config_dict = json.load(configuration_file)
        logging.config.dictConfig(config_dict)

# Create the module logger.
_logger = logging.getLogger('fimama')

# Log that the logger was configured.
_logger.info('Completed configuring logger.')
