"""
Heightmap modifiers.

This module provides the :class:`HeightmapModifier` for procedurally
altering the topographical heightmap state stored in a `FimamaMap`.
"""

import logging

import numpy as np

from fimama.configuration import MapScaleConfiguration
from fimama.voronoi import FimamaMap

_logger = logging.getLogger(__name__)


class HeightmapModifier:
    """
    Topographical modifiers for a heightmap.

    This class implements topographical tools (hills, pits, ridges,
    valleys) to operate directly on a `FimamaMap` within strict physical
    scale boundaries.

    Parameters
    ----------
    world_map : FimamaMap
        The state container storing the map data.
    scale_config : MapScaleConfiguration
        The configuration detailing the physical bounds of the map.

    Examples
    --------
    >>> modifier = HeightmapModifier(world_map=map_obj, scale_config=config)
    >>> modifier.apply_hill(center_x=50, center_y=50, radius=10, power=20.0)
    """

    def __init__(
        self, world_map: FimamaMap, scale_config: MapScaleConfiguration
    ) -> None:
        self.world_map = world_map
        self.scale_config = scale_config

        # Extract the exact array dimensions to prevent masking mismatches
        self.grid_height, self.grid_width = world_map.heightmap.shape

        _logger.debug(msg="Initialised HeightmapModifier.")

    def generate_random_walk(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        randomness: float
    ) -> list[tuple[int, int]]:
        """
        Generate a random path between two points via midpoint displacement.

        Used for creating organic-looking brush strokes and preview lines.

        Parameters
        ----------
        start_x : int
            X coordinate of the starting point.
        start_y : int
            Y coordinate of the starting point.
        end_x : int
            X coordinate of the ending point.
        end_y : int
            Y coordinate of the ending point.
        randomness : float
            Factor controlling deviation from a straight line.

        Returns
        -------
        list[tuple[int, int]]
            A list of (x, y) coordinates forming the generated continuous path.

        Examples
        --------
        >>> path = modifier.generate_random_walk(
        ...     start_x=0, start_y=0, end_x=100, end_y=100, randomness=0.5
        ... )
        """
        path = [(start_x, start_y), (end_x, end_y)]

        def displace(
            p1: tuple[int, int], p2: tuple[int, int], r: float
        ) -> list[tuple[int, int]]:
            """Recursively displace midpoints to create fractal noise."""
            if abs(p1[0] - p2[0]) <= 1 and abs(p1[1] - p2[1]) <= 1:
                return [p1, p2]

            mid_x = (p1[0] + p2[0]) / 2.0
            mid_y = (p1[1] + p2[1]) / 2.0

            dist = np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
            displacement = (np.random.random() - 0.5) * dist * r

            mid_x += displacement
            mid_y += displacement

            mid_point = (
                int(np.clip(a=mid_x, a_min=0, a_max=self.grid_width - 1)),
                int(np.clip(a=mid_y, a_min=0, a_max=self.grid_height - 1))
            )

            return displace(p1, mid_point, r)[:-1] + displace(mid_point, p2, r)

        detailed_path = displace(p1=path[0], p2=path[-1], r=randomness)

        # Interpolate missing steps to ensure a fully continuous line
        continuous_path = []
        for i in range(len(detailed_path) - 1):
            x1, y1 = detailed_path[i]
            x2, y2 = detailed_path[i+1]
            steps = max(abs(x2 - x1), abs(y2 - y1), 1)
            for step in range(steps):
                cx = int(x1 + (x2 - x1) * (step / steps))
                cy = int(y1 + (y2 - y1) * (step / steps))
                if not continuous_path or continuous_path[-1] != (cx, cy):
                    continuous_path.append((cx, cy))

        continuous_path.append(detailed_path[-1])
        return continuous_path

    def apply_hill(
        self,
        center_x: int,
        center_y: int,
        radius: int,
        power: float,
        baseline: np.ndarray | None = None,
        blend_mode: str = 'max'
    ) -> None:
        """
        Add a procedural hill to the heightmap at the given coordinates.

        Parameters
        ----------
        center_x : int
            X coordinate of the hill's peak.
        center_y : int
            Y coordinate of the hill's peak.
        radius : int
            Radius of the hill in grid cells.
        power : float
            Maximum elevation to add at the peak.
        baseline : np.ndarray | None, optional
            A snapshot of the heightmap to calculate additions against.
        blend_mode : str, optional
            Merge strategy ('add', 'max', 'min'), by default 'max'.
        """
        _logger.info(msg=f"Applying hill at ({center_x}, {center_y})")
        y_grid, x_grid = np.ogrid[:self.grid_height, :self.grid_width]
        dist_sq = (x_grid - center_x)**2 + (y_grid - center_y)**2
        mask = dist_sq <= radius**2

        dist = np.sqrt(dist_sq[mask])
        normalized_dist = dist / radius
        # Calculate cosine curve for a smooth bell-shaped hill
        height_added = power * (0.5 + 0.5 * np.cos(normalized_dist * np.pi))

        if baseline is not None:
            base_vals = baseline[mask]
        else:
            base_vals = self.world_map.heightmap[mask]

        new_vals = np.clip(
            a=base_vals + height_added,
            a_min=self.scale_config.min_elevation,
            a_max=self.scale_config.max_elevation
        )

        if blend_mode == 'max':
            self.world_map.heightmap[mask] = np.maximum(
                self.world_map.heightmap[mask], new_vals
            )
        elif blend_mode == 'min':
            self.world_map.heightmap[mask] = np.minimum(
                self.world_map.heightmap[mask], new_vals
            )
        else:
            self.world_map.heightmap[mask] = new_vals

    def apply_pit(
        self,
        center_x: int,
        center_y: int,
        radius: int,
        power: float,
        baseline: np.ndarray | None = None,
        blend_mode: str = 'min'
    ) -> None:
        """
        Carve a procedural pit into the heightmap at the given coordinates.

        Parameters
        ----------
        center_x : int
            X coordinate of the pit's center.
        center_y : int
            Y coordinate of the pit's center.
        radius : int
            Radius of the pit in grid cells.
        power : float
            Maximum elevation to subtract at the center.
        baseline : np.ndarray | None, optional
            A snapshot of the heightmap to calculate additions against.
        blend_mode : str, optional
            Merge strategy ('add', 'max', 'min'), by default 'min'.
        """
        _logger.info(msg=f"Applying pit at ({center_x}, {center_y})")
        y_grid, x_grid = np.ogrid[:self.grid_height, :self.grid_width]
        dist_sq = (x_grid - center_x)**2 + (y_grid - center_y)**2
        mask = dist_sq <= radius**2

        dist = np.sqrt(dist_sq[mask])
        normalized_dist = dist / radius
        height_sub = power * (0.5 + 0.5 * np.cos(normalized_dist * np.pi))

        if baseline is not None:
            base_vals = baseline[mask]
        else:
            base_vals = self.world_map.heightmap[mask]

        new_vals = np.clip(
            a=base_vals - height_sub,
            a_min=self.scale_config.min_elevation,
            a_max=self.scale_config.max_elevation
        )

        if blend_mode == 'min':
            self.world_map.heightmap[mask] = np.minimum(
                self.world_map.heightmap[mask], new_vals
            )
        elif blend_mode == 'max':
            self.world_map.heightmap[mask] = np.maximum(
                self.world_map.heightmap[mask], new_vals
            )
        else:
            self.world_map.heightmap[mask] = new_vals

    def apply_ridge(
        self, path: list[tuple[int, int]], power: float, radius: int
    ) -> None:
        """
        Apply a mountain ridge along a given path.

        Parameters
        ----------
        path : list[tuple[int, int]]
            The continuous path of the ridge.
        power : float
            Maximum elevation to add per step.
        radius : int
            Radius of the ridge in grid cells.
        """
        _logger.info(msg=f"Applying ridge along path of length {len(path)}")
        for x, y in path:
            self.apply_hill(
                center_x=x,
                center_y=y,
                radius=radius,
                power=power,
                baseline=None,
                blend_mode='add'
            )

    def apply_valley(
        self, path: list[tuple[int, int]], power: float, radius: int
    ) -> None:
        """
        Apply a deep valley/trough along a given path.

        Parameters
        ----------
        path : list[tuple[int, int]]
            The continuous path of the valley.
        power : float
            Maximum elevation to subtract per step.
        radius : int
            Radius of the valley in grid cells.
        """
        _logger.info(msg=f"Applying valley along path of length {len(path)}")
        for x, y in path:
            self.apply_pit(
                center_x=x,
                center_y=y,
                radius=radius,
                power=power,
                baseline=None,
                blend_mode='add'
            )

    def apply_strait(
        self, path: list[tuple[int, int]], power: float, radius: int
    ) -> None:
        """
        Carve a strait down toward sea level along a given path.

        Parameters
        ----------
        path : list[tuple[int, int]]
            The continuous path of the strait.
        power : float
            Maximum elevation to subtract per step.
        radius : int
            Radius of the strait in grid cells.
        """
        _logger.info(msg=f"Applying strait along path of length {len(path)}")
        for x, y in path:
            self.apply_pit(
                center_x=x,
                center_y=y,
                radius=radius,
                power=power,
                baseline=None,
                blend_mode='add'
            )

    def mask(self) -> None:
        """
        Apply a radial mask tapering the map edges to minimum elevation.
        """
        _logger.info(msg="Applying radial mask.")
        y_grid, x_grid = np.meshgrid(
            np.arange(self.grid_width), np.arange(self.grid_height)
        )
        nx = (2.0 * x_grid) / self.grid_width - 1.0
        ny = (2.0 * y_grid) / self.grid_height - 1.0

        distance = (1.0 - nx**2) * (1.0 - ny**2)

        masked_map = self.scale_config.min_elevation + (
            self.world_map.heightmap - self.scale_config.min_elevation
        ) * distance

        self.world_map.heightmap = np.clip(
            a=masked_map,
            a_min=self.scale_config.min_elevation,
            a_max=self.scale_config.max_elevation
        )

    def smooth(self) -> None:
        """
        Apply a simple box blur smoothing to the heightmap.
        """
        _logger.info(msg="Applying smoothing filter.")
        # Manual 3x3 average filter to avoid scipy.ndimage dependency
        padded = np.pad(
            array=self.world_map.heightmap, pad_width=1, mode='edge'
        )
        smoothed = (
            padded[:-2, :-2] + padded[:-2, 1:-1] + padded[:-2, 2:]
            + padded[1:-1, :-2] + padded[1:-1, 1:-1] + padded[1:-1, 2:]
            + padded[2:, :-2] + padded[2:, 1:-1] + padded[2:, 2:]
        ) / 9.0

        self.world_map.heightmap = np.clip(
            a=smoothed,
            a_min=self.scale_config.min_elevation,
            a_max=self.scale_config.max_elevation
        )

    def invert(self) -> None:
        """
        Invert all terrain heights globally.

        Mountains become valleys and valleys become mountains, scaled
        strictly within the map's minimum and maximum elevation limits.
        """
        _logger.info(msg="Inverting map heights globally.")
        max_elevation = self.scale_config.max_elevation
        min_elevation = self.scale_config.min_elevation
        zero_point = (max_elevation + min_elevation)/2

        self.world_map.heightmap = zero_point - self.world_map.heightmap

    def add(self, amount: float) -> None:
        """
        Add a flat global value to all terrain heights.
        """
        _logger.info(msg=f"Adding {amount} to all heights.")
        self.world_map.heightmap = np.clip(
            a=self.world_map.heightmap + amount,
            a_min=self.scale_config.min_elevation,
            a_max=self.scale_config.max_elevation
        )

    def multiply(self) -> None:
        """
        Multiply all terrain heights globally by a 1.2 flat factor.
        """
        _logger.info(msg="Multiplying all heights by 1.2.")
        self.world_map.heightmap = np.clip(
            a=self.world_map.heightmap * 1.2,
            a_min=self.scale_config.min_elevation,
            a_max=self.scale_config.max_elevation
        )
