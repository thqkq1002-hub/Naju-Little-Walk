"""Refine a COPY of the authored colored scene. Never rebuild or overwrite the source .blend."""
import bpy,math,json,gzip,random,shutil,struct,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/geumseonggwan-exclusive-v76'
SOURCE=ROOT/'outputs/palette-v51/geumseonggwan-color-v51.blend'
OUT.mkdir(parents=True,exist_ok=True)
backup=OUT/'city-world-before.json'
if not backup.exists():shutil.copy2(ROOT/'public/city-world.json',backup)
world=json.loads(backup.read_text(encoding='utf-8'))
boundary=world['surroundings']['precinctBoundary']
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene

def inside(x,z):
    odd=False
    for (ax,az),(bx,bz) in zip(boundary,boundary[1:]+boundary[:1]):
        if (az>z)!=(bz>z) and x<(bx-ax)*(z-az)/(bz-az)+ax:odd=not odd
        dx,dz=bx-ax,bz-az;t=max(0,min(1,((x-ax)*dx+(z-az)*dz)/max(dx*dx+dz*dz,1e-9)))
        if math.hypot(x-ax-t*dx,z-az-t*dz)<.8:return True
    return odd
def center(ob):
    vv=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    return Vector(tuple((min(v[i] for v in vv)+max(v[i] for v in vv))/2 for i in range(3)))
exclude=('context_','osm-building_','roof-cap_','road_','road-edge','street_','parking_','parked_','vehicle_','entry_granite','entrance_roadside','walk-floor_front_apron')
remove=[]
for ob in list(scene.objects):
    c=center(ob)
    if ob.type!='MESH' or ob.name.startswith(exclude) or not inside(c.x,-c.y) or ob.name.startswith(('lawn_fine_grass','photo-tree_fine_foliage','photo-tree_trunk_stone')):remove.append(ob)
    elif max(ob.dimensions.x,ob.dimensions.y)>180:remove.append(ob)
bpy.data.batch_remove(remove)
print('PRECINCT_ONLY',len(scene.objects),'removed',len(remove),flush=True)

def linear(c):return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)
def color(hex):return linear(tuple(int(hex.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)))
materials={};images={}
def mat(name,col,kind=None):
    key=(name,tuple(col),kind)
    if key in materials:return materials[key]
    m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*col,1);m.diffuse_color=(*col,1);bs.inputs['Roughness'].default_value=.86
    if kind:
        for suffix,input_name in [('color','Base Color'),('roughness','Roughness'),('normal','Normal')]:
            file=ROOT/f'assets/geumseonggwan-v76/materials/{kind}-{suffix}.png'
            key_img=str(file)
            if key_img not in images:
                image=bpy.data.images.load(str(file));image.colorspace_settings.name='sRGB' if suffix=='color' else 'Non-Color';images[key_img]=image
            node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=images[key_img]
            if suffix=='color':
                tint=m.node_tree.nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1
                tint.inputs[2].default_value=(*tuple(min(1,v*1.22) for v in col),1)
                m.node_tree.links.new(node.outputs['Color'],tint.inputs[1]);m.node_tree.links.new(tint.outputs['Color'],bs.inputs['Base Color'])
            if suffix=='normal':
                normal=m.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.35
                m.node_tree.links.new(node.outputs['Color'],normal.inputs['Color']);m.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
            elif suffix!='color':m.node_tree.links.new(node.outputs['Color'],bs.inputs[input_name])
    materials[key]=m;return m
def uv(ob,kind):
    mesh=ob.data;layer=mesh.uv_layers.new(name='HeritageUV_v76') if not mesh.uv_layers else mesh.uv_layers.active
    is_wood=kind=='wood';scale=.75 if is_wood else .9 if kind=='stone' else .42
    vv=[ob.matrix_world@v.co for v in mesh.vertices]
    dims=ob.dimensions
    long_axis=max(range(3),key=lambda i:dims[i]);other=0 if long_axis==2 else 2
    values=[]
    for p in mesh.polygons:
        normal=ob.matrix_world.to_3x3()@p.normal;dominant=max(range(3),key=lambda i:abs(normal[i]));axes=[i for i in range(3) if i!=dominant]
        if is_wood:axes=[other,long_axis]
        for loop in p.loop_indices:
            v=vv[mesh.loops[loop].vertex_index];values.extend((v[axes[0]]*scale,v[axes[1]]*scale))
    layer.data.foreach_set('uv',values)
def mesh(name,verts,faces,mats,smooth=False):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob)
    for m in mats:data.materials.append(m)
    for p in data.polygons:p.use_smooth=smooth
    ob['source_class']='Photo-informed original detail; unmeasured dimensions'
    return ob

# Keep existing colors and architectural geometry, add original physical material maps.
for ob in list(scene.objects):
    name=ob.name
    kind='tile' if name.startswith(('roof_','precinct_coping','precinct_pitched')) else 'stone' if any(t in name for t in ('stone','rubble','terrace','step','stele','plinth')) else 'grass' if 'lawn' in name else 'earth' if name.startswith(('ground_geum','ground_floor_stele_bed')) else 'wood' if any(t in name for t in ('column','maroo','plank','stile','timber','rafter','beam','post','tree_trunk','tree_spreading_branch')) else None
    if not kind:continue
    for i,old in enumerate(list(ob.data.materials)):
        if old:ob.data.materials[i]=mat('Geum_v76_'+kind+'_'+old.name,tuple(old.diffuse_color[:3]),kind)
    uv(ob,kind)

# A zero-height walkable floor constrains visitors to the real mapped precinct.
if not any(o.name=='ground_geumseonggwan_boundary' for o in scene.objects):
    mesh('ground_geumseonggwan_boundary',[(x,-z,.022) for x,z in boundary],[tuple(range(len(boundary)))],[mat('Geum_v76_courtyard',color('#c8b997'),'earth')])
    uv(bpy.data.objects['ground_geumseonggwan_boundary'],'earth')

lat,lon=world['origin']['lat'],world['origin']['lon'];mx=111320*math.cos(math.radians(lat))
xml=ET.parse(ROOT/'knowledge/sources/geumseonggwan.osm').getroot()
nodes={n.attrib['id']:((float(n.attrib['lon'])-lon)*mx,-(float(n.attrib['lat'])-lat)*111320) for n in xml.findall('node')}
ways={w.attrib['id']:[nodes[n.attrib['ref']] for n in w.findall('nd')] for w in xml.findall('way')}
class Frame:
    def __init__(self,origin,u):self.origin=origin;self.u=u;self.v=(u[1],-u[0])
    def point(self,x,z):return self.origin[0]+self.u[0]*x+self.v[0]*z,self.origin[1]+self.u[1]*x+self.v[1]*z
    def xyz(self,x,y,z):
        wx,wz=self.point(x,z);return wx,-wz,y
def frame_way(id):
    pts=ways[id][:-1];a,b=pts[1:3];w=math.dist(a,b)
    return Frame(a,((b[0]-a[0])/w,(b[1]-a[1])/w)),w,math.dist(pts[0],a)
f,fullwidth,_=frame_way('832423358');info=world['architecture'];c=info['center'];lo,hi=info['lo'],info['hi']
pts=ways['832423358'][:-1]
proj=lambda p:(p[0]-f.origin[0])*f.u[0]+(p[1]-f.origin[1])*f.u[1]
roof_left,roof_right=sorted((proj(pts[7]),proj(pts[4])))

tile_mats=[mat('Geum_v76_barrel_tile_'+str(i),color(v),'tile') for i,v in enumerate(['#535550','#60625c','#494e4d','#747569','#585e54'])]
def roof_caps(frame,name,cx,cz,width,depth,eave,rise,paljak=True):
    verts=[];faces=[];rng=random.Random(name);hip=depth*.13 if paljak else 0
    def y(t,x):return eave+rise*t**1.35+.16*(1-t)**10+.28*abs(x/(width/2))**10
    rows=max(14,int(depth/2/.43));columns=max(24,int(width/.31))
    for side in (-1,1):
        for row in range(rows):
            t0=row/rows;t1=(row+1)/rows;span=width/2-hip*min(t0/.58,1)
            for col in range(columns+1):
                x=-width/2+width*col/columns
                if abs(x)>span-.015:continue
                start=len(verts);r=.069+rng.uniform(-.005,.005)
                for t in (t0,min(1,t1+.012)):
                    for a in range(7):
                        angle=math.pi*a/6;xx=x+r*math.cos(angle)
                        verts.append(frame.xyz(cx+xx,y(t,xx)+.015+r*math.sin(angle),cz+side*depth/2*(1-t)))
                for a in range(6):faces.append((start+a,start+a+1,start+a+8,start+a+7))
    ob=mesh(name,verts,faces,tile_mats,True)
    for p in ob.data.polygons:p.material_index=rng.choices(range(5),[.45,.18,.2,.06,.11])[0]
    uv(ob,'tile')
roof_caps(f,'v76_main_overlapping_barrel_tiles',c,10.74,roof_right-roof_left,21.48,6.55,3.6)
roof_caps(f,'v76_west_wing_barrel_tiles',roof_left/2,7.4,roof_left,14.8,4.15,2.28)
roof_caps(f,'v76_east_wing_barrel_tiles',(roof_right+fullwidth)/2,7.35,fullwidth-roof_right,14.7,4.55,2.48)
for id,name,eave,rise,paljak in [('832423356','v76_manghwaru_barrel_tiles',6.88,2.60,True),('832423357','v76_middle_gate_barrel_tiles',3.38,1.62,False)]:
    gf,w,d=frame_way(id);roof_caps(gf,name,w/2,d/2,w+1.2,d+1.15,eave,rise,paljak)
print('ROOF_TILE_DETAIL_COMPLETE',flush=True)

# Painted motifs are original interpretations of the color rhythm seen in photographs.
paint=[mat('Geum_v76_dancheong_'+str(i),color(v)) for i,v in enumerate(['#b99155','#bdc3a0','#7a4431','#347565','#476c79'])]
verts=[];faces=[];indices=[]
def flower(frame,x,y,z,size):
    for petal in range(8):
        a=petal*math.tau/8;start=len(verts)
        for k in range(12):
            t=math.tau*k/12;u=size*(.36+.3*math.cos(t));v=size*.14*math.sin(t)
            verts.append(frame.xyz(x+u*math.cos(a)-v*math.sin(a),y+u*math.sin(a)+v*math.cos(a),z))
        faces.append(tuple(range(start,start+12)));indices.append(1 if petal%2 else 0)
for i in range(5):
    a,b=info['columns'][i:i+2]
    for j in range(4):flower(f,a+(j+.5)*(b-a)/4,5.72,info['front']-.182,.19)
for id in ['832423356','832423357']:
    gf,w,d=frame_way(id)
    for j in range(max(6,int(w/.85))):flower(gf,.8+(w-1.6)*(j+.5)/max(6,int(w/.85)),6.40 if id=='832423356' else 2.90,.707,.16)
ob=mesh('v76_original_dancheong_flower_bands',verts,faces,paint)
for p,i in zip(ob.data.polygons,indices):p.material_index=i

# Replace repeated round clumps with individually shaped, layered leaf silhouettes.
foliage=[mat('Geum_v76_leaf_'+str(i),color(v)) for i,v in enumerate(['#486338','#5d7543','#6d854c','#39572f','#7a9054'])]
rng=random.Random(7610);leafverts=[];leaffaces=[]
trunks=[o for o in scene.objects if o.name.startswith('photo-tree_trunk')]
centers=[center(t) for t in trunks]
orphan_branches=[o for o in scene.objects if o.name.startswith('tree_spreading_branch') and min((math.hypot(center(o).x-t.x,center(o).y-t.y) for t in centers),default=999)>5]
bpy.data.batch_remove(orphan_branches)
for trunk in trunks:
    p=center(trunk);height=trunk.dimensions.z/.56;radius=max(3,height*.30)
    for j in range(6500):
        a=rng.random()*math.tau;rr=radius*math.sqrt(rng.random());zoff=rng.uniform(-1,1)
        lobe=1+.10*math.sin(3*a)+.06*math.cos(5*a)
        pos=Vector((p.x+rr*lobe*math.cos(a),p.y+rr*lobe*math.sin(a),height*.78+height*.27*zoff*math.sqrt(max(.06,1-(rr/radius)**2))))
        az=rng.random()*math.tau;pitch=rng.uniform(-.75,.75)
        axis=Vector((math.cos(az)*math.cos(pitch),math.sin(az)*math.cos(pitch),math.sin(pitch)))
        across=Vector((-math.sin(az),math.cos(az),rng.uniform(-.16,.16))).normalized()
        length=rng.uniform(.26,.46);width=length*rng.uniform(.27,.43);start=len(leafverts)
        for v in (pos-axis*length*.5,pos-across*width,pos+Vector((0,0,.028)),pos+across*width,pos+axis*length*.5):leafverts.append(tuple(v))
        leaffaces.extend([(start,start+1,start+2),(start+1,start+4,start+2),(start+4,start+3,start+2),(start+3,start,start+2)])
if leafverts:
    ob=mesh('v76_layered_tree_leaf_canopies',leafverts,leaffaces,foliage,True)
    polygons=list(ob.data.polygons)
    for i in range(0,len(polygons),4):
        shade=rng.choices(range(5),[.30,.30,.17,.18,.05])[0]
        for p in polygons[i:i+4]:p.material_index=shade

# Group repeated structural parts while retaining named architectural landmarks.
preserve=lambda name:name.startswith(('v76_','roof_832423358','roof_west_wing','roof_east_wing','roof_832423356','roof_832423357')) and not any(k in name for k in ('_tile_end','_lower_rafter','_upper_rafter','_ridge','_course','_gable_board','_eave_fascia')) or name.split('.')[0]=='hall_inner_tall_column'
groups=defaultdict(list)
for ob in list(scene.objects):
    if not preserve(ob.name):groups[ob.name.split('.')[0]].append(ob)
for name,objects in groups.items():
    if len(objects)<2:continue
    verts=[];faces=[];mats=[];material_lookup={};indices=[];uvs=[];smooth=[]
    for ob in objects:
        offset=len(verts);verts.extend(tuple(ob.matrix_world@v.co) for v in ob.data.vertices)
        has_uv=bool(ob.data.uv_layers);layer=ob.data.uv_layers.active.data if has_uv else None
        local=[]
        for m in ob.data.materials:
            if m.name not in material_lookup:material_lookup[m.name]=len(mats);mats.append(m)
            local.append(material_lookup[m.name])
        for p in ob.data.polygons:
            faces.append(tuple(offset+i for i in p.vertices));indices.append(local[p.material_index]);smooth.append(p.use_smooth);uvs.extend(tuple(layer[i].uv) if layer else (0,0) for i in p.loop_indices)
    bpy.data.batch_remove(objects)
    ob=mesh(name,verts,faces,mats,False)
    for p,i,s in zip(ob.data.polygons,indices,smooth):p.material_index=i;p.use_smooth=s
    layer=ob.data.uv_layers.new(name='HeritageUV_v76');layer.data.foreach_set('uv',[v for pair in uvs for v in pair])
print('REPEATED_PARTS_GROUPED',len(scene.objects),flush=True)

# Preserve the map roof outlines and synchronize navigation with the dedicated scene.
def solid_center(s):
    if 'footprint' in s:
        pts=s['footprint'];return sum(p[0] for p in pts)/len(pts)+s['position'][0],sum(p[1] for p in pts)/len(pts)+s['position'][2]
    return s['position'][0],s['position'][2]
world['solids']=[s for s in world['solids'] if not s['name'].startswith(exclude) and inside(*solid_center(s))]
world['solids'].append({'name':'ground_floor_precinct_v76','kind':'building','position':[0,-.025,0],'size':[1,.025,1],'footprint':boundary,'color':'#c8b997','collision':False})
world['bounds']=[min(p[0] for p in boundary)-1,max(p[0] for p in boundary)+1,min(p[1] for p in boundary)-1,max(p[1] for p in boundary)+1]
world['title']='금성관 산책';world['subtitle']='정청 · 익헌 · 망화루 · 경내 산책'
world['verticalNavigation']=True;world['requireFloor']=True
world['places']=[p for p in world['places'] if p['id'] in ['interior','hall','832423356','832423357','gate-lawn']]
for p in world['places']:
    if p['id']=='interior':p['arrivalHeight']=.99
for id,name,x,z in [('west-wing','서익헌 앞',7,-2),('east-wing','동익헌 앞',49,-2),('stele','경내 비석',-1,-80)]:
    wx,wz=f.point(x,z);world['places'].append({'id':id,'name':name,'position':[wx,wz],'arrival':[wx,wz],'radius':6,'description':'금성관 경내의 산책 지점입니다.'})
world['buildings']=[b for b in world['buildings'] if b['osm_id'] in ['832423358','832423356','832423357']]
world['surroundings']['roofObservations']=[];world['surroundings']['entranceRoute']=[]
world['portals']=[];world['sceneLinks']=[]
world['lighting']={'exposure':1.07,'ambient':1.65,'sun':2.5}
world['limitations']=['OSM footprints locate the historic hall, Manghwaru, middle gate and precinct boundary; height and ornamental dimensions are estimates.','The 2009 AKS exterior photographs and official heritage descriptions inform roof forms, timber colors and architectural details; vegetation and current paint condition may differ.','Dedicated Geumseonggwan edition v76 excludes roads, parking and surrounding buildings.','Roof overlaps, original painted floral bands, material maps and individual summer leaves are photo-informed interpretations, not photogrammetry or exact surveyed decorations.']
(ROOT/'public/city-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

scene.unit_settings.system='METRIC'
light=bpy.data.lights.new('Geumseonggwan daylight','SUN');light.energy=2.4;light.angle=.12
sun=bpy.data.objects.new('Geumseonggwan daylight',light);scene.collection.objects.link(sun);sun.rotation_euler=(.6,-.4,-.6)
scene.world=bpy.data.worlds.new('Geumseonggwan sky');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.72,.82,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
cam=bpy.data.objects.new('Geumseonggwan camera',bpy.data.cameras.new('Geumseonggwan camera'));scene.collection.objects.link(cam);scene.camera=cam
cam.location=(45,-145,125);cam.rotation_euler=(Vector((-10,27,0))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=200
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.4
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'geumseonggwan-exclusive-v76.blend'))
# Preserve full editable maps in the new blend; downsample only this web export.
for im in images.values():
    im.scale(512,512)
target=OUT/'geumseonggwan-web-v76.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_active_scene=True,export_cameras=False,export_lights=False,export_extras=True,export_apply=True,export_image_format='WEBP',export_image_quality=82)
# Keep Blender's constant texture tint in glTF without baking duplicate images.
raw=target.read_bytes();jsonlen=struct.unpack_from('<I',raw,12)[0]
gltf=json.loads(raw[20:20+jsonlen]);binary=raw[20+jsonlen:]
for material in gltf['materials']:
    source=bpy.data.materials.get(material.get('name',''))
    if source and source.name.startswith('Geum_v76_') and any(n.type=='TEX_IMAGE' for n in source.node_tree.nodes):
        material.setdefault('pbrMetallicRoughness',{})['baseColorFactor']=[min(1,v*1.22) for v in source.diffuse_color[:3]]+[1]
encoded=json.dumps(gltf,separators=(',',':'),ensure_ascii=False).encode('utf-8');encoded+=b' '*((-len(encoded))%4)
raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary
target.write_bytes(raw)
public=ROOT/'public/models/geumseonggwan.glb'
raw_temp=public.with_suffix('.glb.tmp');raw_temp.write_bytes(raw);raw_temp.replace(public)
packed=public.with_suffix('.glb.gz');temporary=public.with_suffix('.glb.gz.tmp')
temporary.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0));temporary.replace(packed)
metrics={'sourceBlend':str(SOURCE),'outputBlend':str(OUT/'geumseonggwan-exclusive-v76.blend'),'objects':len(scene.objects),'removedObjects':len(remove),'trees':len(trunks),'roofTileDetailMeshes':5,'webBytes':public.stat().st_size,'compressedBytes':packed.stat().st_size,'boundary':boundary,'originalTextureMaps':15,'webTextureResolution':512,'webTextureFormat':'WebP quality 82'}
(ROOT/'knowledge/sources/geumseonggwan-v76/metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
print('EXCLUSIVE_GEUMSEONGGWAN_COMPLETE',json.dumps(metrics,ensure_ascii=False),flush=True)
