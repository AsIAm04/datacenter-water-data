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

import io
AQ='/home/claude/aq/us_aquifers.shp'
OUT='/home/claude/datacenter-water-data/data/'
g=gpd.read_file(AQ).to_crs(4326); g=g[g.AQ_CODE!=999].copy()
print('aquifer polygons',len(g),'| named aquifers',g.AQ_NAME.nunique())
# explode, assign region by representative point
g=g.explode(index_parts=False)
def reg_of(p):
    x,y=p.x,p.y
    if x<-150 and y<25: return 'hi'
    if -68.5<x<-64 and 17<y<19.5: return 'pr'
    if y>50 and x<-125: return None
    return 'conus'
g['reg']=[reg_of(p.representative_point()) for p in g.geometry]
g=g[g.reg.notna()].copy()
paths=[]
from shapely.ops import unary_union
for reg in ['conus','hi','pr']:
    gg=g[g.reg==reg]
    if reg=='hi': gg=gg.assign(geometry=[clip_hi(x) for x in gg.geometry])
    gg=gg.to_crs(REG[reg]['crs'])
    for code,grp in gg.groupby('AQ_CODE'):          # dissolve each aquifer so only its outer edge is drawn
        u=unary_union(list(grp.geometry.buffer(0)))
        px=to_px(u,reg)
        parts=[px] if isinstance(px,Polygon) else list(px.geoms)
        parts=[q for q in parts if q.area>=30]        # drop slivers smaller than 30 square px (map is 975 px wide)
        if not parts: continue
        d=path(MultiPolygon(parts) if len(parts)>1 else parts[0],0.8)
        if d: paths.append(d)
d=''.join(paths); open(OUT+'geo/aquifer_outlines.json','w').write(json.dumps(d))
import os; print('outline path MB',round(os.path.getsize(OUT+'geo/aquifer_outlines.json')/1e6,2))
# county by aquifer withdrawals (2015)
raw=open('/mnt/user-data/uploads/Claude/data-center-water/groundwater_2015/uscopa2015v1.0.csv',encoding='cp1252').read()
i=raw.index('State,State_FIPS'); a=pd.read_csv(io.StringIO(raw[i:]),dtype=str)
num=lambda s: pd.to_numeric(s.replace('--',None),errors='coerce')
a['fips']=a['CountyAquifer'].str[:2]+a['CountyAquifer'].str[3:6]
a['aq']=a['CountyAquifer Name'].str.split('-',n=2).str[2]
for c in ['TO-WGWFr','PS-WGWFr','IT-WGWFr','IN-WGWFr','DO-WGWFr','PT-WGWFr']: a[c]=pd.to_numeric(a[c].replace('--',None),errors='coerce')
a=a.rename(columns={'TO-WGWFr':'total','PS-WGWFr':'ps','IT-WGWFr':'irr','IN-WGWFr':'ind','DO-WGWFr':'dom','PT-WGWFr':'th'})
a[['fips','aq','total','ps','dom','irr','ind','th']].round(2).to_csv(OUT+'aquifer_county_gw_2015.csv',index=False)
D={}
for f,gp in a.groupby('fips'):
    gp=gp.sort_values('total',ascending=False)
    D[f]=[[r.aq,None if pd.isna(r.total) else round(r.total,2),None if pd.isna(r.ps) else round(r.ps,2),None if pd.isna(r.irr) else round(r.irr,2)] for r in gp.itertuples()]
json.dump(D,open(OUT+'aquifer_county_map.json','w'),separators=(',',':'))
print('counties',len(D),'rows',len(a),'| US fresh GW total',round(a.total.sum()),'| names ex',a.aq.dropna().unique()[:6].tolist())
meta=json.load(open(OUT+'county_water_1985_2015.json'))['meta']
print('counties in aquifer file not on map:',[f for f in D if f not in set(s['id'] for s in json.load(open(OUT+'geo/county_shapes.json')))][:10])
