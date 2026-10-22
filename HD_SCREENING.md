# HD truck charging screening near motorways

`hdcs_highway_screening.py` lists charging stations close to the Autobahn that are
usable for heavy-duty electric trucks. It replaces the passenger-car logic of
`chargingApp_V1.py` (ChargePoint scraping + weighted score for one user) with a
region-wide screening, and writes the result in the company scraper schema.

## Run

```
py -3 -m pip install pandas numpy openpyxl
py -3 hdcs_highway_screening.py --region NRW            # OSM stations, NRW
py -3 hdcs_highway_screening.py --region DE             # all of Germany (slow first run, cached afterwards)
py -3 hdcs_highway_screening.py --source xlsx --input stations_Scraped.xlsx   # output of the company scraper
```

Options: `--min-power-kw` (default 150), `--max-dist-km` (default 3),
`--min-points` (default 1), `--region` preset (`DE`, `NRW`, `AACHEN`, `KOELN`) or
`"south,west,north,east"`. Overpass answers are cached in `.hdcs_cache/`.

## Default criteria

| Criterion | Default | Why |
|---|---|---|
| Connector | CCS (Combo) or MCS | Only DC standards trucks use |
| Power per connector | >= 150 kW | Below that a 400-600 kWh truck battery cannot recharge meaningfully in the 45 min driver break |
| Tier A | MCS or CCS >= 350 kW | Fits the EU AFIR targets for HDV charging |
| Tier B | CCS 150-349 kW | Usable, slower |
| Distance | <= 3 km straight line to the nearest motorway carriageway or ramp (OSM `motorway` / `motorway_link`) | Small detour from the route |

Extra info per station: nearest motorway ref, nearest junction (exit), nearest
service/rest area and whether the station is on one, and an `HD_HGV_Hint`
(OSM `hgv=yes`, or operator/name contains Milence, Truck, LKW, Autohof ...).
Whether a truck can physically reach the charger (drive-through bay, height,
parking) is not in the data and still needs a manual check.

## Output (`output_hd/`)

* `HD_charging_<region>_<time>.xlsx`
  * `HD_Stations`: one row per suitable station, sorted by tier, number of HD points, distance
  * `HD_Connectors`: one row per HD connector, the 17 company columns first, then `HD_*` columns
  * `Check_Power_Unknown`: DC stations near the motorway whose power is not tagged in OSM
  * `All_Screened`: everything that was screened
  * `Criteria`: the parameters used
* `..._company_schema.csv`: only the 17 company columns
  (`ID, Country, PostCode, City, Street, Latitude, Longitude, Network, Operator, Count, Connector, Power, Voltage, Current, Manufacturer, Model, URL`)

Mapping notes for OSM rows: `ID` = `osm:node/<id>`, `URL` = OSM link,
`Count` = charging point number 1..n (like "Ladesäule n" in the company
scraper; OSM only gives the number of sockets, so this is an approximation),
`Connector` uses GoingElectric wording (`CCS`, `MCS`, `Typ2`, `CHAdeMO`, ...).
