"""
HDCS highway screening: find charging stations near motorways (Autobahn)
that are suitable for heavy-duty (HD) electric trucks.

Output follows the field schema of the company GoingElectric scraper, so the
result can be merged into the company app directly:

    ID, Country, PostCode, City, Street, Latitude, Longitude, Network, Operator,
    Count, Connector, Power, Voltage, Current, Manufacturer, Model, URL

One row = one connector (same as the company scraper). Screening results are
appended as extra columns prefixed with "HD_" so the first 17 columns stay
identical to the company schema.

Two input sources:
  --source osm   fetch stations from OpenStreetMap (Overpass API), no key needed
  --source xlsx  read the Excel produced by the company scraper (*_Scraped.xlsx)

Motorway geometry always comes from OpenStreetMap (highway=motorway and
motorway_link), plus motorway junctions and service/rest areas.

Default HD criteria (all configurable on the command line):
  * connector is CCS (Combo) or MCS
  * power >= 150 kW per connector
  * straight-line distance to the nearest motorway carriageway / ramp <= 3 km
  Tier A = MCS or CCS >= 350 kW, Tier B = CCS 150-349 kW.

Examples:
  py -3 hdcs_highway_screening.py --region NRW
  py -3 hdcs_highway_screening.py --region DE --max-dist-km 2 --min-power-kw 300
  py -3 hdcs_highway_screening.py --source xlsx --input stations_Scraped.xlsx

Only needs pandas, numpy and openpyxl (no shapely/geopandas).
"""

import argparse
import hashlib
import json
import math
import os
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Company schema (copied from the company GoingElectric scraper)
# ---------------------------------------------------------------------------
RESULTS_COLUMNS = ['ID', 'Country', 'PostCode', 'City', 'Street', 'Latitude', 'Longitude',
                   'Network', 'Operator', 'Count', 'Connector', 'Power', 'Voltage', 'Current',
                   'Manufacturer', 'Model', 'URL']

# Bounding boxes as (south, west, north, east)
REGIONS = {
    'DE': (47.27, 5.87, 55.06, 15.04),
    'NRW': (50.32, 5.86, 52.53, 9.46),
    'AACHEN': (50.60, 5.95, 50.95, 6.50),
    'KOELN': (50.75, 6.70, 51.10, 7.25),
}

OVERPASS_URLS = ['https://overpass-api.de/api/interpreter',
                 'https://overpass.kumi.systems/api/interpreter']
USER_AGENT = 'HDCS-highway-screening/1.0 (research, RWTH)'
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.hdcs_cache')

# OSM socket key -> connector name in GoingElectric wording
OSM_SOCKETS = {
    'mcs': 'MCS',
    'type2_combo': 'CCS',
    'chademo': 'CHAdeMO',
    'type2': 'Typ2',
    'type2_cable': 'Typ2',
    'schuko': 'Schuko',
    'cee_blue': 'CEE Blau',
    'cee_red_16a': 'CEE Rot',
    'cee_red_32a': 'CEE Rot',
    'cee_red_63a': 'CEE Rot',
    'tesla_supercharger': 'Tesla Supercharger',
    'tesla_supercharger_ccs': 'CCS',
}

HD_CONNECTOR_PATTERN = re.compile(r'mcs|ccs|combo', re.IGNORECASE)
MCS_PATTERN = re.compile(r'mcs|megawatt', re.IGNORECASE)
HGV_KEYWORDS = re.compile(r'milence|truck|lkw|hgv|nutzfahrzeug|e-?trucking|autohof|mcs', re.IGNORECASE)

EARTH_KM_PER_DEG_LAT = 110.574
EARTH_KM_PER_DEG_LON_EQ = 111.320


# ---------------------------------------------------------------------------
# Overpass helpers
# ---------------------------------------------------------------------------
def overpass(query, use_cache=True, retries=5):
    """Run an Overpass query and cache the JSON answer on disk."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.sha1(query.encode('utf-8')).hexdigest()
    cache_file = os.path.join(CACHE_DIR, key + '.json')
    if use_cache and os.path.exists(cache_file):
        with open(cache_file, encoding='utf-8') as f:
            return json.load(f)

    data = urllib.parse.urlencode({'data': query}).encode('utf-8')
    last_error = None
    for attempt in range(retries):
        for url in OVERPASS_URLS:
            try:
                req = urllib.request.Request(url, data=data, headers={'User-Agent': USER_AGENT})
                with urllib.request.urlopen(req, timeout=400) as resp:
                    result = json.loads(resp.read().decode('utf-8'))
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f)
                return result
            except Exception as e:  # rate limit / timeout -> try next server, then wait
                last_error = e
                print(f'\tOverpass request failed at {url}: {e}')
        time.sleep(20 * (attempt + 1))
    raise RuntimeError(f'Overpass query failed: {last_error}')


def tiles(bbox, step=2.0):
    """Split a bbox in tiles so big regions (e.g. all of Germany) don't time out."""
    s, w, n, e = bbox
    lat = s
    while lat < n:
        lon = w
        while lon < e:
            yield (round(lat, 4), round(lon, 4), round(min(lat + step, n), 4), round(min(lon + step, e), 4))
            lon += step
        lat += step


def bbox_str(b):
    return f'{b[0]},{b[1]},{b[2]},{b[3]}'


# ---------------------------------------------------------------------------
# Motorway network
# ---------------------------------------------------------------------------
class MotorwayIndex:
    """Grid index of motorway segments for fast point-to-line distance."""

    def __init__(self, cell_deg=0.1):
        self.cell = cell_deg
        self.seg = []          # (lat1, lon1, lat2, lon2)
        self.seg_ref = []      # motorway ref, e.g. "A 4"
        self.grid = defaultdict(list)
        self.junctions = []    # (lat, lon, label)
        self.services = []     # (lat, lon, label)

    def load(self, bbox):
        for t in tiles(bbox, step=1.0):  # smaller tiles, motorway geometry is large
            print(f'\tMotorways in tile {t}')
            q = (f'[out:json][timeout:300];'
                 f'way["highway"~"^(motorway|motorway_link)$"]({bbox_str(t)});'
                 f'out tags geom;')
            for el in overpass(q).get('elements', []):
                geom = el.get('geometry') or []
                ref = el.get('tags', {}).get('ref', '')
                for p1, p2 in zip(geom[:-1], geom[1:]):
                    self._add_segment(p1['lat'], p1['lon'], p2['lat'], p2['lon'], ref)
            q = (f'[out:json][timeout:300];'
                 f'node["highway"="motorway_junction"]({bbox_str(t)});out;'
                 f'nwr["highway"~"^(services|rest_area)$"]({bbox_str(t)});out center tags;')
            for el in overpass(q).get('elements', []):
                tags = el.get('tags', {})
                lat = el.get('lat', el.get('center', {}).get('lat'))
                lon = el.get('lon', el.get('center', {}).get('lon'))
                if lat is None:
                    continue
                if tags.get('highway') == 'motorway_junction':
                    label = ' '.join(x for x in [tags.get('name', ''), tags.get('ref', '')] if x)
                    self.junctions.append((lat, lon, label))
                else:
                    label = tags.get('name', tags.get('highway', ''))
                    self.services.append((lat, lon, label))
        self.seg = np.array(self.seg, dtype=float) if self.seg else np.zeros((0, 4))
        self.junctions_arr = np.array([(a, b) for a, b, _ in self.junctions]) if self.junctions else np.zeros((0, 2))
        self.services_arr = np.array([(a, b) for a, b, _ in self.services]) if self.services else np.zeros((0, 2))
        print(f'\t{len(self.seg)} motorway segments, {len(self.junctions)} junctions, '
              f'{len(self.services)} service/rest areas')

    def _add_segment(self, lat1, lon1, lat2, lon2, ref):
        idx = len(self.seg)
        self.seg.append((lat1, lon1, lat2, lon2))
        self.seg_ref.append(ref)
        for i in range(int(math.floor(min(lat1, lat2) / self.cell)), int(math.floor(max(lat1, lat2) / self.cell)) + 1):
            for j in range(int(math.floor(min(lon1, lon2) / self.cell)), int(math.floor(max(lon1, lon2) / self.cell)) + 1):
                self.grid[(i, j)].append(idx)

    def nearest_motorway(self, lat, lon, search_km=10.0):
        """Return (distance_km, ref) of the closest motorway segment, NaN if none within search_km."""
        kx = EARTH_KM_PER_DEG_LON_EQ * math.cos(math.radians(lat))
        ky = EARTH_KM_PER_DEG_LAT
        di = int(math.ceil(search_km / (ky * self.cell)))
        dj = int(math.ceil(search_km / (kx * self.cell)))
        ci, cj = int(math.floor(lat / self.cell)), int(math.floor(lon / self.cell))
        cand = set()
        for i in range(ci - di, ci + di + 1):
            for j in range(cj - dj, cj + dj + 1):
                cand.update(self.grid.get((i, j), ()))
        if not cand:
            return float('nan'), ''
        idx = np.fromiter(cand, dtype=int)
        s = self.seg[idx]
        # local flat projection around the station (km)
        ax, ay = (s[:, 1] - lon) * kx, (s[:, 0] - lat) * ky
        bx, by = (s[:, 3] - lon) * kx, (s[:, 2] - lat) * ky
        dx, dy = bx - ax, by - ay
        len2 = dx * dx + dy * dy
        t = np.where(len2 > 0, -(ax * dx + ay * dy) / np.where(len2 > 0, len2, 1), 0.0).clip(0, 1)
        px, py = ax + t * dx, ay + t * dy
        d = np.sqrt(px * px + py * py)
        k = int(np.argmin(d))
        if d[k] > search_km:
            return float('nan'), ''
        # ramps (motorway_link) usually have no ref -> name the closest segment that has one
        refs = np.array([self.seg_ref[i] for i in idx])
        has_ref = refs != ''
        ref = refs[has_ref][int(np.argmin(d[has_ref]))] if has_ref.any() else ''
        return float(d[k]), ref

    @staticmethod
    def _nearest_point(arr, labels, lat, lon):
        if len(arr) == 0:
            return float('nan'), ''
        kx = EARTH_KM_PER_DEG_LON_EQ * math.cos(math.radians(lat))
        d = np.hypot((arr[:, 1] - lon) * kx, (arr[:, 0] - lat) * EARTH_KM_PER_DEG_LAT)
        k = int(np.argmin(d))
        return float(d[k]), labels[k][2]

    def nearest_junction(self, lat, lon):
        return self._nearest_point(self.junctions_arr, self.junctions, lat, lon)

    def nearest_service(self, lat, lon):
        return self._nearest_point(self.services_arr, self.services, lat, lon)


# ---------------------------------------------------------------------------
# Station sources -> company schema
# ---------------------------------------------------------------------------
def parse_number(text, unit_pattern):
    """Max number found in an OSM value like '150 kW;350 kW' (MW converted to kW)."""
    if text is None:
        return float('nan')
    values = []
    for m in re.finditer(r'(\d+(?:[.,]\d+)?)\s*(' + unit_pattern + r')?', str(text), re.IGNORECASE):
        v = float(m.group(1).replace(',', '.'))
        if m.group(2) and m.group(2).lower() == 'mw':
            v *= 1000
        values.append(v)
    return max(values) if values else float('nan')


def stations_from_osm(bbox):
    rows, extra = [], {}
    for t in tiles(bbox):
        print(f'\tCharging stations in tile {t}')
        q = (f'[out:json][timeout:300];('
             f'nwr["amenity"="charging_station"]["socket:type2_combo"]({bbox_str(t)});'
             f'nwr["amenity"="charging_station"]["socket:mcs"]({bbox_str(t)});'
             f'nwr["amenity"="charging_station"]["socket:tesla_supercharger_ccs"]({bbox_str(t)});'
             f');out center tags;')
        for el in overpass(q).get('elements', []):
            osm_id = f"osm:{el['type']}/{el['id']}"
            if osm_id in extra:
                continue
            tags = el.get('tags', {})
            lat = el.get('lat', el.get('center', {}).get('lat'))
            lon = el.get('lon', el.get('center', {}).get('lon'))
            street = ' '.join(x for x in [tags.get('addr:street', ''), tags.get('addr:housenumber', '')] if x)
            base = [osm_id, tags.get('addr:country', ''), tags.get('addr:postcode', ''),
                    tags.get('addr:city', ''), street, lat, lon, tags.get('network', ''),
                    tags.get('operator', '')]
            tail = [tags.get('manufacturer', ''), tags.get('model', ''),
                    f"https://www.openstreetmap.org/{el['type']}/{el['id']}"]
            extra[osm_id] = {
                'HD_Name': tags.get('name', ''),
                'HD_HGV_Tag': tags.get('hgv', ''),
                'HD_Access': tags.get('access', ''),
            }
            for key, connector in OSM_SOCKETS.items():
                value = tags.get(f'socket:{key}')
                if value is None or value == 'no':
                    continue
                n = int(value) if str(value).isdigit() else 1
                power = parse_number(tags.get(f'socket:{key}:output'), r'kw|mw')
                if math.isnan(power) and connector in ('CCS', 'MCS'):
                    # fall back to station level output if it is the only DC type
                    power = parse_number(tags.get('charging_station:output'), r'kw|mw')
                voltage = parse_number(tags.get(f'socket:{key}:voltage'), r'v')
                current = parse_number(tags.get(f'socket:{key}:current'), r'a')
                # one row per connector, Count = charging point number (like "Ladesäule n")
                for count in range(1, min(n, 40) + 1):
                    rows.append(base + [count, connector, power, voltage, current] + tail)
    df = pd.DataFrame(rows, columns=RESULTS_COLUMNS)
    meta = pd.DataFrame.from_dict(extra, orient='index').rename_axis('ID').reset_index()
    return df, meta


def stations_from_xlsx(path):
    df = pd.read_excel(path)
    missing = [c for c in RESULTS_COLUMNS if c not in df.columns]
    if missing:
        raise SystemExit(f'Input file misses company columns: {missing}')
    df = df[RESULTS_COLUMNS].copy()
    for c in ['Latitude', 'Longitude', 'Power', 'Voltage', 'Current']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    meta = pd.DataFrame({'ID': df['ID'].unique()})
    for c in ['HD_Name', 'HD_HGV_Tag', 'HD_Access']:
        meta[c] = ''
    return df, meta


# ---------------------------------------------------------------------------
# Screening
# ---------------------------------------------------------------------------
def connector_tier(connector, power, min_power):
    connector = str(connector)
    if MCS_PATTERN.search(connector):
        return 'A'
    if not HD_CONNECTOR_PATTERN.search(connector) or pd.isna(power):
        return ''
    if power >= max(350, min_power):
        return 'A'
    if power >= min_power:
        return 'B'
    return ''


def screen(df, meta, motorways, args):
    df = df.copy()
    df['HD_Connector_Tier'] = [connector_tier(c, p, args.min_power_kw) for c, p in zip(df['Connector'], df['Power'])]
    df['HD_Power_Unknown'] = df['Connector'].astype(str).str.contains(HD_CONNECTOR_PATTERN) & df['Power'].isna()

    # station level distances (only for stations that have at least one DC fast connector)
    stations = df[df['Connector'].astype(str).str.contains(HD_CONNECTOR_PATTERN)] \
        .groupby('ID', as_index=False).first()[['ID', 'Latitude', 'Longitude']]
    print(f'\tComputing motorway distance for {len(stations)} stations')
    records = []
    for sid, lat, lon in stations.itertuples(index=False):
        if pd.isna(lat) or pd.isna(lon):
            records.append((sid, np.nan, '', np.nan, '', np.nan, ''))
            continue
        d_mw, ref = motorways.nearest_motorway(lat, lon, search_km=max(10.0, args.max_dist_km))
        d_j, j = motorways.nearest_junction(lat, lon)
        d_s, s = motorways.nearest_service(lat, lon)
        records.append((sid, d_mw, ref, d_j, j, d_s, s))
    dist = pd.DataFrame(records, columns=['ID', 'HD_Dist_Motorway_km', 'HD_Motorway', 'HD_Dist_Junction_km',
                                          'HD_Junction', 'HD_Dist_ServiceArea_km', 'HD_ServiceArea'])

    df = df.merge(dist, on='ID', how='left').merge(meta, on='ID', how='left')
    df['HD_On_ServiceArea'] = df['HD_Dist_ServiceArea_km'] <= 0.3

    text = (df['Operator'].astype(str) + ' ' + df['Network'].astype(str) + ' ' + df['HD_Name'].astype(str))
    df['HD_HGV_Hint'] = df['HD_HGV_Tag'].isin(['yes', 'designated']) | text.str.contains(HGV_KEYWORDS)

    # station summary
    hd = df[df['HD_Connector_Tier'] != '']
    agg = hd.groupby('ID').agg(HD_Points=('Count', 'nunique'),
                              HD_Max_Power_kW=('Power', 'max'),
                              HD_Has_MCS=('Connector', lambda s: s.astype(str).str.contains(MCS_PATTERN).any()),
                              HD_Best_Tier=('HD_Connector_Tier', 'min')).reset_index()
    df = df.merge(agg, on='ID', how='left')
    df['HD_Points'] = df['HD_Points'].fillna(0).astype(int)
    df['HD_Near_Motorway'] = df['HD_Dist_Motorway_km'] <= args.max_dist_km
    df['HD_Suitable'] = df['HD_Best_Tier'].notna() & df['HD_Near_Motorway'] & (df['HD_Points'] >= args.min_points)
    return df


def write_outputs(df, args):
    os.makedirs(args.out_dir, exist_ok=True)
    stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    tag = args.region if args.source == 'osm' else os.path.splitext(os.path.basename(args.input))[0]
    xlsx = os.path.join(args.out_dir, f'HD_charging_{tag}_{stamp}.xlsx')
    csv = os.path.join(args.out_dir, f'HD_charging_{tag}_{stamp}_company_schema.csv')

    sort_cols = ['HD_Best_Tier', 'HD_Points', 'HD_Dist_Motorway_km', 'ID', 'Count']
    suitable = df[df['HD_Suitable']].sort_values(sort_cols, ascending=[True, False, True, True, True])
    # connectors of suitable stations, HD connectors only, company columns first
    hd_rows = suitable[suitable['HD_Connector_Tier'] != '']

    station_cols = ['ID', 'HD_Name', 'Operator', 'Network', 'City', 'Street', 'Latitude', 'Longitude',
                    'HD_Best_Tier', 'HD_Has_MCS', 'HD_Points', 'HD_Max_Power_kW', 'HD_Motorway',
                    'HD_Dist_Motorway_km', 'HD_Junction', 'HD_Dist_Junction_km', 'HD_ServiceArea',
                    'HD_On_ServiceArea', 'HD_HGV_Hint', 'HD_HGV_Tag', 'URL']
    stations = suitable.drop_duplicates('ID')[station_cols]

    # near motorway, DC connector, but power not tagged -> manual check list
    check = df[df['HD_Power_Unknown'] & df['HD_Near_Motorway'] & ~df['HD_Suitable']].drop_duplicates('ID')[station_cols]

    criteria = pd.DataFrame({
        'Criterion': ['Connector', 'Min power per connector', 'Tier A', 'Tier B', 'Max distance to motorway',
                      'Min HD charging points per station', 'Motorway definition', 'Source', 'Region / input',
                      'Created'],
        'Value': ['CCS (Combo) or MCS', f'{args.min_power_kw} kW', 'MCS or CCS >= 350 kW',
                  f'CCS {args.min_power_kw}-349 kW', f'{args.max_dist_km} km (straight line)',
                  args.min_points, 'OSM highway=motorway + motorway_link', args.source,
                  args.region if args.source == 'osm' else args.input, stamp],
    })

    with pd.ExcelWriter(xlsx) as w:
        stations.to_excel(w, sheet_name='HD_Stations', index=False)
        hd_rows.to_excel(w, sheet_name='HD_Connectors', index=False)
        check.to_excel(w, sheet_name='Check_Power_Unknown', index=False)
        df.to_excel(w, sheet_name='All_Screened', index=False)
        criteria.to_excel(w, sheet_name='Criteria', index=False)
    # pure company schema (17 columns) for direct import into the company app
    hd_rows[RESULTS_COLUMNS].to_csv(csv, index=False, encoding='utf-8-sig')
    print(f'\n{len(stations)} HD suitable stations ({len(hd_rows)} connectors), '
          f'{len(check)} stations to check manually')
    print(f'Written: {xlsx}\n         {csv}')
    return xlsx, csv


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--source', choices=['osm', 'xlsx'], default='osm')
    p.add_argument('--input', help='company scraper output (*.xlsx) when --source xlsx')
    p.add_argument('--region', default='NRW', help=f'preset {list(REGIONS)} or bbox "south,west,north,east"')
    p.add_argument('--min-power-kw', type=float, default=150)
    p.add_argument('--max-dist-km', type=float, default=3.0)
    p.add_argument('--min-points', type=int, default=1, help='min number of HD connectors per station')
    p.add_argument('--out-dir', default='output_hd')
    args = p.parse_args()

    if args.source == 'xlsx':
        if not args.input:
            from tkinter import filedialog  # same dialog as the company scraper
            args.input = filedialog.askopenfilename(title='Select scraped charging point list',
                                                    filetypes=[('Excel file', '*.xlsx'), ('All files', '*.*')])
            if not args.input:
                raise SystemExit('Process terminated by user')
        print('Import company scraper file')
        df, meta = stations_from_xlsx(args.input)
        lat, lon = df['Latitude'].dropna(), df['Longitude'].dropna()
        bbox = (lat.min() - 0.1, lon.min() - 0.1, lat.max() + 0.1, lon.max() + 0.1)
    else:
        if args.region.upper() in REGIONS:
            bbox = REGIONS[args.region.upper()]
        else:
            bbox = tuple(float(x) for x in args.region.split(','))
        print(f'Fetch charging stations from OpenStreetMap for {args.region} {bbox}')
        df, meta = stations_from_osm(bbox)
    print(f'\t{df["ID"].nunique()} stations, {len(df)} connector rows')

    print('Load motorway network')
    motorways = MotorwayIndex()
    motorways.load(bbox)

    print('Screen stations')
    result = screen(df, meta, motorways, args)
    write_outputs(result, args)


if __name__ == '__main__':
    main()
