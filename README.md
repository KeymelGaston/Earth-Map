# Earth Game Map

A real-Earth world map, built with code, designed as a **base layer for a game engine**.

It combines real geographic data (coastlines, countries, rivers, lakes, cities, relief) into:

1. a compact **tile grid** (1440 × 720 tiles, 0.25° each) that a game can load directly, and
2. an **interactive viewer** (a single HTML file) to explore and inspect the data.

> **Live viewer:** open `docs/index.html` in any modern browser, or publish the `docs/` folder with GitHub Pages
> (Settings → Pages → *Deploy from a branch* → `main` / `/docs`).
> The viewer UI is in Spanish.

---

## Features

- **Grid data for engines**: biome, country, elevation, sea depth and water (river / lake) for every tile.
- **255 countries and territories** from Natural Earth 1:10m, including small island states
  (e.g. Marshall Islands) and U.S. Minor Outlying Islands (Midway).
- **3,118 cities** (population ≥ 100k, plus all national capitals).
- **Vector detail** drawn on top of the grid: coastlines and borders, 1,454 rivers, 1,325 lakes and 3,537 small islands,
  with level-of-detail rules so deep zoom stays sharp.
- **Viewer layers**: Atlas (shaded relief), Satellite, Biomes, Elevation, Countries; toggles for rivers/lakes, borders,
  graticule, chunk grid, labels and cities; scale bar; per-tile inspector; **chunk export** to JSON.
- **Reproducible pipeline**: every file in `data/` and `docs/` can be rebuilt from the original sources with one command.
- **TypeScript loader** example for the binary format.

## Repository layout

```
data/
  earth_1440x720.bin     Binary grid (5 layers x 1440 x 720 bytes)
  earth_meta.json        Country names, cities, label anchors
docs/
  index.html             Standalone interactive viewer (all data embedded)
examples/
  EarthMap.ts            TypeScript loader / query API
tools/                   Build pipeline (see "Rebuilding")
viewer/
  template.html          Viewer source (data is injected at build time)
requirements.txt         Python dependencies for the pipeline
```

## Quick start

### Explore the map

Open `docs/index.html`. Mouse wheel = zoom, drag = pan, hover = inspect a tile, click = select a chunk
(the *Exportar un chunk* panel shows its JSON).

### Query the data from TypeScript

```bash
npx tsx examples/EarthMap.ts
```

```ts
import { EarthMap } from "./examples/EarthMap";

const map = EarthMap.fromFiles("data/earth_1440x720.bin", "data/earth_meta.json");
const tile = map.at(171.38, 7.1);      // lon, lat
// { biomeName: "Grassland / savanna", country: "Marshall Is.", isLand: true, river: false, ... }
```

In the browser, `fetch` both files and pass an `ArrayBuffer` and the parsed JSON to `new EarthMap(buffer, meta)`.

## Data format

### Grid: `data/earth_1440x720.bin`

Raw bytes, **5 layers stored one after another**, each `1440 × 720 = 1,036,800` bytes (file size: 5,184,000 bytes).
Index inside a layer: `y * 1440 + x`. Layer `k` starts at byte offset `k * 1,036,800`.

| # | Layer     | Values |
|---|-----------|--------|
| 0 | biome     | Biome id, see table below |
| 1 | country   | `0` = none (ocean); otherwise index into `names` in `earth_meta.json` **plus one** |
| 2 | elevation | `0–255`, relative land height (see limitations); `0` over water |
| 3 | depth     | `0–255`, relative sea-floor shading proxy; `0` over land |
| 4 | water     | `0` none, `1` river, `2` lake |

Projection: **equirectangular** (plate carrée), whole planet, no wrap-around.

```
lon = -180 + (x + 0.5) * 0.25        x = floor((lon + 180) / 0.25)
lat =   90 - (y + 0.5) * 0.25        y = floor((90 - lat) / 0.25)
```

One tile is 0.25° (about 28 km at the equator, narrower east-west towards the poles).
A **chunk** is 16 × 16 tiles (4° × 4°), giving 90 × 45 chunks.

| Id | Biome | Notes |
|----|-------|-------|
| 0 | Deep ocean | water |
| 1 | Ocean | water |
| 2 | Shallow water | water |
| 3 | Ice | land |
| 4 | Tundra | land |
| 5 | Desert | land |
| 6 | Grassland / savanna | land |
| 7 | Forest | land |
| 8 | Jungle | land |
| 9 | Mountain | land |
| 10 | High mountain | land |
| 11 | Lake | water body inside land |

`biome >= 3` means "land or inland water". Walkability, movement costs, etc. are game rules and are intentionally left to you.

### Metadata: `data/earth_meta.json`

```jsonc
{
  "W": 1440, "H": 720,
  "names":  ["Afghanistan", "Angola", ...],             // 255 entries, country id = index + 1
  "cities": [["Tokyo", 139.75, 35.69, 35676000, 1], ...],// name, lon, lat, population, isNationalCapital (1/0); sorted by population
  "labels": [["Indonesia", 100.64, -0.14, 10.9], ...]    // name, lon, lat, width in degrees (viewer label anchors)
}
```

### Exported chunk (from the viewer)

```jsonc
{
  "chunk": [cx, cy], "tileSize": 16, "degreesPerTile": 0.25,
  "origin": { "lon": ..., "lat": ... },                   // north-west corner of the chunk
  "layers": { "biome": [16 rows of hex], "height": [...], "country": [...], "water": [...] },
  "countries": [...], "biomes": [...]
}
```
Rows are strings: biome and water use 1 hex digit per tile, height and country use 2.

## How it is built

Pipeline (`tools/run_all.sh`), executed from the repository root:

| Step | Script | What it does |
|------|--------|--------------|
| 1 | `01_fetch_sources.sh` | Downloads the raw datasets into `sources/` |
| 2 | `02_build_grid.py` | Rasterizes countries (Natural Earth 1:10m) and small islands (land 1:10m), builds elevation and depth from imagery, classifies biomes, cleans source artifacts |
| 3 | `03_add_water_and_cities.py` | Rasterizes rivers and lakes into the water layer, marks lake tiles, builds the city list |
| 4 | `04_labels_and_islands.py` | Computes country label anchors and the vector list of small islands |
| 5 | `05_pack_vectors.py` | Simplifies rivers, lakes, borders (Douglas-Peucker, ~0.012°) and compresses the vector data |
| 6 | `06_build_viewer.py` | Embeds everything into `docs/index.html` and copies final files to `data/` |

```bash
pip install -r requirements.txt     # numpy, Pillow, scipy, shapely
bash tools/run_all.sh               # needs curl, unzip, pip, npm and internet access
```

The build is deterministic: rebuilding from scratch reproduces `data/earth_1440x720.bin` byte for byte.

### Method notes

- **Countries**: polygons are rasterized largest-first so enclaves (e.g. Lesotho) stay on top. Polygons that cross the
  antimeridian are drawn on both sides. Antarctica is completed from the elevation image.
- **Small islands**: islands smaller than one tile are drawn with an outline so they occupy at least one tile; their country
  is the nearest country within 25° (e.g. Midway → United States Minor Outlying Is.). Their biome is a placeholder.
- **Biomes**: classified from satellite colour (Blue Marble) with latitude rules, then overridden by elevation
  (mountains, high mountains) and by water bodies.
- **Elevation**: a grayscale global topography image, resampled to the grid.
- **Viewer**: canvas 2D. Images are cropped to the visible region before drawing (avoids huge destination sizes at deep zoom);
  vector layers use bounding-box culling and point decimation based on zoom.

## Limitations (please read)

- **Resolution**: 0.25° per tile (~28 km). Fine for continent / region scale, too coarse for local maps.
  The deep-zoom sharpness in the viewer comes from vector overlays, not from higher-resolution grid data.
- **Biomes are an approximation** derived from image colour, not from climate data. Expect local errors
  (for example irrigated river deltas can appear as grassland). Island biomes are placeholders.
- **Elevation is relative** (0–255). The viewer shows roughly `value × 20 m` as an estimate; very high ranges saturate.
  Do not use it for precise heights.
- **No wrap-around** at ±180° longitude; features crossing it are split.
- **Rivers/lakes in the grid** are rasterized from Natural Earth centerlines/polygons (rivers up to rank 8), so thin
  rivers are 1 tile wide and small lakes below tile size are missing from the grid (they still appear in the viewer vectors).
- **Political borders are a snapshot** of Natural Earth's dataset and follow its conventions for disputed areas.
- No ocean currents, climate, resources or road networks are included.

## Data sources and credits

This project is a derived work built on openly available data. **Please verify each license before redistributing
or using commercially.**

| Data | Source |
|------|--------|
| Countries, coastlines, land, rivers, lakes, populated places | [Natural Earth](https://www.naturalearthdata.com/) vector data (public domain), fetched from the `nvkelso/natural-earth-vector` repository |
| Country/land topology files | [`world-atlas`](https://github.com/topojson/world-atlas) npm package (derived from Natural Earth) |
| Shaded relief, Blue Marble satellite imagery, ETOPO1 relief image | Bundled in the `basemap-data` PyPI package (Natural Earth, NASA Blue Marble Next Generation, NOAA ETOPO1) |
| Grayscale global topography | Texture bundled in the `earth-visualization` npm package; check the original provider and license of that texture before redistributing derived data |

The `sources/` directory is intentionally not committed; `tools/01_fetch_sources.sh` downloads everything on demand.

## Ideas for next steps

- Group tiles into **provinces / regions** (e.g. subdivide each country) for strategy or simulation games.
- Add movement costs and passability rules per biome, rivers as obstacles, and path finding.
- Add rivers/lakes with finer width classes, a night-lights layer, or an antique-map style.
- Replace the satellite-derived biomes with climate-based classification (temperature and precipitation datasets).
- Increase local detail by streaming higher-resolution data for selected regions.

## Development notes

Built by Keymel (GitHub: KeymelGaston) with AI assistance (Claude, by Anthropic). The pipeline was verified end to end
from clean sources, and the TypeScript loader was type-checked and run against the real data.

## License

Source code: MIT (see `LICENSE`). Datasets and imagery keep their original licenses (see above).
