"""
Fimama Commandline main command.
"""

from pathlib import Path

import click
from click_default_group import DefaultGroup

from fimama.build_map import build_map
from fimama.plot import plot_map


@click.command(name="open")
@click.argument(
    "path",
    type=click.Path(
        exists=True, dir_okay=False, file_okay=True, path_type=Path
    ),
)
def open(
        path: Path
) -> None:
    """
    Open a saved map in the GUI.

    NOT IMPLEMENTED YET.

    \b
    PATH to the map.
    """
    # config, logger = initialise_config(
    #     path=path, require_gui=True, require_data=True)
    # run_maker(config=config)


@click.command(name="run")
@click.argument(
    "path",
    type=click.Path(dir_okay=False, file_okay=True, path_type=Path),
    required=False,
)
def generate_from_file(path: Path | None):
    """
    Generate a new map from a configuration file.

    \b
    PATH to a `.yaml` file which contains the parameters for generating a map.
    """
    heightmap, colormap = build_map(path)
    fig, ax1 = plot_map(heightmap=heightmap, colormap=colormap)


@click.group(
    cls=DefaultGroup, default='run', default_if_no_args=True)
@click.pass_context
@click.option('--verbosity', '-v', default=1, show_default=True)
@click.version_option()
def run_cli(
        context: click.Context,
        verbosity: int
) -> None:
    """
    fimama - Fictional Map Maker

    Generate and edit random maps.

    By default, fimama will generate a new map from the default settings and
    display it.
    """


# noinspection PyTypeChecker
run_cli.add_command(open)
# noinspection PyTypeChecker
run_cli.add_command(generate_from_file)
