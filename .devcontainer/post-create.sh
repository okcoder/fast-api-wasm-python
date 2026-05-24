#!/usr/bin/env bash
set -euo pipefail

mise trust --yes "$PWD/.mise.toml"
mise install
poetry install
