"""Dasi Elementary School: mapped footprints + photo-referenced exterior.

Blender --background --python scripts/build_dasi_school.py -- --render
The existing Geumseonggwan scene is never opened or overwritten.
"""
import bpy
import json
import math
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
NEIGHBORHOOD = '--neighborhood' in sys.argv
OUTPUT = ROOT / 'outputs' / ('dasi-neighborhood.blend' if NEIGHBORHOOD else 'dasi-elementary-detailed.blend')
WORLD_NAME = 'dasi-neighborhood' if NEIGHBORHOOD else 'dasi'
MODEL_NAME = 'dasi-neighborhood' if NEIGHBORHOOD else 'dasi-elementary'
if OUTPUT.exists() and '--replace' not in sys.argv:
    raise RuntimeError('Output exists. Save your edits separately before using -- --replace.')
OUTPUT.parent.mkdir(exist_ok=True)
(ROOT / 'public' / 'models').mkdir(exist_ok=True)
scene = bpy.data.scenes.new('Naju_Dasi_Elementary')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
groups = {}
for name in ('01_Mapped_Ground', '02_Photo_Exterior', '03_Estimated_Details', '04_Presentation', '05_Illustrative_Interior', '06_Neighborhood_Mapped', '07_Neighborhood_Image_Trace', '08_Railway'):
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    groups[name] = collection
LAT, LON = 35.017517, 126.6400205
bounds = [-285, 285, -245, 195] if NEIGHBORHOOD else [-120, 125, -100, 82]
SOURCE_URL = 'https://api.openstreetmap.org/api/0.6/map?bbox=' + ('126.6369,35.0157,126.6432,35.0196' if NEIGHBORHOOD else '126.63865,35.0167,126.6415,35.0186')
def project(lon, lat):
    return [(float(lon)-LON)*111320*math.cos(math.radians(LAT)), -(float(lat)-LAT)*111320]
def bp(x, y, z):
    return (x, -z, y)
xml = ET.parse(ROOT / 'knowledge/sources' / ('dasi-neighborhood.osm' if NEIGHBORHOOD else 'dasi-school.osm')).getroot()
nodes = {n.attrib['id']: project(n.attrib['lon'], n.attrib['lat']) for n in xml.findall('node')}
ways = {}
for w in xml.findall('way'):
    ways[w.attrib['id']] = dict(tags={t.attrib['k']:t.attrib['v'] for t in w.findall('tag')}, points=[nodes[n.attrib['ref']] for n in w.findall('nd') if n.attrib['ref'] in nodes])
solids, signs, places, buildings = [], [], [], []
materials = {}
def mat(color):
    if color not in materials:
        rgb = [int(color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
        rgb = [c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
        m = bpy.data.materials.new('material_'+color.lstrip('#'))
        m.diffuse_color = (*rgb, 1)
        m.use_nodes = True
        bsdf = m.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Base Color'].default_value = (*rgb,1)
        bsdf.inputs['Roughness'].default_value = .78
        materials[color] = m
    return materials[color]

def mesh_object(name, verts, faces, color, group='03_Estimated_Details'):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    uv = mesh.uv_layers.new(name='FacadeUV')
    for face in mesh.polygons:
        normal = face.normal
        tangent = Vector((-normal.y,normal.x,0)).normalized() if abs(normal.z)<.8 else Vector((1,0,0))
        for li in face.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = (v.dot(tangent)/1.2, (v.z if abs(normal.z)<.8 else v.y)/.56)
    obj = bpy.data.objects.new(name,mesh)
    groups[group].objects.link(obj)
    mesh.materials.append(mat(color))
    obj['provenance'] = group
    return obj

def box(name,x,y,z,w,h,d,color,collision=False,rotation=0,group='03_Estimated_Details'):
    vertices = [(-w/2,-d/2,-h/2),(w/2,-d/2,-h/2),(w/2,d/2,-h/2),(-w/2,d/2,-h/2),(-w/2,-d/2,h/2),(w/2,-d/2,h/2),(w/2,d/2,h/2),(-w/2,d/2,h/2)]
    o = mesh_object(name,vertices,[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],color,group)
    o.location = bp(x,y,z)
    o.rotation_euler.z = rotation
    o['collision'] = collision
    solids.append(dict(name=name,kind='box',position=[x,y,z],size=[w,h,d],color=color,collision=collision,rotation=rotation))
    return o

def polygon(name,pts,height,color,collision=False,base=0,group='01_Mapped_Ground'):
    pts = pts[:-1] if pts[0]==pts[-1] else pts
    # Enforce counterclockwise winding in Blender XY for outward normals.
    signed_area = sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1]))
    if signed_area > 0: pts = list(reversed(pts))
    n = len(pts)
    vertices = [bp(x,base,z) for x,z in pts]+[bp(x,base+height,z) for x,z in pts]
    faces = [tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o = mesh_object(name,vertices,faces,color,group)
    o['collision'] = collision
    solids.append(dict(name=name,kind='building',position=[0,base,0],size=[1,height,1],footprint=pts,color=color,collision=collision))
    return o

def segment(name,a,b,width,height,color,collision=False,base=0,group='03_Estimated_Details'):
    dx,dz = b[0]-a[0],b[1]-a[1]
    return box(name,(a[0]+b[0])/2,base+height/2,(a[1]+b[1])/2,math.hypot(dx,dz),height,width,color,collision,math.atan2(-dz,dx),group)

def clip(a,b):
    dx,dz=b[0]-a[0],b[1]-a[1]
    lo,hi=0.,1.
    for p,q in [(-dx,a[0]-bounds[0]),(dx,bounds[1]-a[0]),(-dz,a[1]-bounds[2]),(dz,bounds[3]-a[1])]:
        if abs(p)<1e-9:
            if q<0:return None
        elif p<0:lo=max(lo,q/p)
        else:hi=min(hi,q/p)
    return None if lo>hi else ([a[0]+lo*dx,a[1]+lo*dz],[a[0]+hi*dx,a[1]+hi*dz])

def cylinder(name,x,y,z,radius,height,color,vertices=12,group='03_Estimated_Details'):
    verts=[bp(x+radius*math.cos(i*2*math.pi/vertices),level,z+radius*math.sin(i*2*math.pi/vertices)) for level in (y-height/2,y+height/2) for i in range(vertices)]
    faces=[tuple(range(vertices)),tuple(reversed(range(vertices,vertices*2)))]+[(i,i+vertices,(i+1)%vertices+vertices,(i+1)%vertices) for i in range(vertices)]
    return mesh_object(name,verts,faces,color,group)

font_path=Path('C:/Windows/Fonts/malgunbd.ttf')
font=bpy.data.fonts.load(str(font_path)) if font_path.exists() else None
def label(text,x,y,z,width=8,rotation=0,color='#234150',height=1.05):
    curve=bpy.data.curves.new('text_'+text,'FONT')
    curve.body=text; curve.align_x='CENTER'; curve.align_y='CENTER'; curve.size=1; curve.extrude=.008
    if font:curve.font=font
    o=bpy.data.objects.new('label_'+text,curve)
    groups['04_Presentation'].objects.link(o)
    o.location=bp(x,y,z); o.rotation_euler=(math.pi/2,0,rotation)
    o.data.materials.append(mat(color))
    bpy.context.view_layer.update()
    # Measure in the font's local plane. World X collapses for side-facing signs.
    local_width=max(p[0] for p in o.bound_box)-min(p[0] for p in o.bound_box)
    local_height=max(p[1] for p in o.bound_box)-min(p[1] for p in o.bound_box)
    scale=min(width/max(local_width,.01),height/max(local_height,.01))
    o.scale=(scale,scale,scale)
    o['label_text']=text
    signs.append(dict(text=text,position=[x,y,z],width=width,height=height,rotation=rotation,color=color))
    return o

def tree(x,z,size=1,index=0):
    cylinder('tree-trunk_'+str(index),x,1.25*size,z,.18*size,2.5*size,'#7c6450')
    # Three offset low-poly crowns remain lightweight for the browser.
    for j,(dx,dy,dz,r) in enumerate(((0,3.3,0,1.6),(-.8,2.8,.3,1.25),(.7,2.9,-.35,1.25))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=r*size,location=bp(x+dx*size,dy*size,z+dz*size))
        o=bpy.context.object; o.name=f'tree-crown_{index}_{j}'
        for c in list(o.users_collection):c.objects.unlink(o)
        groups['03_Estimated_Details'].objects.link(o)
        o.data.materials.append(mat(('#628358','#769356','#4f7551')[j]))

# Mapped ground and roads; widths are estimates.
box('ground_base',(bounds[0]+bounds[1])/2,-1,(bounds[2]+bounds[3])/2,bounds[1]-bounds[0]+(24 if NEIGHBORHOOD else 0),2,bounds[3]-bounds[2]+(24 if NEIGHBORHOOD else 0),'#c4d1b6',group='04_Presentation')
if NEIGHBORHOOD:
    exec((ROOT/'scripts/dasi_neighborhood.py').read_text(encoding='utf-8'))
    build_neighborhood_ground()
campus=ways['963585633']['points']
polygon('ground_floor_campus',campus,.065,'#d5d6c9')
for wid,w in ways.items():
    if not w['tags'].get('highway'):continue
    width=road_width(w) if NEIGHBORHOOD else (2.2 if w['tags']['highway'] in ('footway','path','steps') else 6.5)
    for i,(a,b) in enumerate(zip(w['points'],w['points'][1:])):
        clipped=clip(a,b)
        if not clipped:continue
        a,b=clipped
        if math.dist(a,b)<.1:continue
        segment(f'road-edge_{wid}_{i}',a,b,width+1.2,.03,'#eef0e1',group='01_Mapped_Ground')
        segment(f'road_{wid}_{i}',a,b,width,.045,'#89918d',group='01_Mapped_Ground')

# An original procedural brick material: no school photographs are republished.
rng=random.Random(1920)
brick_image=bpy.data.images.new('Original_brick_courses',width=128,height=128)
pixels=[]
for y in range(128):
    course=y//16
    for x in range(128):
        joint=(y%16<2 or (x+(32 if course%2 else 0))%64<2)
        jitter=rng.uniform(-.045,.045)
        color=(.68,.63,.56) if joint else (.46+jitter,.255+jitter,.205+jitter)
        pixels.extend((*color,1))
brick_image.pixels=pixels
brick_image.pack()
brick=mat('#884e3b')
texture=brick.node_tree.nodes.new('ShaderNodeTexImage'); texture.image=brick_image
brick.node_tree.links.new(texture.outputs['Color'],brick.node_tree.nodes['Principled BSDF'].inputs['Base Color'])

main=ways['963585634']['points'][:-1]
gym=ways['963585635']['points'][:-1]
for wid,pts,height,name in [('963585634',main,8.3,'교사동'),('963585635',gym,6.2,'서쪽 별동')]:
    buildings.append(dict(osm_id=wid,name=name,footprint=pts,height=height,height_source='Photo-informed estimate, not measured'))

# Keep the mapped upper volume; a hollow first floor has actual door/window openings.
exec((ROOT/'scripts/dasi_interior.py').read_text(encoding='utf-8'))
polygon('osm-building_963585634',main,4.58,'#884e3b',False,3.785,'02_Photo_Exterior')
interior_data=build_school_first_floor(main)
polygon('roof_main_flat',main,.18,'#aaa597',base=8.37,group='02_Photo_Exterior')

def facade_window(name,a,b,t,base,w=2.6,h=1.9,offset=.10):
    dx,dz=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dz)
    ux,uz=dx/length,dz/length
    # Right-hand normal of the mapped edge points out of this polygon.
    nx,nz=uz,-ux
    x,z=a[0]+t*dx+nx*offset,a[1]+t*dz+nz*offset
    theta=math.atan2(-dz,dx)
    for off in (-w/2-.045,w/2+.045):
        box(name+'_frame_side',x+ux*off,base+h/2,z+uz*off,.09,h+.18,.18,'#e6e6dc',rotation=theta,group='02_Photo_Exterior')
    for yy in (base-.045,base+h+.045):
        box(name+'_frame_horizontal',x,yy,z,w,.09,.18,'#e6e6dc',rotation=theta,group='02_Photo_Exterior')
    box(name+'_glass',x+nx*.09,base+h/2,z+nz*.09,w,h,.035,'#486672' if base<2 else '#47606a',rotation=theta,group='02_Photo_Exterior')
    for off in (-w/6,w/6):
        box(name+'_mullion',x+ux*off+nx*.13,base+h/2,z+uz*off+nz*.13,.055,h,.045,'#e9ede5',rotation=theta)
    box(name+'_transom',x+nx*.13,base+h*.73,z+nz*.13,w,.055,.045,'#e9ede5',rotation=theta)
    box(name+'_sill',x+nx*.08,base-.1,z+nz*.08,w+.35,.12,.35,'#d2cbb9',rotation=theta)

for i,(a,b) in enumerate(zip(main,main[1:]+main[:1])):
    length=math.dist(a,b)
    segment(f'brick-coping_{i}',a,b,.30,.16,'#aa6354',base=8.50,group='02_Photo_Exterior')
    segment(f'floor-band_{i}',a,b,.17,.19,'#d0b39a',base=3.88,group='02_Photo_Exterior')
    if length<3.5:continue
    bays=max(1,int(length/4.1))
    for j in range(bays):
        t=(j+.5)/bays
        for floor in (0,1):
            if floor==0 and overlaps_school_entry(i,t*length,min(2.75,length/bays-.8),length):continue
            facade_window(f'window_{i}_{j}_{floor}',a,b,t,1.05+floor*3.6,w=min(2.75,length/bays-.8))

# South-facing covered walkway: visible in the school photo, depth is estimated.
front_edges=[20,21,22]
for i in front_edges:
    a,b=main[i],main[(i+1)%len(main)]
    dx,dz=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dz)
    nx,nz=dz/length,-dx/length
    outside_a=[a[0]+nx*2.1,a[1]+nz*2.1]; outside_b=[b[0]+nx*2.1,b[1]+nz*2.1]
    segment(f'walk-floor_colonnade_{i}',outside_a,outside_b,4.1,.18,'#cfc9b5')
    segment(f'canopy_{i}',outside_a,outside_b,4.3,.25,'#d9ccb2',base=3.44,group='02_Photo_Exterior')
    count=max(2,int(length/4.3))
    for j in range(count+1):
        t=j/count
        if overlaps_school_entry(i,t*length,.8,length):continue
        x=a[0]+t*dx+nx*3.65; z=a[1]+t*dz+nz*3.65
        cylinder(f'colonnade_pillar_{i}_{j}',x,1.75,z,.18,3.5,'#e8d6b4')
        box(f'column_collision_{i}_{j}',x,.05,z,.36,.1,.36,'#d7cdb8',True)

# Clock and cream-colored roof feature on the front's western wing.
a,b=main[22],main[0]
dx,dz=b[0]-a[0],b[1]-a[1]; ln=math.hypot(dx,dz); ux,uz=dx/ln,dz/ln; nx,nz=uz,-ux
clock_x,clock_z=(a[0]+b[0])/2+nx*.25,(a[1]+b[1])/2+nz*.25
theta=math.atan2(-dz,dx)
box('clock_roof_beam',clock_x,9.25,clock_z,13.0,.35,1.1,'#e2d7bd',rotation=theta,group='02_Photo_Exterior')
for off in (-5.6,0,5.6):
    box('clock_roof_support',clock_x+ux*off,8.7,clock_z+uz*off,.48,1.1,.55,'#e2d7bd',rotation=theta,group='02_Photo_Exterior')
# Circular school mark: the photo does not establish that this is a clock.
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.64,depth=.10,location=bp(clock_x+nx*.15,7.38,clock_z+nz*.15))
clock=bpy.context.object; clock.name='school_round_emblem'
clock.rotation_euler=(math.pi/2,0,theta)
for c in list(clock.users_collection):c.objects.unlink(clock)
groups['02_Photo_Exterior'].objects.link(clock); clock.data.materials.append(mat('#edf0db'))
label('다시',clock_x+nx*.24,7.38,clock_z+nz*.24,.62,theta+math.pi,'#4e655e',.30)
# Edge 22 runs west: the former text faced into the wall and appeared mirrored.
box('school_name_plaque',clock_x+nx*.40,4.29,clock_z+nz*.40,8.9,.68,.14,'#28594b',rotation=theta)
school_name=label('다시초등학교',clock_x+nx*.51,4.29,clock_z+nz*.51,8.1,theta+math.pi,'#fff4d9',.48)
school_name.name='school_name_readable'

# Pink end panels and taller stair-tower caps seen on the front elevation.
for i,t in ((22,.90),(20,.07)):
    sa,sb=main[i],main[(i+1)%len(main)]
    sx,sz=sb[0]-sa[0],sb[1]-sa[1]; sl=math.hypot(sx,sz)
    snx,snz=sz/sl,-sx/sl; st=math.atan2(-sz,sx)
    cx,cz=sa[0]+t*sx,sa[1]+t*sz
    box(f'pink_stair_panel_{i}',cx+snx*.20,4.55,cz+snz*.20,3.8,9.1,.3,'#c59187',rotation=st,group='02_Photo_Exterior')
    box(f'pink_stair_roof_{i}',cx-snx*2,8.7,cz-snz*2,4.1,.9,4.4,'#c59187',rotation=st,group='02_Photo_Exterior')

# Climbing greenery concentrated on the western facade as seen in the photo.
for j in range(28):
    t=.61+(j%7)*.048
    x=a[0]+t*dx+nx*.25; z=a[1]+t*dz+nz*.25
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=bp(x,4.6+(j//7)*.95,z))
    ivy=bpy.context.object; ivy.name=f'ivy_clump_{j}'
    ivy.scale=(.30+(j%3)*.15,.15,.58); ivy.rotation_euler.z=theta
    for collection in list(ivy.users_collection):collection.objects.unlink(ivy)
    groups['02_Photo_Exterior'].objects.link(ivy)
    ivy.data.materials.append(mat(('#405f38','#4b6b3e','#557449')[j%3]))

# Western hall: actual footprint, red barrel roof and light front band from photos.
polygon('osm-building_963585635',gym,6.2,'#c58b85',True,.065,'02_Photo_Exterior')
g0,g1,g2,g3=gym
front=[(g0[0]+g1[0])/2,(g0[1]+g1[1])/2]
back=[(g2[0]+g3[0])/2,(g2[1]+g3[1])/2]
width=math.dist(g0,g1)+1.2
depth=math.dist(front,back)+1.2
gx,gz=(front[0]+back[0])/2,(front[1]+back[1])/2
gux,guz=(g1[0]-g0[0])/math.dist(g0,g1),(g1[1]-g0[1])/math.dist(g0,g1)
gvx,gvz=(back[0]-front[0])/math.dist(front,back),(back[1]-front[1])/math.dist(front,back)
N=24
verts=[]
for v in (-depth/2,depth/2):
    for i in range(N+1):
        angle=math.pi*i/N
        u=math.cos(angle)*width/2
        verts.append(bp(gx+gux*u+gvx*v,6.3+math.sin(angle)*4.4,gz+guz*u+gvz*v))
faces=[(i,i+1,i+N+2,i+N+1) for i in range(N)]
faces.extend([tuple(reversed(range(N+1))),tuple(range(N+1,2*N+2))])
mesh_object('roof_west_barrel',verts,faces,'#a9544e','02_Photo_Exterior')
segment('west_front_white_band',g0,g1,1.0,.8,'#e2e4db',base=5.25,group='02_Photo_Exterior')
for j in range(6):
    # The gym front edge has the opposite winding from the main block.
    facade_window(f'west_window_{j}',g1,g0,(j+.5)/6,3.3,w=2.0,h=1.35)
for j in range(11):
    u=-width/2+j*width/10
    # White narrow roof seams follow the curved cross section at the front.
    y=6.3+4.4*math.sqrt(max(0,1-(u/(width/2))**2))
    segment(f'roof_west_seam_{j}',[gx+gux*u-gvx*depth/2,gz+guz*u-gvz*depth/2],[gx+gux*u+gvx*depth/2,gz+guz*u+gvz*depth/2],.06,.055,'#cc9b90',base=y)

# Full campus zoning: visual trace of 2022-10-14 aerial imagery, cross-checked
# against the 2025/2026 school photos. Boundaries have at least ~5m uncertainty.
lawn=[[-29,-6],[42,2],[36,17],[-35,14]]
polygon('ground_floor_school_lawn',lawn,.015,'#8ba357',base=.065,group='03_Estimated_Details')
parking=[[-74,-17],[-46,-12],[-32,-7],[-36,17],[-79,9]]
polygon('ground_floor_school_parking',parking,.02,'#848d88',base=.065,group='03_Estimated_Details')
grove=[[-40,16],[21,24],[16,49],[-44,42]]
polygon('ground_floor_south_grove',grove,.025,'#768c58',base=.065,group='03_Estimated_Details')
segment('field_south_walk',[-38,15],[33,23],2.0,.095,'#c8af83')
segment('school_front_path',[-74,-8],[41,4],2.6,.10,'#c8af83')
segment('school_west_walk',[-38,-2],[-44,35],2.2,.10,'#c8af83')
segment('school_grove_path',[-43,35],[16,43],1.8,.105,'#bcac88')
segment('entry_path',[78,9],[42,10],4.5,.11,'#b6b9ad')

# Small blue-roofed building and sports court are visible in the 2025 photo.
# Their coordinates and dimensions are estimates because OSM does not map them.
# Southeast buildings extend beyond the incomplete OSM school boundary.
# Their approximate aerial locations are retained; their ownership is unverified.
box('photo-building_blue_annex',34,2.0,28.3,13.8,4,8.5,'#e4e5dd',True,rotation=-.20)
annex_verts=[]
for x,y,z in [(-7.3,4,-4.7),(7.3,4,-4.7),(7.3,4,4.7),(-7.3,4,4.7),(0,6.0,-4.7),(0,6.0,4.7)]:
    annex_verts.append(bp(34+x*math.cos(-.20)+z*math.sin(-.20),y,28.3-x*math.sin(-.20)+z*math.cos(-.20)))
mesh_object('roof_blue_annex',annex_verts,[(3,5,4,0),(5,2,1,4),(4,1,0),(2,5,3)],'#3a89b4','02_Photo_Exterior')
box('annex_door',34.9,1.35,24.1,1.45,2.6,.16,'#536763',rotation=-.20)
box('annex_awning',35.0,3.15,23.7,2.3,.18,1.5,'#729c8a',rotation=-.20)
box('photo-building_south_shed',24.6,2.15,45.8,10,4.3,18.0,'#d3d7cc',True,rotation=-.20)
box('south_shed_metal_roof',24.6,4.37,45.8,10.6,.22,18.6,'#b6c6c7',rotation=-.20)
for i in range(12):
    box('shed_roof_rib',19.8+i*.8,4.52,45.8,.035,.06,18.6,'#e2e4dc',rotation=-.20)
box('ground_floor_sport_court',56,.085,2,23,.025,20,'#ab6553')
for ax,az,bx,bz in [(45,-7,67,-7),(67,-7,67,11),(67,11,45,11),(45,11,45,-7),(56,-7,56,11)]:
    segment('court_marking',[ax,az],[bx,bz],.09,.005,'#e6dbc2',base=.10)

# Site boundary follows OSM; fence height, openings and landscaping are estimates.
for i,(a,b) in enumerate(zip(campus,campus[1:])):
    if i in (3,4,5,6):continue  # Unverified south/east OSM boundary is not a physical barrier.
    if NEIGHBORHOOD and i==2:
        neighborhood_gate_opening(a,b)
        continue
    segment(f'boundary_wall_{i}',a,b,.35,.45,'#b9b9a8',True)
    segment(f'boundary_rail_{i}',a,b,.09,.065,'#566c61',base=1.2)
    n=max(1,int(math.dist(a,b)/2.2))
    for j in range(n+1):
        t=j/n
        cylinder(f'boundary_post_{i}_{j}',a[0]+(b[0]-a[0])*t,.76,a[1]+(b[1]-a[1])*t,.035,1.05,'#536b60',8)
# Photo-informed stone gate, with an approximate east-side placement.
for i,z in enumerate((-1,13)):
    box(f'gate_pier_{i}',82.5,1.4,z,1.25,2.8,1.25,'#b3b4ab',True)
    for level,width in enumerate((1.65,1.3,.95)):
        box(f'gate_cap_{i}_{level}',82.5,2.86+level*.18,z,width,.18,width,'#c2c3b9')
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.32,location=bp(82.5,3.56,z))
    o=bpy.context.object; o.name=f'gate_finial_{i}'
    for c in list(o.users_collection):c.objects.unlink(o)
    groups['02_Photo_Exterior'].objects.link(o); o.data.materials.append(mat('#b9bcb4'))
    box(f'gate_nameplate_{i}',83.15,1.45,z,.08,2.0,.45,'#275a4b')
    label('다\n시\n초\n등\n학\n교',83.20,1.5,z,.4,math.pi/2,'#d8bd73',1.80)
box('centenary_monument',79,2.45,-4,1.2,4.9,.8,'#c8ccc1',True)
label('개교\n100주년',79,3.1,-3.56,1.0,0,'#42564c',1.4)
for i,(x,z,s) in enumerate([(-78,21,1.5),(-75,8,1.6),(-65,40,1.3),(-52,42,1.25),(-29,46,1.2),(-10,48,1.3),(13,39,1.6),(70,-34,1.6),(74,-20,1.4),(70,-6,1.7),(64,17,1.5),(38,-62,1.2),(-57,-61,1.3)]):
    tree(x,z,s,i)
for i in range(3):
    x,z=49+i*5,16+i*.2
    box('bench_seat',x,.55,z,2.8,.14,.60,'#927052',True)
    box('bench_back',x,.93,z+.3,2.8,.5,.10,'#927052')
    for off in (-1,1):box('bench_leg',x+off,.26,z,.10,.52,.5,'#526359')

detail_school_campus()
spawn=interior_data['spawn']
places=interior_data['places']+[
    dict(id='clock-front',name='본관 앞',position=[clock_x+nx*8,clock_z+nz*8],radius=13,description='붉은 벽돌과 흰 창틀, 사진 속 원형 장식을 찾아보세요.'),
    dict(id='west-hall',name='서쪽 별동 앞',position=[front[0],front[1]+6],radius=13,description='둥근 붉은 지붕을 사진에 맞춰 표현했어요.'),
    dict(id='school-field',name='잔디 운동장',position=[3,7],radius=35,footprint=lawn,description='항공사진에서 운동장 범위를 대조하고 최근 사진의 잔디를 반영했어요.'),
    dict(id='south-grove',name='운동장 남쪽 나무 구역',position=[-10,33],radius=27,footprint=grove,description='잔디 운동장 뒤편으로 이어지는 나무 구역입니다.'),
    dict(id='west-parking',name='서쪽 주차 공간',position=[-56,0],radius=22,footprint=parking,description='서쪽 별동 아래의 주차 공간을 항공사진과 대조했어요.'),
    dict(id='sport-court',name='야외 코트',position=[56,2],radius=14,description='최근 학교 사진에서 보이는 붉은 코트를 표현했어요. 치수와 위치는 추정입니다.'),
    dict(id='east-yard',name='교사동 옆마당',position=[62,2],radius=25,description='본관의 초록색 입구 안내를 따라 복도와 교실로 들어가 보세요.'),
]
limitations=[
    'School boundary and two building footprints use OpenStreetMap coordinates.',
    'Two-story brick facades, light window frames, round emblem, ivy, stone gate and barrel roof are photo-informed.',
    'Heights, window counts, emblem placement, paths, individual trees, gate location and details are approximate.',
    'Lawn, parking, south grove and southeast structures are visually traced from Esri World Imagery dated 2022-10-14, with roughly 5m or greater placement uncertainty; 2025/2026 photos inform appearance. Southeast building ownership and current changes are unverified.',
    'The court and blue-roof structure are photo-informed without surveyed footprints. Matching the barrel roof to the west OSM building is an inference.',
    'Flat terrain. The first-floor corridor, classroom, reading room and furniture are illustrative, not the real school interior. Upper floors remain exterior-only.',
]
neighborhood_data = build_neighborhood() if NEIGHBORHOOD else None
if NEIGHBORHOOD:
    places.extend(neighborhood_data['places'])
    limitations.extend(neighborhood_data['limitations'])
world=dict(title='나주 산책',subtitle='다시초등학교 · 실제 지도와 사진 참고',source='© OpenStreetMap contributors, ODbL 1.0',source_url=SOURCE_URL,origin=dict(lat=LAT,lon=LON),bounds=bounds,spawn=spawn,solids=solids,signs=signs,places=places,buildings=buildings,limitations=limitations,campus_osm_id='963585633',interior=interior_data,lights=interior_data['lights'])
if neighborhood_data: world['neighborhood'] = neighborhood_data
(ROOT/'public'/f'{WORLD_NAME}-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(ROOT/'knowledge/sources'/f'{WORLD_NAME}-model-provenance.json').write_text(json.dumps({k:world[k] for k in ('source','source_url','origin','campus_osm_id','buildings','limitations')},ensure_ascii=False,indent=2),encoding='utf-8')

bpy.ops.object.camera_add(location=(50,-145,125))
camera=bpy.context.object; camera.name='School_overview_camera'
camera.rotation_euler=(Vector((-5,15,0))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'; camera.data.ortho_scale=200; scene.camera=camera
if NEIGHBORHOOD:
    camera.name='Dasi_neighborhood_overview'; camera.location=bp(165,440,350)
    camera.rotation_euler=(Vector(bp(-5,0,-25))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=640; camera.data.clip_end=2000
bpy.ops.object.light_add(type='SUN',location=(-70,-80,130))
sun=bpy.context.object; sun.rotation_euler=(.6,-.4,-.4); sun.data.energy=2.3; sun.data.angle=.14
scene.world=bpy.data.worlds.new('School_daylight'); scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.78,.85,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=1440; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(ROOT/'outputs/dasi-overview.png')
if NEIGHBORHOOD:
    scene.render.resolution_x=1920; scene.render.resolution_y=1440
    scene.render.filepath=str(ROOT/'outputs/dasi-neighborhood-overview.png')
scene.view_settings.view_transform='AgX'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models'/f'{MODEL_NAME}.glb'),export_format='GLB',use_active_scene=True,export_cameras=False,export_lights=False,export_extras=True,export_apply=True)
print(json.dumps(dict(blend=str(OUTPUT),buildings=len(buildings),objects=len(scene.objects),spawn=spawn),ensure_ascii=False))
if '--render' in sys.argv:bpy.ops.render.render(write_still=True)
if NEIGHBORHOOD and '--render' in sys.argv:
    camera.data.type='PERSP'; camera.data.lens=32
    scene.render.resolution_x=1600; scene.render.resolution_y=1000
    for name,eye,target in [('dasi-station-detail',(98,7,67),(100,3.8,94)),('dasi-neighborhood-school',(-7,65,105),(-25,0,-30))]:
        camera.data.lens=24 if name=='dasi-station-detail' else 32
        camera.location=bp(*eye)
        camera.rotation_euler=(Vector(bp(*target))-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(ROOT/'outputs'/f'{name}.png')
        bpy.ops.render.render(write_still=True)
if '--render-details' in sys.argv:
    camera.data.type='PERSP'; camera.data.lens=30; camera.data.clip_start=.1
    scene.render.resolution_x=1440; scene.render.resolution_y=960
    for name,eye,target in [('dasi-sign-detail',(17,5.2,-22),(17,4.2,0)),('dasi-classroom',(2.7,2.10,4.7),(9,1.55,9.0)),('dasi-library',(25,2.1,4.9),(23,1.7,10.5))]:
        x,z=local_point(eye[0],eye[2]); tx,tz=local_point(target[0],target[2])
        camera.location=bp(x,eye[1],z)
        camera.rotation_euler=(Vector(bp(tx,target[1],tz))-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(ROOT/'outputs'/f'{name}.png')
        bpy.ops.render.render(write_still=True)
