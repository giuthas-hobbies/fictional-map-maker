
from importlib.resources import path as resource_path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import yaml

from fimama.configuration import MapConfiguration
from fimama.perlin import perlin_map
from fimama.voronoi import voronoi_map

matplotlib.use('qtagg')


def main() -> None:
    # plot
    anchor='fimama.resources'

    # read the config
    with resource_path(anchor, "default.yaml") as config_path:
        with open(config_path, 'r', encoding='utf-8') as config_file:
            raw_config = yaml.safe_load(config_file)
            config = MapConfiguration(**raw_config)

    terrain = perlin_map(
        width=config.width, height=config.height, params=config.perlin_parameters).T
    # terrain = np.arange(width*height).reshape((width,height))

    # Read the colormap
    with resource_path(anchor, f"{config.colormap_name}.gpf") as colormap_path:
        tmp = []
        for row in np.loadtxt(colormap_path):
            tmp.append( [ row[0], row[1:4] ] )
        colormap = matplotlib.colors.LinearSegmentedColormap.from_list(config.colormap_name, tmp)

    fig, (ax1) = plt.subplots(nrows=1, ncols=1, layout="constrained")
    ax1.set_aspect('equal', 'box')
    # ax2.set_aspect('equal', 'box')

    voronoi_map(fig=fig, axes=ax1, heightmap=terrain, colormap=colormap)

    # Colored elevation map
    # ax2.imshow(X=terrain, cmap=colormap)
    # plt.tight_layout()
    plt.show()
