"""Entities for the disclosed-water diamond layer: one per site (sites in the same county are fanned out on the map, never summed);
a site spanning several counties is one shared entity placed at the mean of their county positions. Never summed across operators or sites.
Google carries FY2024 and FY2025 (2025 and 2026 environmental reports). Per-site rows are kept because a county or location total
cannot separate heavier use from added buildings, and three sites appear only in the 2025 table (not established as new facilities).
Entity: [op, fy, sites, fips, x, y, wd, cons, pct, S, shared, V, SR]
 wd/cons/pct = latest year (Google FY2025, Microsoft FY2025); V = {"24":[wd,cons,pct],"25":[...]} (Microsoft only "25");
 SR = per-site rows [site, wd24, cons24, wd25, cons25, first_in_2025_flag, county_basis]."""
import pandas as pd, json, math
pos=json.load(open('data/geo/county_positions.json'))
sup=pd.read_csv('data/supply/iwaa_county_supply_wy2010_2020.csv',dtype={'fips':str}).set_index('fips').supply_mgd_mean_wy2010_2020
g24=pd.read_csv('data/datacenters/google_fy2024_us_site_water.csv',dtype={'county_fips':str}).set_index('site')
g25=pd.read_csv('data/datacenters/google_fy2025_us_site_water.csv',dtype={'county_fips':str}).set_index('site')
m=pd.read_csv('data/datacenters/microsoft_fy25_us_site_water.csv',dtype={'county_fips':str})
def nz(v): return None if (v is None or (isinstance(v,float) and math.isnan(v))) else float(v)
ents={}
for s,r in g25.iterrows():
    key=('Google',s)
    e=ents.setdefault(key,dict(op='Google',fips=r.county_fips.split('|'),rows=[]))
    p=g24.loc[s] if s in g24.index else None
    # county assignment must agree between years for paired sites
    if p is not None: assert p.county_fips==r.county_fips,s
    e['rows'].append([s,None if p is None else float(p.withdrawal_mgal),None if p is None else float(p.consumption_mgal),float(r.withdrawal_mgal),float(r.consumption_mgal),p is None,r.county_basis])
assert set(g24.index)<=set(g25.index)
for _,r in m.iterrows():
    key=('Microsoft',r.site)
    e=ents.setdefault(key,dict(op='Microsoft',fips=r.county_fips.split('|'),rows=[]))
    e['rows'].append([r.site,None,None,float(r.withdrawal_mgal),None,False,''])
out=[]
for e in ents.values():
    xy=[pos[f] for f in e['fips'] if f in pos]; assert xy,e
    S=float(sup.reindex(e['fips']).sum(min_count=1))
    R=e['rows']
    def yr(i,j,days):
        rr=[x for x in R if x[i] is not None]
        if not rr: return None
        wd=sum(x[i] for x in rr); cs=[x[j] for x in rr if x[j] is not None]
        return [round(wd,1),round(sum(cs),1) if len(cs)==len(rr) else None,round(100*wd/days/S,4)]
    v25=yr(3,4,365); v24=yr(1,2,366) if e['op']=='Google' else None
    V={'25':v25}
    if v24: V['24']=v24
    out.append([e['op'],'FY2025',[x[0] for x in R],e['fips'],round(sum(a for a,_ in xy)/len(xy),1),round(sum(b for _,b in xy)/len(xy),1),v25[0],v25[1],v25[2],round(S,1),len(e['fips'])>1,V,[x[:6] for x in R]])
json.dump(out,open('data/datacenters/disclosed_water_map.json','w'),separators=(',',':'))
print(len(out),'entities;',sum(1 for o in out if o[10]),'shared;',sum(1 for o in out if o[0]=='Google'),'Google;',sum(len(o[12]) for o in out if o[0]=='Google'),'Google site rows;',sum(1 for o in out for x in o[12] if x[5]),'first in 2025')
