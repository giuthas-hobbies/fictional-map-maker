"""
Configuration classes and extensions to Pydantic BaseModel.
"""

import logging

from pydantic import BaseModel, ConfigDict, model_validator

_logger = logging.getLogger('patkit.base_model_extensions')

# TODO: write a method that will dump the model in a dict with human readable
# keys. ie. replace underscores with spaces. then make another one that will
# convert in the other direction for the dict to be feedable to inheritors of
# UpdatableBaseModel.


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
    scale: float = 100.0
    octaves: int = 6
    persistence: float = 0.5
    lacunarity: float = 2.0
    base: int = 42


class VoronoiConfiguration(FimamaModel):
    plot_voronoi_grid: bool = False
    show_ridges: bool = True
    show_vertices: bool = False
    show_points: bool = False


class MapConfiguration(FimamaModel):
    height: int = 125
    width: int = 200
    generator: str = "perlin"
    colormap_name: str = "dark-atlas"
    perlin_parameters: PerlinParameters | None = None
    voronoi_configuration: VoronoiConfiguration | None = None
