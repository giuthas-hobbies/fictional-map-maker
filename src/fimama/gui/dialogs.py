"""
Dialog windows for configuring Fimama settings.

This module provides PyQt6 dialog interfaces for inspecting and editing
the various `FimamaModel` configuration structures.
"""

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from fimama.configuration import (
    MapConfiguration,
    MapScaleConfiguration,
    PerlinParameters,
    VoronoiConfiguration,
)
from fimama.constants import DistanceUnit, MapGenerator


class ExportDialog(QDialog):
    """Dialog for image export options."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Export Image Options")

        layout = QFormLayout(self)

        self.combo_scope = QComboBox()
        self.combo_scope.addItems(["Whole Map", "Currently Visible Part"])
        layout.addRow("Export Scope:", self.combo_scope)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)


class PerlinSettingsDialog(QDialog):
    """
    Dialog for configuring Perlin noise parameters.

    Parameters
    ----------
    params : PerlinParameters
        The current parameters to populate the fields with.
    parent : QWidget, optional
        The parent widget of the dialog.
    """

    def __init__(
        self, params: PerlinParameters, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Perlin Noise Settings")

        layout = QFormLayout(self)

        self.spin_scale = QDoubleSpinBox()
        self.spin_scale.setMaximum(10000.0)
        self.spin_scale.setValue(params.scale)
        layout.addRow("Scale:", self.spin_scale)

        self.spin_octaves = QSpinBox()
        self.spin_octaves.setMinimum(1)
        self.spin_octaves.setMaximum(20)
        self.spin_octaves.setValue(params.octaves)
        layout.addRow("Octaves:", self.spin_octaves)

        self.spin_persist = QDoubleSpinBox()
        self.spin_persist.setSingleStep(0.1)
        self.spin_persist.setValue(params.persistence)
        layout.addRow("Persistence:", self.spin_persist)

        self.spin_lacunarity = QDoubleSpinBox()
        self.spin_lacunarity.setSingleStep(0.1)
        self.spin_lacunarity.setValue(params.lacunarity)
        layout.addRow("Lacunarity:", self.spin_lacunarity)

        self.spin_base = QSpinBox()
        self.spin_base.setMaximum(10000)
        self.spin_base.setValue(params.base)
        layout.addRow("Base Seed:", self.spin_base)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_params(self) -> PerlinParameters:
        """Return a new PerlinParameters instance from the form."""
        return PerlinParameters(
            scale=self.spin_scale.value(),
            octaves=self.spin_octaves.value(),
            persistence=self.spin_persist.value(),
            lacunarity=self.spin_lacunarity.value(),
            base=self.spin_base.value()
        )


class VoronoiSettingsDialog(QDialog):
    """Dialog for configuring Voronoi grid visual settings."""

    def __init__(
        self, config: VoronoiConfiguration, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Voronoi Grid Settings")

        layout = QVBoxLayout(self)

        self.chk_grid = QCheckBox(text="Plot Voronoi Grid")
        self.chk_grid.setChecked(config.plot_voronoi_grid)
        layout.addWidget(self.chk_grid)

        self.chk_ridges = QCheckBox(text="Show Ridges")
        self.chk_ridges.setChecked(config.show_ridges)
        layout.addWidget(self.chk_ridges)

        self.chk_vertices = QCheckBox(text="Show Vertices")
        self.chk_vertices.setChecked(config.show_vertices)
        layout.addWidget(self.chk_vertices)

        self.chk_points = QCheckBox(text="Show Base Points")
        self.chk_points.setChecked(config.show_points)
        layout.addWidget(self.chk_points)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_config(self) -> VoronoiConfiguration:
        """Return a new VoronoiConfiguration instance from the form."""
        return VoronoiConfiguration(
            plot_voronoi_grid=self.chk_grid.isChecked(),
            show_ridges=self.chk_ridges.isChecked(),
            show_vertices=self.chk_vertices.isChecked(),
            show_points=self.chk_points.isChecked()
        )


class ScaleSettingsDialog(QDialog):
    """Dialog for configuring physical map scales and units."""

    def __init__(
        self, config: MapScaleConfiguration, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Map Scale Settings")

        layout = QFormLayout(self)

        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(-20000.0, 20000.0)
        self.spin_min.setValue(config.min_elevation)
        layout.addRow("Min Elevation:", self.spin_min)

        self.spin_max = QDoubleSpinBox()
        self.spin_max.setRange(-20000.0, 20000.0)
        self.spin_max.setValue(config.max_elevation)
        layout.addRow("Max Elevation:", self.spin_max)

        self.combo_elev_unit = QComboBox()
        self.combo_elev_unit.addItems([u.value for u in DistanceUnit])
        self.combo_elev_unit.setCurrentText(config.elevation_unit.value)
        layout.addRow("Elevation Unit:", self.combo_elev_unit)

        self.combo_size_unit = QComboBox()
        self.combo_size_unit.addItems([u.value for u in DistanceUnit])
        self.combo_size_unit.setCurrentText(config.map_size_unit.value)
        layout.addRow("Map Size Unit:", self.combo_size_unit)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_config(self) -> MapScaleConfiguration:
        """Return a new MapScaleConfiguration instance from the form."""
        return MapScaleConfiguration(
            min_elevation=self.spin_min.value(),
            max_elevation=self.spin_max.value(),
            elevation_unit=DistanceUnit(self.combo_elev_unit.currentText()),
            map_size_unit=DistanceUnit(self.combo_size_unit.currentText())
        )


class MapSettingsDialog(QDialog):
    """Dialog for configuring root map generation dimensions."""

    def __init__(
        self, config: MapConfiguration, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Map Configuration")
        self.current_config = config

        layout = QFormLayout(self)

        self.spin_width = QSpinBox()
        self.spin_width.setRange(10, 10000)
        self.spin_width.setValue(config.width)
        layout.addRow("Width (cells):", self.spin_width)

        self.spin_height = QSpinBox()
        self.spin_height.setRange(10, 10000)
        self.spin_height.setValue(config.height)
        layout.addRow("Height (cells):", self.spin_height)

        self.combo_gen = QComboBox()
        self.combo_gen.addItems([g.value for g in MapGenerator])
        self.combo_gen.setCurrentText(config.generator.value)
        layout.addRow("Generator:", self.combo_gen)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_config(self) -> MapConfiguration:
        """Return a merged MapConfiguration instance from the form."""
        # Update only the base fields, leave sub-configurations alone
        data = self.current_config.model_dump()
        data["width"] = self.spin_width.value()
        data["height"] = self.spin_height.value()
        data["generator"] = MapGenerator(self.combo_gen.currentText())
        return MapConfiguration(**data)
