"""True-north angle per county for the map's north arrow.
The map uses one projection per region (same as prep_geometry.py): CONUS EPSG:5070,
Alaska EPSG:3338, Hawaii ESRI:102007, Puerto Rico EPSG:32161. Insets are translated and
scaled but not rotated, so screen-up is grid north in that region's projection.
Angle = degrees clockwise from screen-up to true north, at the county's representative point.
Output: data/geo/county_north.json {fips: angle}, plus map-center value for CONUS (lon -96 => 0).
"""
import geopandas as gpd, pyproj, math, json, sys, warnings
warnings.filterwarnings('ignore')
src=sys.argv[1] if len(sys.argv)>1 else 'zip:///mnt/user-data/uploads/Claude/data-center-water/census/cb_2015_us_county_500k.zip'
cty=gpd.read_file(src); cty['GEOID']=cty['GEOID'].astype(str)
REG={'conus':'EPSG:5070','ak':'EPSG:3338','hi':'ESRI:102007','pr':'EPSG:32161'}
def reg(st): return 'ak' if st=='02' else 'hi' if st=='15' else 'pr' if st=='72' else None if st in ('60','66','69','78') else 'conus'
T={r:pyproj.Transformer.from_crs(4326,c,always_xy=True) for r,c in REG.items()}
out={}
for _,r in cty.iterrows():
    rg=reg(r['STATEFP'])
    if rg is None: continue
    p=r.geometry.representative_point(); lon,lat=p.x,p.y
    if r['STATEFP']=='02' and lon>0: lon-=360  # Aleutians east of 180
    x0,y0=T[rg].transform(lon,lat); x1,y1=T[rg].transform(lon,lat+0.01)
    out[r['GEOID']]=round(math.degrees(math.atan2(x1-x0,y1-y0)),1)
json.dump(out,open('data/geo/county_north.json','w'),separators=(',',':'))
vs=sorted(out.values()); print(len(out),'counties; min',vs[0],'max',vs[-1])
for f in ('39045','39049','51107','06037','02020','15003','72127','53033'):
    print(f,out.get(f))
