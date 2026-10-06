"""Photo-informed painted joinery in a new, preserved Blender revision.

Reference photographs guide silhouettes and paint placement; maps are original
drawings. Neither historic photographs nor downloaded survey scans are embedded.
"""
import bpy, bmesh, json, math, gzip, struct, hashlib
import xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path
from mathutils import Vector

root=Path(__file__).resolve().parents[1]
out=root/'outputs/geumseonggwan-v78';out.mkdir(parents=True,exist_ok=True)
source=root/'outputs/geumseonggwan-v77/geumseonggwan-v77.blend'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
world=json.loads((root/'public/city-world.json').read_text(encoding='utf-8'))
backup=out/'world-before.json'
if not backup.exists():backup.write_text(json.dumps(world,ensure_ascii=False),encoding='utf-8')
world=json.loads(backup.read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
lat,lon=world['origin']['lat'],world['origin']['lon'];mx=111320*math.cos(math.radians(lat))
xml=ET.parse(root/'knowledge/sources/geumseonggwan.osm').getroot()
nodes={n.attrib['id']:((float(n.attrib['lon'])-lon)*mx,-(float(n.attrib['lat'])-lat)*111320) for n in xml.findall('node')}
ways={w.attrib['id']:[nodes[n.attrib['ref']] for n in w.findall('nd')] for w in xml.findall('way')}
class Frame:
    def __init__(self,a,u):self.a=a;self.u=u;self.v=(u[1],-u[0])
    def xyz(self,x,y,z):return (self.a[0]+self.u[0]*x+self.v[0]*z,-self.a[1]-self.u[1]*x-self.v[1]*z,y)
    def view(self,x,y,z):
        p=self.xyz(x,y,z);return [p[0],p[2],-p[1]]
def frame(id):
    pts=ways[id][:-1];a,b=pts[1:3];w=math.dist(a,b)
    return Frame(a,((b[0]-a[0])/w,(b[1]-a[1])/w)),w,math.dist(pts[0],a)
f,fullwidth,_=frame('832423358');info=world['architecture'];c=info['center'];columns=info['columns'];front=info['front'];back=info['back']
gf,gw,gd=frame('832423356')
def linear(hex):
    a=tuple(int(hex.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a)
def material(name,hex='#ffffff',kind=None):
    m=bpy.data.materials.new('Geum_v78_'+name);m.use_nodes=True
    m.diffuse_color=(*linear(hex),1);bs=m.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=.87
    if kind:
        for suffix,target in [('color','Base Color'),('roughness','Roughness')]:
            im=bpy.data.images.load(str(root/f'assets/geumseonggwan-v78/materials/{kind}-{suffix}.png'),check_existing=True)
            im.colorspace_settings.name='sRGB' if suffix=='color' else 'Non-Color'
            tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
            m.node_tree.links.new(tex.outputs['Color'],bs.inputs[target])
    return m
def generic_uv(ob):
    layer=ob.data.uv_layers.active or ob.data.uv_layers.new(name='HeritageUV_v78')
    for p in ob.data.polygons:
        axis=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=axis]
        for i in p.loop_indices:
            v=ob.data.vertices[ob.data.loops[i].vertex_index].co
            layer.data[i].uv=(v[axes[0]]*.7,v[axes[1]]*.7)
class Builder:
    def __init__(self,name,mats):self.name=name;self.mats=mats;self.vertices=[];self.faces=[];self.indices=[]
    def polygon(self,points,faces,mat=0):
        start=len(self.vertices);self.vertices.extend(points)
        self.faces.extend(tuple(start+i for i in face) for face in faces);self.indices.extend([mat]*len(faces))
    def box(self,fr,x,y,z,w,h,d,mat=0):
        points=[fr.xyz(xx,yy,zz) for yy in [y-h/2,y+h/2] for xx,zz in [(x-w/2,z-d/2),(x+w/2,z-d/2),(x+w/2,z+d/2),(x-w/2,z+d/2)]]
        self.polygon(points,[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],mat)
    def tube(self,fr,a,b,r,mat=0,sides=7):
        a,b=Vector(fr.xyz(*a)),Vector(fr.xyz(*b));axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
        if u.length<.001:u=axis.cross(Vector((1,0,0)))
        u.normalize();v=axis.cross(u).normalized()
        vv=[tuple(p+r*(math.cos(i*math.tau/sides)*u+math.sin(i*math.tau/sides)*v)) for p in [a,b] for i in range(sides)]
        self.polygon(vv,[tuple(reversed(range(sides))),tuple(range(sides,2*sides))]+[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)],mat)
    def finish(self,smooth=False,quad_uv=False):
        data=bpy.data.meshes.new(self.name);data.from_pydata(self.vertices,[],self.faces);data.update()
        for m in self.mats:data.materials.append(m)
        for p,i in zip(data.polygons,self.indices):p.material_index=i;p.use_smooth=smooth
        bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
        ob=bpy.data.objects.new(self.name,data);scene.collection.objects.link(ob)
        ob['source_class']='2015 survey photographs and 2009 field photographs; original paint, inferred dimensions'
        generic_uv(ob)
        if quad_uv:
            for p in data.polygons:
                for i in p.loop_indices:data.uv_layers.active.data[i].uv=[(0,0),(1,0),(1,1),(0,1)][data.loops[i].vertex_index%4]
        return ob

# Remove superseded decorative meshes only inside this newly opened copy.
obsolete=('v77_ikgong_curved_arms','v77_ikgong_painted_edges','v77_morodancheong_scrolls',
          'v76_original_dancheong_flower_bands','ceiling_original_lotus','ceiling_lotus_center',
          'beam_original_ornament','beam_original_ornament_inset','hall_name_readable','hall_coffer_frame')
removed=[o.name for o in scene.objects if o.name in obsolete]
bpy.data.batch_remove([o for o in scene.objects if o.name in removed])
green=material('carved_leaf_green','#497b6a');red=material('carved_leaf_red','#9b6750')
cream=material('paint_edge_cream','#d6c8a3');ochre=material('paint_edge_ochre','#b59e72')
arms=Builder('v78_ikgong_leaf_arms',[green,red]);edges=Builder('v78_ikgong_leaf_outlines',[cream,ochre])
stations=[(f,x,z,5.88) for x in columns for z in [front-.16,back+.16]]
stations.extend((gf,.45+(gw-.9)*i/3,z,6.25) for i in range(4) for z in [.85,gd-.85])
# Pronounced rounded, upswept leaf ends, read in profile under the rafters.
profile=[(-1.04,.28),(-1.02,.15),(-.94,.06),(-.72,-.07),(-.35,-.12),(.35,-.12),(.73,-.07),(.94,.06),(1.02,.15),(1.04,.28),(1.01,.37),(.94,.38),(.91,.28),(.84,.22),(.75,.25),(.80,.31),(.78,.35),(.72,.32),(.60,.13),(.36,.05),(-.36,.05),(-.60,.13),(-.72,.32),(-.78,.35),(-.80,.31),(-.75,.25),(-.84,.22),(-.91,.28),(-.94,.38),(-1.01,.37)]
for fr,x,z,y in stations:
    arms.box(fr,x,y-.10,z,.46,.23,.52,1)
    for tier in range(3):
        sy=y+tier*.18;sz=1+tier*.10;thick=.18+tier*.055;n=len(profile)
        vv=[fr.xyz(x+side*thick/2,sy+py,z+pz*sz) for side in [-1,1] for pz,py in profile]
        arms.polygon(vv,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],0)
        for side in [-1,1]:
            for (za,ya),(zb,yb) in zip(profile,profile[1:]+profile[:1]):
                edges.tube(fr,(x+side*(thick/2+.009),sy+ya*.92,z+za*sz*.96),(x+side*(thick/2+.009),sy+yb*.92,z+zb*sz*.96),.012,tier%2,6)
    arms.box(fr,x,y+.55,z,.64,.12,1.28)
arms.finish();edges.finish(True)['no_shadow']=True

coffers=Builder('v78_painted_lotus_coffers',[material('lotus_coffer',kind='coffer'),material('lotus_coffer_blue',kind='coffer-blue'),material('lotus_coffer_gold',kind='coffer-gold')])
inner=[front+(back-front)*.25,front+(back-front)*.75];width=columns[4]-columns[1];depth=inner[1]-inner[0]
for row in range(8):
    for k in range(12):
        x=columns[1]+(k+.5)*width/12;z=inner[0]+(row+.5)*depth/8;w=width/12-.025;d=depth/8-.025
        coffers.polygon([f.xyz(x-w/2,7.662,z-d/2),f.xyz(x+w/2,7.662,z-d/2),f.xyz(x+w/2,7.662,z+d/2),f.xyz(x-w/2,7.662,z+d/2)],[(0,1,2,3)],(row+k)%3)
coffers.finish(quad_uv=True)['no_shadow']=True
frames=Builder('v78_coffer_edge_frames',[red,cream])
for i in range(13):
    x=columns[1]+i*width/12
    frames.box(f,x,7.642,(inner[0]+inner[1])/2,.045,.035,depth)
    frames.box(f,x,7.620,(inner[0]+inner[1])/2,.012,.012,depth,1)
for j in range(9):
    z=inner[0]+j*depth/8
    frames.box(f,c,7.642,z,width,.035,.045)
    frames.box(f,c,7.620,z,width,.012,.012,1)
frames.finish()['no_shadow']=True

beam=Builder('v78_painted_beam_faces',[material('painted_beam',kind='beam')])
def face_board(fr,x,y,z,w,h,mat=0):
    beam.polygon([fr.xyz(x-w/2,y-h/2,z),fr.xyz(x+w/2,y-h/2,z),fr.xyz(x+w/2,y+h/2,z),fr.xyz(x-w/2,y+h/2,z)],[(0,1,2,3)],mat)
for a,b in zip(columns,columns[1:]):
    for z in [front-.205,front+.205,back-.205,back+.205]:face_board(f,(a+b)/2,5.73,z,b-a-.18,.28)
for z in inner:
    for side in [-1,1]:face_board(f,c,6.40,z+side*.175,columns[-1]-columns[0],.45)
beam.finish(quad_uv=True)['no_shadow']=True

# Paint cylinder caps radially, and long bodies along their real axis. Previous
# generic mapping incorrectly gave these timber members the roof tile texture.
body=material('painted_rafter_body',kind='rafter-body');end=material('painted_rafter_end',kind='rafter-end')
rafter_groups=[];rafter_count=0
for ob in list(scene.objects):
    if ob.type!='MESH' or not (ob.name.endswith(('_lower_rafter','_upper_rafter')) or ob.name in ['hall_exposed_ceiling_rafter','hall_front_back_ceiling_rafter']):continue
    mesh=ob.data;mesh.materials.clear();mesh.materials.append(body);mesh.materials.append(end)
    layer=mesh.uv_layers.active or mesh.uv_layers.new(name='RafterAxisUV')
    incidence=[[] for _ in mesh.vertices]
    for p in mesh.polygons:
        for v in p.vertices:incidence[v].append(p.index)
    seen=set();valid=0
    for p in mesh.polygons:
        if p.index in seen:continue
        stack=[p.index];component=[]
        while stack:
            n=stack.pop()
            if n in seen:continue
            seen.add(n);q=mesh.polygons[n];component.append(q)
            for v in q.vertices:stack.extend(i for i in incidence[v] if i not in seen)
        # The preserved source is already triangulated. Infer the cylinder axis
        # from its vertex covariance instead of expecting untriangulated caps.
        vertex_ids=sorted({i for q in component for i in q.vertices})
        points=np.array([mesh.vertices[i].co[:] for i in vertex_ids]);mean=points.mean(axis=0)
        _,vectors=np.linalg.eigh((points-mean).T@(points-mean));axis=Vector(vectors[:,-1]);projected=(points-mean)@np.array(axis)
        a=Vector(points[projected<projected.min()+.001].mean(axis=0));b=Vector(points[projected>projected.max()-.001].mean(axis=0))
        length=(b-a).length
        if length<.01:continue
        axis=(b-a).normalized();caps={q.index for q in component if abs(q.normal.dot(axis))>.95}
        radial=Vector(points[projected.argmin()])-a;u=radial.normalized();v=axis.cross(u).normalized();radius=radial.length
        if radius<.001:continue
        for q in component:
            q.material_index=1 if q.index in caps else 0
            values=[]
            for li in q.loop_indices:
                pt=mesh.vertices[mesh.loops[li].vertex_index].co;delta=pt-a
                if q.index in caps:
                    center=a if (pt-a).dot(axis)<length/2 else b;rad=pt-center;values.append((.5+.5*rad.dot(u)/radius,.5+.5*rad.dot(v)/radius))
                else:values.append(((math.atan2(delta.dot(v),delta.dot(u))/math.tau)%1,delta.dot(axis)/length))
            if q.index not in caps and max(t[0] for t in values)-min(t[0] for t in values)>.5:values=[(s+1 if s<.5 else s,t) for s,t in values]
            for li,st in zip(q.loop_indices,values):layer.data[li].uv=st
        valid+=1
    rafter_count+=valid;rafter_groups.append({'name':ob.name,'cylinders':valid})

panel=material('faded_door_panel',kind='door-panel')
door_count=0
for ob in scene.objects:
    if ob.type!='MESH' or '_bottom_panel' not in ob.name:continue
    ob.data.materials.clear();ob.data.materials.append(panel);layer=ob.data.uv_layers.active or ob.data.uv_layers.new(name='PanelUV')
    # Each disconnected rectangular face keeps its complete painted border.
    for p in ob.data.polygons:
        verts=[ob.data.vertices[v].co for v in p.vertices];axis=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=axis]
        # Use the face edge basis rather than world axes, which would skew rotated doors.
        origin=verts[0];e=(verts[1]-origin).normalized();n=p.normal;up=n.cross(e).normalized()
        coords=[((pt-origin).dot(e),(pt-origin).dot(up)) for pt in verts];lo=[min(t[j] for t in coords) for j in [0,1]];hi=[max(t[j] for t in coords) for j in [0,1]]
        for li,st in zip(p.loop_indices,coords):layer.data[li].uv=tuple((st[j]-lo[j])/max(1e-6,hi[j]-lo[j]) for j in [0,1])
    door_count+=1

plaster=Builder('v78_yellow_plaster_knee_walls',[material('aged_yellow_plaster','#bdae80')])
for bay in [0,1,3,4]:
    a,b=columns[bay:bay+2]
    for z in [front-.10,back+.10]:plaster.box(f,(a+b)/2,1.155,z,b-a-.5,.15,.13)
plaster.finish()
plaque=Builder('v78_brush_style_nameboard',[material('plaque_lettering',kind='plaque')])
plaque.polygon([f.xyz(c-2.02,4.985,front-.805),f.xyz(c+2.02,4.985,front-.805),f.xyz(c+2.02,5.875,front-.805),f.xyz(c-2.02,5.875,front-.805)],[(0,1,2,3)])
plaque.finish(quad_uv=True)['no_shadow']=True

world['architectureViews'].append({'id':'ceiling','label':'천장·단청','center':f.view(c,7.55,(inner[0]+inner[1])/2),'radius':5,'elevation':-.95,'angle':math.atan2(-f.v[0],-f.v[1]),'fov':60})
next(v for v in world['architectureViews'] if v['id']=='eaves')['elevation']=-.095
world['detailVersion']='geumseonggwan-v78-20261003'
world['limitations'].append('v78 paint placement and leaf-profile joinery are guided by 2015 survey and 2009 field photos. Original raster patterns and font-based plaque are interpretations, not measured facsimiles; all verified doorway and floor envelopes remain unchanged.')
scene['research_revision']='v78; 2014-2015 official survey metadata and photos; 2009 field photos'
scene.view_settings.exposure=.4
bpy.ops.file.pack_all();blend=out/'geumseonggwan-v78.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
for ob in scene.objects:
    if ob.type=='MESH':
        coords=np.empty(len(ob.data.vertices)*3,dtype=np.float32);ob.data.vertices.foreach_get('co',coords)
        ob.data.vertices.foreach_set('co',np.round(coords*10000)/10000);ob.data.update()
for im in bpy.data.images:
    if im.type=='IMAGE' and max(im.size)>512:
        w,h=im.size;scale=512/max(w,h);im.scale(max(1,round(w*scale)),max(1,round(h*scale)))
target=out/'geumseonggwan-web-v78.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_active_scene=True,export_cameras=False,export_lights=False,export_extras=True,export_apply=True,export_image_format='WEBP',export_image_quality=87)
raw=target.read_bytes();length=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+length]);binary=raw[20+length:]
# Retain earlier multiplicative material tints. New fully painted maps already
# contain the final color and must not get the legacy tint multiplied again.
for m in gltf['materials']:
    original=bpy.data.materials.get(m.get('name',''))
    if original and original.name.startswith('Geum_v') and not original.name.startswith('Geum_v78_') and any(n.type=='TEX_IMAGE' for n in original.node_tree.nodes):
        m.setdefault('pbrMetallicRoughness',{})['baseColorFactor']=[min(1,v*1.22) for v in original.diffuse_color[:3]]+[1]
encoded=json.dumps(gltf,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary
packed=gzip.compress(raw,9,mtime=0)
if len(packed)>=25*1024*1024:raise RuntimeError('Web export exceeds hosting budget')
for name,data in [('geumseonggwan.glb',raw),('geumseonggwan.glb.gz',packed)]:
    temp=root/'public/models'/('v78-'+name+'.tmp');temp.write_bytes(data);temp.replace(root/'public/models'/name)
(root/'public/city-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
metrics={'source':str(source.relative_to(root)),'sourceSHA256':source_hash,'sourceUnchanged':hashlib.sha256(source.read_bytes()).hexdigest()==source_hash,'editableBlend':str(blend.relative_to(root)),
         'removedSupersededGroups':removed,'ikgongStations':len(stations),'paintedCoffers':96,'paintedDoorGroups':door_count,'paintedRafterCount':rafter_count,'rafterGroups':rafter_groups,
         'objects':len(scene.objects),'triangles':sum(gltf['accessors'][p['indices']]['count']//3 for m in gltf['meshes'] for p in m['primitives']),'rawBytes':len(raw),'gzipBytes':len(packed),'textureImages':len(gltf['images']),
         'collisionUnchanged':world['solids']==json.loads(backup.read_text(encoding='utf-8'))['solids']}
(out/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
print('GEUMSEONGGWAN_V78_COMPLETE',json.dumps(metrics,ensure_ascii=True),flush=True)
