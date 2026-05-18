"""
GUI editor tool for the interactive manipulation of heightmaps.
"""

import logging

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGroupBox,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle

from fimama.configuration import MapScaleConfiguration
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
    scale_config : MapScaleConfiguration
        The configuration detailing the physical bounds of the map.
    """

    def __init__(
        self,
        figure: Figure,
        axes: Axes,
        canvas: FigureCanvasQTAgg,
        world_map: FimamaMap,
        scale_config: MapScaleConfiguration
    ) -> None:
        super().__init__()
        self.figure = figure
        self.axes = axes
        self.canvas = canvas
        self.world_map = world_map
        self.scale_config = scale_config

        self.modifier = HeightmapModifier(
            world_map=self.world_map,
            scale_config=self.scale_config
        )

        # State machine for the active interactive tool
        self.active_tool: str | None = None
        self.tool_mode: str | None = None

        # Variables for storing drawing path coordinates
        self.x_indices: list[int] = []
        self.y_indices: list[int] = []
        self.x_coords: list[float] = []
        self.y_coords: list[float] = []
        self.temp_plot = None

        # Add a dynamic circle patch to the plot to visualise tool radius
        self.cursor_circle = Circle(
            xy=(0, 0), radius=10, color='red', fill=False, visible=False,
            linestyle='--'
        )
        self.axes.add_patch(self.cursor_circle)

        # Setup the UI structure
        self._setup_ui()

        # Hook up matplotlib interactions
        self.cid_click = self.canvas.mpl_connect(
            s='button_press_event', func=self.onclick
        )
        self.cid_hover = self.canvas.mpl_connect(
            s='motion_notify_event', func=self.on_hover
        )

    def _setup_ui(self) -> None:
        """Initialise the layout, sliders, and grouped tool buttons."""
        layout = QVBoxLayout(self)

        # Active Tool Indicator
        self.lbl_active_tool = QLabel(text="Active Tool: None")
        self.lbl_active_tool.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.lbl_active_tool)

        # Sliders Setup
        self.lbl_power = QLabel(text="Power:")
        layout.addWidget(self.lbl_power)

        self.slider_power = QSlider(orientation=Qt.Orientation.Horizontal)
        self.slider_power.setMinimum(0)
        self.slider_power.setMaximum(100)
        self.slider_power.setValue(20)
        self.slider_power.valueChanged.connect(self._update_labels)
        layout.addWidget(self.slider_power)

        self.lbl_radius = QLabel(text="Radius:")
        layout.addWidget(self.lbl_radius)

        self.slider_radius = QSlider(orientation=Qt.Orientation.Horizontal)
        self.slider_radius.setMinimum(1)
        self.slider_radius.setMaximum(200)
        self.slider_radius.setValue(20)
        self.slider_radius.valueChanged.connect(self._update_labels)
        layout.addWidget(self.slider_radius)

        self._update_labels()

        # Group 1: Point Tools
        grp_point = QGroupBox("Point Tools (1 Click)")
        layout_point = QVBoxLayout()
        for tool in ["Hill", "Pit"]:
            btn = QPushButton(text=tool)
            btn.clicked.connect(
                lambda checked, t=tool: self._set_tool(name=t, mode="Point")
            )
            layout_point.addWidget(btn)
        grp_point.setLayout(layout_point)
        layout.addWidget(grp_point)

        # Group 2: Line Tools
        grp_line = QGroupBox("Line Tools (2 Clicks)")
        layout_line = QVBoxLayout()
        for tool in ["Range", "Trough", "Strait"]:
            btn = QPushButton(text=tool)
            btn.clicked.connect(
                lambda checked, t=tool: self._set_tool(name=t, mode="Line")
            )
            layout_line.addWidget(btn)
        grp_line.setLayout(layout_line)
        layout.addWidget(grp_line)

        # Group 3: Global Tools
        grp_global = QGroupBox("Global Tools (Instant)")
        layout_global = QVBoxLayout()

        btn_mask = QPushButton("Mask Edges")
        btn_mask.clicked.connect(self._gui_mask)
        layout_global.addWidget(btn_mask)

        btn_smooth = QPushButton("Smooth Map")
        btn_smooth.clicked.connect(self._gui_smooth)
        layout_global.addWidget(btn_smooth)

        btn_invert = QPushButton("Invert (H)")
        btn_invert.clicked.connect(self._gui_invert)
        layout_global.addWidget(btn_invert)

        btn_multiply = QPushButton("Multiply x1.2")
        btn_multiply.clicked.connect(self._gui_multiply)
        layout_global.addWidget(btn_multiply)

        btn_add = QPushButton("Add Power")
        btn_add.clicked.connect(self._gui_add_val)
        layout_global.addWidget(btn_add)

        grp_global.setLayout(layout_global)
        layout.addWidget(grp_global)

        layout.addStretch()

    def _get_power(self) -> float:
        """Map the 0-100 slider strictly to 0.0 - max_elevation bounds."""
        pct = self.slider_power.value() / 100.0
        return float(pct * self.scale_config.max_elevation)

    def _update_labels(self) -> None:
        """Update slider labels with their physical unit readouts."""
        pwr = self._get_power()
        elevation_unit = self.scale_config.elevation_unit.value
        self.lbl_power.setText(f"Power: {pwr:.1f} {elevation_unit}")

        rad = self.slider_radius.value()
        unit_size = self.scale_config.map_size_unit.value
        self.lbl_radius.setText(f"Radius: {rad} {unit_size}")

        # Keep the dynamic cursor in sync with the slider if active
        self.cursor_circle.set_radius(rad)
        self.canvas.draw_idle()

    def _set_tool(self, name: str, mode: str) -> None:
        """Activate an interactive map-clicking tool."""
        self.active_tool = name
        self.tool_mode = mode
        self.lbl_active_tool.setText(f"Active Tool: {name} ({mode})")

        # Reset line drawing states
        self.x_indices.clear()
        self.y_indices.clear()
        self.x_coords.clear()
        self.y_coords.clear()
        if self.temp_plot:
            self.temp_plot[0].remove()
            self.temp_plot = None
        self.canvas.draw_idle()

    def on_hover(self, event) -> None:
        """
        Update cursor circle position for immediate area-of-effect feedback.
        """
        if event.inaxes != self.axes:
            if self.cursor_circle.get_visible():
                self.cursor_circle.set_visible(False)
                self.canvas.draw_idle()
            return

        if self.tool_mode in ("Point", "Line"):
            self.cursor_circle.set_center((event.xdata, event.ydata))
            self.cursor_circle.set_visible(True)
            self.canvas.draw_idle()

    def onclick(self, event) -> None:
        """Handle execution of Point and Line tools upon clicking the map."""
        if event.inaxes != self.axes or not self.active_tool:
            return

        x, y = self.world_map.closest_point(x=event.xdata, y=event.ydata)
        pwr = self._get_power()
        rad = self.slider_radius.value()

        if self.tool_mode == "Point":
            if self.active_tool == "Hill":
                self.modifier.hill(x=x, y=y, power=pwr, radius=rad)
            elif self.active_tool == "Pit":
                self.modifier.pit(x=x, y=y, power=pwr, radius=rad)
            self._update_plot()

        elif self.tool_mode == "Line":
            self.x_indices.append(x)
            self.y_indices.append(y)
            self.x_coords.append(event.xdata)
            self.y_coords.append(event.ydata)

            # First click visual feedback
            if len(self.x_indices) == 1:
                self.temp_plot = self.axes.plot(
                    self.x_coords, self.y_coords, 'ro'
                )
                self.canvas.draw_idle()

            # Second click execution
            elif len(self.x_indices) == 2:
                sx, sy = self.x_indices[0], self.y_indices[0]
                ex, ey = self.x_indices[1], self.y_indices[1]

                if self.active_tool == "Range":
                    self.modifier.range_(sx, sy, ex, ey, power=pwr, radius=rad)
                elif self.active_tool == "Trough":
                    self.modifier.trough(sx, sy, ex, ey, power=pwr, radius=rad)
                elif self.active_tool == "Strait":
                    self.modifier.strait(sx, sy, ex, ey, power=pwr, radius=rad)

                # Cleanup state
                if self.temp_plot:
                    self.temp_plot[0].remove()
                    self.temp_plot = None
                self.x_indices.clear()
                self.y_indices.clear()
                self.x_coords.clear()
                self.y_coords.clear()
                self._update_plot()

    # --- Global Tools Triggered Directly by Buttons ---

    def _gui_mask(self) -> None:
        self.modifier.mask()
        self._update_plot()

    def _gui_smooth(self) -> None:
        self.modifier.smooth()
        self._update_plot()

    def _gui_invert(self) -> None:
        self.modifier.invert()
        self._update_plot()

    def _gui_multiply(self) -> None:
        self.modifier.multiply()
        self._update_plot()

    def _gui_add_val(self) -> None:
        self.modifier.add(amount=self._get_power())
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
