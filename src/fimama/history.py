"""
Undo and redo history management for Fimama.
"""

import numpy as np
from PyQt6.QtGui import QUndoCommand


class HeightmapEditCommand(QUndoCommand):
    """
    Command to execute and undo heightmap modifications using sparse deltas.

    By storing only the modified 1D indices rather than a full copy of the
    heightmap, memory usage per action remains virtually zero.

    Parameters
    ----------
    heightmap : np.ndarray
        Reference to the full map array being modified.
    indices : tuple[np.ndarray, ...]
        The specific array indices that were altered.
    old_values : np.ndarray
        The original float values of the altered indices.
    new_values : np.ndarray
        The new float values to apply to the altered indices.
    redraw_callback : callable
        Function to call after undo/redo to refresh the GUI canvas.
    text : str, optional
        A description of the action (e.g., "Hill Brush"), by default "Edit".
    parent : QUndoCommand | None, optional
        Parent command for macro-actions, by default None.
    """

    def __init__(
        self,
        heightmap: np.ndarray,
        indices: tuple[np.ndarray, ...],
        old_values: np.ndarray,
        new_values: np.ndarray,
        redraw_callback: callable,
        text: str = "Edit",
        parent: QUndoCommand | None = None,
    ) -> None:
        super().__init__(text, parent=parent)
        self.heightmap = heightmap
        self.indices = indices
        self.old_values = old_values
        self.new_values = new_values
        self.redraw_callback = redraw_callback

    def undo(self) -> None:
        """Revert the heightmap to the old values and redraw."""
        self.heightmap[self.indices] = self.old_values
        self.redraw_callback()

    def redo(self) -> None:
        """Apply the new values to the heightmap and redraw."""
        self.heightmap[self.indices] = self.new_values
        self.redraw_callback()
