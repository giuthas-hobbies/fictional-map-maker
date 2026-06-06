"""
Fimama Commandline main command.
"""

from pathlib import Path
import sys

import click
from click_default_group import DefaultGroup
from PyQt6.QtWidgets import QApplication

from fimama.load import load_map_configuration, get_colormap
from fimama.heightmap_generation import construct_heightmap
from fimama.voronoi import FimamaMap
from fimama.gui import FimamaGui


@click.command(name="open")
@click.argument(
    "path",
    type=click.Path(
        exists=True, dir_okay=False, file_okay=True, path_type=Path
    ),
)
def open_map(path: Path) -> None:
    """Open a saved map in the GUI. (NOT IMPLEMENTED YET)"""
    pass


@click.command(name="run")
@click.argument(
    "path",
    type=click.Path(dir_okay=False, file_okay=True, path_type=Path),
    required=False,
)
def generate_from_file(path: Path | None) -> None:
    """
    Generate a new map from a configuration file.

    \b
    PATH to a `.yaml` file containing the map parameters.
    """
    # 1. Pure data initialisation (safe for future batch/headless runs)
    map_config = load_map_configuration(config_path=path)
    colormap = get_colormap(colormap_name=map_config.colormap_name)
    heightmap = construct_heightmap(config=map_config)
    world_map = FimamaMap.make_map(heightmap=heightmap)

    # 2. GUI initialisation
    app = QApplication(sys.argv)
    gui = FimamaGui(
        world_map=world_map,
        map_config=map_config,
        colormap=colormap,
    )
    gui.show()
    sys.exit(app.exec())


@click.group(
    cls=DefaultGroup, default='run', default_if_no_args=True
)
@click.pass_context
@click.option('--verbosity', '-v', default=1, show_default=True)
@click.version_option()
def run_cli(context: click.Context, verbosity: int) -> None:
    """Fimama map generator."""
    pass


run_cli.add_command(open_map)
run_cli.add_command(generate_from_file)

if __name__ == "__main__":
    run_cli()
