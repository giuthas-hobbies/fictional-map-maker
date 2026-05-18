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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence, QWheelEvent
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from fimama.configuration import MapConfiguration
from fimama.heightmap_editor import HeightmapEditor
from fimama.plot import plot_map
from fimama.voronoi import FimamaMap

_logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """
    Popup dialog for adjusting application settings.
    To be expanded with actual setting form fields.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fimama Settings")
        self.resize(300, 200)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Settings configuration will go here."))


class NewMapDialog(QDialog):
    """
    Popup dialog for defining generation parameters for a new map.
    To be expanded with inputs for map size, scale, and generator type.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Generate New Map")
        self.resize(300, 200)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("New map parameters will go here."))


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
        
        # Track if the map has been altered since the last save
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
        """Construct the menu bar and bind actions to keyboard shortcuts."""
        menubar = self.menuBar()

        # --- File Menu ---
        file_menu = menubar.addMenu("&File")

        action_new = QAction("&New Map", self)
        action_new.setShortcut(QKeySequence.StandardKey.New)
        action_new.triggered.connect(self._cmd_new)
        file_menu.addAction(action_new)

        action_open = QAction("&Open...", self)
        action_open.setShortcut(QKeySequence.StandardKey.Open)
        action_open.triggered.connect(self._cmd_open)
        file_menu.addAction(action_open)

        action_save = QAction("&Save As...", self)
        action_save.setShortcut(QKeySequence.StandardKey.Save)
        action_save.triggered.connect(self._cmd_save)
        file_menu.addAction(action_save)

        file_menu.addSeparator()

        action_quit = QAction("&Quit", self)
        action_quit.setShortcuts(["Ctrl+Q", "Ctrl+W"])
        action_quit.triggered.connect(self.close)
        file_menu.addAction(action_quit)

        # --- Settings Menu ---
        settings_menu = menubar.addMenu("&Settings")
        
        action_prefs = QAction("&Preferences", self)
        action_prefs.triggered.connect(self._cmd_settings)
        settings_menu.addAction(action_prefs)

    def _setup_ui(self) -> None:
        """Initialise the layout, canvas, splitters, and sidebar."""
        splitter = QSplitter(orientation=Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        splitter.addWidget(self.scroll_area)

        self.canvas = FigureCanvasQTAgg(figure=self.figure)
        self.scroll_area.setWidget(self.canvas)
        self.canvas.wheelEvent = self._handle_zoom

        self.sidebar_container = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar_container)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(self.sidebar_container)

        self._load_editor()
        splitter.setSizes([900, 300])

    def _load_editor(self) -> None:
        """Initialise the editor widget and bind its modification signal."""
        # Clear existing sidebar if loading a new map
        for i in reversed(range(self.sidebar_layout.count())): 
            widget_to_remove = self.sidebar_layout.itemAt(i).widget()
            self.sidebar_layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)

        self.heightmap_editor = HeightmapEditor(
            figure=self.figure,
            axes=self.axes,
            canvas=self.canvas,
            world_map=self.world_map,
            scale_config=self.config.scale_configuration
        )
        
        # Listen for changes to flag the document as modified
        self.heightmap_editor.map_modified.connect(self._mark_modified)
        self.sidebar_layout.addWidget(self.heightmap_editor)

    def _mark_modified(self) -> None:
        """Flag the current map state as having unsaved changes."""
        if not self.is_modified:
            self.is_modified = True
            self.setWindowTitle("Fimama Map Maker*")

    def _prompt_unsaved(self) -> bool:
        """
        Prompt user to save changes before proceeding.
        Returns False if the user cancels the operation.
        """
        if not self.is_modified:
            return True

        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save before closing?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Save:
            return self._cmd_save()
        elif reply == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def _cmd_new(self) -> None:
        """Command to generate a new map safely."""
        if not self._prompt_unsaved():
            return
        
        dialog = NewMapDialog(self)
        if dialog.exec():
            _logger.info("New map generation requested.")
            # Trigger configuration generation and rebuild here in the future.

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

        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                # 1. Parse configuration YAML
                yaml_data = zf.read("map_data.yaml")
                config_dict = yaml.safe_load(yaml_data)
                self.config = MapConfiguration(**config_dict)

                # 2. Extract exact numpy array
                npy_data = zf.read("heightmap.npy")
                buf = io.BytesIO(npy_data)
                loaded_heights = np.load(buf)
                
                # Replace current heightmap data
                self.world_map.heightmap = loaded_heights

            self.is_modified = False
            self.setWindowTitle("Fimama Map Maker")
            self.heightmap_editor._update_plot()
            _logger.info(f"Successfully loaded map from {filepath}")
            
        except Exception as e:
            _logger.error(f"Failed to open map: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load map:\n{e}")

    def _cmd_save(self) -> bool:
        """
        Command to save the current map state to a zip archive.
        Returns True if successful.
        """
        filepath, _ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save Fimama Map",
            filter="Fimama Map (*.zip)"
        )
        
        if not filepath:
            return False

        # Ensure .zip extension
        if not filepath.endswith(".zip"):
            filepath += ".zip"

        try:
            with zipfile.ZipFile(filepath, 'w') as zf:
                # 1. Serialize parameters to human-readable YAML
                config_dict = self.config.model_dump()
                yaml_str = yaml.dump(config_dict, sort_keys=False)
                zf.writestr("map_data.yaml", yaml_str)
                
                # 2. Serialize exact heightmap float data to NumPy binary
                buf = io.BytesIO()
                np.save(file=buf, arr=self.world_map.heightmap)
                zf.writestr("heightmap.npy", buf.getvalue())

            self.is_modified = False
            self.setWindowTitle("Fimama Map Maker")
            _logger.info(f"Successfully saved map to {filepath}")
            return True
            
        except Exception as e:
            _logger.error(f"Failed to save map: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save map:\n{e}")
            return False

    def _cmd_settings(self) -> None:
        """Command to open the application settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Intercept application closure (Alt+F4, X button, Ctrl+W)."""
        if self._prompt_unsaved():
            event.accept()
        else:
            event.ignore()

    def _handle_zoom(self, event: QWheelEvent) -> None:
        """Handle mouse wheel events to zoom the canvas."""
        angle = event.angleDelta().y()
        current_size = self.canvas.size()

        if angle > 0:
            new_w = int(current_size.width() * 1.1)
            new_h = int(current_size.height() * 1.1)
            self.zoom_factor *= 1.1
        elif angle < 0:
            new_w = int(current_size.width() / 1.1)
            new_h = int(current_size.height() / 1.1)
            self.zoom_factor /= 1.1
        else:
            return

        if self.zoom_factor <= 1.0:
            self.zoom_factor = 1.0
            self.scroll_area.setWidgetResizable(True)
            self.canvas.setMinimumSize(0, 0)
            self.canvas.setMaximumSize(16777215, 16777215)
        else:
            self.scroll_area.setWidgetResizable(False)
            self.canvas.setFixedSize(new_w, new_h)

        event.accept()