#!/usr/bin/env bash
# Rebuilds everything from the original sources. Run from the repository root.
set -euo pipefail
bash tools/01_fetch_sources.sh
python3 tools/02_build_grid.py
python3 tools/03_add_water_and_cities.py
python3 tools/04_labels_and_islands.py
python3 tools/05_pack_vectors.py
python3 tools/06_build_viewer.py
