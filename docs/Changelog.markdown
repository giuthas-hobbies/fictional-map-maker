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

* Provide means for working with different world geometries.
  * My own main application is a cylinder world.
  * SciPy can deal with Voronoi diagrams on a ball. Obviously we should be able
    to use this for mapping a whole planet.
* Erosion/hydrology modelling with differentiation for different terrain types
  would be nice.

## [0.1.0a4] - 2026-01-15

### Highlights

- Second test version


## [0.1.0a2] - 2026-01-15

### Highlights

- First test version.

### Added

- Voronoi grid that will be the basis of rest of the map.
- Automated release mechanic.
