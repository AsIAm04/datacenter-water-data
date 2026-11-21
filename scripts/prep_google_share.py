import pandas as pd
s=pd.read_csv('data/supply/iwaa_county_supply_wy2010_2020.csv',dtype={'fips':str}).set_index('fips').supply_mgd_mean_wy2010_2020
for fy,days in (('2024',366),('2025',365)):
    df=pd.read_csv(f'data/datacenters/google_fy{fy}_us_site_water.csv',dtype={'county_fips':str})
    o=[]
    for _,r in df.iterrows():
        S=s.reindex(r.county_fips.split('|')).sum(min_count=1)
        o.append(dict(site=r.site,county_fips=r.county_fips,straddles=('STRADDLES' in r.county_basis),withdrawal_mgd=round(r.withdrawal_mgal/days,4),consumption_mgd=round(r.consumption_mgal/days,4),local_supply_mgd=round(S,1),context_ratio_withdrawal_pct_of_local_modeled_runoff=round(100*r.withdrawal_mgal/days/S,4),context_ratio_consumption_pct_of_local_modeled_runoff=round(100*r.consumption_mgal/days/S,4)))
    pd.DataFrame(o).to_csv(f'data/datacenters/google_fy{fy}_share_of_local_supply.csv',index=False)
print('written')
