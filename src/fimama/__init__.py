import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from fimama.perlin import perlin_map
from fimama.voronoi import voronoi_map

matplotlib.use('qtagg')

def main() -> None:
    # plot
    fig, (ax1) = plt.subplots(nrows=1, ncols=1, layout="constrained")
    ax1.set_aspect('equal', 'box')
    # ax2.set_aspect('equal', 'box')

    width = 200
    height = 125
    terrain = perlin_map(width=width, height=height).T
    # terrain = np.arange(width*height).reshape((width,height))

    # Read the colormap
    tmp = []
    for row in np.loadtxt( "dark-atlas.gpf" ):
        tmp.append( [ row[0], row[1:4] ] )
    colormap = matplotlib.colors.LinearSegmentedColormap.from_list( "dark-atlas", tmp )

    voronoi_map(fig=fig, axes=ax1, heightmap=terrain, colormap=colormap)

    # Colored elevation map
    # ax2.imshow(X=terrain, cmap=colormap)
    # plt.tight_layout()
    plt.show()
