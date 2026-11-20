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
rows=[]; allpx=[]
for reg in REG:
    g=parts[reg]
    for _,r in g.iterrows():
        px=to_px(r.geometry,reg)
        d=path(px,0.35)
        if d: rows.append({'id':r['GEOID'],'name':r['NAME'],'st':r['st'],'d':d})
        allpx.append((r['st'],px))
json.dump(rows,open('/home/claude/out/county_shapes.json','w'),separators=(',',':'))
import os; print('counties',len(rows),'MB',os.path.getsize('/home/claude/out/county_shapes.json')/1e6)
# state outlines: dissolve counties by state
sp=pd.DataFrame(allpx,columns=['st','geom'])
sl=[]
for st,grp in sp.groupby('st'):
    u=unary_union(list(grp.geom)); sl.append(path(u,0.5))
json.dump([{'id':'states','d':''.join(sl)}],open('/home/claude/out/state_lines.json','w'),separators=(',',':'))
print('state lines MB',os.path.getsize('/home/claude/out/state_lines.json')/1e6)
json.dump({'width':W,'height':round(H+10+135+22),'ly':round(H+10+135+14)},open('/home/claude/out/geo_meta.json','w'))
# HUC8
hj=json.load(open('/mnt/user-data/uploads/Claude/data-center-water/wbd_huc8_simplified.geojson'))
hrows=[]; skipped=0
for f in hj['features']:
    p=f['properties']; stt=(p['states'] or '')
    reg='ak' if stt.startswith('AK') else 'hi' if stt.startswith('HI') else 'pr' if stt.startswith('PR') or stt.startswith('VI') else 'conus'
    if reg=='pr' and 'VI' in stt: skipped+=1; continue
    geom=shape(f['geometry'])
    if reg=='hi': geom=clip_hi(geom) if isinstance(geom,MultiPolygon) else geom
    gg=gpd.GeoSeries([geom],crs=4326).to_crs(REG[reg]['crs']).iloc[0]
    px=to_px(gg,reg)
    # drop huge Canadian/ocean spill? keep as is
    d=path(px,0.5)
    if d: hrows.append({'huc8':p['huc8'],'name':p['name'],'states':stt,'areasqkm':p['areasqkm'],'d':d})
json.dump(hrows,open('/home/claude/out/huc8_shapes.json','w'),separators=(',',':'))
print('huc8',len(hrows),'skipped',skipped,'MB',os.path.getsize('/home/claude/out/huc8_shapes.json')/1e6)
