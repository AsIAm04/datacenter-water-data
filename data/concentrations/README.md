# Data center concentrations (HUC8 subbasins)
Inputs from the 2026-11-21 study update: pool.csv (20 subbasins with the most mapped atlas sites: atlas site count, states, counties, building footprint, modeled local runoff), record_site.csv (atlas record to site to HUC8), pool_aqueduct.csv (WRI Aqueduct 4.0 baseline values), pool_usdm.csv (U.S. Drought Monitor summaries).

## The nine (confirmed by the study author, 2026-11-21)
The map layer (data/concentrations_map.json, built by scripts/prep_concentrations.py) outlines the rows with case=True in pool_usdm.csv:
02070010 Middle Potomac-Anacostia-Occoquan, 02070008 Middle Potomac-Catoctin, 07120004 Des Plaines, 18050003 Coyote, 15060106 Lower Salt, 15050100 Middle Gila, 10190003 Middle South Platte-Cherry Creek, 17070101 Middle Columbia-Lake Wallula, 17090010 Tualatin.
The other 11 pool members were screened and not selected.
Selection rule: the five largest by atlas site count (the original protocol said four, and a tie at 19 sites between Coyote and Lower Salt added a fifth by amendment), plus the two highest and two lowest Aqueduct baseline values among the remaining pool.
Outlines come from the simplified WBD HUC8 shapes used for the HUC8 layer.
Label: geographic concentration, not a verified shared supply. Atlas is OpenStreetMap-derived and incomplete.

## Site counts
pool.csv counts sites, and each site is assigned to one HUC8. record_site.csv counts records. Ten of 740 sites have records in two subbasins, so counting records adds one site to five subbasins: Middle Potomac-Anacostia-Occoquan (32 vs 31), Middle Potomac-Catoctin (24 vs 23), Des Plaines (22 vs 21), Upper Scioto (15 vs 14) and Big Papillion-Mosquito (13 vs 12). The page uses the pool.csv counts.
Assignment rule (from the study author): a site goes to the subbasin holding most of its records. Two one-record ties went to the lower HUC8 code, which was an unplanned rule. My own re-derivation by most frequent HUC8 matched 18 of 20 counts, so the two ties are the likely source of the difference.

## Aqueduct (pool_aqueduct.csv)
WRI Aqueduct 4.0 baseline annual water stress, read at the site-weighted centroid of each subbasin's atlas sites. The value describes the surrounding HydroBASINS level 6 basin, which is larger than the HUC8. It is not a classification of the whole subbasin. Computed for these 20 only. A map-wide layer would need the 261 MB WRI geodatabase.

## Drought Monitor columns (pool_usdm.csv), not shown on the page
Source: US Drought Monitor (NDMC, USDA, NOAA), HUC8 area statistics, weekly maps 2000-01-04 to 2026-11-17 (1,403 maps per subbasin). Each weekly value is the percent of the subbasin's area in a drought class. Classes are cumulative (D1 means D1 or worse). D0 >= D1 >= D2 >= D3 >= D4 holds in every row (checked by the study author).
- weeks: number of weekly maps used (1,403).
- D1_mean_all, D1_mean_2020on, D1_mean_2023on: mean weekly percent of area in D1 or worse over that period.
- D1_ge25_all, _2020on, _2023on: percent of weeks in which 25% or more of the area was in D1 or worse. The 25% threshold is an analysis-time choice, not a Drought Monitor standard.
- D2_ge25_*: same, for D2 (severe drought) or worse.
- latest, latest_D1, latest_D2: the 2026-11-17 map and that week's percent of area in D1+ and D2+.
- case: true for the nine concentrations.
These describe drought across the whole subbasin. They do not describe the water source of any facility inside it. If a drought toggle is built, label it a screening layer and keep it apart from the disclosed-water layer. Leaving them off the page is a reasonable choice until then.
