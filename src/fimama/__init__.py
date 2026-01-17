import matplotlib
matplotlib.use('qtagg')
import matplotlib.pyplot as plt

from fimama.perlin import perlin_map
from fimama.voronoi import voronoi_map


def main() -> None:
    terrain = perlin_map()
    voronoi_map(heightmap=terrain)

    # Colored elevation map
    plt.imshow(terrain, cmap='terrain')
    plt.title("Colored Terrain Elevation")
    plt.colorbar()
    plt.show()
