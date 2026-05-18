import logging

import numpy as np

from scipy.spatial import Voronoi, cKDTree


_logger = logging.getLogger(__name__)


class FimamaMap(Voronoi):
    @classmethod
    def make_map(
        cls,
        heightmap: np.ndarray | None = None,
        random_seed: int = 1234,
        grid_shape: tuple[int, int] = (200, 200),
    ) -> 'FimamaMap':
        np.random.seed(random_seed)
        if heightmap is not None:
            grid_shape = (heightmap.shape[0] - 1, heightmap.shape[1] - 1, )

        # make up data points
        base_points = np.mgrid[
            0:grid_shape[0]:(grid_shape[0]+1)*1j,
            0:grid_shape[1]:(grid_shape[1]+1)*1j
        ]
        base_points = base_points.reshape(2, -1).T
        points = base_points + np.random.random_sample(base_points.shape) - .5

        # These keep the cells corresponding to actual grid points finite.
        dummy_points = [
            [10*grid_shape[0]+grid_shape[0], 10*grid_shape[1]+grid_shape[1]],
            [-10*grid_shape[0], 10*grid_shape[1]+grid_shape[1]],
            [10*grid_shape[0]+10*grid_shape[0], -10*grid_shape[1]],
            [-10*grid_shape[0], -10*grid_shape[1]]
        ]

        _logger.debug(
            f"Using dummy points {dummy_points} in voronoi grid generation."
        )
        base_points = np.append(base_points, dummy_points, axis=0)
        points = np.append(points, dummy_points, axis=0)

        return cls(
            base_points=base_points,
            points=points,
            dummy_points=dummy_points,
            grid_shape=grid_shape,
            heightmap=heightmap
        )

    def __init__(
        self,
        base_points: np.ndarray,
        points: np.ndarray,
        dummy_points: np.ndarray,
        grid_shape: tuple[int, int],
        heightmap: np.ndarray | None = None,
    ):
        super().__init__(points)
        self.base_points = base_points
        self.dummy_points = dummy_points
        self.grid_shape = grid_shape
        self.heightmap = heightmap

    # @property
    # def grid_points(self):
    #     self.points[]

    def closest_point(self, x: float, y: float) -> tuple[int, int]:
        """
        Find the closest grid indices to a given spatial coordinate.

        Parameters
        ----------
        x : float
            The x-coordinate in the spatial map.
        y : float
            The y-coordinate in the spatial map.

        Returns
        -------
        tuple[int, int]
            The (x_index, y_index) of the closest point in the underlying
            heightmap.
        """
        # Lazily instantiate the KDTree the first time a user clicks the map.
        if not hasattr(self, '_kdtree'):
            self._kdtree = cKDTree(data=self.points)

        # Query the KDTree for the 1D index of the closest Voronoi point
        _, closest_idx = self._kdtree.query(x=[x, y])

        # Protect against clicks pulling the extreme boundary dummy points
        num_valid_points = len(self.points) - len(self.dummy_points)
        if closest_idx >= num_valid_points:
            closest_idx = num_valid_points - 1

        # Because the base_points meshgrid matches the heightmap dimensions,
        # we can perfectly map the 1D flat index back to the 2D heightmap shape
        # using numpy's built-in unravel_index
        y_idx, x_idx = np.unravel_index(
            indices=closest_idx, shape=self.heightmap.shape
        )

        return int(x_idx), int(y_idx)
