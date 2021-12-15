#!/bin/bash

# copy upstream performance test script and patch it

cp upstream/performance/benchmark.py performance/benchmark.py
sed -i "s/from marshmallow/import althaia; althaia.patch()\nfrom marshmallow/" performance/benchmark.py
set -x
python performance/benchmark.py --object-count 1000
python performance/benchmark.py --iterations=5 --repeat=5 --object-count 20000
python performance/benchmark.py --iterations=10 --repeat=10 --object-count 10000
set +x
