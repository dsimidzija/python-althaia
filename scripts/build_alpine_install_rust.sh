#!/bin/bash

if [ ! -f /etc/alpine-release ]
then
    exit 0
fi

set -x -o pipefail

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

source ~/.cargo/env
cargo --version
rustc --version

# no idea why these things aren't visible to subsequent commands
ln -s $(which cargo) /usr/bin/cargo
ln -s $(which rustc) /usr/bin/rustc
