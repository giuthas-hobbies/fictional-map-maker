"""
GUI editor for the interactive manipulation of the FimamaMap heightmap.
"""

from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider

import numpy as np

from fimama.heightmap_modifier import HeightmapModifier
from fimama.voronoi import FimamaMap


class HeightmapEditor:
    """
    Interactive GUI for modifying heightmaps.

    This editor wraps a `FimamaMap` and uses `HeightmapModifier` to
    apply user actions via Matplotlib sliders and buttons.

    Parameters
    ----------
    figure : Figure
        The main matplotlib figure.
    axes : Axes
        The matplotlib axes where the map is drawn.
    world_map : FimamaMap
        The state container storing the map data.
    """

    def __init__(self, figure: Figure, axes: Axes, world_map: FimamaMap):
        self.figure = figure
        self.axes = axes
        self.world_map = world_map

        self.modifier = HeightmapModifier(world_map=self.world_map)

        self.x_values: list[float] = []
        self.y_values: list[float] = []
        self.x_indeces: list[int] = []
        self.y_indeces: list[int] = []

        self.cid = figure.canvas.mpl_connect(
            'button_press_event', self.onclick
        )

        # Allocate space on the left for the GUI tools
        plt.subplots_adjust(left=0.3)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize all buttons and sliders for the UI."""
        ax_strength = self.figure.add_axes([0.05, 0.9, 0.2, 0.03])
        self.slider_strength = Slider(
            ax=ax_strength, label='Strength', valmin=1, valmax=100, valinit=20
        )

        ui_layout = [
            ("Add Hill", self._gui_add_hill, 0.80),
            ("Add Pit", self._gui_add_pit, 0.75),
            ("Add Range", self._gui_add_range, 0.70),
            ("Add Trough", self._gui_add_trough, 0.65),
            ("Add Strait", self._gui_add_strait, 0.60),
            ("Mask Edges", self._gui_mask, 0.55),
            ("Smooth Map", self._gui_smooth, 0.50),
            ("Invert (H)", self._gui_invert, 0.45),
            ("Multiply x1.2", self._gui_multiply, 0.40),
            ("Add +10", self._gui_add_val, 0.35),
        ]

        self.buttons = []
        for label, callback, y_pos in ui_layout:
            ax_btn = self.figure.add_axes([0.05, y_pos, 0.2, 0.04])
            btn = Button(ax=ax_btn, label=label)
            btn.on_clicked(func=callback)
            self.buttons.append(btn)

    def _gui_add_hill(self, event) -> None:
        self.modifier.add_hill(height=self.slider_strength.val)
        self._update_plot()

    def _gui_add_pit(self, event) -> None:
        self.modifier.add_pit(depth=self.slider_strength.val)
        self._update_plot()

    def _gui_add_range(self, event) -> None:
        self.modifier.add_range(height=self.slider_strength.val)
        self._update_plot()

    def _gui_add_trough(self, event) -> None:
        self.modifier.add_trough(depth=self.slider_strength.val)
        self._update_plot()

    def _gui_add_strait(self, event) -> None:
        self.modifier.add_strait(width=self.slider_strength.val)
        self._update_plot()

    def _gui_mask(self, event) -> None:
        self.modifier.mask(power=1.0)
        self._update_plot()

    def _gui_smooth(self, event) -> None:
        self.modifier.smooth(fraction=2)
        self._update_plot()

    def _gui_invert(self, event) -> None:
        self.modifier.invert(axis="horizontal")
        self._update_plot()

    def _gui_multiply(self, event) -> None:
        self.modifier.multiply(factor=1.2)
        self._update_plot()

    def _gui_add_val(self, event) -> None:
        self.modifier.add(amount=10)
        self._update_plot()

    def _update_plot(self) -> None:
        """Push updated heights to the view and redraw."""
        h_map_flat = self.world_map.heightmap.flatten()
        num_valid_points = len(self.world_map.points) - len(
            self.world_map.dummy_points
        )
        
        heights = []
        
        # Iterate through points directly to ensure valid mapping
        for i in range(num_valid_points):
            region_idx = self.world_map.point_region[i]
            region = self.world_map.regions[region_idx]
            
            if -1 not in region and len(region) > 0:
                heights.append(h_map_flat[i])
                
        heights_array = np.array(heights)

        for collection in self.axes.collections:
            collection.set_array(heights_array)

        self.figure.canvas.draw_idle()

    def onclick(self, event) -> None:
        """Handle canvas click events."""
        if event.inaxes != self.axes:
            return

        self.x_values.append(event.xdata)
        self.y_values.append(event.ydata)
        x, y = self.world_map.closest_point(event.xdata, event.ydata)
        self.x_indeces.append(x)
        self.y_indeces.append(y)

        if len(self.x_values) == 2:
            self.axes.plot(self.x_values, self.y_values, color="r")
            self.figure.canvas.draw()
            self.figure.canvas.mpl_disconnect(cid=self.cid)