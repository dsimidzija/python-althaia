# Changelog

## Unreleased

* ?

## 3.21.1

* Added an additional handler to Althaia meta path finder to handle the new way marshmallow is exposing its version
  and package information.

## 3.20.1

* Prebuild wheels for aarch64 Linux now supported thanks to @hvalev
* Officially support Python 3.11
* Dropped support for Python 3.7 and 3.8 due to significant typing annotation changes unsupported by Cython 3.0.0,
  which would make it very difficult to maintain.
* Performance gains have dropped from ~55% to ~30% after updating to Python 3.11 and Cython 3.0.0, needs further
  investigation to figure out why.
