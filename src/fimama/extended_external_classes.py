from enum import Enum


class ListablePrintableEnum(Enum):
    """
    Enum whose values can be listed and which returns its value as a string.
    """

    @classmethod
    def values(cls) -> list:
        """
        Classmethod which returns a list of the Enum's values.

        Returns
        -------
        list
            list of the Enum's values.
        """
        return list(map(lambda c: c.value, cls))

    def __str__(self) -> str:
        return str(self.value)
