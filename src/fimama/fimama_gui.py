"""
Main GUI application for Fimama.
"""

from matplotlib.colors import LinearSegmentedColormap
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import (
    QMainWindow,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from fimama.configuration import MapConfiguration
from fimama.heightmap_editor import HeightmapEditor
from fimama.plot import plot_map
from fimama.voronoi import FimamaMap


class FimamaGui(QMainWindow):
    """
    Main application GUI window.

    Orchestrates the PyQt6 window, the Matplotlib canvas, and manages
    different interactive modes (like the HeightmapEditor).
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

        self.setWindowTitle("Fimama Map Maker")
        self.resize(1200, 800)

        # Build the matplotlib figure independent of pyplot
        self.figure, self.axes = plot_map(
            world_map=self.world_map,
            colormap=self.colormap,
            config=self.config.voronoi_configuration,
            scale_config=self.config.scale_configuration,
        )

        self._setup_ui()

        # Load the initial tool mode into the right panel
        self.heightmap_editor = HeightmapEditor(
            figure=self.figure,
            axes=self.axes,
            canvas=self.canvas,
            world_map=self.world_map,
            scale_config=self.config.scale_configuration,
        )
        self.sidebar_layout.addWidget(self.heightmap_editor)

    def _setup_ui(self) -> None:
        """Initialise the layout, canvas, and splitters."""
        splitter = QSplitter(orientation=Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        # Left side: Scroll Area holding the Map Canvas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        splitter.addWidget(self.scroll_area)

        self.canvas = FigureCanvasQTAgg(figure=self.figure)
        self.scroll_area.setWidget(self.canvas)
        self.canvas.wheelEvent = self._handle_zoom

        # Right side: Container for tool modes
        self.sidebar_container = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar_container)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(self.sidebar_container)

        splitter.setSizes([900, 300])

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
