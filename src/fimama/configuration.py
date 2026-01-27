"""
Configuration classes and extensions to Pydantic BaseModel.
"""

import logging

from pydantic import BaseModel, ConfigDict, model_validator

_logger = logging.getLogger(__name__)


class FimamaModel(BaseModel):
    """
    The extended Pydantic BaseModel for fimama.

    This BaseModel which accepts empty strings for any field as None.

    This BaseModel which can be updated with new data. The update will trigger
    validation again.

    Additionally, trying to parse undefined fields will raise an exception.
    """

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def empty_str_to_none(cls, input_string: str) -> str | None:
        """
        Validate empty strings to None, but non-empties to themselves.

        Parameters
        ----------
        input_string : str
            String to be validated.

        Returns
        -------
        Optional[str]
            None for empty string, otherwise the string itself.
        """
        if input_string == '':
            input_string = None
        return input_string

    def update(self, data: dict) -> 'FimamaModel':
        """
        Update the BaseModel with the contents of data and validate.

        The update does not happen in place but rather a new updated object is
        returned and updating triggers validation.

        Parameters
        ----------
        data : dict
            Only valid key, value pairs are accepted.

        Returns
        -------
        UpdatableBaseModel
            The updated BaseModel.
        """
        update = self.model_dump()
        update.update(data)
        new_dict = self.model_validate(
            update).model_dump(exclude_defaults=True)
        for key, value in new_dict.items():
            _logger.debug(
                "Updating value of '%s' from '%s' to '%s'.",
                str(key), str(getattr(self, key, None)), str(value))
            setattr(self, key, value)
        return self


class PerlinParameters(FimamaModel):
    """
    Parameters for generating a heightmap with Perlin noise.

    Apart from `scale` these are parameters of the `noise.pnoise2` function.

    Parameters
    ----------
        scale : float
            Factor to zoom into the noise field by. Small values will produce a
            very densely noisy map, by default 100.0.
        octaves: int
            The number of passes for generating fractional Brownian motion
            (fBm) noise, by default 6.
        persistence: float
            The amplitude of each successive octave relative to the one below
            it. Note the amplitude of the first pass is always 1.0. Defaults to
            0.5 (each higher octave's amplitude is halved).
        lacunarity: float
            The frequency of each successive octave relative to the one below
            it, similar to persistence. Defaults to 2.0.
        base: int
            Fixed offset for the input coordinates. Useful for generating
            different noise textures with the same repeat interval, by default
            42.
    """
    scale: float = 100.0
    octaves: int = 6
    persistence: float = 0.5
    lacunarity: float = 2.0
    base: int = 42


class VoronoiConfiguration(FimamaModel):
    """
    Configuration for plotting elements of the Voronoi grid.

    Note that these parameters do not affect drawing the Voronoi cell polygons.
    Their plotting is controlled by configuration for drawing the heightmap.

    Parameters
    ----------
        plot_voronoi_grid: bool
            Should any part of the grid be plotted, if set to False, none of
            the elements get plotted regardless of the parameter values, by
            default False.
        show_ridges: bool
            Should the perimeter of the polygons - the Voronoi ridges - be
            plotted, by default True.
        show_vertices: bool
            Should the vertices, or intersections of the ridges, be plotted, by
            default False.
        show_points: bool
            Should the points that the Voronoi grid is based on be plotted, by
            default False.
    """
    plot_voronoi_grid: bool = False
    show_ridges: bool = True
    show_vertices: bool = False
    show_points: bool = False


class MapConfiguration(FimamaModel):
    """
    Map generation configuration.

    Parameters
    ----------
        height: int
            Height of the map in cells, by default 125.
        width: int
            Width of the map in cells, by default 200.
        generator: str
            Which generator to use for the heightmap, by default "perlin".
        colormap_name: str
            Name of the colormap to use for displaying the heightmap, by
            default "dark-atlas".
        perlin_parameters: `PerlinParameters` | None
            Parameters for generating a heightmap with Perlin noise, by default
            None.
        voronoi_configuration: `VoronoiConfiguration` | None
            Parameters for plotting the Voronoi grid (not the voronoi polygons,
            but rather associated edges and points), by default None.
    """
    height: int = 125
    width: int = 200
    generator: str = "perlin"
    colormap_name: str = "dark-atlas"
    perlin_parameters: PerlinParameters | None = None
    voronoi_configuration: VoronoiConfiguration | None = None
