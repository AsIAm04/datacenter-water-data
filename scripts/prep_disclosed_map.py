"""Entities for the disclosed-water diamond layer: one per operator per county (sites in one county summed within an operator);
sites spanning several counties are one shared entity placed at the mean of their county positions. Never summed across operators."""
import pandas as pd, json
pos=json.load(open('data/geo/county_positions.json'))
sup=pd.read_csv('data/supply/iwaa_county_supply_wy2010_2020.csv',dtype={'fips':str}).set_index('fips').supply_mgd_mean_wy2010_2020
g=pd.read_csv('data/datacenters/google_fy2024_us_site_water.csv',dtype={'county_fips':str})
m=pd.read_csv('data/datacenters/microsoft_fy25_us_site_water.csv',dtype={'county_fips':str})
rows=[]
for _,r in g.iterrows(): rows.append(dict(op='Google',fy='FY2024',days=366,site=r.site,fips=r.county_fips.split('|'),wd=r.withdrawal_mgal,cons=r.consumption_mgal))
for _,r in m.iterrows(): rows.append(dict(op='Microsoft',fy='FY2025',days=365,site=r.site,fips=r.county_fips.split('|'),wd=r.withdrawal_mgal,cons=None))
ents={}
for r in rows:
    key=(r['op'],'|'.join(r['fips']))
    e=ents.setdefault(key,dict(op=r['op'],fy=r['fy'],days=r['days'],fips=r['fips'],sites=[],wd=0.0,cons=0.0 if r['cons'] is not None else None))
    e['sites'].append(r['site']); e['wd']+=r['wd']
    if r['cons'] is not None: e['cons']+=r['cons']
out=[]
for e in ents.values():
    xy=[pos[f] for f in e['fips'] if f in pos]; assert xy,e
    S=sup.reindex(e['fips']).sum(min_count=1)
    out.append([e['op'],e['fy'],e['sites'],e['fips'],round(sum(a for a,_ in xy)/len(xy),1),round(sum(b for _,b in xy)/len(xy),1),round(e['wd'],1),None if e['cons'] is None else round(e['cons'],1),round(100*e['wd']/e['days']/S,4),round(S,1),len(e['fips'])>1])
json.dump(out,open('data/datacenters/disclosed_water_map.json','w'),separators=(',',':'))
print(len(out),'entities;',sum(1 for o in out if o[10]),'shared');[print(o[0],o[2],o[3],o[6],o[8]) for o in sorted(out,key=lambda o:-o[6])[:6]]
