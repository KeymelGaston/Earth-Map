/**
 * Minimal TypeScript loader for data/earth_1440x720.bin and data/earth_meta.json.
 * Works in Node (readFileSync) and in the browser (pass an ArrayBuffer to the constructor).
 */
export const WIDTH = 1440;
export const HEIGHT = 720;
export const DEGREES_PER_TILE = 0.25;
export const CHUNK_SIZE = 16; // tiles per chunk side (= 4 degrees)

export const BIOMES = [
  "Deep ocean", "Ocean", "Shallow water", "Ice", "Tundra", "Desert",
  "Grassland / savanna", "Forest", "Jungle", "Mountain", "High mountain", "Lake",
] as const;

export interface City { name: string; lon: number; lat: number; population: number; capital: boolean }
export interface Meta {
  names: string[];                 // country names, country id = index + 1
  cities: [string, number, number, number, number][]; // name, lon, lat, population, isCapital
}
export interface Tile {
  x: number; y: number; lon: number; lat: number;
  biome: number; biomeName: string;
  country: string | null;          // null = ocean / no country
  elevation: number;               // relative, 0..255 (land only)
  depth: number;                   // relative, 0..255 (ocean only)
  river: boolean; lake: boolean; isLand: boolean;
}

export class EarthMap {
  private readonly n = WIDTH * HEIGHT;
  private readonly bytes: Uint8Array;
  constructor(buffer: ArrayBuffer | Uint8Array, private readonly meta: Meta) {
    this.bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
    if (this.bytes.length !== this.n * 5) throw new Error("Unexpected file size: expected 5 layers of 1440x720 bytes");
  }
  static fromFiles(binPath: string, metaPath: string): EarthMap {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const fs = require("node:fs") as typeof import("node:fs");
    return new EarthMap(fs.readFileSync(binPath), JSON.parse(fs.readFileSync(metaPath, "utf8")));
  }
  /** Converts lon/lat (degrees) to tile coordinates. Returns null outside the map. */
  tileAt(lon: number, lat: number): [number, number] | null {
    const x = Math.floor((lon + 180) / DEGREES_PER_TILE), y = Math.floor((90 - lat) / DEGREES_PER_TILE);
    return x < 0 || y < 0 || x >= WIDTH || y >= HEIGHT ? null : [x, y];
  }
  tile(x: number, y: number): Tile {
    const i = y * WIDTH + x, b = this.bytes, n = this.n;
    const biome = b[i], country = b[n + i], water = b[4 * n + i], isLand = biome >= 3;
    return {
      x, y, lon: -180 + (x + 0.5) * DEGREES_PER_TILE, lat: 90 - (y + 0.5) * DEGREES_PER_TILE,
      biome, biomeName: BIOMES[biome], country: country ? this.meta.names[country - 1] : null,
      elevation: b[2 * n + i], depth: b[3 * n + i], river: water === 1, lake: water === 2, isLand,
    };
  }
  at(lon: number, lat: number): Tile | null {
    const t = this.tileAt(lon, lat);
    return t ? this.tile(t[0], t[1]) : null;
  }
  chunkOf(x: number, y: number): [number, number] { return [Math.floor(x / CHUNK_SIZE), Math.floor(y / CHUNK_SIZE)]; }
  cities(): City[] {
    return this.meta.cities.map(([name, lon, lat, population, cap]) => ({ name, lon, lat, population, capital: cap === 1 }));
  }
}

// Quick demo: `npx tsx examples/EarthMap.ts`
if (typeof process !== "undefined" && process.argv[1]?.endsWith("EarthMap.ts")) {
  const map = EarthMap.fromFiles("data/earth_1440x720.bin", "data/earth_meta.json");
  for (const [name, lon, lat] of [["Majuro", 171.38, 7.1], ["Midway", -177.38, 28.2], ["Cairo", 31.24, 30.04], ["Mid-Pacific", -140, 0]] as const)
    console.log(name, map.at(lon, lat));
}
