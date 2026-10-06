"""Advance the existing authored precinct in a NEW Blender file, preserving v76."""
import bpy,bmesh,json,math,random,gzip,struct,hashlib,xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'outputs/geumseonggwan-v77';out.mkdir(parents=True,exist_ok=True)
source=root/'outputs/geumseonggwan-exclusive-v76/geumseonggwan-exclusive-v76.blend'
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
def col(hex):
    a=tuple(int(hex.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a)
def tint(m,rgb):
    m.diffuse_color=(*rgb,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*rgb,1)
    for n in m.node_tree.nodes:
        if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY':n.inputs[2].default_value=(*[min(1,v*1.22) for v in rgb],1)
def uv(ob,scale=.7):
    layer=ob.data.uv_layers.active or ob.data.uv_layers.new(name='HeritageUV_v77');values=[]
    for p in ob.data.polygons:
        axis=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=axis]
        for i in p.loop_indices:
            v=ob.data.vertices[ob.data.loops[i].vertex_index].co;values.extend((v[axes[0]]*scale,v[axes[1]]*scale))
    layer.data.foreach_set('uv',values)
loaded={}
def img(kind,suffix):
    key=(kind,suffix)
    if key not in loaded:
        im=bpy.data.images.load(str(root/f'assets/geumseonggwan-v77/materials/{kind}-{suffix}.png'))
        im.colorspace_settings.name='sRGB' if suffix=='color' else 'Non-Color';loaded[key]=im
    return loaded[key]
def maps(m,kind):
    bs=m.node_tree.nodes.get('Principled BSDF')
    for suffix,target in [('color','Base Color'),('roughness','Roughness'),('normal','Normal')]:
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img(kind,suffix)
        if suffix=='color':
            mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*[min(1,v*1.22) for v in m.diffuse_color[:3]],1)
            m.node_tree.links.new(tex.outputs['Color'],mix.inputs[1]);m.node_tree.links.new(mix.outputs['Color'],bs.inputs[target])
        elif suffix=='normal':
            normal=m.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.22
            m.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);m.node_tree.links.new(normal.outputs['Normal'],bs.inputs[target])
        else:m.node_tree.links.new(tex.outputs['Color'],bs.inputs[target])
def material(name,hex,kind=None):
    m=bpy.data.materials.new(name);m.use_nodes=True;tint(m,col(hex));m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.86
    if kind:maps(m,kind)
    return m

# Refresh original material maps and reduce paint saturation, with the exact same
# multiplicative tint retained in both the Blender scene and its web export.
wood_recolored=0
for m in list(bpy.data.materials):
    if not m.use_nodes:continue
    if m.name.startswith('Geum_v76_wood'):
        for n in m.node_tree.nodes:
            if n.type=='TEX_IMAGE':
                suffix=next((s for s in ['color','roughness','normal'] if s in n.image.name),'color');n.image=img('wood',suffix)
        rgb=tuple(m.diffuse_color[:3]);maximum=max(rgb)
        if rgb[0]>rgb[1]*1.45 and maximum>.08:
            tint(m,(rgb[0]*.98,rgb[1]*1.18,rgb[2]*1.15));wood_recolored+=1
    if any(t in m.name for t in ['dancheong','mat_3b7161','mat_528473','mat_3c7764','mat_467b68']):
        rgb=tuple(m.diffuse_color[:3]);mean=sum(rgb)/3;tint(m,tuple(v*.84+mean*.16 for v in rgb))

for ob in scene.objects:
    if ob.type!='MESH':continue
    if ob.name=='ground_geumseonggwan_boundary':
        m=material('Geum_v77_warm_mineral_courtyard','#cabc9f','earth');ob.data.materials.clear();ob.data.materials.append(m);uv(ob,.09)
    if ob.name=='photo_stone_walkway':
        for i,m in enumerate(ob.data.materials):
            replacement=m.copy();replacement.name='Geum_v77_paving_'+str(i);tint(replacement,col(['#afa58d','#bbb197','#a69c85','#c2b8a0'][i%4]));maps(replacement,'earth');ob.data.materials[i]=replacement
        uv(ob,.58);ob['no_shadow']=True
    if '_paper' in ob.name:
        for i,m in enumerate(ob.data.materials):
            replacement=material('Geum_v77_hanji_'+str(i)+'_'+ob.name,'#c8c5ae','paper');ob.data.materials[i]=replacement
        uv(ob,.5);ob['no_shadow']=True
    if any(t in ob.name for t in ['_diamond','stone_walkway_division','terrace_stone_joint','maroo_board_seam','floor_joint','coffer_frame','original_dancheong_flower']):ob['no_shadow']=True

green=material('Geum_v77_ikgong_green','#497562','wood');red=material('Geum_v77_ikgong_red','#85563e','wood');ochre=material('Geum_v77_ochre','#b5a071');cream=material('Geum_v77_cream','#c2c3a3');blue=material('Geum_v77_blue','#617e85');iron=material('Geum_v77_iron','#41433e');wood=material('Geum_v77_aged_timber','#815b41','wood')
class Builder:
    def __init__(self,name,mats):self.name=name;self.mats=mats;self.vertices=[];self.faces=[];self.indices=[]
    def polygon(self,points,faces,mat=0):
        start=len(self.vertices);self.vertices.extend(points);self.faces.extend(tuple(start+i for i in face) for face in faces);self.indices.extend([mat]*len(faces))
    def box(self,fr,x,y,z,w,h,d,mat=0):
        points=[fr.xyz(xx,yy,zz) for yy in [y-h/2,y+h/2] for xx,zz in [(x-w/2,z-d/2),(x+w/2,z-d/2),(x+w/2,z+d/2),(x-w/2,z+d/2)]]
        self.polygon(points,[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],mat)
    def tube(self,fr,a,b,r,mat=0,sides=7):
        a,b=Vector(fr.xyz(*a)),Vector(fr.xyz(*b));axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
        if u.length<.001:u=axis.cross(Vector((1,0,0)))
        u.normalize();v=axis.cross(u).normalized()
        vv=[tuple(p+r*(math.cos(i*math.tau/sides)*u+math.sin(i*math.tau/sides)*v)) for p in [a,b] for i in range(sides)]
        self.polygon(vv,[tuple(reversed(range(sides))),tuple(range(sides,2*sides))]+[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)],mat)
    def finish(self,smooth=False):
        data=bpy.data.meshes.new(self.name);data.from_pydata(self.vertices,[],self.faces);data.update()
        for m in self.mats:data.materials.append(m)
        for p,i in zip(data.polygons,self.indices):p.material_index=i;p.use_smooth=smooth
        bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
        ob=bpy.data.objects.new(self.name,data);scene.collection.objects.link(ob);ob['source_class']='Official structural description and photo-informed original detail; dimensions inferred';uv(ob)
        return ob

# Replace the straight block arms with three separated, profiled ikgong arms.
remove=[o for o in scene.objects if o.name.startswith(('hall_ikgong_','manghwaru_ikgong_'))]
bpy.data.batch_remove(remove)
arms=Builder('v77_ikgong_curved_arms',[green,red]);edging=Builder('v77_ikgong_painted_edges',[ochre,cream])
stations=[(f,x,z,6.16) for x in columns for z in [front-.16,back+.16]]
gf,gw,gd=frame('832423356');lo=.45;hi=gw-.45
stations.extend((gf,lo+(hi-lo)*i/3,z,6.54) for i in range(4) for z in [.85,gd-.85])
profile=[(-.93,-.03),(-.79,-.08),(-.40,-.08),(-.18,-.06),(.38,-.06),(.67,-.015),(.92,.15),(.93,.24),(.83,.245),(.76,.14),(.38,.055),(-.34,.045),(-.56,.10),(-.72,.20),(-.85,.21),(-.94,.09)]
for fr,x,z,y in stations:
    arms.box(fr,x,y-.17,z,.48,.23,.53,1)
    for tier in range(3):
        sy=y-.08+tier*.16;sz=1+tier*.1;thick=.18+tier*.055
        points=[fr.xyz(x+side*thick/2,sy+py,z+pz*sz) for side in [-1,1] for pz,py in profile];n=len(profile)
        arms.polygon(points,[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],tier%2)
        for side in [-1,1]:
            for (za,ya),(zb,yb) in zip(profile[8:15],profile[9:16]):
                edging.tube(fr,(x+side*(thick/2+.006),sy+ya-.026,z+za*sz),(x+side*(thick/2+.006),sy+yb-.026,z+zb*sz),.009,tier%2,5)
    arms.box(fr,x,y+.40,z,.65,.11,1.35,0)
arms.finish();edging.finish(True)

# Fine painted ribbons and leaf scrolls over the existing beam faces, no new walls.
paint=Builder('v77_morodancheong_scrolls',[ochre,cream,blue,red])
for a,b in zip(columns,columns[1:]):
    for side in [-1,1]:
        z=front-.184 if side==-1 else back+.184
        for cx in [a+.43,b-.43]:
            for mirror in [-1,1]:
                pts=[(cx+mirror*(.06+t*.22)*math.cos(t*5),5.72+.075*math.sin(t*5),z) for t in [i/16 for i in range(17)]]
                for p,q in zip(pts,pts[1:]):paint.tube(f,p,q,.009,0,5)
                paint.box(f,cx,5.72,z,.035,.07,.018,1)
paint.finish(True)['no_shadow']=True

# Recessed door fittings only on closed leaves; the central opening stays clear.
fittings=Builder('v77_door_iron_fittings',[iron])
for bay in [0,1,3,4]:
    a,b=columns[bay:bay+2];width=b-a-.48;count=2 if bay in [0,4] else 4
    for j in range(count):
        x=(a+b)/2-width/2+(j+.5)*width/count;handle=x+(-1 if j%2 else 1)*(width/count*.34)
        fittings.box(f,handle,2.08,front-.218,.06,.095,.019)
        for k in range(16):
            aa,bb=math.tau*k/16,math.tau*(k+1)/16
            fittings.tube(f,(handle+.05*math.cos(aa),2.02+.05*math.sin(aa),front-.235),(handle+.05*math.cos(bb),2.02+.05*math.sin(bb),front-.235),.007,0,5)
        for y in [1.54,3.84]:fittings.box(f,x-width/count/2+.035,y,front-.21,.058,.075,.018)
fittings.finish(True)

# Gentle bevels soften stone edges without changing the collision envelope.
beveled=[]
for ob in list(scene.objects):
    if ob.type=='MESH' and (ob.name.startswith(('walk-floor_step','walk-floor_terrace','inner_gate_stone_base','memorial_stele_plinth','hall-column_stone','hall-side-column_stone'))):
        bpy.context.view_layer.objects.active=ob
        bevel=ob.modifiers.new('v77 worn stone edges','BEVEL');bevel.width=.018;bevel.segments=2;bevel.limit_method='ANGLE'
        bpy.ops.object.modifier_apply(modifier=bevel.name);beveled.append(ob.name)

# Detail the lower side roofs that lacked separate barrel courses in v76.
hips=Builder('v77_hip_roof_barrel_courses',[bpy.data.materials['Geum_v76_barrel_tile_0'],bpy.data.materials['Geum_v76_barrel_tile_1']])
pts=ways['832423358'][:-1];project=lambda p:(p[0]-f.a[0])*f.u[0]+(p[1]-f.a[1])*f.u[1];rl,rr=sorted((project(pts[7]),project(pts[4])))
roofspec=[(f,c,10.74,rr-rl,21.48,6.55,3.60),(f,rl/2,7.4,rl,14.8,4.15,2.28),(f,(rr+fullwidth)/2,7.35,fullwidth-rr,14.7,4.55,2.48),(gf,gw/2,gd/2,gw+1.2,gd+1.15,6.88,2.60)]
for fr,cx,cz,w,d,eave,rise in roofspec:
    half=d/2;hip=d*.13
    def height(t,x):return eave+rise*t**1.35+.16*(1-t)**10+.28*abs(x/(w/2))**10
    for side in [-1,1]:
        for k in range(int(d/.32)+1):
            z=-half+d*k/int(d/.32)
            for row in range(7):
                t0=row/7;t1=(row+1)/7
                if abs(z)>half*(1-.58*t1):continue
                start=len(hips.vertices)
                vv=[]
                for t in [t0,t1+.008]:
                    x=side*(w/2-hip*t)
                    for q in range(6):
                        az=math.pi*q/5;zz=z+.062*math.cos(az);vv.append(fr.xyz(cx+x,height(.58*t,x)+.043+.062*math.sin(az),cz+zz))
                hips.polygon(vv,[(q,q+1,q+7,q+6) for q in range(5)],k%2)
hips.finish(True)

world['architectureViews']=[
    {'id':'hall-front','label':'정청 정면','center':f.view(c,3.8,6),'radius':50,'elevation':.13,'angle':math.atan2(f.v[0]*-1,f.v[1]*-1)},
    {'id':'eaves','label':'처마·공포','center':f.view(columns[1],6.1,front),'radius':10,'elevation':.035,'angle':math.atan2(-f.v[0],-f.v[1])-.28,'fov':35},
    {'id':'manghwaru','label':'망화루','center':gf.view(gw/2,3.9,gd/2),'radius':26,'elevation':.17,'angle':math.atan2(-gf.v[0],-gf.v[1])+.13}]
world['lighting']={'exposure':1.03,'ambient':1.9,'sun':2.1}
world['limitations'].append('v77 profiled ikgong silhouettes, painted scrolls, paper fibers, weathered timber and minor ironwork are photo-informed interpretations; collision envelopes and actual doorway openings are unchanged.')
world['detailVersion']='geumseonggwan-v77-20261003'
scene.view_settings.exposure=.4
bpy.ops.file.pack_all();blend=out/'geumseonggwan-v77.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))

# Web-only rounding to 0.1 mm lowers coordinate entropy; editable source remains
# at its full precision. Export shared 512px textures, not one baked map per tint.
for ob in scene.objects:
    if ob.type=='MESH':
        coords=np.empty(len(ob.data.vertices)*3,dtype=np.float32);ob.data.vertices.foreach_get('co',coords);coords=np.round(coords*10000)/10000;ob.data.vertices.foreach_set('co',coords);ob.data.update()
for im in bpy.data.images:
    if im.type=='IMAGE' and max(im.size)>512:im.scale(512,512)
target=out/'geumseonggwan-web-v77.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_active_scene=True,export_cameras=False,export_lights=False,export_extras=True,export_apply=True,export_image_format='WEBP',export_image_quality=87)
raw=target.read_bytes();length=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+length]);binary=raw[20+length:]
for m in gltf['materials']:
    original=bpy.data.materials.get(m.get('name',''))
    if original and original.name.startswith('Geum_v') and any(n.type=='TEX_IMAGE' for n in original.node_tree.nodes):m.setdefault('pbrMetallicRoughness',{})['baseColorFactor']=[min(1,v*1.22) for v in original.diffuse_color[:3]]+[1]
encoded=json.dumps(gltf,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary
packed=gzip.compress(raw,9,mtime=0)
if len(packed)>=25*1024*1024:raise RuntimeError('Web export exceeds hosting limit; do not publish it.')
for name,data in [('geumseonggwan.glb',raw),('geumseonggwan.glb.gz',packed)]:
    temp=root/'public/models'/('v77-'+name+'.tmp');temp.write_bytes(data);temp.replace(root/'public/models'/name)
(root/'public/city-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
metrics={'source':str(source.relative_to(root)),'sourceSHA256':source_hash,'sourceUnchanged':hashlib.sha256(source.read_bytes()).hexdigest()==source_hash,'editableBlend':str(blend.relative_to(root)),'ikgongStations':len(stations),'beveledStoneGroups':beveled,'objects':len(scene.objects),'triangles':sum(gltf['accessors'][p['indices']]['count']//3 for m in gltf['meshes'] for p in m['primitives']),'rawBytes':len(raw),'gzipBytes':len(packed),'textureImages':len(gltf['images']),'webCoordinatePrecisionMeters':.0001,'collisionUnchanged':world['solids']==json.loads(backup.read_text(encoding='utf-8'))['solids']}
(out/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
print('GEUMSEONGGWAN_V77_COMPLETE',json.dumps(metrics,ensure_ascii=False),flush=True)
