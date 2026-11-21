# Data center water use: data and county map

Data and page source for the AsIAm county water stress project. The goal is to compare data center water withdrawals against local water supply. This repo currently holds the county baseline of USGS withdrawals (1985 to 2015). It does not contain data center water use yet.

## What is here

- `index.html`: the interactive county map. It loads everything from `data/` at runtime, so serve it over HTTP (GitHub Pages, or `python3 -m http.server`).
- `dist/embed.html`: the same map as an HTML fragment for a Squarespace Code Block. It loads data from jsDelivr (`cdn.jsdelivr.net/gh/AsIAm04/datacenter-water-data@main/data/`), so the repo must stay public. Change `data-base` on the root div to point elsewhere.
- `data/county_water_1985_2015.json`: harmonized county series. Keys: `years`, `sectors`, `cols`, `data` (FIPS to one array per year of groundwater and surface-water values by sector, Mgal/d), `meta` (county name and state).
- `data/geo/`: county shapes (Albers, with AK, HI and PR insets), state lines, simplified HUC8 outlines, layout metadata.
- `data/unmatched_counties.csv`: legacy areas that could not be mapped to 2015 county boundaries.
- `data/siddik_2021_huc8_attributes.csv`: attribute table of the Siddik et al. 2021 HUC8 shapefile (2,106 HUC8s): counties touched by each HUC8 (`FIPS_C`), the six attribution-method results, and the characterization factor. Geometry is not included; the original shapefile is 340 MB.
- `scripts/`: `prep_county_series.py`, `prep_geometry.py`, `build_site.py`. The two prep scripts were run in a scratch environment and use its file paths; read them for method, adjust paths to rerun. `build_site.py` rebuilds the pages from `src/template.html` and `data/`.

## Method summary

- Source: USGS "Revised" county series, 1985 to 2015 (DOI 10.5066/P14Q6AVK); 2015 release DOI 10.5066/F7TB15V5. Freshwater withdrawals, groundwater plus surface water, Mgal/d.
- Seven sectors harmonized across years: public supply, domestic, irrigation (1985 to 1995: IR; 2000 to 2015: IR+IC+IG), thermoelectric (1985 to 1995: PF+PG+PN; 2000 to 2015: PO+PC), industrial, mining, livestock plus aquaculture. Commercial is excluded because USGS reported it only through 1995.
- FIPS handling: Dade to Miami-Dade, Shannon to Oglala Lakota, Wade Hampton to Kusilvak; independent Virginia cities (Bedford, Clifton Forge, South Boston) summed into their counties. Old Alaska census areas, Yellowstone Park MT and the Virgin Islands stay unmapped.
- Boundaries: Census 2015 cartographic boundaries (1:500,000). HUC8: USGS Watershed Boundary Dataset, simplified.
- Check: 160 random county-year values re-derived from source files with zero mismatches. Mapped 2015 total is 280,436 Mgal/d versus 280,689 in the 2015 release (0.09% lower, from the revised irrigation series and unmapped territories).

## Limits

USGS values are withdrawals, not consumption. Estimation methods changed between compilations, so single-county trends are approximate. Nothing after 2015 is included: USGS 2020 estimates use a different modeled method and will be shown separately.

## Planned layers

Aquifer withdrawals (USGS county-by-principal-aquifer, 2015), disclosed data center sites (operator reports, direct and indirect water never summed), and a modeled local water supply denominator from the USGS water budget release (DOI 10.5066/P142J9XG), labeled as modeled supply and never as a risk score.

## Sources and licenses

USGS data are public domain. Census boundaries are public domain. Siddik et al. 2021, Environmental Research Letters 16, 064017; data DOI 10.7294/14504913 (CC0).

## Data center symbol layer (item 3, first part)
data/datacenters/ holds the IM3 Open Source Data Center Atlas (OSM-derived, ODbL), county_datacenter_summary.csv and county_datacenter_map.json. Symbols are sized by building footprint only; campus polygons are land parcels and are not summed with buildings. Counties with only a campus or point are hollow markers. Atlas county assignment is kept; five Connecticut planning-region rows are placed by location into 2015 counties. Rebuild with scripts/prep_datacenters.py then scripts/build_site.py. Footprint says nothing about water use.

## Disclosed-water layer and naming (2026-11-20)
The page is titled "Data center water disclosure and local supply". It is not a water stress index: stress depends on demand from all users relative to available supply, and nothing here attributes stress to data centers. Layers: USGS county withdrawals (1985-2015), OSM footprint circles, and company-disclosed site water diamonds (Google FY2024, Microsoft FY2025) with the share of modeled local runoff as a labeled, modeled ratio. Rebuild: scripts/prep_datacenters.py, prep_google_water.py, prep_microsoft_water.py, prep_google_share.py, prep_disclosed_map.py, then build_site.py.

Context sources (not used as data): Rosa et al. 2026, Environ. Sci. Technol. 60, 27780-27791 (global data center exposure to modeled water gap at 50 km; results on Zenodo; it states that exposure does not establish operational or community impact); Lincoln Institute of Land Policy, "Data Drain" (Gorey, 2025-10-17).
