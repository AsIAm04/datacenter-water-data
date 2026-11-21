"""Microsoft FY25 (Jul 2024 to Jun 2025) US datacenter water withdrawal by location, Environmental Data Fact Sheet 2026, Table 15 (megaliters).
Withdrawal only (site-level consumption is not published). Pool counts in the source equal ML/2.5, which cross-checks each ML value."""
import pandas as pd
ML=0.264172  # million gallons per megaliter
R=[ # location, ML, pools_in_source, non_potable_pct, counties, basis
('Ashburn (VA)',239,95,None,['51107'],'metro name; Loudoun County (atlas Microsoft buildings there)'),
('Atlanta (GA)',19,7,None,['13121','13097'],'METRO: atlas shows Microsoft buildings in Fulton and Douglas; volume not split'),
('Boydton (VA)',362,145,None,['51117'],'Boydton is in Mecklenburg County; atlas has Microsoft there'),
('Cheyenne (WY)',188,75,None,['56021'],'Laramie County (atlas)'),
('Chicago (IL)',204,81,None,['17031'],'Cook County (atlas); metro may include other counties'),
('Des Moines (IA)',264,105,None,['19153','19049','19181','19121'],'METRO: atlas shows Microsoft in Polk, Dallas, Warren, Madison; volume not split'),
('East Wenatchee (WA)',51,20,None,['53017'],'Douglas County (atlas)'),
('Manassas (VA)',11,4,None,['51153'],'Prince William County (atlas); Manassas independent cities not separately mapped'),
('Phoenix (AZ)',981,392,None,['04013'],'Maricopa County (atlas)'),
('Quincy (WA)',1292,517,74,['53025'],'Grant County (atlas)'),
('San Antonio (TX)',420,168,79,['48029','48325'],'METRO: atlas shows Microsoft in Bexar and Medina; volume not split'),
]
sup=pd.read_csv('data/supply/iwaa_county_supply_wy2010_2020.csv',dtype={'fips':str}).set_index('fips').supply_mgd_mean_wy2010_2020
rows=[]
for loc,ml,pools,np_,f,b in R:
    assert abs(ml/2.5-pools)<1,(loc,ml,pools)   # source cross-check
    mg=ml*ML; S=sup.reindex(f).sum(min_count=1)
    rows.append(dict(site=loc,year='FY2025',withdrawal_ml=ml,withdrawal_mgal=round(mg,1),non_potable_pct=np_,county_fips='|'.join(f),multi_county=len(f)>1,county_basis=b,operator='Microsoft',water_type='direct, withdrawal only (no consumption published by site)',withdrawal_mgd=round(mg/365,4),local_supply_mgd=round(S,1),withdrawal_pct_of_local_supply=round(100*mg/365/S,4)))
df=pd.DataFrame(rows); df.to_csv('data/datacenters/microsoft_fy25_us_site_water.csv',index=False)
print(df[['site','withdrawal_mgal','county_fips','local_supply_mgd','withdrawal_pct_of_local_supply']].sort_values('withdrawal_pct_of_local_supply',ascending=False).to_string(index=False))
print('US named total ML',sum(r[1] for r in R),'| Mgal',round(sum(r[1] for r in R)*ML))
