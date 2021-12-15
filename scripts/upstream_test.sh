#!/bin/bash

# copy upstream tests and patch, this should always work out of the box

cp upstream/tests/*.py tests/
echo "import althaia; althaia.patch()" >>tests/__init__.py
pytest tests
