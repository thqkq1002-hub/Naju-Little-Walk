"""Keep geographic footprints from public OSM; never treat estimates as surveyed heights."""
import json, math, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'knowledge/sources/bitgaram'
nodes={};ways={}
for path in SRC.glob('*.osm'):
    root=ET.parse(path).getroot()
    for n in root.findall('node'):nodes[n.attrib['id']]=(float(n.attrib['lon']),float(n.attrib['lat']))
    for w in root.findall('way'):ways[w.attrib['id']]=w
origin=(126.790447,35.016925)
def xy(p):return [round((p[0]-origin[0])*111320*math.cos(math.radians(origin[1])),3),round((origin[1]-p[1])*111320,3)]
records=[]
for wid,w in ways.items():
    tags={t.attrib['k']:t.attrib['v'] for t in w.findall('tag')}
    pts=[nodes.get(n.attrib['ref']) for n in w.findall('nd')]
    if None in pts or len(pts)<2:continue
    records.append(dict(id=wid,tags=tags,points=[xy(p) for p in pts],coordinates=pts))
data=dict(origin=dict(lon=origin[0],lat=origin[1]),source='© OpenStreetMap contributors, ODbL 1.0',retrieved='2026-09-15',ways=records)
(SRC/'geometry.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
for r in records:
    if any(t in r['tags'].get('name','') for t in ['전망대','전시관리','한국전력']):print(r['id'],r['tags'],len(r['points']))
print('ways',len(records))
