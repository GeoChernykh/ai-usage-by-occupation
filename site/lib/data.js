// All fetches. Paths are relative: the site is served from a subdirectory.

const cache = new Map();

async function get(path) {
  if (!cache.has(path)) {
    cache.set(path, fetch(path).then(r => {
      if (!r.ok) throw new Error(path + ' -> ' + r.status);
      return r.json();
    }));
  }
  return cache.get(path);
}

export const index = () => get('data/index.json');
export const occupation = soc => get('data/occ/' + soc + '.json');
export const tasks = () => get('data/tasks.json');
export const countries = () => get('data/countries.json');
export const subregions = () => get('data/subregions.json');
export const world = () => get('data/world.geojson');

// series.json is Stage D and may not exist. A 404 is an expected state, and the
// miss is cached too, so a month switch never re-requests it.
let seriesPromise;
export function series() {
  if (!seriesPromise) {
    seriesPromise = get('data/series.json').catch(() => {
      console.info('series.json not present; the Compare screen stays hidden');
      return null;
    });
  }
  return seriesPromise;
}
