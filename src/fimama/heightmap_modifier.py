"""
Heightmap modifiers.

This module provides the :class:`HeightmapModifier` for procedurally
altering the topographical heightmap state stored in a `FimamaMap`.
"""

import logging

import numpy as np
from scipy.spatial import cKDTree

from fimama.configuration import MapScaleConfiguration
from fimama.voronoi import FimamaMap

_logger = logging.getLogger(__name__)


class HeightmapModifier:
    """
    Topographical modifiers for a heightmap.

    This class implements topographical tools (hills, pits, ranges,
    troughs) to operate directly on a `FimamaMap` within strict physical
    scale boundaries.
    """

    def __init__(
        self, world_map: FimamaMap, scale_config: MapScaleConfiguration
    ) -> None:
        self.world_map = world_map
        self.scale_config = scale_config

        self.grid_width = world_map.grid_shape[1]
        self.grid_height = world_map.grid_shape[0]

        _logger.debug("Initialised HeightmapModifier.")

    def generate_random_walk(
        self, start_x: int, start_y: int, end_x: int, end_y: int, 
        randomness: float
    ) -> list[tuple[int, int]]:
        """
        Generate a random path between two points via midpoint displacement.

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
            Float between 0.0 and 1.0 driving lateral jitter intensity.

        Returns
        -------
        list[tuple[int, int]]
            A list of contiguous coordinate tuples defining the path.
        """
        # Bind seed to coordinates to prevent flickering during hover
        seed_val = hash((start_x, start_y, end_x, end_y)) % (2**32)
        rng = np.random.default_rng(seed_val)
        
        path = [(float(start_x), float(start_y)), (float(end_x), float(end_y))]
        length = np.hypot(end_x - start_x, end_y - start_y)
        num_subdivisions = int(np.log2(max(length, 1))) + 1
        
        for _ in range(num_subdivisions):
            new_path = []
            for i in range(len(path) - 1):
                p1, p2 = path[i], path[i+1]
                mid_x = (p1[0] + p2[0]) / 2.0
                mid_y = (p1[1] + p2[1]) / 2.0
                
                dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                seg_len = np.hypot(dx, dy)
                
                if seg_len > 0:
                    px, py = -dy / seg_len, dx / seg_len
                else:
                    px, py = 0, 0
                
                # Apply scaled random jitter perpendicular to the line
                jitter = (rng.random() - 0.5) * seg_len * randomness
                mid_x += px * jitter
                mid_y += py * jitter
                
                new_path.extend([p1, (mid_x, mid_y)])
            new_path.append(path[-1])
            path = new_path
            
        # Convert fractal float boundaries into a continuous integer grid line
        continuous_path = []
        for i in range(len(path) - 1):
            x1, y1 = int(round(path[i][0])), int(round(path[i][1]))
            x2, y2 = int(round(path[i+1][0])), int(round(path[i+1][1]))
            
            steps = max(abs(x2 - x1), abs(y2 - y1), 1)
            for step in range(steps):
                cx = int(x1 + (x2 - x1) * (step / steps))
                cy = int(y1 + (y2 - y1) * (step / steps))
                if not continuous_path or continuous_path[-1] != (cx, cy):
                    continuous_path.append((cx, cy))
                    
        end_idx = (int(round(path[-1][0])), int(round(path[-1][1])))
        if not continuous_path or continuous_path[-1] != end_idx:
            continuous_path.append(end_idx)
            
        return continuous_path

    def hill(
        self, center_x: int, center_y: int, power: float, radius: float
    ) -> None:
        """Apply a radial hill to a specific coordinate."""
        _logger.info(f"Adding hill at ({center_x}, {center_y}).")
        self._add_blob(center_x, center_y, power, radius, is_pit=False)

    def pit(
        self, center_x: int, center_y: int, power: float, radius: float
    ) -> None:
        """Apply a radial pit to a specific coordinate."""
        _logger.info(f"Adding pit at ({center_x}, {center_y}).")
        self._add_blob(center_x, center_y, power, radius, is_pit=True)

    def _add_blob(
        self, center_x: int, center_y: int, peak_change: float, 
        radius: float, is_pit: bool
    ) -> None:
        """Inject a blob using vectorised distance falloff."""
        min_x = max(0, int(center_x - radius - 1))
        max_x = min(self.grid_width, int(center_x + radius + 2))
        min_y = max(0, int(center_y - radius - 1))
        max_y = min(self.grid_height, int(center_y + radius + 2))

        xx, yy = np.meshgrid(np.arange(min_x, max_x), np.arange(min_y, max_y))
        distances = np.hypot(xx - center_x, yy - center_y)

        # Scale effect from 1.0 at center to 0.0 at radius edge
        falloff = np.clip(1.0 - (distances / radius), a_min=0.0, a_max=1.0)
        
        rng = np.random.default_rng()
        noise = rng.uniform(low=0.8, high=1.2, size=distances.shape)
        
        changes = np.where(distances <= radius, peak_change * falloff * noise, 0)

        if is_pit:
            self.world_map.heightmap[min_y:max_y, min_x:max_x] -= changes
        else:
            self.world_map.heightmap[min_y:max_y, min_x:max_x] += changes
            
        self.world_map.heightmap = np.clip(
            a=self.world_map.heightmap, 
            a_min=self.scale_config.min_elevation, 
            a_max=self.scale_config.max_elevation
        )

    def range_(
        self, path: list[tuple[int, int]], power: float, radius: float
    ) -> None:
        """Generate a mountain ridge along a path."""
        _logger.info("Adding mountain range line.")
        self._add_line(path, power, radius, is_trough=False)

    def trough(
        self, path: list[tuple[int, int]], power: float, radius: float
    ) -> None:
        """Generate a trough (lowered ridge) along a path."""
        _logger.info("Adding trough line.")
        self._add_line(path, power, radius, is_trough=True)

    def strait(
        self, path: list[tuple[int, int]], power: float, radius: float
    ) -> None:
        """Generate a deep path lowering terrain to connect oceans."""
        _logger.info("Adding strait line.")
        self._add_line(path, power, radius, is_trough=True)

    def _add_line(
        self, path: list[tuple[int, int]], peak_change: float, 
        radius: float, is_trough: bool
    ) -> None:
        """Inject a ridge or trough using KDTree path lookups."""
        if not path:
            return

        path_x = [p[0] for p in path]
        path_y = [p[1] for p in path]
        min_x = max(0, int(min(path_x) - radius - 1))
        max_x = min(self.grid_width, int(max(path_x) + radius + 2))
        min_y = max(0, int(min(path_y) - radius - 1))
        max_y = min(self.grid_height, int(max(path_y) + radius + 2))

        xx, yy = np.meshgrid(np.arange(min_x, max_x), np.arange(min_y, max_y))
        grid_points = np.c_[xx.ravel(), yy.ravel()]

        # KDTree resolves the closest distance to the jagged line instantly
        tree = cKDTree(path)
        distances, _ = tree.query(grid_points)
        distances = distances.reshape(xx.shape)

        falloff = np.clip(1.0 - (distances / radius), a_min=0.0, a_max=1.0)
        rng = np.random.default_rng()
        noise = rng.uniform(low=0.8, high=1.2, size=distances.shape)
        
        changes = np.where(distances <= radius, peak_change * falloff * noise, 0)

        if is_trough:
            self.world_map.heightmap[min_y:max_y, min_x:max_x] -= changes
        else:
            self.world_map.heightmap[min_y:max_y, min_x:max_x] += changes
            
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
                
                # Fetch cross-neighbors for smoothing
                neighbors = []
                for nx in range(max(0, x - 1), min(self.grid_width, x + 2)):
                    for ny in range(max(0, y - 1), min(self.grid_height, y + 2)):
                        if nx != x or ny != y:
                            neighbors.append((nx, ny))
                            
                neighbor_vals = [
                    self.world_map.heightmap[ny, nx] for nx, ny in neighbors
                ]
                neighbor_vals.append(current_val)
                
                avg = np.mean(neighbor_vals)
                new_heights[y, x] = (current_val + avg) / 2.0

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