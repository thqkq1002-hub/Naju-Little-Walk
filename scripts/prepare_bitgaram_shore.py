"""Polygon-exact visual lawn and low shore transitions; no new walking terrain.
Run with the bundled Python and Shapely 2.1.2 in work/python-geo (tool only).
"""
from pathlib import Path
import sys,json,hashlib,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/python-geo'))
import shapely
from shapely.geometry import Polygon,box,Point
from shapely.ops import unary_union
O=R/'outputs/quality-v75';O.mkdir(exist_ok=True)
out=O/'shore-surface-v75.json'
if out.exists():raise RuntimeError('Prepared revision preserved')
source=R/'knowledge/sources/bitgaram/geometry.json';ways=json.loads(source.read_text(encoding='utf8'))['ways']
park=Polygon(next(w['points'] for w in ways if w['id']=='508048299'))
assert park.is_valid,'Mapped park polygon invalid'
waters=[]
for w in ways:
 if w['tags'].get('natural')=='water':
  p=Polygon(w['points']);assert p.is_valid,w['id']
  if p.intersects(park):waters.append((w['id'],p))
water=unary_union([p for _,p in waters]);hill=box(-140,-140,140,140)
land=park.difference(water).difference(hill)
coast=unary_union([p for id,p in waters if id in ['334275809','534052766']])
# Two narrow land-side bands follow the exact mapped coast. Width/height are estimates.
edge=coast.buffer(.9,quad_segs=4).difference(water).intersection(land)
transition=coast.buffer(2.4,quad_segs=4).difference(coast.buffer(.9,quad_segs=4)).intersection(land)
core=land.difference(edge.union(transition))
vertices=[];faces=[];materials=[];lookup={};areas={}
for label,geom,mat in [('lawn',core,0),('grass_shore_transition',transition,0),('low_bank',edge,1)]:
 tris=list(shapely.constrained_delaunay_triangles(geom).geoms)
 assert abs(sum(t.area for t in tris)-geom.area)<1e-6,label
 areas[label]=geom.area
 for t in tris:
  assert land.covers(t) or land.buffer(1e-7).covers(t),label
  f=[]
  for x,z in list(t.exterior.coords)[:3]:
   d=coast.distance(Point(x,z))
   y=-.018+(d/.9)*.058 if d<=.9+1e-7 else .04-(min(2.4,d)-.9)/1.5*.115 if d<2.4 else -.075
   if label=='lawn':y=-.075
   key=(round(x,9),round(y,9),round(z,9))
   if key not in lookup:lookup[key]=len(vertices);vertices.append([x,y,z])
   f.append(lookup[key])
  faces.append(f);materials.append(mat)
assert abs(sum(areas.values())-land.area)<1e-6
report={'revision':'v75','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'park_osm_id':'508048299','water_osm_ids':[i for i,p in waters],'shore_osm_ids':['334275809','534052766'],'central_under_hill_exclusion':[-140,-140,140,140],'mapped_land_area':land.area,'areas':areas,'shore_width_estimate':2.4,'shore_height_estimate':[-.018,.04,-.075],'vertices':vertices,'faces':faces,'material_indices':materials,'tool':{'shapely':shapely.__version__,'geos':shapely.geos_version_string},'walkable_expansion':False,'note':'Exact stored OSM outline, estimated land-side narrow banks. Existing active hill and paths are unchanged.'}
out.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':')),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ['vertices','faces','material_indices']},ensure_ascii=False));print('MESH',len(vertices),len(faces),flush=True)
