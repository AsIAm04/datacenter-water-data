"""Nine data center concentrations: HUC8 subbasins flagged case=True in data/concentrations/pool_usdm.csv (the study's case set; the flag is the only
definition in the files, so the list is one place to change). Geometry from the same simplified WBD HUC8 shapes used for the outlines layer.
Site counts are pool.csv 'sites' (each atlas site assigned to one subbasin). Aqueduct category is WRI Aqueduct 4.0 baseline category joined by location
(HydroBASINS level 6, a larger unit than HUC8). Drought Monitor columns are NOT used: their definitions are not documented in the files."""
import pandas as pd, json
pool=pd.read_csv('data/concentrations/pool.csv',dtype={'huc8':str})
aq=pd.read_csv('data/concentrations/pool_aqueduct.csv',dtype={'huc8':str}).set_index('huc8')
us=pd.read_csv('data/concentrations/pool_usdm.csv',dtype={'huc8':str}).set_index('huc8')
keep=[h for h in pool.huc8 if str(us.loc[h,'case'])=='True']; assert len(keep)==9,keep
shapes={r['huc8']:r['d'] for r in json.load(open('/home/claude/out/huc8_shapes.json'))}
out=[]
for _,r in pool[pool.huc8.isin(keep)].sort_values('sites',ascending=False).iterrows():
    out.append(dict(huc8=r.huc8,name=r['name'],sites=int(r.sites),states=r.states.replace('|',', '),counties=int(r.counties),fp_msqft=float(r.fp_msqft),runoff_mgd=float(r.runoff_mgd),aq=aq.loc[r.huc8,'bws_label'],d=shapes[r.huc8]))
json.dump(out,open('data/concentrations_map.json','w'),separators=(',',':'))
print([(o['name'],o['sites'],o['aq']) for o in out])
