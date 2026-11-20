import pandas as pd, numpy as np, geopandas as gpd
d=pd.read_csv('/mnt/user-data/uploads/Downloads/usgs_nwdc_incrunoff_huc12_wy2010_2020.csv',dtype={'huc12':str})
yc=[c for c in d.columns if c.startswith('incrunoff')]; yrs=[int(c[-4:]) for c in yc]
d['huc8']=d.huc12.str[:8]
print('HUC12',len(d),'missing area',int(d.area_km2.isna().sum()),'rows with any null year',int(d[yc].isna().any(axis=1).sum()))
# volume in Mgal/d: mm/month * km2 -> m3/month = v*area*1000 ; per day /30.4375 ; Mgal = 3785.411784 m3
K=1000/30.4375/3785.411784
ok=d.area_km2.notna()
v=d.loc[ok,yc].mul(d.loc[ok,'area_km2'],axis=0)*K
v['huc8']=d.loc[ok,'huc8'];v['area']=d.loc[ok,'area_km2']
# null years: treat as missing, not zero; track
g=v.groupby('huc8')
hu=g[yc].sum(min_count=1)
hu.columns=['supply_mgd_wy%d'%y for y in yrs]
hu['supply_mgd_mean_wy2010_2020']=hu.mean(axis=1)
hu['n_huc12_used']=g.size(); hu['area_km2_used']=g.area.sum()
nulls=d[d[yc].isna().any(axis=1)].groupby('huc8').size().rename('n_huc12_with_null_year')
hu=hu.join(nulls).fillna({'n_huc12_with_null_year':0})
tot=d.groupby('huc8').size().rename('n_huc12_total'); hu=hu.join(tot)
na=d[~ok].groupby('huc8').size().rename('n_huc12_no_area'); hu=hu.join(na).fillna({'n_huc12_no_area':0})
h=gpd.read_file('/mnt/user-data/uploads/Claude/data-center-water/wbd_huc8_simplified.geojson')[['huc8','name','areasqkm']]
hu=hu.reset_index().merge(h,on='huc8',how='left')
hu['coverage']=(hu.area_km2_used/hu.areasqkm).round(3)
print('HUC8',len(hu),'coverage<0.95:',int((hu.coverage<0.95).sum()),'no WBD match',int(hu.areasqkm.isna().sum()))
print('national mean local runoff (all HUC8 as used) Mgal/d',round(hu.supply_mgd_mean_wy2010_2020.sum()))
print('by year',{y:round(hu['supply_mgd_wy%d'%y].sum()) for y in yrs})
hu.round(3).to_csv('out/iwaa_huc8_supply_wy2010_2020.csv',index=False)
# county allocation
w=pd.read_csv('out/huc8_county_weights.csv',dtype={'huc8':str,'fips':str})
m=w.merge(hu[['huc8']+['supply_mgd_wy%d'%y for y in yrs]+['supply_mgd_mean_wy2010_2020']],on='huc8',how='left')
sc=['supply_mgd_wy%d'%y for y in yrs]+['supply_mgd_mean_wy2010_2020']
for c in sc: m[c]=m[c]*m['weight']
cs=m.groupby('fips')[sc].sum(min_count=1)
cs['n_huc8']=m.groupby('fips').huc8.nunique()
cs=cs.reset_index(); print('counties',len(cs),'sum',round(cs.supply_mgd_mean_wy2010_2020.sum()))
cs.round(3).to_csv('out/iwaa_county_supply_wy2010_2020.csv',index=False)
# exploratory: county withdrawals 2015 (7 sectors) over local supply
import json
P=json.load(open('out/county_data.json'))
tw={f:(sum(x for x in a[6] if x) if a[6] else None) for f,a in P['data'].items()}
x=cs.set_index('fips'); x['w2015']=pd.Series(tw); x['ratio']=x.w2015/x.supply_mgd_mean_wy2010_2020
print(x.ratio.describe(percentiles=[.5,.9,.99]).round(3))
print(x.sort_values('ratio',ascending=False).head(8)[['supply_mgd_mean_wy2010_2020','w2015','ratio']].round(2))
