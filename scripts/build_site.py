"""Build site pages from src/template.html and data/*.json.
Outputs: index.html (fetches ./data), dist/embed.html (fragment for Squarespace, fetches jsDelivr),
dist/inline.html (self-contained, no fetch). Run from the repo root: python3 scripts/build_site.py"""
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rd=lambda p: open(os.path.join(ROOT,p)).read()
t=rd('src/template.html')
HEAD_MARK="var GEO=__GEO__;\nvar DATA=__DATA__;\nvar SHAPES=__SHAPES__;\nvar STATES=__STATES__;\nvar HUC=__HUC__;\nvar DC=__DC__;"
assert HEAD_MARK in t
INLINE=HEAD_MARK.replace('__GEO__',rd('data/geo/geo_meta.json')).replace('__DATA__',rd('data/county_water_1985_2015.json')).replace('__SHAPES__',rd('data/geo/county_shapes.json')).replace('__STATES__',rd('data/geo/state_lines.json')).replace('__HUC__',rd('data/geo/huc8_outlines.json')).replace('__DC__',rd('data/datacenters/county_datacenter_map.json'))
FETCH="""var GEO,DATA,SHAPES,STATES,HUC,DC;
var BASE=(document.getElementById('wq-root').getAttribute('data-base')||'data/');
try{var R=await Promise.all(['geo/geo_meta.json','county_water_1985_2015.json','geo/county_shapes.json','geo/state_lines.json','geo/huc8_outlines.json','datacenters/county_datacenter_map.json'].map(function(u){return fetch(BASE+u).then(function(r){if(!r.ok)throw new Error(u+' '+r.status);return r.json()})}));
GEO=R[0];DATA=R[1];SHAPES=R[2];STATES=R[3];HUC=R[4];DC=R[5];}
catch(e){document.getElementById('wq-take').textContent='Could not load map data ('+e.message+').';return;}"""
def page(body,fetchmode,base=None):
    b=body.replace(HEAD_MARK,FETCH if fetchmode else INLINE)
    if fetchmode: b=b.replace('(function(){\n'+FETCH,'(async function(){\n'+FETCH)
    if base: b=b.replace('<div class="wq" id="wq-root">','<div class="wq" id="wq-root" data-base="%s">'%base)
    return b
doc=lambda inner,title: '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title>\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lora:wght@600&family=Public+Sans:wght@400;500;600&display=swap">\n<style>body{margin:0;background:#fff}</style></head><body>\n%s\n</body></html>'%(title,inner)
TITLE='County water use baseline, 1985 to 2015'
os.makedirs(os.path.join(ROOT,'dist'),exist_ok=True)
open(os.path.join(ROOT,'index.html'),'w').write(doc(page(t,True),TITLE))
open(os.path.join(ROOT,'dist/embed.html'),'w').write(page(t,True,'https://cdn.jsdelivr.net/gh/AsIAm04/datacenter-water-data@main/data/'))
open(os.path.join(ROOT,'dist/inline.html'),'w').write(doc(page(t,False),TITLE))
print('built')
