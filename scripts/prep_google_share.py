import pandas as pd
df=pd.read_csv('data/datacenters/google_fy2024_us_site_water.csv',dtype={'county_fips':str})
s=pd.read_csv('data/supply/iwaa_county_supply_wy2010_2020.csv',dtype={'fips':str}).set_index('fips').supply_mgd_mean_wy2010_2020
o=[]
for _,r in df.iterrows():
    S=s.reindex(r.county_fips.split('|')).sum(min_count=1)
    o.append(dict(site=r.site,county_fips=r.county_fips,low_confidence_county=('LOW CONFIDENCE' in r.county_basis),withdrawal_mgd=round(r.withdrawal_mgal/366,4),consumption_mgd=round(r.consumption_mgal/366,4),local_supply_mgd=round(S,1),withdrawal_pct_of_local_supply=round(100*r.withdrawal_mgal/366/S,4),consumption_pct_of_local_supply=round(100*r.consumption_mgal/366/S,4)))
pd.DataFrame(o).to_csv('data/datacenters/google_fy2024_share_of_local_supply.csv',index=False); print(pd.DataFrame(o).loc[lambda d:d.site=='New Albany, OH'].T)
