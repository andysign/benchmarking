#! /usr/bin/env bash

set -e

docker build -t rust-boi -f Dockerfile.rust_build_env .
