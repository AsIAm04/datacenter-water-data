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
from scipy.stats import spearmanr
OUT='/home/claude/datacenter-water-data/data/'
H8=gpd.read_file('/mnt/user-data/uploads/Claude/data-center-water/wbd_huc8_simplified.geojson')[['huc8','name','geometry']]
H8['huc8']=H8.huc8.astype(str).str.zfill(8)
if H8.crs is None: H8=H8.set_crs(4326)
H8=H8.to_crs(REG['conus']['crs']); cen=H8.geometry.representative_point()
px=to_px(shapely.points(np.column_stack([cen.x.values,cen.y.values])),'conus')
H8['x']=[round(p.x,1) for p in px]; H8['y']=[round(p.y,1) for p in px]
H8=H8.set_index('huc8')
# Siddik 2018 modeled data-center water footprint, m3/yr, six geographic attribution methods
S=pd.read_csv(OUT+'siddik_2021_huc8_attributes.csv',dtype={'HUC_8':str}); S['huc8']=S.HUC_8.str.zfill(8)
meth=['WF_PCA','WF_PCA_NT','WF_HUC4','WF_Interco','WF_eGRID','WF_State']
M3=3785.411784
S['wf']=S.WF_PCA/M3*1.0/1000.0   # m3 -> Mgal: 1 Mgal = 3785.411784 m3, so Mgal = m3/3785.41; stored in Mgal/yr
S['wf']=S.WF_PCA/M3
S['lo']=S[meth].min(axis=1)/M3; S['hi']=S[meth].max(axis=1)/M3
S=S.set_index('huc8')
# USGS Data Companion modeled withdrawals, annual mean Mgal/d (HUC12 summed to HUC8)
U=pd.read_csv('/home/claude/datacenter-water-data/data/supply/nwdc_wu_huc8_annual_mgd_2000_2020.csv',dtype={'huc8':str})
Up=U.pivot_table(index='huc8',columns=['sector','year'],values='mgd',aggfunc='sum')
def g(h,s,y):
    try: v=Up.loc[h,(s,y)]; return None if pd.isna(v) else round(float(v),3)
    except KeyError: return None
hs=sorted(set(S.index)&set(H8.index))
hm={}
for h in hs:
    r=S.loc[h]
    wf=float(r.wf); lo=float(r.lo); hi=float(r.hi)
    row=[H8.loc[h,'name'] or h, round(wf,3), round(lo,3), round(hi,3),
         g(h,'ps_wd',2015),g(h,'ps_wd',2020),g(h,'ir_wd',2015),g(h,'ir_wd',2020),g(h,'te_wd',2015),g(h,'te_wd',2020),
         H8.loc[h,'x'],H8.loc[h,'y']]
    hm[h]=row
print('HUC8 in map',len(hm),'with WF>0',sum(1 for v in hm.values() if v[1]>0),'in Siddik not in WBD',len(set(S.index)-set(H8.index)))
# county -> overlapping HUC8 (largest overlap first, drop slivers under 2% of the HUC8)
W=pd.read_csv(OUT+'supply/huc8_county_weights.csv',dtype={'huc8':str,'fips':str}); W['huc8']=W.huc8.str.zfill(8)
W=W[W.huc8.isin(hm)&(W.weight>=0.02)].sort_values(['fips','overlap_m2'],ascending=[True,False])
cm={f:list(gr.huc8.head(4)) for f,gr in W.groupby('fips')}
cm_n={f:int(len(gr)) for f,gr in W.groupby('fips')}
cm={f:[l,cm_n[f]] for f,l in cm.items()}
json.dump({'h':hm,'c':cm},open(OUT+'huc8_modeled_map.json','w'),separators=(',',':'))
import os; print('map json KB',round(os.path.getsize(OUT+'huc8_modeled_map.json')/1024),'counties',len(cm))
# ---- USGS 2020 reconciliation test: modeled (Data Companion, CONUS) vs compiled county data (all states) ----
D=json.load(open(OUT+'county_water_1985_2015.json')); cols=D['cols']; yrs=D['years']
def comp(s,y,fips=None):
    yi=yrs.index(y); t={}
    for f,v in D['data'].items():
        r=v[yi]
        if r is None: continue
        t[f]=sum((x or 0) for c,x in zip(cols,r) if c.startswith(s+'_'))
    return t
rows=[]
for s,ms,lab in [('ps','ps_wd','public supply'),('irr','ir_wd','irrigation'),('th','te_wd','thermoelectric (fresh)')]:
    for y in [2000,2005,2010,2015]:
        ct=sum(comp(s,y).values()); mm=U[(U.sector==ms)&(U.year==y)].mgd.sum() if not U[(U.sector==ms)&(U.year==y)].empty else np.nan
        rows.append(dict(sector=lab,year=y,compiled_mgd=round(ct),modeled_mgd=None if np.isnan(mm) else round(mm),ratio=None if np.isnan(mm) else round(mm/ct,2)))
    m20=U[(U.sector==ms)&(U.year==2020)].mgd.sum(); rows.append(dict(sector=lab,year=2020,compiled_mgd=None,modeled_mgd=round(m20),ratio=None))
# county-level: allocate modeled HUC8 volume to counties by area weight (crude), compare to compiled 2015
Wf=pd.read_csv(OUT+'supply/huc8_county_weights.csv',dtype={'huc8':str,'fips':str}); Wf['huc8']=Wf.huc8.str.zfill(8)
stats=[]
for s,ms,lab in [('ps','ps_wd','public supply'),('irr','ir_wd','irrigation'),('th','te_wd','thermoelectric (fresh)')]:
    for y in [2010,2015]:
        m=U[(U.sector==ms)&(U.year==y)].set_index('huc8').mgd
        a=Wf.assign(v=Wf.huc8.map(m).fillna(0)*Wf.weight).groupby('fips').v.sum()
        c=pd.Series(comp(s,y)); j=pd.concat([c.rename('c'),a.rename('m')],axis=1).dropna(); j=j[(j.c>=1)|(j.m>=1)]
        rho=spearmanr(j.c,j.m).correlation; both=j[(j.c>=1)&(j.m>=1)]; rr=(both.m/both.c)
        stats.append(dict(sector=lab,year=y,counties=len(j),spearman=round(float(rho),2),median_ratio=round(float(rr.median()),2),within_factor_2=round(float(((rr>=.5)&(rr<=2)).mean()),2)))
R=pd.DataFrame(rows); R.to_csv(OUT+'usgs_2020_reconciliation_national.csv',index=False)
St=pd.DataFrame(stats); St.to_csv(OUT+'usgs_2020_reconciliation_county.csv',index=False)
print(R.to_string(index=False)); print(St.to_string(index=False))
