"""Normalize the public OSM snapshot without claiming measured tree positions."""
import json,math,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1];folder=root/'knowledge/sources/arboretum'
xml=ET.parse(folder/'campus.osm').getroot();lat0,lon0=35.00648,126.8256689
nodes={n.get('id'):((float(n.get('lon'))-lon0)*111320*math.cos(math.radians(lat0)),-(float(n.get('lat'))-lat0)*111320) for n in xml.findall('node')}
ways=[dict(id=w.get('id'),tags={t.get('k'):t.get('v') for t in w.findall('tag')},points=[nodes[n.get('ref')] for n in w.findall('nd')]) for w in xml.findall('way')]
(folder/'geometry.json').write_text(json.dumps(dict(origin=[lat0,lon0],source='OpenStreetMap contributors, ODbL, 2026-09-16',ways=ways),ensure_ascii=False),encoding='utf-8')
im=Image.new('RGB',(1000,1000),'#e8ecdf');d=ImageDraw.Draw(im)
def xy(p):return (500+p[0],500+p[1])
for w in ways:
 p=[xy(p) for p in w['points']];t=w['tags']
 if w['id']=='1306096596':d.polygon(p,fill='#b4c793')
for w in ways:
 p=[xy(p) for p in w['points']];t=w['tags']
 if 'highway' in t or 'building' in t or t.get('natural')=='water':
  d.line(p,fill='#537589' if t.get('natural')=='water' else '#696458',width=3)
  x,y=p[len(p)//2]
  if 0<x<1000 and 0<y<1000:d.text((x,y),w['id'],fill='black')
im.save(root/'work/arboretum-osm-plan.png')
