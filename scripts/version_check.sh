#!/bin/bash

# check if our version is okay according to PEP440

python -m pep440 $(poetry version -s)
