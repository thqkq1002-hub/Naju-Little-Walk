"""Refine the exact mapped lawn in the changed region; keep water/perimeter.
Shapely is an offline tool from work/python-geo, never a shipped dependency.
"""
from pathlib import Path
import sys,json,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/python-geo'));sys.path.insert(0,str(R/'scripts'))
import shapely
from shapely.geometry import Polygon,box,Point
from shapely.ops import unary_union
from bitgaram_terrain_v89 import Terrain
ways=json.loads((R/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf8'))['ways']
park=Polygon(next(w['points'] for w in ways if w['id']=='508048299'))
waters=[(w['id'],Polygon(w['points'])) for w in ways if w['tags'].get('natural')=='water']
water=unary_union([p for _,p in waters if p.intersects(park)])
coast=unary_union([p for i,p in waters if i in ('334275809','534052766')])
land=park.difference(water).difference(box(-140,-140,140,140))
edge=coast.buffer(.9,quad_segs=4).difference(water).intersection(land)
transition=coast.buffer(2.4,quad_segs=4).difference(coast.buffer(.9,quad_segs=4)).intersection(land)
core=land.difference(edge.union(transition));region=box(-300,-300,300,300)
old=json.loads((R/'outputs/terrain-v89/world-before.json').read_text(encoding='utf8'));T=Terrain(next(s['footprint'] for s in old['solids'] if s['name']=='photo_exhibition_shell'))
verts=[];faces=[];mats=[];lookup={};area=0
def triangulate(geom,label,mat):
 global area
 if geom.is_empty:return
 for t in shapely.constrained_delaunay_triangles(geom).geoms:
  coords=list(t.exterior.coords)[:3];area+=t.area;face=[]
  for x,z in coords:
   d=coast.distance(Point(x,z));offset=-.018+d/.9*.058 if d<=.9+1e-7 else .04-(min(2.4,d)-.9)/1.5*.115 if d<2.4 else -.075
   if label=='lawn':offset=-.075+.06*(1-T.smooth((max(abs(x),abs(z))-220)/80))
   y=T.ground(x,z)+offset;key=(round(x,8),round(z,8),round(y,8))
   if key not in lookup:lookup[key]=len(verts);verts.append((x,y,z))
   face.append(lookup[key])
  a,b,c=coords;cross=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
  faces.append([face[0],face[2],face[1]] if cross>0 else face);mats.append(mat)
for label,geom,mat in [('lawn',core,0),('transition',transition,0),('bank',edge,1)]:
 triangulate(geom.difference(region),label,mat)
 local=geom.intersection(region)
 for z in range(-300,300,4):
  for x in range(-300,300,4):
   if x>=-140 and x<140 and z>=-140 and z<140:continue
   tile=box(x,z,x+4,z+4)
   if local.intersects(tile):triangulate(local.intersection(tile),label,mat)
assert abs(area-land.area)<1e-5, (area,land.area)
out=R/'outputs/terrain-v89/dense-shore-ground.json'
out.write_text(json.dumps(dict(vertices=verts,faces=faces,material_indices=mats),separators=(',',':')),encoding='utf8')
report=dict(vertices=len(verts),triangles=len(faces),mappedLandAreaMetres2=land.area,triangulatedAreaMetres2=area,
 refinementRegion=[-300,-300,300,300],displayCellMetres=4,nativeSourceResolutionMetres=30,
 parkOutlinePreserved=True,waterHolesPreserved=True,centralExclusionPreserved=True,source='OSM stored park/water polygons plus recorded DSM')
(R/'knowledge/sources/bitgaram/terrain-v89/ground-refinement.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report),flush=True)
