"""
Heightmap modifiers.

This module provides the :class:`HeightmapModifier` for procedurally
altering the topographical heightmap state stored in a `FimamaMap`.
"""

import logging
import random

import numpy as np

from fimama.constants import BLOB_POWER_MAP, LINE_POWER_MAP
from fimama.voronoi import FimamaMap

_logger = logging.getLogger(__name__)


class HeightmapModifier:
    """
    Topographical modifiers for a heightmap.

    This class implements topographical tools (hills, pits, ranges,
    troughs, straits, masks, smoothing, and math operations) to
    operate directly on a `FimamaMap`. It does not store its own copy
    of the heightmap but alters the map's state in place.

    Parameters
    ----------
    world_map : FimamaMap
        The map object containing the heightmap to modify.

    Attributes
    ----------
    world_map : FimamaMap
        The reference to the underlying map state.
    num_cells : int
        The total number of cells in the map.
    blob_power : float
        Falloff power for blob-like generations (hills/pits).
    line_power : float
        Falloff power for line-like generations (ranges/troughs).

    Examples
    --------
    >>> modifier = HeightmapModifier(world_map=my_map)
    >>> modifier.add_hill(count=5, height=50, range_x="10-90", range_y="10-90")
    >>> modifier.mask(power=1.0)
    >>> modifier.smooth(fraction=2)
    """

    def __init__(self, world_map: FimamaMap) -> None:
        self.world_map = world_map

        # Assuming the heightmap is stored as a 2D grid that maps to points
        # If the heightmap shape doesn't match grid shape, we use grid_shape
        self.grid_width = world_map.grid_shape[1]
        self.grid_height = world_map.grid_shape[0]
        self.num_cells = self.grid_width * self.grid_height

        self.blob_power = BLOB_POWER_MAP.get(self.num_cells, 0.98)
        self.line_power = LINE_POWER_MAP.get(self.num_cells, 0.81)

        _logger.debug(
            f"Initialized HeightmapModifier for map with {self.num_cells} cells."
        )

    def _get_point_in_range(self, bounds: str, length: int) -> int:
        """
        Parse a string range and return a random point within those bounds.
        """
        parts = bounds.split("-")
        min_pct = int(parts[0]) / 100.0 if len(parts) > 0 else 0.0
        max_pct = int(parts[1]) / 100.0 if len(parts) > 1 else min_pct

        min_val = int(min_pct * length)
        max_val = int(max_pct * length)

        return random.randint(a=min_val, b=max_val)

    def _get_neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        """
        Find valid 8-way neighbor coordinates for a given grid cell.
        """
        neighbors = []
        for nx in range(max(0, x - 1), min(self.grid_width, x + 2)):
            for ny in range(max(0, y - 1), min(self.grid_height, y + 2)):
                if nx != x or ny != y:
                    neighbors.append((nx, ny))
        return neighbors

    def add_hill(
        self, count: str | int = 1, height: str | float = 10,
        range_x: str = "10-90", range_y: str = "10-90"
    ) -> None:
        """Generate radial hills and apply them to the heightmap."""
        hill_count = int(count)
        peak_height = float(height)

        _logger.info(f"Adding {hill_count} hills to the map.")
        for _ in range(hill_count):
            self._add_blob(
                peak_change=peak_height, range_x=range_x, range_y=range_y,
                is_pit=False
            )

    def add_pit(
        self, count: str | int = 1, depth: str | float = 10,
        range_x: str = "10-90", range_y: str = "10-90"
    ) -> None:
        """Generate radial pits (depressions) in the heightmap."""
        pit_count = int(count)
        max_depth = float(depth)

        _logger.info(f"Adding {pit_count} pits to the map.")
        for _ in range(pit_count):
            self._add_blob(
                peak_change=max_depth, range_x=range_x, range_y=range_y,
                is_pit=True
            )

    def _add_blob(
        self, peak_change: float, range_x: str, range_y: str, is_pit: bool
    ) -> None:
        """Helper method to inject a blob (hill or pit) using a BFS."""
        change_map = np.zeros_like(self.world_map.heightmap)
        limit = 0

        while limit < 50:
            start_x = self._get_point_in_range(bounds=range_x, length=self.grid_width)
            start_y = self._get_point_in_range(bounds=range_y, length=self.grid_height)
            
            current_h = self.world_map.heightmap[start_y, start_x]
            if is_pit and current_h - peak_change >= 0:
                break
            elif not is_pit and current_h + peak_change <= 100:
                break
            limit += 1

        change_map[start_y, start_x] = peak_change
        queue = [(start_x, start_y)]

        while queue:
            qx, qy = queue.pop(0)
            current_change = change_map[qy, qx]

            for nx, ny in self._get_neighbors(x=qx, y=qy):
                if change_map[ny, nx] > 0:
                    continue
                
                new_val = (current_change ** self.blob_power) * \
                          (random.random() * 0.2 + 0.9)
                change_map[ny, nx] = new_val

                if new_val > 1.0:
                    queue.append((nx, ny))

        if is_pit:
            self.world_map.heightmap -= change_map
        else:
            self.world_map.heightmap += change_map
            
        self.world_map.heightmap = np.clip(
            self.world_map.heightmap, a_min=0, a_max=100
        )

    def add_range(self, count: int = 1, height: float = 15) -> None:
        """Generate mountain ridges along a line."""
        _logger.info(f"Adding {count} mountain ranges.")
        for _ in range(count):
            self._add_line(peak_change=height, is_trough=False)

    def add_trough(self, count: int = 1, depth: float = 15) -> None:
        """Generate troughs (lowered ridges) along a line."""
        _logger.info(f"Adding {count} troughs.")
        for _ in range(count):
            self._add_line(peak_change=depth, is_trough=True)

    def add_strait(self, width: float = 10) -> None:
        """Generate a path lowering terrain to ensure oceans connect."""
        _logger.info("Adding strait.")
        self._add_line(peak_change=width, is_trough=True, is_strait=True)

    def _add_line(
        self, peak_change: float, is_trough: bool, is_strait: bool = False
    ) -> None:
        """Helper method to inject a ridge or trough using BFS."""
        change_map = np.zeros_like(self.world_map.heightmap)
        
        # Pick start and end points
        sx = random.randint(a=0, b=self.grid_width - 1)
        sy = random.randint(a=0, b=self.grid_height - 1)
        ex = random.randint(a=0, b=self.grid_width - 1)
        ey = random.randint(a=0, b=self.grid_height - 1)

        if is_strait:
            # Force edges
            sx = 0 if random.choice([True, False]) else self.grid_width - 1
            ex = 0 if sx != 0 else self.grid_width - 1

        queue = []
        # Create line interpolation
        steps = max(abs(ex - sx), abs(ey - sy))
        if steps > 0:
            for step in range(steps):
                x = int(sx + (ex - sx) * (step / steps))
                y = int(sy + (ey - sy) * (step / steps))
                change_map[y, x] = peak_change
                queue.append((x, y))

        # BFS spread across line
        while queue:
            qx, qy = queue.pop(0)
            current_change = change_map[qy, qx]

            for nx, ny in self._get_neighbors(x=qx, y=qy):
                if change_map[ny, nx] > 0:
                    continue
                
                new_val = (current_change ** self.line_power) * \
                          (random.random() * 0.2 + 0.9)
                change_map[ny, nx] = new_val

                if new_val > 1.0:
                    queue.append((nx, ny))

        if is_trough:
            self.world_map.heightmap -= change_map
        else:
            self.world_map.heightmap += change_map
            
        self.world_map.heightmap = np.clip(
            self.world_map.heightmap, a_min=0, a_max=100
        )

    def smooth(self, fraction: int = 2, add: float = 0.0) -> None:
        """Smooth the heightmap using neighbor-averaging."""
        _logger.info("Applying smoothing algorithm to heightmap.")
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
                if fraction <= 1:
                    smoothed = avg + add
                else:
                    smoothed = (
                        (current_val * (fraction - 1) + avg + add) / fraction
                    )
                new_heights[y, x] = smoothed

        self.world_map.heightmap = np.clip(new_heights, a_min=0, a_max=100)

    def mask(self, power: float = 1.0) -> None:
        """Apply a radial mask to force edges toward 0."""
        _logger.info("Masking edges to generate island shapes.")
        fr = max(abs(power), 1.0)
        
        x_grid, y_grid = np.meshgrid(
            np.arange(self.grid_width), np.arange(self.grid_height)
        )
        
        nx = (2.0 * x_grid) / self.grid_width - 1.0
        ny = (2.0 * y_grid) / self.grid_height - 1.0
        
        distance = (1.0 - nx**2) * (1.0 - ny**2)
        if power < 0:
            distance = 1.0 - distance
            
        masked_map = self.world_map.heightmap * distance
        self.world_map.heightmap = np.clip(
            (self.world_map.heightmap * (fr - 1.0) + masked_map) / fr,
            a_min=0, a_max=100
        )

    def invert(self, axis: str = "both") -> None:
        """
        Mirror the heightmap horizontally, vertically, or both.

        Parameters
        ----------
        axis : str, optional
            'horizontal', 'vertical', or 'both'. Defaults to 'both'.
        """
        _logger.info(f"Inverting map across axis: {axis}")
        if axis in ("horizontal", "both"):
            self.world_map.heightmap = np.fliplr(self.world_map.heightmap)
        if axis in ("vertical", "both"):
            self.world_map.heightmap = np.flipud(self.world_map.heightmap)

    def add(self, amount: float) -> None:
        """Add a flat value to all terrain heights."""
        _logger.info(f"Adding {amount} to all heights.")
        self.world_map.heightmap = np.clip(
            self.world_map.heightmap + amount, a_min=0, a_max=100
        )

    def multiply(self, factor: float) -> None:
        """Multiply all terrain heights by a flat factor."""
        _logger.info(f"Multiplying all heights by {factor}.")
        self.world_map.heightmap = np.clip(
            self.world_map.heightmap * factor, a_min=0, a_max=100
        )