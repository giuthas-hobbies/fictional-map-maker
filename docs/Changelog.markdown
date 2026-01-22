# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


[//]: # (Possible headings in a release:)
[//]: # (Highlights for shiny new features.)
[//]: # (Added for new features.)
[//]: # (Changed for changes in existing functionality.)
[//]: # (Refactor when functionality does not change but moves.)
[//]: # (Documentation for updates to docs.)
[//]: # (Testing for updates to tests.)
[//]: # (Deprecated for soon-to-be removed features.)
[//]: # (Removed for now removed features.)
[//]: # (Bugs for any known issues, especially in use before 1.0.)
[//]: # (Fixed for any bug fixes.)
[//]: # (Security in case of vulnerabilities.)
[//]: # (New contributors for first contributions.)

[//]: # (And of course if a version needs to be YANKED:)
[//]: # (## [version number] [data] [YANKED])

## [Unreleased]

- logging
- better command line interface
* Make the maps extendable.
  * This includes continuing a map from one or more sides and
  * Creating submaps/overmaps with larger/smaller scales.
* Provide means for working with different world geometries.
  * My own main application is a cylinder world.
  * SciPy can deal with Voronoi diagrams on a ball. Obviously we should be able
    to use this for mapping a whole planet.
* Erosion/hydrology modelling with differentiation for different terrain types
  would be nice.
- Later on map configuration in the gui and saveable/loadable to/from a
      file.


## [0.5.0] - 2026-01-22

### Highlights

- Docstrings and automated documentation generation.

### Added

- Automated documentation generation and the documentation itself.

### Fixed

- Wrote docstrings for all functions, methods and classes.


## [0.4.1] - 2026-01-22

### Highlights

- The content that should have been in v0.4.0.
- Config file for map generation parameters.
- Second colormap with darker colours.

### Added

- Config file for map generation parameters.
  - For now this is implemented as a .yaml file read in simple mode (no fancy
    object parsing) and then parsed into a proper config object with Pydantic.
  - As we are still for the foreseeable future in versions before 1.0, and
    therefore in alpha/beta stages, this implementation like everything else may change in compatibility breaking ways between minor versions.
- Second color map with darker colours than the first. 

### Fixed 

- The colormaps are now package resources so will be included in installations.


## [0.4.1] - 2026-01-22

### Highlights

- Mistaken release with no actual updates.


## [0.3.0] - 2026-01-21

### Highlights

- Better colormap from [Philipp K. Janert](https://janert.me/blog/2022/the-diamond-square-algorithm-for-terrain-generation/).

### Added

- Better colormap which differentiates between land and water.


## [0.2.0] - 2026-01-18

### Highlights

- Random Perlin noise heightmap instead of just random cell values.

### Added

- Heightmap generation with Perlin noise from the `noise` package.


## [0.1.2] - 2026-01-15

### Highlights

- Third PyPi release attempt.


## [0.1.0] - 2026-01-15

### Highlights

- First PyPi release attempt.


## [0.1.0-alpha.7] - 2026-01-15

### Highlights

- Fixed semantic versioning of past releases.


## [0.1.0-alpha.5] - 2026-01-15

### Highlights

- Test version with fixed version number


## [0.1.0-alpha.4] - 2026-01-15

### Highlights

- Second test version


## [0.1.0-alpha.2] - 2026-01-15

### Highlights

- First test version.

### Added

- Voronoi grid that will be the basis of rest of the map.
- Automated release mechanic.
