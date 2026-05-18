"""
Main GUI application for Fimama.
"""

import io
import logging
import zipfile

import numpy as np
import yaml
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.colors import LinearSegmentedColormap
from PyQt6.QtCore import Qt, QSignalBlocker
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence, QWheelEvent
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QMainWindow,
    QMessageBox,
    QScrollBar,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from fimama.configuration import (
    MapConfiguration, PerlinParameters, VoronoiConfiguration
)
from fimama.dialogs import (
    ExportDialog,
    MapSettingsDialog,
    PerlinSettingsDialog,
    ScaleSettingsDialog,
    VoronoiSettingsDialog,
)
from fimama.heightmap_editor import HeightmapEditor
from fimama.heightmap_generation import construct_heightmap
from fimama.plot import plot_map
from fimama.voronoi import FimamaMap

_logger = logging.getLogger(__name__)


class FimamaGui(QMainWindow):
    """
    Main application GUI window.

    Orchestrates the PyQt6 window, menus, save/load states, and manages
    the interactive heightmap editor.

    Parameters
    ----------
    world_map : FimamaMap
        The state container storing the map data and heightmap.
    map_config : MapConfiguration
        Configuration specifying how the map was built.
    colormap : LinearSegmentedColormap | str
        Colormap for displaying the heightmap.
    """

    def __init__(
        self,
        world_map: FimamaMap,
        map_config: MapConfiguration,
        colormap: LinearSegmentedColormap | str
    ) -> None:
        super().__init__()
        self.world_map = world_map
        self.config = map_config
        self.colormap = colormap
        self.zoom_factor: float = 1.0

        self.is_modified: bool = False

        self.setWindowTitle("Fimama Map Maker")
        self.resize(1200, 800)

        self._setup_menus()

        self.figure, self.axes = plot_map(
            world_map=self.world_map,
            colormap=self.colormap,
            config=self.config.voronoi_configuration,
            scale_config=self.config.scale_configuration,
        )

        self._setup_ui()

    def _setup_menus(self) -> None:
        """Construct the menu bar and bind actions to shortcuts."""
        menubar = self.menuBar()

        # --- File Menu ---
        file_menu = menubar.addMenu("&File")

        action_new = QAction("&New Map...", self)
        action_new.setShortcut(QKeySequence.StandardKey.New)
        action_new.triggered.connect(self._cmd_new)
        file_menu.addAction(action_new)

        action_open = QAction("&Open...", self)
        action_open.setShortcut(QKeySequence.StandardKey.Open)
        action_open.triggered.connect(self._cmd_open)
        file_menu.addAction(action_open)

        action_save = QAction("&Save Map As...", self)
        action_save.setShortcut(QKeySequence.StandardKey.Save)
        action_save.triggered.connect(self._cmd_save)
        file_menu.addAction(action_save)

        action_export = QAction("E&xport Image...", self)
        action_export.triggered.connect(self._cmd_export)
        file_menu.addAction(action_export)

        file_menu.addSeparator()

        action_quit = QAction("&Quit", self)
        action_quit.setShortcuts(["Ctrl+Q", "Ctrl+W"])
        action_quit.triggered.connect(self.close)
        file_menu.addAction(action_quit)

        # --- View Menu ---
        view_menu = menubar.addMenu("&View")

        action_zoom_in = QAction("Zoom &In", self)
        action_zoom_in.setShortcuts(
            [QKeySequence("Ctrl++"), QKeySequence("Ctrl+=")])
        action_zoom_in.triggered.connect(self._cmd_zoom_in)
        view_menu.addAction(action_zoom_in)

        action_zoom_out = QAction("Zoom &Out", self)
        action_zoom_out.setShortcut("Ctrl+-")
        action_zoom_out.triggered.connect(self._cmd_zoom_out)
        view_menu.addAction(action_zoom_out)

        action_zoom_reset = QAction("&Reset Zoom", self)
        action_zoom_reset.setShortcut("Ctrl+0")
        action_zoom_reset.triggered.connect(self._cmd_zoom_reset)
        view_menu.addAction(action_zoom_reset)

        # --- Settings Menu ---
        settings_menu = menubar.addMenu("&Settings")

        act_cfg_map = QAction("Map Generation Settings...", self)
        act_cfg_map.triggered.connect(self._cmd_cfg_map)
        settings_menu.addAction(act_cfg_map)

        act_cfg_scale = QAction("Scale and Unit Settings...", self)
        act_cfg_scale.triggered.connect(self._cmd_cfg_scale)
        settings_menu.addAction(act_cfg_scale)

        act_cfg_perlin = QAction("Perlin Noise Parameters...", self)
        act_cfg_perlin.triggered.connect(self._cmd_cfg_perlin)
        settings_menu.addAction(act_cfg_perlin)

        act_cfg_voronoi = QAction("Voronoi Visual Settings...", self)
        act_cfg_voronoi.triggered.connect(self._cmd_cfg_voronoi)
        settings_menu.addAction(act_cfg_voronoi)

        settings_menu.addSeparator()

        act_load_cfg = QAction("Load Configuration...", self)
        act_load_cfg.triggered.connect(self._cmd_load_cfg)
        settings_menu.addAction(act_load_cfg)

        act_save_cfg = QAction("Save Configuration As...", self)
        act_save_cfg.triggered.connect(self._cmd_save_cfg)
        settings_menu.addAction(act_save_cfg)

    def _setup_ui(self) -> None:
        """Initialise the layout, canvas, splitters, and sidebar."""
        splitter = QSplitter(orientation=Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        self.plot_container = QWidget()
        plot_layout = QGridLayout(self.plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(0)

        self.canvas = FigureCanvasQTAgg(figure=self.figure)
        plot_layout.addWidget(self.canvas, 0, 0)
        self.canvas.wheelEvent = self._handle_zoom

        # Bind PyQt Scrollbars to Matplotlib's internal view limits
        self.v_scrollbar = QScrollBar(Qt.Orientation.Vertical)
        self.v_scrollbar.valueChanged.connect(self._on_vscroll)
        plot_layout.addWidget(self.v_scrollbar, 0, 1)

        self.h_scrollbar = QScrollBar(Qt.Orientation.Horizontal)
        self.h_scrollbar.valueChanged.connect(self._on_hscroll)
        plot_layout.addWidget(self.h_scrollbar, 1, 0)

        self._update_scrollbars()
        splitter.addWidget(self.plot_container)

        self.sidebar_container = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar_container)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(self.sidebar_container)

        self._load_editor()
        splitter.setSizes([900, 300])

    def _cmd_zoom_in(self) -> None:
        self.zoom_factor *= 1.2
        self._apply_zoom()

    def _cmd_zoom_out(self) -> None:
        self.zoom_factor /= 1.2
        if self.zoom_factor < 1.0:
            self.zoom_factor = 1.0
        self._apply_zoom()

    def _cmd_zoom_reset(self) -> None:
        self.zoom_factor = 1.0
        self._apply_zoom()

    def _handle_zoom(self, event: QWheelEvent) -> None:
        """Handle mouse wheel events to zoom the axes limits directly."""
        angle = event.angleDelta().y()
        if angle > 0:
            self._cmd_zoom_in()
        elif angle < 0:
            self._cmd_zoom_out()
        event.accept()

    def _apply_zoom(self) -> None:
        """Calculate and apply mathematical view limits based on zoom level."""
        base_w = self.world_map.grid_shape[0]
        base_h = self.world_map.grid_shape[1]

        view_w = base_w / self.zoom_factor
        view_h = base_h / self.zoom_factor

        curr_xlim = self.axes.get_xlim()
        curr_ylim = self.axes.get_ylim()
        cx = (curr_xlim[0] + curr_xlim[1]) / 2.0
        cy = (curr_ylim[0] + curr_ylim[1]) / 2.0

        new_xmin = max(0, cx - view_w / 2.0)
        new_xmax = new_xmin + view_w
        if new_xmax > base_w:
            new_xmax = base_w
            new_xmin = max(0, new_xmax - view_w)

        new_ymin = max(0, cy - view_h / 2.0)
        new_ymax = new_ymin + view_h
        if new_ymax > base_h:
            new_ymax = base_h
            new_ymin = max(0, new_ymax - view_h)

        self.axes.set_xlim(new_xmin, new_xmax)
        self.axes.set_ylim(new_ymin, new_ymax)

        self._update_scrollbars()
        self.canvas.draw_idle()

    def _update_scrollbars(self) -> None:
        """Sync PyQt scrollbar handles with Matplotlib's zoom state."""
        base_w = self.world_map.grid_shape[0]
        base_h = self.world_map.grid_shape[1]

        curr_xlim = self.axes.get_xlim()
        curr_ylim = self.axes.get_ylim()

        view_w = curr_xlim[1] - curr_xlim[0]
        view_h = curr_ylim[1] - curr_ylim[0]

        if self.zoom_factor <= 1.01:
            self.h_scrollbar.setEnabled(False)
            self.v_scrollbar.setEnabled(False)
            self.h_scrollbar.setRange(0, 0)
            self.v_scrollbar.setRange(0, 0)
        else:
            self.h_scrollbar.setEnabled(True)
            self.v_scrollbar.setEnabled(True)

            self.h_scrollbar.setRange(0, int(base_w - view_w))
            self.h_scrollbar.setPageStep(int(view_w))

            # Use QSignalBlocker instead of blockSignals(True)
            with QSignalBlocker(self.h_scrollbar):
                self.h_scrollbar.setValue(int(curr_xlim[0]))

            self.v_scrollbar.setRange(0, int(base_h - view_h))
            self.v_scrollbar.setPageStep(int(view_h))
            with QSignalBlocker(self.v_scrollbar):
                self.v_scrollbar.setValue(int(base_h - curr_ylim[1]))

    def _on_hscroll(self, value: int) -> None:
        """Pan the map horizontally."""
        view_w = self.axes.get_xlim()[1] - self.axes.get_xlim()[0]
        self.axes.set_xlim(value, value + view_w)
        self.canvas.draw_idle()

    def _on_vscroll(self, value: int) -> None:
        """Pan the map vertically."""
        view_h = self.axes.get_ylim()[1] - self.axes.get_ylim()[0]
        base_h = self.world_map.grid_shape[1]
        new_ymax = base_h - value
        new_ymin = new_ymax - view_h
        self.axes.set_ylim(new_ymin, new_ymax)
        self.canvas.draw_idle()

    def _load_editor(self) -> None:
        """Initialise the editor widget and bind its signal."""
        for i in reversed(range(self.sidebar_layout.count())):
            widget = self.sidebar_layout.itemAt(i).widget()
            self.sidebar_layout.removeWidget(widget)
            widget.setParent(None)

        self.heightmap_editor = HeightmapEditor(
            figure=self.figure,
            axes=self.axes,
            canvas=self.canvas,
            world_map=self.world_map,
            scale_config=self.config.scale_configuration
        )

        self.heightmap_editor.map_modified.connect(self._mark_modified)
        self.sidebar_layout.addWidget(self.heightmap_editor)

    def _mark_modified(self) -> None:
        """Flag the current map state as having unsaved changes."""
        if not self.is_modified:
            self.is_modified = True
            self.setWindowTitle("Fimama Map Maker*")

    def _prompt_unsaved(self) -> bool:
        """Prompt user to save changes; returns False if cancelled."""
        if not self.is_modified:
            return True

        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Save before proceeding?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Save:
            return self._cmd_save()
        elif reply == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def _prompt_save_cfg(self) -> None:
        """Prompt the user to optionally save the new configuration state."""
        reply = QMessageBox.question(
            self,
            "Save Configuration",
            "Would you like to save this configuration to a file?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._cmd_save_cfg()

    def _cmd_new(self) -> None:
        """Command to generate an entirely new map."""
        if not self._prompt_unsaved():
            return

        dialog = MapSettingsDialog(config=self.config, parent=self)
        dialog.setWindowTitle("Generate New Map")

        if dialog.exec():
            _logger.info("New map generation requested.")
            self.config = dialog.get_config()

            # Generate new baseline map data
            new_heights = construct_heightmap(config=self.config)
            self.world_map = FimamaMap.make_map(heightmap=new_heights)

            # Completely replace the matplotlib figure
            self.figure, self.axes = plot_map(
                world_map=self.world_map,
                colormap=self.colormap,
                config=self.config.voronoi_configuration,
                scale_config=self.config.scale_configuration,
            )

            # Mount the new figure to the Qt window
            new_canvas = FigureCanvasQTAgg(figure=self.figure)
            self.scroll_area.setWidget(new_canvas)
            self.canvas = new_canvas
            self.canvas.wheelEvent = self._handle_zoom

            self._load_editor()
            self.is_modified = False
            self.setWindowTitle("Fimama Map Maker")

    def _cmd_open(self) -> None:
        """Command to open a saved map zip file."""
        if not self._prompt_unsaved():
            return

        filepath, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Open Fimama Map",
            filter="Fimama Map (*.zip)"
        )
        if not filepath:
            return

        with zipfile.ZipFile(file=filepath, mode='r') as zf:
            # Load pristine YAML parameters
            yaml_data = zf.read("map_data.yaml")
            config_dict = yaml.safe_load(yaml_data)
            self.config = MapConfiguration(**config_dict)

            # Load raw binary float data for the terrain
            npy_data = zf.read("heightmap.npy")
            buf = io.BytesIO(npy_data)
            loaded_heights = np.load(file=buf)
            self.world_map.heightmap = loaded_heights

        self.is_modified = False
        self.setWindowTitle("Fimama Map Maker")
        self.heightmap_editor._update_plot()
        _logger.info(f"Loaded map from {filepath}")

    def _cmd_save(self) -> bool:
        """Command to save the current map state to a zip archive."""
        filepath, _ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save Fimama Map",
            filter="Fimama Map (*.zip)"
        )
        if not filepath:
            return False

        if not filepath.endswith(".zip"):
            filepath += ".zip"

        with zipfile.ZipFile(file=filepath, mode='w') as zf:
            # 'json' mode ensures enums/paths are cast to raw primitives
            config_dict = self.config.model_dump(mode='json')
            yaml_str = yaml.dump(
                data=config_dict,
                sort_keys=False,
                default_flow_style=False
            )
            zf.writestr("map_data.yaml", yaml_str)

            # Serialize exact heightmap float data to NumPy binary
            buf = io.BytesIO()
            np.save(file=buf, arr=self.world_map.heightmap)
            zf.writestr("heightmap.npy", buf.getvalue())

        self.is_modified = False
        self.setWindowTitle("Fimama Map Maker")
        _logger.info(f"Saved map to {filepath}")
        return True

    def _cmd_cfg_map(self) -> None:
        """Open the Map Generation settings dialog."""
        dialog = MapSettingsDialog(config=self.config, parent=self)
        if dialog.exec():
            self.config = dialog.get_config()
            self._mark_modified()
            self._prompt_save_cfg()

    def _cmd_cfg_scale(self) -> None:
        """Open the Map Scale settings dialog."""
        dialog = ScaleSettingsDialog(
            config=self.config.scale_configuration, parent=self
        )
        if dialog.exec():
            self.config.scale_configuration = dialog.get_config()
            self._mark_modified()

            # Pass the new scaling object safely down the component tree
            self.heightmap_editor.scale_config = \
                self.config.scale_configuration
            self.heightmap_editor.modifier.scale_config = \
                self.config.scale_configuration

            # Re-read physical UI slider scales
            self.heightmap_editor._update_labels()

            # Dynamically update the plot bounds
            scale_cfg = self.config.scale_configuration
            collection = self.axes.collections[0]
            collection.set_clim(
                vmin=scale_cfg.min_elevation,
                vmax=scale_cfg.max_elevation
            )

            # Find the colorbar attached to the figure and
            # dynamically update its unit label
            for ax in self.figure.axes:
                if ax != self.axes:
                    ax.set_ylabel(
                        f"Elevation ({scale_cfg.elevation_unit.value})")

            self.canvas.draw_idle()
            self._prompt_save_cfg()

    def _cmd_cfg_perlin(self) -> None:
        """Open the Perlin Noise settings dialog."""
        if self.config.perlin_parameters is None:
            self.config.perlin_parameters = PerlinParameters()

        dialog = PerlinSettingsDialog(
            params=self.config.perlin_parameters, parent=self
        )
        if dialog.exec():
            self.config.perlin_parameters = dialog.get_params()
            self._mark_modified()
            self._prompt_save_cfg()

    def _cmd_cfg_voronoi(self) -> None:
        """Open the Voronoi Visual settings dialog."""
        if self.config.voronoi_configuration is None:
            self.config.voronoi_configuration = VoronoiConfiguration()

        dialog = VoronoiSettingsDialog(
            config=self.config.voronoi_configuration, parent=self
        )
        if dialog.exec():
            self.config.voronoi_configuration = dialog.get_config()
            self._mark_modified()
            self._prompt_save_cfg()

    def _cmd_save_cfg(self) -> None:
        """Save just the current application settings to a YAML file."""
        filepath, _ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save Configuration",
            filter="YAML Configuration (*.yaml *.yml)"
        )
        if not filepath:
            return

        config_dict = self.config.model_dump(mode='json')
        yaml_str = yaml.dump(
            data=config_dict, sort_keys=False, default_flow_style=False
        )
        with open(file=filepath, mode='w', encoding='utf-8') as f:
            f.write(yaml_str)
        _logger.info(f"Saved configuration to {filepath}")

    def _cmd_load_cfg(self) -> None:
        """Load application settings from a YAML file."""
        filepath, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Load Configuration",
            filter="YAML Configuration (*.yaml *.yml)"
        )
        if not filepath:
            return

        with open(file=filepath, mode='r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        self.config = MapConfiguration(**config_dict)
        self._mark_modified()
        _logger.info(f"Loaded configuration from {filepath}")

    def _cmd_export(self) -> None:
        """Command to export the generated map as an image file."""
        dialog = ExportDialog(parent=self)
        if not dialog.exec():
            return

        scope = dialog.combo_scope.currentText()

        filepath, _ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Export Image",
            filter=(
                "PNG Image (*.png);;JPEG Image (*.jpg);"
                ";SVG Vector (*.svg);;PDF Document (*.pdf)"
            )
        )
        if not filepath:
            return

        if scope == "Whole Map":
            # Cache the current user's view
            orig_xlim = self.axes.get_xlim()
            orig_ylim = self.axes.get_ylim()
            # Stretch view to capture the whole map
            self.axes.set_xlim(0, self.world_map.grid_shape[0])
            self.axes.set_ylim(0, self.world_map.grid_shape[1])
            self.figure.savefig(fname=filepath, bbox_inches='tight', dpi=300)
            # Restore user's view
            self.axes.set_xlim(orig_xlim)
            self.axes.set_ylim(orig_ylim)
        else:
            # Capture strictly what the user currently sees
            self.figure.savefig(fname=filepath, bbox_inches='tight', dpi=300)

        _logger.info(f"Image successfully exported to {filepath}")

    def closeEvent(self, event: QCloseEvent) -> None:
        """Intercept application closure (Alt+F4, X button, Ctrl+W)."""
        if self._prompt_unsaved():
            event.accept()
        else:
            event.ignore()
