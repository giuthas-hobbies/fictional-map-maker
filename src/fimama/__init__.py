import matplotlib
matplotlib.use('qtagg')
import matplotlib.pyplot as plt

import numpy as np

from fimama.perlin import perlin_map
from fimama.voronoi import voronoi_map


def main() -> None:
    # plot
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
    ax1.set_aspect('equal', 'box')
    ax2.set_aspect('equal', 'box')

    width = 300
    height = 300
    terrain = perlin_map(width=width, height=height)
    # terrain = np.arange(width*height).reshape((width,height))
    voronoi_map(fig=fig, axes=ax1, heightmap=terrain)

    # Colored elevation map
    ax2.imshow(X=terrain, cmap='terrain')
    plt.show()
