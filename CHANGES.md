
0.4.5 / 2020-05-13
==================

  * Ignored columns are removed from records

0.4.4 / 2020-05-11
==================

  * let pyexcel handle file type

0.4.3 / 2020-05-11
==================

  * Correctly extract srid from data
  * fix typo in separators name
  * Ensure correct csv decoding

0.4.2 / 2020-05-07
==================

  * Add CSVSource source

0.4.1 / 2020-03-24
==================

  * Fix wmts geom_type mandatory

0.4.0 / 2020-03-19
==================

  * BREAKING CHANGE : change way celery is working to allow using celery in another app

0.3.7 / 2020-03-17
==================

  * Enhance tests to valide search and filter
  * Add option to sync sources to have more control
  * Add zipfile shapefilesource

0.3.6 / 2019-12-19
==================

  * Fix bug with FileSourceSerializer

0.3.5 / 2019-12-18
==================

  * Add ordering and filtering for sources
  * Add flake8 linting to CI

0.3.4 / 2019-12-16
==================

### Improves

  * Improve documentation
  * Fix python3.8, django 3.0 and DRF 3.11 compatibility

0.3.3 / 2019-11-06
==================

### Improves

  * Define MANIFEST.in

0.3.1 / 2019-11-06
==================

### Improves

  * Improve error message when identifier field is not found in the source
  * Improve error message when geojson features has bad geometries
  * Use black for linting in pipelines

0.3.0 / 2019-10-18
==================

### Release

  * First release
