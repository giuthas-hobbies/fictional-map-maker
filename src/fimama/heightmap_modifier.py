"""
Heightmap modifiers.

This module provides the :class:`HeightmapModifier` for procedurally
altering the topographical heightmap state stored in a `FimamaMap`.
"""

import logging
import random

import numpy as np

from fimama.configuration import MapScaleConfiguration
from fimama.constants import BLOB_POWER_MAP, LINE_POWER_MAP
from fimama.voronoi import FimamaMap

_logger = logging.getLogger(__name__)


class HeightmapModifier:
    """
    Topographical modifiers for a heightmap.

    This class implements topographical tools (hills, pits, ranges,
    troughs) to operate directly on a `FimamaMap` within strict physical
    scale boundaries.

    Parameters
    ----------
    world_map : FimamaMap
        The map object containing the heightmap to modify.
    scale_config : MapScaleConfiguration
        The configuration detailing the physical bounds of the map.

    Attributes
    ----------
    world_map : FimamaMap
        The reference to the underlying map state.
    scale_config : MapScaleConfiguration
        The physical scaling parameters for the map.
    """

    def __init__(
        self, world_map: FimamaMap, scale_config: MapScaleConfiguration
    ) -> None:
        self.world_map = world_map
        self.scale_config = scale_config

        self.grid_width = world_map.grid_shape[1]
        self.grid_height = world_map.grid_shape[0]
        self.num_cells = self.grid_width * self.grid_height

        self.blob_power = BLOB_POWER_MAP.get(self.num_cells, 0.98)
        self.line_power = LINE_POWER_MAP.get(self.num_cells, 0.81)

        _logger.debug(
            f"Initialised HeightmapModifier for {self.num_cells} cells."
        )

    @property
    def threshold(self) -> float:
        """
        The minimum physical value change required to keep the BFS queue
        expanding. Calculated as 1% of the total physical elevation range.
        """
        return self.scale_config.elevation_range * 0.01

    def _get_neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        """Find valid 8-way neighbour coordinates for a given grid cell."""
        neighbors = []
        for nx in range(max(0, x - 1), min(self.grid_width, x + 2)):
            for ny in range(max(0, y - 1), min(self.grid_height, y + 2)):
                if nx != x or ny != y:
                    neighbors.append((nx, ny))
        return neighbors

    def hill(self, x: int, y: int, power: float, radius: float) -> None:
        """Apply a radial hill to a specific coordinate."""
        _logger.info(f"Adding hill at ({x}, {y}).")
        self._add_blob(cx=x, cy=y, peak_change=power, radius=radius, is_pit=False)

    def pit(self, x: int, y: int, power: float, radius: float) -> None:
        """Apply a radial pit to a specific coordinate."""
        _logger.info(f"Adding pit at ({x}, {y}).")
        self._add_blob(cx=x, cy=y, peak_change=power, radius=radius, is_pit=True)

    def _add_blob(
        self, cx: int, cy: int, peak_change: float, radius: float, is_pit: bool
    ) -> None:
        """Inject a blob (hill or pit) using Breadth-First Search."""
        change_map = np.zeros_like(self.world_map.heightmap)
        change_map[cy, cx] = peak_change
        queue = [(cx, cy)]

        while queue:
            qx, qy = queue.pop(0)
            current_change = change_map[qy, qx]

            for nx, ny in self._get_neighbors(x=qx, y=qy):
                if change_map[ny, nx] > 0:
                    continue
                
                # Constrain the blob strictly to the defined radius
                dist = np.hypot(nx - cx, ny - cy)
                if dist > radius:
                    continue
                
                new_val = (current_change ** self.blob_power) * \
                          (random.random() * 0.2 + 0.9)

                # Dynamically decay against the physical threshold
                if new_val > self.threshold:
                    change_map[ny, nx] = new_val
                    queue.append((nx, ny))

        if is_pit:
            self.world_map.heightmap -= change_map
        else:
            self.world_map.heightmap += change_map
            
        self.world_map.heightmap = np.clip(
            a=self.world_map.heightmap, 
            a_min=self.scale_config.min_elevation, 
            a_max=self.scale_config.max_elevation
        )

    def range_(
        self, sx: int, sy: int, ex: int, ey: int, power: float, radius: float
    ) -> None:
        """Generate a mountain ridge along a line."""
        _logger.info("Adding mountain range line.")
        self._add_line(sx, sy, ex, ey, power, radius, is_trough=False)

    def trough(
        self, sx: int, sy: int, ex: int, ey: int, power: float, radius: float
    ) -> None:
        """Generate a trough (lowered ridge) along a line."""
        _logger.info("Adding trough line.")
        self._add_line(sx, sy, ex, ey, power, radius, is_trough=True)

    def strait(
        self, sx: int, sy: int, ex: int, ey: int, power: float, radius: float
    ) -> None:
        """Generate a deep path lowering terrain to connect oceans."""
        _logger.info("Adding strait line.")
        self._add_line(sx, sy, ex, ey, power, radius, is_trough=True)

    def _add_line(
        self, sx: int, sy: int, ex: int, ey: int, peak_change: float, 
        radius: float, is_trough: bool
    ) -> None:
        """Inject a ridge or trough using line interpolation and BFS."""
        change_map = np.zeros_like(self.world_map.heightmap)
        queue = []
        
        # Interpolate coordinates along the line
        steps = max(abs(ex - sx), abs(ey - sy), 1)
        for step in range(steps + 1):
            x = int(sx + (ex - sx) * (step / steps))
            y = int(sy + (ey - sy) * (step / steps))
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                change_map[y, x] = peak_change
                queue.append((x, y))

        def point_line_dist(px: int, py: int) -> float:
            """Calculate Euclidean distance from a point to the line segment."""
            line_mag = np.hypot(ex - sx, ey - sy)
            if line_mag == 0:
                return float(np.hypot(px - sx, py - sy))
            u = ((px - sx) * (ex - sx) + (py - sy) * (ey - sy)) / (line_mag ** 2)
            u = max(min(u, 1.0), 0.0)
            ix = sx + u * (ex - sx)
            iy = sy + u * (ey - sy)
            return float(np.hypot(px - ix, py - iy))

        while queue:
            qx, qy = queue.pop(0)
            current_change = change_map[qy, qx]

            for nx, ny in self._get_neighbors(x=qx, y=qy):
                if change_map[ny, nx] > 0:
                    continue
                
                # Constrain spread to the line's radius
                if point_line_dist(nx, ny) > radius:
                    continue
                
                new_val = (current_change ** self.line_power) * \
                          (random.random() * 0.2 + 0.9)

                if new_val > self.threshold:
                    change_map[ny, nx] = new_val
                    queue.append((nx, ny))

        if is_trough:
            self.world_map.heightmap -= change_map
        else:
            self.world_map.heightmap += change_map
            
        self.world_map.heightmap = np.clip(
            a=self.world_map.heightmap, 
            a_min=self.scale_config.min_elevation, 
            a_max=self.scale_config.max_elevation
        )

    def smooth(self) -> None:
        """Smooth the heightmap globally using neighbor-averaging."""
        _logger.info("Applying global smoothing to heightmap.")
        new_heights = np.zeros_like(self.world_map.heightmap)

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                current_val = self.world_map.heightmap[y, x]
                neighbors = self._get_neighbors(x=x, y=y)
                neighbor_vals = [
                    self.world_map.heightmap[ny, nx] for nx, ny in neighbors
                ]
                neighbor_vals.append(current_val)
                
                avg = np.mean(neighbor_vals)
                smoothed = (current_val + avg) / 2.0
                new_heights[y, x] = smoothed

        self.world_map.heightmap = np.clip(
            a=new_heights, 
            a_min=self.scale_config.min_elevation, 
            a_max=self.scale_config.max_elevation
        )

    def mask(self) -> None:
        """Apply a global radial mask to force edges to minimum elevation."""
        _logger.info("Masking edges to generate island shapes.")
        
        x_grid, y_grid = np.meshgrid(
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

    def invert(self) -> None:
        """Mirror the heightmap globally across the horizontal axis."""
        _logger.info("Inverting map across horizontal axis.")
        self.world_map.heightmap = np.fliplr(self.world_map.heightmap)

    def add(self, amount: float) -> None:
        """Add a flat global value to all terrain heights."""
        _logger.info(f"Adding {amount} to all heights.")
        self.world_map.heightmap = np.clip(
            a=self.world_map.heightmap + amount, 
            a_min=self.scale_config.min_elevation, 
            a_max=self.scale_config.max_elevation
        )

    def multiply(self) -> None:
        """Multiply all terrain heights globally by a 1.2 flat factor."""
        _logger.info("Multiplying all heights by 1.2.")
        self.world_map.heightmap = np.clip(
            a=self.world_map.heightmap * 1.2, 
            a_min=self.scale_config.min_elevation, 
            a_max=self.scale_config.max_elevation
        )