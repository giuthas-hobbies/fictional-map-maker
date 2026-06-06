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

* New and updated edit commands/buttons.
* Could the voronoi feature be dynamically turned on when zooming? 
  * Currently map gen does not really use voronoi cells for anything but later
    it will.
  * For this to work the voronoi grid would need to be genrated in a way that
    is recoverable when needed. 
  * It could also be generated once as a separate step and saved and used as
    needed.
  * Was there a reason why it cannot not be parallelised? Is the reason real or
    hallucinated?
* Import bitmaps and similar as a heightmap.
  * This should do round tripping of fimama-generated maps.
* Make the maps extendable.
  * This includes continuing a map from one or more sides and
  * Creating submaps/overmaps with larger/smaller scales and different cell
    sizes.
* Provide means for working with different world geometries.
  * My own main application is a cylinder world.
  * SciPy can deal with Voronoi diagrams on a ball. Obviously we should be able
    to use this for mapping a whole planet.
* Erosion/hydrology modelling
  * Differentiation for terrain types would be nice.


## [0.10.0] - 2026-06-07

### Highlights

- New and updated edit commands/buttons.
- Moved to {new version numbering}.
- Code restructuring.

### Added

- Edit commands and buttons:
  - .

### Changed

- Updated edit commands and buttons:
  - 
- Moved GUI modules to a new gui subpackage.

### Fixed


## [0.9.0] - 2026-05-20

### Highlights

- Implemented some unit tests and some integration tests.

### Added

- Some unit and integration tests. This is nothing too fancy yet.

### Fixed

- 'dark-atlas' and 'light-atlas' colormaps now produce a correct sea level. 


## [0.8.0] - 2026-05-20

### Highlights

- Undo and redo for map editing.
- Better colormap with the option 'atlas'

### Bugs

- 'dark-atlas' and 'light-atlas' colormaps need to be re-mapped to produce a
  correct sea level. 


## [0.7.0] - 2026-05-19

### Highlights

- Height map editing tools.
- Save and load.
- Export the map as an image.

### Added

- Height map editing tools mimicking similar functionality in Azgaar's fantasy
  mapmaker.
- Save and load functionality. The save format is a zip file which contains
  parameters and other human readable parts of the map in human readable
  formats.
- Export either the visible part of the map or the whole map as an image.


## [0.6.0] - 2026-01-26

### Highlights

- Command line interface update with click.
- Logging and logging configuration.

### Added

- Click for parsing command line commands.
- Logging across the files.


## [0.5.0] - 2026-01-23

### Highlights

- Docstrings and automated documentation generation.

### Added

- Automated documentation generation and the documentation itself.

### Fixed

- Wrote docstrings for all functions, methods and classes.


## [0.4.2] - 2026-01-22

### Highlights

- Fixed Changelog to make release run work.
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
- Fixed Changelog to make release run work.


## [0.4.1] - 2026-01-22

### Highlights

- Broken release due to Changelog heading conflict.


## [0.4.0] - 2026-01-22

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
