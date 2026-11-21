# IM3 Open Source Data Center Atlas v2026.11.02

Source: Mongird, Vernon, Burleyson, Akdemir & Rice (2026), MSD-LIVE, https://doi.org/10.57931/17054299 (record qxpk8-yae09). Licence: ODbL 1.0; derived from OpenStreetMap contributors. Counties from Census 2024 boundaries.

Files: CSV (2,018 rows; point 128, building 1,636, campus 254) and GeoPackage (layers point, building, campus; WGS84).

Use notes (from the record): crowd-sourced and incomplete; campus and building polygons can overlap, so do not sum sqft across layers; facilities straddling a county line appear once per county with the same id; the atlas holds locations and footprint only, no water or power data. Footprint is a siting layer, not a water estimate.

## Google FY2024 disclosed water (separate layer, direct only)
google_fy2024_us_site_water.csv: 23 US sites from Google's 2025 environmental report (FY2024), million gallons withdrawal/discharge/consumption. Covers 79% of Google's reported 9,866 Mgal total withdrawal (rest is non-US and an unallocated "Other" line, not mapped). Operational water at the sites only; electricity-related (indirect) water is not included and must never be added. Site-to-county is by place name (inferred), cross-checked against the atlas for the Ohio sites and Lenoir NC; Midlothian TX not checked. New Albany OH straddles Franklin and Licking counties; its volume is not split and is compared with the two counties' combined supply. google_fy2024_share_of_local_supply.csv divides withdrawal and consumption (Mgal/yr / 366 days, 2024 leap year) by the county's mean local runoff (data/supply). Other operators are absent, so county values are a floor for all data centers.
