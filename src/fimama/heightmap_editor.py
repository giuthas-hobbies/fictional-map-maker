"""
GUI editor tool for the interactive manipulation of heightmaps.
"""

import logging

from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle
import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QUndoStack
from PyQt6.QtWidgets import (
    QGroupBox,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from fimama.configuration import MapScaleConfiguration
from fimama.constants import MapTool, ToolMode
from fimama.heightmap_modifier import HeightmapModifier
from fimama.history import HeightmapEditCommand
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
    undo_stack : QUndoStack
    """

    # Signal emitted whenever the heightmap is altered
    map_modified = pyqtSignal()

    def __init__(
        self,
        figure: Figure,
        axes: Axes,
        canvas: FigureCanvasQTAgg,
        world_map: FimamaMap,
        scale_config: MapScaleConfiguration,
        undo_stack: QUndoStack,
    ) -> None:
        super().__init__()
        self.figure = figure
        self.axes = axes
        self.canvas = canvas
        self.world_map = world_map
        self.scale_config = scale_config
        self.undo_stack = undo_stack

        self.modifier = HeightmapModifier(
            world_map=self.world_map,
            scale_config=self.scale_config
        )

        self.active_tool: MapTool | None = None
        self.tool_mode: ToolMode = ToolMode.POINT

        self.x_indices: list[int] = []
        self.y_indices: list[int] = []

        # Dynamic visual patches for tool feedback
        self.cursor_circle = Circle(
            xy=(0, 0), radius=10, color='red', fill=False, visible=False,
            linestyle='--'
        )
        self.axes.add_patch(self.cursor_circle)

        self.temp_path_line, = self.axes.plot(
            [], [], 'r--', visible=False, linewidth=2
        )

        # Store references to interactive tool buttons for highlighting
        self.tool_buttons: dict[str, QPushButton] = {}

        # Drag State trackers
        self._drag_active: bool = False
        self._drag_baseline: np.ndarray | None = None
        self._last_drag_point: tuple[int, int] | None = None

        self._setup_ui()

        self.cid_click = self.canvas.mpl_connect(
            s='button_press_event', func=self.on_press
        )
        self.cid_click = self.canvas.mpl_connect(
            s='button_release_event', func=self.on_release
        )
        self.cid_hover = self.canvas.mpl_connect(
            s='motion_notify_event', func=self.on_hover
        )
        self.cid_leave = self.canvas.mpl_connect(
            s='axes_leave_event', func=self.on_leave
        )

    def _setup_ui(self) -> None:
        """Initialise the layout, sliders, and grouped tool buttons."""
        layout = QVBoxLayout(self)

        self.lbl_active_tool = QLabel(text="Active Tool: None")
        self.lbl_active_tool.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.lbl_active_tool)

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

        self.lbl_randomness = QLabel(text="Path Randomness:")
        layout.addWidget(self.lbl_randomness)

        self.slider_randomness = QSlider(orientation=Qt.Orientation.Horizontal)
        self.slider_randomness.setMinimum(0)
        self.slider_randomness.setMaximum(100)
        self.slider_randomness.setValue(20)
        self.slider_randomness.valueChanged.connect(self._update_labels)
        layout.addWidget(self.slider_randomness)

        self._update_labels()

        # Group 1: Point Tools
        grp_point = QGroupBox("Point Tools (1 Click)")
        layout_point = QVBoxLayout()
        for tool in ["Hill", "Pit"]:
            btn = QPushButton(text=tool)
            self.tool_buttons[tool] = btn  # Store reference
            btn.clicked.connect(
                lambda checked, t=tool: self._set_tool(name=t, mode="Point")
            )
            layout_point.addWidget(btn)
        grp_point.setLayout(layout_point)
        layout.addWidget(grp_point)

        # Group 2: Line Tools
        grp_line = QGroupBox("Line Tools (2 Clicks)")
        layout_line = QVBoxLayout()
        for tool in ["Ridge", "Trough", "Strait"]:
            btn = QPushButton(text=tool)
            self.tool_buttons[tool] = btn  # Store reference
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

    def _set_tool(self, name: str, mode: str) -> None:
        """Activate an interactive tool and highlight its button."""
        self.active_tool = name
        self.tool_mode = mode
        self.lbl_active_tool.setText(f"Active Tool: {name} ({mode})")

        # Highlight the active button and reset all others
        for btn_name, btn in self.tool_buttons.items():
            if btn_name == name:
                # Use Qt Stylesheets to indicate the active state
                btn.setStyleSheet(
                    "background-color: #cce5ff; font-weight: bold;"
                )
            else:
                btn.setStyleSheet("")

        self.x_indices.clear()
        self.y_indices.clear()
        self.temp_path_line.set_visible(False)
        self.canvas.draw_idle()

    def _get_power(self) -> float:
        """Map the 0-100 slider strictly to 0.0 - max_elevation bounds."""
        pct = self.slider_power.value() / 100.0
        return float(pct * self.scale_config.max_elevation)

    def _get_radius(self) -> int:
        """
        Retrieve the current brush radius from the UI slider.

        Returns
        -------
        int
            The radius in grid cells.
        """
        return self.slider_radius.value()

    def _update_labels(self) -> None:
        """Update slider labels with their physical unit readouts."""
        pwr = self._get_power()
        elevation_unit = self.scale_config.elevation_unit.value
        self.lbl_power.setText(f"Power: {pwr:.1f} {elevation_unit}")

        rad = self.slider_radius.value()
        unit_size = self.scale_config.map_size_unit.value
        self.lbl_radius.setText(f"Radius: {rad} {unit_size}")

        rand_val = self.slider_randomness.value() / 100.0
        self.lbl_randomness.setText(f"Path Randomness: {rand_val:.2f}")

        self.cursor_circle.set_radius(rad)
        self.canvas.draw_idle()

    def _push_undo_command(self, baseline: np.ndarray, text: str) -> None:
        """
        Extract the sparse delta from a modification and push it to the stack.
        """
        changed = self.world_map.heightmap != baseline
        if np.any(changed):
            indices = np.where(changed)
            old_vals = baseline[indices]
            new_vals = self.world_map.heightmap[indices]

            # Revert the live map temporarily so the QUndoCommand handles the
            # forward state transition natively via redo()
            self.world_map.heightmap[indices] = old_vals

            cmd = HeightmapEditCommand(
                heightmap=self.world_map.heightmap,
                indices=indices,
                old_values=old_vals,
                new_values=new_vals,
                redraw_callback=self._update_plot,
                text=text
            )
            self.undo_stack.push(cmd)

    def on_press(self, event) -> None:
        """Handle start of dragging (Point) or sequence clicking (Line)."""
        if event.inaxes != self.axes or not self.active_tool:
            return

        hover_x, hover_y = self.world_map.closest_point(
            x=event.xdata, y=event.ydata
        )

        if self.tool_mode == ToolMode.POINT:
            self._drag_active = True
            self._drag_baseline = self.world_map.heightmap.copy()
            self._last_drag_point = (hover_x, hover_y)
            self._apply_point_tool(
                x=hover_x, y=hover_y, baseline=self._drag_baseline
            )
            self._update_plot()

        elif self.tool_mode == ToolMode.LINE:
            self.x_indices.append(hover_x)
            self.y_indices.append(hover_y)

            if len(self.x_indices) == 2:
                baseline = self.world_map.heightmap.copy()

                randomness = self.slider_randomness.value() / 100.0
                path = self.modifier.generate_random_walk(
                    start_x=self.x_indices[0],
                    start_y=self.y_indices[0],
                    end_x=self.x_indices[1],
                    end_y=self.y_indices[1],
                    randomness=randomness
                )

                pwr = self._get_power()
                rad = self._get_radius()

                if self.active_tool == MapTool.RIDGE:
                    self.modifier.apply_ridge(
                        path=path, power=pwr, radius=rad
                    )
                elif self.active_tool == MapTool.VALLEY:
                    self.modifier.apply_valley(
                        path=path, power=pwr, radius=rad
                    )
                elif self.active_tool == MapTool.STRAIT:
                    self.modifier.apply_strait(
                        path=path, power=pwr, radius=rad
                    )

                self.temp_path_line.set_visible(False)
                self.x_indices.clear()
                self.y_indices.clear()
                self._push_undo_command(
                    baseline=baseline, text=f"{self.active_tool.value} Line"
                )

    def on_hover(self, event) -> None:
        """Handle continuous drawing during a drag, and cursor updates."""
        if event.inaxes != self.axes:
            if self.cursor_circle.get_visible():
                self.cursor_circle.set_visible(False)
                self.temp_path_line.set_visible(False)
                self.canvas.draw_idle()
            return

        hover_x, hover_y = self.world_map.closest_point(
            x=event.xdata, y=event.ydata
        )

        # Handle interactive dragging
        if self._drag_active and self.tool_mode == ToolMode.POINT:
            if (hover_x, hover_y) != self._last_drag_point:
                self._apply_point_tool(
                    x=hover_x, y=hover_y, baseline=self._drag_baseline
                )
                self._last_drag_point = (hover_x, hover_y)
                self._update_plot()

        # Handle Visual Cursors
        if self.tool_mode in (ToolMode.POINT, ToolMode.LINE):
            self.cursor_circle.set_center((event.xdata, event.ydata))
            self.cursor_circle.set_visible(True)

            if self.tool_mode == ToolMode.LINE and len(self.x_indices) == 1:
                randomness = self.slider_randomness.value() / 100.0
                path = self.modifier.generate_random_walk(
                    start_x=self.x_indices[0],
                    start_y=self.y_indices[0],
                    end_x=hover_x,
                    end_y=hover_y,
                    randomness=randomness
                )
                path_plot_x = [p[1] for p in path]
                path_plot_y = [p[0] for p in path]
                self.temp_path_line.set_data(path_plot_x, path_plot_y)
                self.temp_path_line.set_visible(True)
            else:
                self.temp_path_line.set_visible(False)

            self.canvas.draw_idle()

    def on_release(self, event) -> None:
        """
        Conclude a drag operation and package it as a single undo command.
        """
        if self._drag_active:
            self._drag_active = False
            self._push_undo_command(
                self._drag_baseline, f"{self.active_tool} Brush")
            self._drag_baseline = None
            self._last_drag_point = None

    def on_leave(self, event) -> None:
        """
        Hide the cursor circle and path when the mouse leaves the map area.
        """
        if self.cursor_circle.get_visible():
            self.cursor_circle.set_visible(False)
            self.temp_path_line.set_visible(False)
            self.canvas.draw_idle()

    def _apply_point_tool(self, x: int, y: int, baseline: np.ndarray) -> None:
        """Helper to route execution of active point tool safely."""
        pwr = self._get_power()
        rad = self._get_radius()

        match self.active_tool:
            case MapTool.HILL:
                self.modifier.apply_hill(
                    center_x=x, center_y=y, radius=rad, power=pwr,
                    baseline=baseline, blend_mode='max'
                )
            case MapTool.PIT:
                self.modifier.apply_pit(
                    center_x=x, center_y=y, radius=rad, power=pwr,
                    baseline=baseline, blend_mode='min'
                )
            case _:
                raise ValueError(
                    "Unrecognised active tool {self.active_tool}.")

    def _gui_mask(self) -> None:
        baseline = self.world_map.heightmap.copy()
        self.modifier.mask()
        self._push_undo_command(baseline, "Apply Mask")

    def _gui_smooth(self) -> None:
        baseline = self.world_map.heightmap.copy()
        self.modifier.smooth()
        self._push_undo_command(baseline, "Smooth Map")

    def _gui_invert(self) -> None:
        baseline = self.world_map.heightmap.copy()
        self.modifier.invert()
        self._push_undo_command(baseline, "Invert Map")

    def _gui_multiply(self) -> None:
        baseline = self.world_map.heightmap.copy()
        self.modifier.multiply()
        self._push_undo_command(baseline, "Multiply Heights")

    def _gui_add_val(self) -> None:
        baseline = self.world_map.heightmap.copy()
        self.modifier.add(amount=self._get_power())
        self._push_undo_command(baseline, "Add Flat Height")

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
        # Notify the main GUI that unsaved changes exist
        self.map_modified.emit()
