"""Author overview relief in Blender; preserve original indices, palette and distant city.

Only changed vertex/normal streams are exported. The original static transport
layout remains intact so apartment facade data and mapped city topology survive.
"""
import bpy, json, struct, gzip, math, sys, hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from bitgaram_terrain_v89 import Terrain
O=R/'outputs/relief-v96';O.mkdir(parents=True,exist_ok=True)
K=R/'knowledge/sources/observatory-relief-v96'
target=O/'bitgaram-overview-relief-v96.blend'
if target.exists():raise RuntimeError('Preserve artist revision')
w=json.loads((R/'public/bitgaram-park-world.json').read_text(encoding='utf8'))
T=Terrain(next(s['footprint'] for s in w['solids'] if s['name']=='photo_exhibition_shell'))
du,dl=T.upper-16,T.lower-6.22
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
report=dict(revision='overview-relief-v96',upperMetres=T.upper,lowerMetres=T.lower,
    previousUpperMetres=16,terrain='knowledge/sources/bitgaram/terrain-v89/native-surface-grid.json',parts=[])
def oldhill(x,z):return min(16*math.exp(-((x/100)**2+(z/105)**2)*1.6),15.75)
def sample_shift(x,z):return T.ground(x,z)-oldhill(x,z)
materials={}
def material(g,i):
    src=g['materials'][i];name=src.get('name',str(i))
    if name in materials:return materials[name]
    m=bpy.data.materials.new(name);m.diffuse_color=src.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1]);m.use_nodes=True
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=.85
    materials[name]=m;return m
def decode(g,bin,index):
    a=g['accessors'][index];v=g['bufferViews'][a['bufferView']]
    dtype={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
    count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];size=np.dtype(dtype).itemsize
    arr=np.ndarray((a['count'],count),dtype=dtype,buffer=bin,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',size*count),size)).astype(np.float64)
    if a.get('normalized'):
        scale={5120:127,5121:255,5122:32767,5123:65535}[a['componentType']];arr=np.maximum(-1,arr/scale)
    return arr
def add_stream(g,bin,arr,kind,ctype=5126,normalized=False):
    bin.extend(b'\0'*((-len(bin))%4));offset=len(bin);raw=arr.astype('<f4' if ctype==5126 else 'i1').tobytes();bin.extend(raw)
    vi=len(g['bufferViews']);g['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=len(raw),target=34962))
    a=dict(bufferView=vi,componentType=ctype,count=len(arr),type=kind)
    if normalized:a['normalized']=True
    if kind=='VEC3' and ctype==5126:a.update(min=arr.min(axis=0).tolist(),max=arr.max(axis=0).tolist())
    index=len(g['accessors']);g['accessors'].append(a);return index
def components(faces,n):
    parent=np.arange(n,dtype=np.int32)
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for a,b,c in faces:
        ra=root(int(a));rb=root(int(b));rc=root(int(c));parent[rb]=ra;parent[rc]=ra
    groups={}
    for i in range(n):groups.setdefault(root(i),[]).append(i)
    return groups.values()
for key in ['bitgaram-overview','bitgaram-overview-part2']:
    path=R/'public/models'/(key+'.glb');source=path.read_bytes();(O/(key+'-before.glb')).write_bytes(source)
    n=struct.unpack_from('<I',source,12)[0];g=json.loads(source[20:20+n]);binary=bytearray(source[28+n:]);changed=[]
    for ni,node in enumerate(g['nodes']):
        if 'mesh' not in node:continue
        name=node.get('name','');matrix=np.array(node.get('matrix',np.eye(4).T.ravel().tolist())).reshape(4,4).T
        changed_node=False
        for pi,prim in enumerate(g['meshes'][node['mesh']]['primitives']):
            pos=decode(g,binary,prim['attributes']['POSITION']);world=np.c_[pos,np.ones(len(pos))]@matrix.T;world=world[:,:3]
            faces=decode(g,binary,prim['indices']).astype(np.int32).reshape(-1,3)
            after=world.copy();radius=np.hypot(world[:,0],world[:,2]);affected=False
            if name=='estimated_hill':
                for i,(x,y,z) in enumerate(world):after[i,1]=T.ground(x,z)+.02
                affected=True
            elif name=='ground_floor_summit' or name.startswith(('tower_','aerial_','ground_floor_observatory','entry_sign','photo_entry','lift_door')):
                after[:,1]+=du;affected=True
            elif name.startswith(('photo_exhibition','roof_garden','context_roof_garden')):
                after[:,1]+=dl;affected=True
            elif name.startswith('surrounding_mapped_paths'):
                for i,(x,y,z) in enumerate(world):
                    if math.hypot(x,z)<240:after[i,1]+=T.ground(x,z)-(oldhill(x,z) if y>.2 else 0)
                affected=bool(np.max(np.abs(after-world))>.001)
            elif name.startswith(('overview_batch_Museum_','surrounding_recreation')):
                # A batched object contains independent trees/fittings and distant
                # buildings. Move each connected piece rigidly, retaining tree height.
                if radius.min()<180:
                    for ids in components(faces,len(world)):
                        pts=world[ids];x,y,z=pts.mean(axis=0);r=math.hypot(x,z)
                        if r>165 or np.ptp(pts[:,0])>160 or np.ptp(pts[:,2])>160:continue
                        shift=du if r<26 else dl if 90<z<150 and abs(x)<40 else sample_shift(x,z)
                        after[ids,1]+=shift
                    affected=bool(np.max(np.abs(after-world))>.001)
            # Store all displayed geometry in an editable Blender review file.
            mesh=bpy.data.meshes.new(f'{key}:{name}:{pi}');mesh.from_pydata([(x,-z,y) for x,y,z in after],[],faces.tolist());mesh.update()
            ob=bpy.data.objects.new(f'{key}:{name}:{pi}',mesh);scene.collection.objects.link(ob)
            mesh.materials.append(material(g,prim['material']))
            if 'COLOR_0' in prim['attributes']:
                colors=decode(g,binary,prim['attributes']['COLOR_0'])
                if colors.shape[1]==3:colors=np.c_[colors,np.ones(len(colors))]
                layer=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
                layer.data.foreach_set('color',colors.astype(np.float32).ravel())
                mat=mesh.materials[0].copy();mesh.materials[0]=mat
                bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
                vertex=mat.node_tree.nodes.new('ShaderNodeVertexColor');vertex.layer_name='Color'
                mix=mat.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
                mix.inputs[2].default_value=mat.diffuse_color
                mat.node_tree.links.new(vertex.outputs['Color'],mix.inputs[1]);mat.node_tree.links.new(mix.outputs[0],bs.inputs['Base Color'])
            for p in mesh.polygons:p.use_smooth=True
            if affected:
                # Recalculate relief normals through Blender; constant translated
                # objects retain original authored normals transformed to world space.
                norms=decode(g,binary,prim['attributes']['NORMAL'])@matrix[:3,:3].T
                norms/=np.maximum(np.linalg.norm(norms,axis=1,keepdims=True),1e-12)
                if name=='estimated_hill':
                    norms=np.array([(v.normal.x,v.normal.z,-v.normal.y) for v in mesh.vertices])
                prim['attributes']['POSITION']=add_stream(g,binary,after,'VEC3')
                # BYTE VEC3 requires 4-byte aligned rows.
                packed=np.zeros((len(norms),4),dtype=np.int8);packed[:,:3]=np.rint(norms*127).clip(-127,127)
                ai=add_stream(g,binary,packed,'VEC3',5120,True);g['bufferViews'][g['accessors'][ai]['bufferView']]['byteStride']=4
                prim['attributes']['NORMAL']=ai;changed_node=True
        if changed_node:
            node.pop('matrix',None);node.pop('translation',None);node.pop('rotation',None);node.pop('scale',None)
            node['extras']={**node.get('extras',{}),'relief_revision':'v96','surveyed_bare_earth':False};changed.append(name)
    binary.extend(b'\0'*((-len(binary))%4));g['buffers'][0]['byteLength']=len(binary)
    encoded=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
    raw=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(binary),b'BIN\0')+binary
    (O/(key+'-v96.glb')).write_bytes(raw)
    report['parts'].append(dict(key=key,changedNodes=changed,sourceSha256=hashlib.sha256(source).hexdigest(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
    print('AUTHORED',key,len(changed),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(target))
code=(R/'scripts/pack_overview_relief_v96.py').read_text(encoding='utf8')
exec(compile(code,str(R/'scripts/pack_overview_relief_v96.py'),'exec'),{'__file__':str(R/'scripts/pack_overview_relief_v96.py')})
print('OVERVIEW_RELIEF_COMPLETE',flush=True)
