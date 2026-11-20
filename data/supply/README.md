# Local water supply denominator (USGS IWAA / NWAA)

Source: USGS National Water Availability Assessment Data Companion API (model wqn-ensemble-conus-nwaa-v1, variable incrunoff = ensemble baseflow + quickflow), HUC12, monthly mm, annual water-year mean, WY2010-2020, CONUS only.

What it is: locally generated runoff (supply generated inside each unit). It excludes upstream inflow, interbasin transfers, return flows, groundwater storage and reservoir operations. It is not a measure of what is legally or physically available to a user.

Why not strflow/availab: both include upstream inflow (checked: equal to incrunoff in headwater HUC12s, different downstream), so they are not additive across units and would double count.

Files
- usgs_nwdc_incrunoff_huc12_wy2010_2020.csv: raw pull, 83,322 HUC12, mm/month, area_km2 from WBD.
- iwaa_huc8_supply_wy2010_2020.csv: Mgal/d per HUC8 (sum of depth x area), with coverage columns.
- huc8_county_weights.csv: area weights HUC8 to county.
- iwaa_county_supply_wy2010_2020.csv: Mgal/d per county (area-weighted allocation).

Conversion: mm/month x km2 x 1000 = m3/month; / 30.4375 days; / 3785.41 m3 per Mgal.

Known gaps (not silently dropped): 587 HUC12 have no WBD area (excluded from volume); 797 HUC12 have a null year (that year left out of the sum, so that HUC8-year is understated; mean over years is used); 88 HUC8 have <95% area coverage (see coverage column). Alaska, Hawaii, territories not covered.

Checks: national sum of local runoff 1.28 million Mgal/d (about 1,282 bgd), within the expected order for conterminous US runoff. Plausibility check only; not reconciled to a published total.

Caution: total county withdrawals often exceed local runoff (e.g. Maricopa AZ) because of imported surface water and groundwater. A ratio above 1 reflects that, not a stress score.
