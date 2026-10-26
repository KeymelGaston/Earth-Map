#!/usr/bin/env bash
# Downloads every raw source dataset into ./sources (not committed to git).
set -euo pipefail
mkdir -p sources build && cd sources
NE=https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson
for f in ne_10m_rivers_lake_centerlines ne_10m_lakes ne_10m_populated_places_simple ne_50m_populated_places_simple; do
  [ -f $f.geojson ] || curl -fsSL -o $f.geojson $NE/$f.geojson
done
[ -f world-atlas.tgz ] || curl -fsSL -o world-atlas.tgz https://registry.npmjs.org/world-atlas/-/world-atlas-2.0.2.tgz
if [ ! -d basemap-data ]; then
  pip download --no-deps -q -d _bm basemap-data --break-system-packages 2>/dev/null || pip download --no-deps -q -d _bm basemap-data
  mkdir basemap-data && unzip -q _bm/*.whl -d basemap-data && rm -rf _bm
fi
if [ ! -d earth-visualization ]; then
  mkdir _ev && (cd _ev && npm pack earth-visualization --silent >/dev/null) && mkdir earth-visualization && tar xzf _ev/*.tgz -C earth-visualization && rm -rf _ev
fi
echo "sources ready"
