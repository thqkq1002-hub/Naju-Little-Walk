"""Blender-authored palette revision; transfer material values without repacking geometry.

The original GLB BIN chunk, nodes, animation and texture records remain byte-identical.
Editable full-scene .blend revisions and material-only glTF exports accompany the pass.
"""
import bpy,json,struct,colorsys,hashlib,gzip,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/palette-v51';O.mkdir(exist_ok=True)
W=R/'work/palette-v51';W.mkdir(parents=True,exist_ok=True)
S=R/'knowledge/sources/palette-v51';S.mkdir(parents=True,exist_ok=True)
def srgb(c):return 12.92*c if c<=.0031308 else 1.055*c**(1/2.4)-.055
def linear(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def readglb(b):
 n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[20+n:]
def output(b,d):
 original,tail=readglb(b);j=json.dumps(d,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
 return struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail
def tone(rgb):
 h,s,v=colorsys.rgb_to_hsv(*[srgb(c) for c in rgb]);family='neutral'
 if .16<h<.46 and s>.19:
  h=h*.84+.33*.16;s=min(.78,s*1.15);v*=.94;family='foliage'
 elif .46<=h<.67 and s>.13:
  s=min(.62,s*1.22);v*=.94;family='water_glass'
 elif .025<h<.16 and s>.18:
  s=min(.69,s*1.09);v*=.985;family='earth_timber'
 elif s<.18 and .18<v<.92:
  h=.108 if v>.68 else .56;s=max(s,.055 if v>.68 else .065);v*=.985
 return [linear(c) for c in colorsys.hsv_to_rgb(h,s,v)],family
stats=[]
files=sorted((R/'public/models').glob('*.glb'))
for path in files:
 if path.stem=='deudeulgang':continue
 target=O/(path.stem+'-color-v51.blend')
 if target.exists():
  print('Preserved completed revision',path.stem,flush=True);continue
 original=path.read_bytes();backup=W/path.name
 if backup.exists():raise RuntimeError('Unexpected prior backup: '+str(backup))
 backup.write_bytes(original);d,tail=readglb(original)
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(path));scene=bpy.context.scene;changes=[];protected=[]
 for i,m in enumerate(d.get('materials',[])):
  p=m.get('pbrMetallicRoughness',{});name=m.get('name','');mat=bpy.data.materials.get(name)
  # Printed exhibitions, foliage textures, the panorama and transparent panes keep their originals.
  if not mat or 'baseColorTexture' in p or m.get('alphaMode','OPAQUE')!='OPAQUE' or 'KHR_materials_unlit' in m.get('extensions',{}) or any(m.get('emissiveFactor',[0,0,0])):
   protected.append(name);continue
  bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if not bs or bs.inputs['Base Color'].is_linked:protected.append(name);continue
  before=list(bs.inputs['Base Color'].default_value);after,family=tone(before[:3]);after+=[before[3]]
  if max(abs(a-b) for a,b in zip(before,after))<.0001:continue
  bs.inputs['Base Color'].default_value=after;mat.diffuse_color=after
  changes.append(dict(index=i,name=name,before=p.get('baseColorFactor',[1,1,1,1]),after=list(bs.inputs['Base Color'].default_value),family=family))
 # Save complete editable imported scene; earlier artist .blend files are untouched.
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
 # Blender glTF exporter authors the material PBR values. A small palette mesh avoids
 # rewriting quantized geometry, external images, animation or custom scene metadata.
 for o in scene.objects:o.select_set(False)
 mesh=bpy.data.meshes.new('Palette_export');verts=[];faces=[]
 for c in changes:
  n=len(verts);verts.extend([(0,0,0),(1,0,0),(0,1,0)]);faces.append((n,n+1,n+2));mesh.materials.append(bpy.data.materials[c['name']])
 mesh.from_pydata(verts,[],faces)
 for i,p in enumerate(mesh.polygons):p.material_index=i
 o=bpy.data.objects.new('Palette_export',mesh);scene.collection.objects.link(o);o.select_set(True)
 tmp=W/(path.stem+'-materials.glb')
 bpy.ops.export_scene.gltf(filepath=str(tmp),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
 exported,_=readglb(tmp.read_bytes());byname={m['name']:m for m in exported['materials']}
 for c in changes:
  value=byname[c['name']].get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1])
  d['materials'][c['index']].setdefault('pbrMetallicRoughness',{})['baseColorFactor']=value;c['after']=value
 final=output(original,d);assert readglb(final)[1]==tail
 path.write_bytes(final)
 if Path(str(path)+'.gz').exists():
  with gzip.open(str(path)+'.gz','wb',compresslevel=9) as f:f.write(final)
 audit=dict(model=path.name,changes=changes,protected=protected,binary_sha256=hashlib.sha256(tail).hexdigest(),original_bytes=len(original),final_bytes=len(final))
 (S/(path.stem+'.json')).write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
 stats.append(dict(model=path.name,changed=len(changes),protected=len(protected)))
 print('PALETTE COMPLETE',path.name,len(changes),'materials',flush=True)
(S/'summary.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
