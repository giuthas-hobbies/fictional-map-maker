import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

from fimama.voronoi import voronoi_map


def plot_map(
    heightmap: np.ndarray, colormap: LinearSegmentedColormap,
):
    """
    Plot a heightmap as a field of Voronoi cells.

    Parameters
    ----------
    heightmap : np.ndarray
        Heightmap to plot
    colormap : LinearSegmentedColormap
        Colormap to use in the plotting.

    Returns
    -------
    tuple[matplotlib.figure.Figure, matplotlib.Axes.axes]
        The containing Figure and the Axes the map was plotted on.
    """
    fig, (ax1) = plt.subplots(nrows=1, ncols=1, layout="constrained")
    ax1.set_aspect('equal', 'box')
    # ax2.set_aspect('equal', 'box')

    voronoi_map(fig=fig, axes=ax1, heightmap=heightmap, colormap=colormap)

    # Colored elevation map
    # ax2.imshow(X=terrain, cmap=colormap)
    # plt.tight_layout()
    plt.show()
    return fig, ax1
