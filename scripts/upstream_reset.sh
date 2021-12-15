#!/bin/bash

# reset upstream marshmallow && checkout the version we need for our release

UPSTREAM_VERSION=$(python <<EOF
import toml
content = toml.load("pyproject.toml")
print(content["tool"]["althaia"]["upstream_version"])
EOF
)

git submodule init
git submodule update

cd upstream
git reset --hard
git fetch --prune
git checkout ${UPSTREAM_VERSION}
git status
cd - >/dev/null
