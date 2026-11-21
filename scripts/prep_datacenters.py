import geopandas as gpd, pandas as pd, numpy as np, json, shapely
from shapely.geometry import shape, mapping, Polygon, MultiPolygon, LineString, MultiLineString
from shapely.ops import unary_union, transform as sh_transform
from shapely import affinity
import pyproj, warnings; warnings.filterwarnings('ignore')
cty=gpd.read_file('zip:///mnt/user-data/uploads/Claude/data-center-water/census/cb_2015_us_county_500k.zip')
print(cty.shape, list(cty.columns)[:10]); cty['GEOID']=cty['GEOID'].astype(str)
cty['st']=cty['STATEFP']
REG={'conus':dict(crs='EPSG:5070'),'ak':dict(crs='EPSG:3338'),'hi':dict(crs='ESRI:102007'),'pr':dict(crs='EPSG:32161')}
def region_of_state(st):
    return 'ak' if st=='02' else 'hi' if st=='15' else 'pr' if st=='72' else None if st in ('60','66','69','78') else 'conus'
cty['reg']=cty['st'].map(region_of_state); cty=cty[cty.reg.notna()].copy()
def clip_hi(g):
    if isinstance(g,MultiPolygon):
        keep=[p for p in g.geoms if p.representative_point().x>-161]
        return MultiPolygon(keep) if keep else g
    return g
cty['geometry']=[clip_hi(g) if st=='15' else g for g,st in zip(cty.geometry,cty.st)]
cty=cty.set_crs(4326,allow_override=True) if cty.crs is None else cty
W=975
def proj_region(gdf,reg):
    return gdf.to_crs(REG[reg]['crs'])
parts={}
for reg in REG:
    g=cty[cty.reg==reg]; parts[reg]=proj_region(g,reg)
cb=parts['conus'].total_bounds  # minx,miny,maxx,maxy
k=(W-20)/(cb[2]-cb[0])
H=(cb[3]-cb[1])*k+20
print('conus scale',k,'height',H)
# placement of insets: (scale multiplier, target lower-left corner in px)
PLACE={'conus':(1.0,None),'ak':(0.33,(20,H+10)),'hi':(1.0,(215,H+10)),'pr':(1.3,(345,H+10))}
def tf_factory(reg,bounds):
    mult,ll=PLACE[reg]; kk=k*mult
    if reg=='conus':
        ox,oy=10-bounds[0]*kk, 10+bounds[3]*kk
    else:
        ox,oy=ll[0]-bounds[0]*kk, ll[1]+0 + bounds[3]*kk - (bounds[3]-bounds[1])*kk  # top aligned at ll y
    return kk,ox,oy
TF={}
for reg in REG:
    b=parts[reg].total_bounds; TF[reg]=(tf_factory(reg,b))
def to_px(geom,reg):
    kk,ox,oy=TF[reg]
    return shapely.transform(geom,lambda a: np.column_stack((a[:,0]*kk+ox, oy-a[:,1]*kk)))
def path(geom,tol):
    g=geom.simplify(tol,preserve_topology=True)
    out=[]
    polys=[g] if isinstance(g,Polygon) else list(g.geoms) if isinstance(g,MultiPolygon) else [p for p in getattr(g,'geoms',[]) if isinstance(p,Polygon)]
    for p in polys:
        for ring in [p.exterior]+list(p.interiors):
            c=list(ring.coords)
            if len(c)<4: continue
            out.append('M'+'L'.join(f'{x:.1f},{y:.1f}' for x,y in c[:-1])+'Z')
    return ''.join(out)

import json
ATL='/home/claude/datacenter-water-data/data/datacenters/im3_open_source_data_center_atlas_v2026.11.02.csv'
a=pd.read_csv(ATL,dtype={'state_id':str,'county_id':str})
a['sqft']=pd.to_numeric(a.sqft)
pts=gpd.GeoDataFrame(a,geometry=gpd.points_from_xy(a.lon,a.lat),crs=4326)
c4=cty.to_crs(4326)[['GEOID','geometry']]
j=gpd.sjoin(pts,c4,how='left',predicate='within')
miss=j.GEOID.isna()
if miss.any():  # coastal/edge points: nearest county
    nn=gpd.sjoin_nearest(pts[miss].to_crs(5070),c4.to_crs(5070),how='left')
    j.loc[miss,'GEOID']=nn.GEOID.values
j['atlas_fips']=j.state_id.str.zfill(2)+j.county_id.str.zfill(3)
valid=set(cty.GEOID)
j['fips']=j.atlas_fips.where(j.atlas_fips.isin(valid)&(j.state_id.str.zfill(2)!='09'),j.GEOID)
print('rows',len(j),'| used atlas county:',int((j.fips==j.atlas_fips).sum()),'| CT/other remapped spatially:',int((j.fips!=j.atlas_fips).sum()),j[j.fips!=j.atlas_fips][['atlas_fips','fips']].drop_duplicates().values.tolist())
print('atlas vs spatial disagree (kept atlas):',int(((j.atlas_fips!=j.GEOID)&(j.fips==j.atlas_fips)).sum()))
# straddlers: same id in >1 county -> split polygon sqft equally (approximation, flagged)
n=j.groupby('id').fips.transform('nunique'); j['straddle']=n>1
dup=j.groupby('id').id.transform('size'); j['sqft_adj']=j.sqft/dup.where(j.straddle,1)
print('straddling rows',int(j.straddle.sum()))
def agg(g):
    b=g[g['type']=='building']; c=g[g['type']=='campus']; p=g[g['type']=='point']
    # symbol size uses building footprint only; campus polygons are land parcels (not comparable) and are kept in sqft_campus
    if len(b): sq,basis=b.sqft_adj.sum(),'building'
    elif len(c): sq,basis=None,'campus_only'
    else: sq,basis=None,'point_only'
    return pd.Series(dict(n_building=len(b),n_campus=len(c),n_point=len(p),sqft_building=b.sqft_adj.sum() if len(b) else None,sqft_campus=c.sqft_adj.sum() if len(c) else None,footprint_sqft=sq,footprint_basis=basis,n_straddle_rows=int(g.straddle.sum())))
s=j.groupby('fips').apply(agg).reset_index()
# symbol position = representative point of the county in map px
pos={}
for reg in REG:
    for _,r in parts[reg].iterrows():
        px=to_px(r.geometry,reg); rp=px.representative_point(); pos[r['GEOID']]=(round(rp.x,1),round(rp.y,1))
s['x']=s.fips.map(lambda f:pos.get(f,(None,None))[0]); s['y']=s.fips.map(lambda f:pos.get(f,(None,None))[1])
print('counties',len(s),'no position',int(s.x.isna().sum()))
print('total building sqft (M)',round(s.sqft_building.sum()/1e6,1),'| counties with building',int((s.n_building>0).sum()),'campus-only',int((s.footprint_basis=='campus_only').sum()),'point-only',int((s.footprint_basis=='point_only').sum()))
print(s.sort_values('footprint_sqft',ascending=False).head(8)[['fips','n_building','n_campus','footprint_sqft']])
out='/home/claude/datacenter-water-data/data/datacenters/county_datacenter_summary.csv'
s.round(1).to_csv(out,index=False)
dc={r.fips:[int(r.n_building),int(r.n_campus),int(r.n_point),None if pd.isna(r.footprint_sqft) else round(r.footprint_sqft),r.footprint_basis,r.x,r.y,int(r.n_straddle_rows)] for r in s.itertuples() if pd.notna(r.x)}
json.dump(dc,open('/home/claude/datacenter-water-data/data/datacenters/county_datacenter_map.json','w'),separators=(',',':'))

json.dump({k:list(v) for k,v in pos.items()},open('/home/claude/datacenter-water-data/data/geo/county_positions.json','w'),separators=(',',':'))
print('positions',len(pos))
