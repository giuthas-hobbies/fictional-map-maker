"""
GUI editor tool for the interactive manipulation of heightmaps.
"""

import logging

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from fimama.heightmap_modifier import HeightmapModifier
from fimama.voronoi import FimamaMap

_logger = logging.getLogger(__name__)


class HeightmapEditor(QWidget):
    """
    Sidebar widget containing heightmap modification tools.

    Parameters
    ----------
    figure : Figure
        The main matplotlib figure.
    axes : Axes
        The matplotlib axes where the map is drawn.
    canvas : FigureCanvasQTAgg
        The Qt canvas instance to trigger redraws and catch events.
    world_map : FimamaMap
        The state container storing the map data.
    """

    def __init__(
        self, 
        figure: Figure, 
        axes: Axes, 
        canvas: FigureCanvasQTAgg, 
        world_map: FimamaMap
    ) -> None:
        super().__init__()
        self.figure = figure
        self.axes = axes
        self.canvas = canvas
        self.world_map = world_map

        self.modifier = HeightmapModifier(world_map=self.world_map)

        self.x_values: list[float] = []
        self.y_values: list[float] = []
        self.x_indeces: list[int] = []
        self.y_indeces: list[int] = []

        self._setup_ui()

        self.cid = self.canvas.mpl_connect(
            s='button_press_event', func=self.onclick
        )

    def _setup_ui(self) -> None:
        """Initialise the layout and buttons for the tool panel."""
        layout = QVBoxLayout(self)

        self.lbl_strength = QLabel(text="Strength: 20")
        layout.addWidget(self.lbl_strength)

        self.slider_strength = QSlider(
            orientation=Qt.Orientation.Horizontal
        )
        self.slider_strength.setMinimum(1)
        self.slider_strength.setMaximum(100)
        self.slider_strength.setValue(20)
        self.slider_strength.valueChanged.connect(
            self._update_strength_label
        )
        layout.addWidget(self.slider_strength)

        ui_layout = [
            ("Add Hill", self._gui_add_hill),
            ("Add Pit", self._gui_add_pit),
            ("Add Range", self._gui_add_range),
            ("Add Trough", self._gui_add_trough),
            ("Add Strait", self._gui_add_strait),
            ("Mask Edges", self._gui_mask),
            ("Smooth Map", self._gui_smooth),
            ("Invert (H)", self._gui_invert),
            ("Multiply x1.2", self._gui_multiply),
            ("Add +10", self._gui_add_val),
        ]

        for label, callback in ui_layout:
            btn = QPushButton(text=label)
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        layout.addStretch()

    def _update_strength_label(self, value: int) -> None:
        self.lbl_strength.setText(f"Strength: {value}")

    def _gui_add_hill(self) -> None:
        self.modifier.add_hill(height=self.slider_strength.value())
        self._update_plot()

    def _gui_add_pit(self) -> None:
        self.modifier.add_pit(depth=self.slider_strength.value())
        self._update_plot()

    def _gui_add_range(self) -> None:
        self.modifier.add_range(height=self.slider_strength.value())
        self._update_plot()

    def _gui_add_trough(self) -> None:
        self.modifier.add_trough(depth=self.slider_strength.value())
        self._update_plot()

    def _gui_add_strait(self) -> None:
        self.modifier.add_strait(width=self.slider_strength.value())
        self._update_plot()

    def _gui_mask(self) -> None:
        self.modifier.mask(power=1.0)
        self._update_plot()

    def _gui_smooth(self) -> None:
        self.modifier.smooth(fraction=2)
        self._update_plot()

    def _gui_invert(self) -> None:
        self.modifier.invert(axis="horizontal")
        self._update_plot()

    def _gui_multiply(self) -> None:
        self.modifier.multiply(factor=1.2)
        self._update_plot()

    def _gui_add_val(self) -> None:
        self.modifier.add(amount=10)
        self._update_plot()

    def _update_plot(self) -> None:
        """Push updated heights to the canvas and redraw."""
        h_map_flat = self.world_map.heightmap.flatten()
        num_valid_points = len(self.world_map.points) - len(
            self.world_map.dummy_points
        )

        heights = []
        for i in range(num_valid_points):
            region_idx = self.world_map.point_region[i]
            region = self.world_map.regions[region_idx]

            if -1 not in region and len(region) > 0:
                heights.append(h_map_flat[i])

        heights_array = np.array(heights)
        for collection in self.axes.collections:
            collection.set_array(heights_array)

        self.canvas.draw_idle()

    def onclick(self, event) -> None:
        """Handle canvas click events for path tracing."""
        if event.inaxes != self.axes:
            return

        self.x_values.append(event.xdata)
        self.y_values.append(event.ydata)
        x, y = self.world_map.closest_point(
            x=event.xdata, y=event.ydata
        )
        self.x_indeces.append(x)
        self.y_indeces.append(y)

        if len(self.x_values) == 2:
            self.axes.plot(self.x_values, self.y_values, color="r")
            self.canvas.draw_idle()
            self.x_values.clear()
            self.y_values.clear()