import logging

import numpy as np

from scipy.spatial import Voronoi


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
        x_index = round(x)
        y_index = round(y)
        points = self.points
        # TODO: make a points property that is intuitively indexed
        points.shape = self.grid_shape
        candidates = points[x_index-2:x_index+1, y_index-2:y_index+1]
        # ei toimi koska points on [n, 2]
        print(self.points.shape)
        euclid = np.linalg.norm(candidates-[x, y])
        return np.argmin(euclid) + [x_index-2, y_index-2]
