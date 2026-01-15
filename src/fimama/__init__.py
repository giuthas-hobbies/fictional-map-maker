import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi

from .colorised_voronoi import voronoi_finite_polygons_2d

def main() -> None:
    # make up data points
    np.random.seed(1234)
    points = np.random.rand(15, 2)

    # compute Voronoi tesselation
    vor = Voronoi(points)

    # plot
    regions, vertices = voronoi_finite_polygons_2d(vor)
    print("--")
    print(regions)
    print("--")
    print(vertices)

    # colorize
    for region in regions:
        polygon = vertices[region]
        plt.fill(*zip(*polygon), alpha=0.4)

    plt.plot(points[:,0], points[:,1], 'ko')
    plt.xlim(vor.min_bound[0] - 0.1, vor.max_bound[0] + 0.1)
    plt.ylim(vor.min_bound[1] - 0.1, vor.max_bound[1] + 0.1)

    plt.show()
