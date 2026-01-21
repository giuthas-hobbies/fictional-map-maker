import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from fimama.perlin import perlin_map
from fimama.voronoi import voronoi_map

matplotlib.use('qtagg')

def main() -> None:
    # plot
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
    ax1.set_aspect('equal', 'box')
    ax2.set_aspect('equal', 'box')

    width = 200
    height = 200
    terrain = perlin_map(width=width, height=height)
    # terrain = np.arange(width*height).reshape((width,height))

    # Read the colormap
    tmp = []
    for row in np.loadtxt( "geo-smooth.gpf" ):
        tmp.append( [ row[0], row[1:4] ] )
    colormap = matplotlib.colors.LinearSegmentedColormap.from_list( "geo-smooth", tmp )

    voronoi_map(fig=fig, axes=ax1, heightmap=terrain, colormap=colormap)

    # Colored elevation map
    ax2.imshow(X=terrain, cmap=colormap)
    plt.show()
