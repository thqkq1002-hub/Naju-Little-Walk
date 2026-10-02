"""Refine a copy of the authored park using the mapped Baemesan woodland boundary."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
root=Path(__file__).resolve().parents[1];out=root/'outputs/bitgaram/bitgaram-park-landscape.blend'
if out.exists() and '--replace-generated' not in sys.argv:raise RuntimeError('Existing landscape edit preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-park-detail.blend'))
data=json.loads((root/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))
wood=next(w['points'] for w in data['ways'] if w['id']=='508048953')
def inside(x,z):
    yes=False
    for a,b in zip(wood,wood[1:]+wood[:1]):
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:yes=not yes
    return yes
def distance(x,z):
    result=1e9
    for a,b in zip(wood,wood[1:]+wood[:1]):
        dx,dz=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz or 1)))
        result=min(result,math.hypot(x-a[0]-dx*t,z-a[1]-dz*t))
    return result
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
colors=[[linear(int(c[i:i+2],16)/255) for i in [0,2,4]] for c in ['b4bea4','6f8654']]
hill=bpy.data.objects['estimated_hill'];mesh=hill.data
attr=mesh.color_attributes.new(name='Mapped_woodland',type='FLOAT_COLOR',domain='POINT')
for v in mesh.vertices:
    x,z=v.co.x,-v.co.y
    weight=max(0,min(1,.5+(1 if inside(x,z) else -1)*distance(x,z)/20))
    attr.data[v.index].color=(*[colors[0][i]*(1-weight)+colors[1][i]*weight for i in range(3)],1)
material=hill.data.materials[0].copy();material.name='OSM_Woodland_Transition'
node=material.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name=attr.name
material.node_tree.links.new(node.outputs['Color'],material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
hill.data.materials.clear();hill.data.materials.append(material)
g=MuseumGeometry(bpy.context.scene,(0,0),0)
def height(x,z):return min(16*math.exp(-((x/100)**2+(z/105)**2)*1.6),15.75)+.02 if abs(x)<=150 and abs(z)<=150 else -.1
count=0
for w in data['ways']:
    pts=w['points'];tags=w['tags']
    if tags.get('highway') in ['footway','path','steps']:
        for a,b in zip(pts,pts[1:]):
            if max(math.hypot(*a),math.hypot(*b))>280 or math.dist(a,b)>80:continue
            # Preserve the active deck route and summit floor; mapped paths outside it are visual context.
            if min(math.hypot(*a),math.hypot(*b))<28:continue
            n=max(1,math.ceil(math.dist(a,b)/2))
            for i in range(n):
                u=[a[q]+(b[q]-a[q])*i/n for q in [0,1]];v=[a[q]+(b[q]-a[q])*(i+1)/n for q in [0,1]]
                length=math.dist(u,v)
                if length<.001:continue
                ox,oz=-(v[1]-u[1])*.7/length,(v[0]-u[0])*.7/length
                verts=[(p[0]+ox*side,height(p[0]+ox*side,p[1]+oz*side)+.05,p[1]+oz*side) for p,side in [(u,-1),(v,-1),(v,1),(u,1)]]
                g.mesh('mapped_context_path',verts,[(0,1,2,3)],'#cbbfa4');count+=1
    if tags.get('natural')=='water':
        for a,b in zip(pts,pts[1:]):
            if max(math.hypot(*a),math.hypot(*b))<370:g.segment('mapped_lake_bank',a,b,.8,.16,'#a6b59b',base=.05,record=False)
# Distant water/ground must not self-shadow within the small local shadow volume.
for o in bpy.data.objects:
    if o.type=='MESH' and (o.name.startswith('lake_osm_') or o.name=='context_ground'):
        if hasattr(o,'visible_shadow'):o.visible_shadow=False
bpy.ops.wm.save_as_mainfile(filepath=str(out))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-park.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
print('Mapped path segments',count,flush=True)
