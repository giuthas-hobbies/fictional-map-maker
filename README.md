# fimama - Fictional Map Maker

This is a hobby project which aims to create a map maker program (not a web app) for fictional (not just fantasy) worlds. 

I'll start with a Voronoi cell based heightmap and see how much I can be bothered to work on this.

If things do progress the following I do have the following aims:
* Keep backwards compatibility so that old maps should mostly be openable by later versions.
* Make the maps extendable.
  * This includes continuing a map from one or more sides and
  * Creating submaps/overmaps with larger/smaller scales.
* Make most features editable, make most features lockable when regenerating.
* Erosion/hydrology modelling with differentiation for different terrain types would be nice.
* I do not intend to write any plate tectonics, but will be happy to integrate them if somebody else writes the code.
* Provide means for working with different world geometries.
  * My own main application is a cylinder world.
* I have more ideas too, but time is limited.

Some general principles:
* The project will [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
* The project will use [semantic version numbering](https://semver.org/).
* The project will aim for pythonic code and good documentation.
* Tests will be written as well but instead of code coverage, the priority is on integration tests.

If you want to contribute, please get in touch.
