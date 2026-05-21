"""
Integration tests for Fimama's GUI interaction logic.

Validates that UI signals, button states, and routing logic correctly
translate into modifications on the underlying data models.
"""

from unittest.mock import MagicMock

import numpy as np
import pytest
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtGui import QUndoStack
from PyQt6.QtWidgets import QPushButton

from fimama.configuration import MapScaleConfiguration
from fimama.constants import PointTool, ToolMode
from fimama.heightmap_editor import HeightmapEditor
from fimama.voronoi import FimamaMap


@pytest.fixture
def mock_editor(qtbot) -> HeightmapEditor:
    """
    Construct an isolated HeightmapEditor instance for testing.

    Parameters
    ----------
    qtbot : pytestqt.qtbot.QtBot
        The pytest-qt fixture providing Qt event loop integration.

    Returns
    -------
    HeightmapEditor
        A fully initialised widget with mock dependencies.
    """
    figure = Figure()
    axes = figure.add_subplot(111)
    canvas = FigureCanvasQTAgg(figure=figure)

    mock_heightmap = np.zeros(shape=(10, 10))
    world_map = FimamaMap.make_map(
        heightmap=mock_heightmap, random_seed=42
    )
    scale_config = MapScaleConfiguration()
    undo_stack = QUndoStack()

    editor = HeightmapEditor(
        figure=figure,
        axes=axes,
        canvas=canvas,
        world_map=world_map,
        scale_config=scale_config,
        undo_stack=undo_stack,
    )

    # Register the widget with qtbot for proper teardown
    qtbot.addWidget(editor)
    return editor


def test_tool_button_toggle_state(mock_editor: HeightmapEditor) -> None:
    """
    Test the mutual exclusivity and toggle behaviour of tool buttons.

    Ensures that activating a tool sets internal state correctly and
    clicking it a second time deactivates it.

    Parameters
    ----------
    mock_editor : HeightmapEditor
        The mocked editor instance.
    """
    # Isolate the specific button from the generated UI dictionary
    hill_button = mock_editor._tool_buttons.get(PointTool.HILL)
    assert isinstance(hill_button, QPushButton)

    # Verify initial default state is inactive
    assert mock_editor.active_tool is None
    assert not hill_button.isChecked()

    # Simulate user clicking the "Hill" button
    hill_button.click()

    # Verify the internal routing locked the tool and mode properly
    assert mock_editor.active_tool == PointTool.HILL
    assert mock_editor.tool_mode == ToolMode.POINT
    assert hill_button.isChecked()

    # Simulate user clicking the active "Hill" button again
    hill_button.click()

    # Verify the tool deactivated itself cleanly
    assert mock_editor.active_tool is None
    assert not hill_button.isChecked()


def test_point_tool_application_routing(
    mock_editor: HeightmapEditor
) -> None:
    """
    Test the dispatch of point modifications from canvas clicks.

    Validates that a simulated mouse press safely evaluates through
    the active tool enum and executes the underlying modifier math.

    Parameters
    ----------
    mock_editor : HeightmapEditor
        The mocked editor instance.
    """
    # Mock the plotting and undo calls to prevent GUI redraw errors
    mock_editor._update_plot = MagicMock()
    mock_editor._push_undo_command = MagicMock()

    # Force the active state to HILL
    mock_editor._set_active_tool(
        tool=PointTool.HILL, mode=ToolMode.POINT
    )

    baseline = mock_editor.world_map.heightmap.copy()

    # Programmatically bypass the matplotlib event and execute tool
    # directly on coordinate (5, 5).
    mock_editor._apply_point_tool(x=5, y=5, baseline=baseline)

    # Verify the heightmap array was physically altered by the tool
    assert not np.array_equal(
        a1=mock_editor.world_map.heightmap,
        a2=baseline
    )
