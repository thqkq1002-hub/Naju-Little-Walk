"""Add mapped river polygons to the expanded regional selector, retaining existing data."""
from pathlib import Path
import json,math,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/python-geo'))
from shapely.geometry import Polygon
p=R/'public/naju-region-map.json';w=json.loads(p.read_text(encoding='utf8'));g=json.loads((R/'knowledge/sources/neureoji-v92/geography.json').read_text(encoding='utf8'))
mx=g['metresPerLongitudeDegree'];lat=g['originWGS84']['lat'];lon=g['originWGS84']['lon']
w['paths']=[x for x in w['paths'] if not str(x['id']).startswith('-92')]
for i,river in enumerate(g['water']):
    poly=Polygon(river['points'],river['holes']).simplify(12,preserve_topology=True)
    w['paths'].append(dict(id=-92000-i,kind='water',name='영산강 느러지 굽이',points=[[lon+x/mx,lat-z/111320] for x,z in poly.exterior.coords]))
w['neureojiSource']='OpenStreetMap contributors, ODbL 1.0; geometry from node 6572786690 surroundings, knowledge/sources/neureoji-v92/geography.json'
p.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
print('Expanded selector retains existing roads and adds',len(g['water']),'river polygons')
