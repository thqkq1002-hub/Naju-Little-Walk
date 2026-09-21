"""Lightweight, opaque west-bank woodland, intended only as a scenic backdrop.
Preserves the authored walking grove and all existing collision boundaries.
"""
import bpy,sys,math,json,gzip,struct
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from museum_geometry import MuseumGeometry
O=R/'outputs/deudeulgang';target=O/'deudeulgang-pine-grove-v55-finished.blend'
if target.exists():raise RuntimeError('Existing editable revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(O/'deudeulgang-pine-grove-v54.blend'));scene=bpy.context.scene
g=MuseumGeometry(scene,(0,0),0)
for m in bpy.data.materials:
 if len(m.name)==13 and m.name.startswith('Museum_'):g.materials['#'+m.name[7:]]=m
remove=[o for o in scene.objects if o.name.startswith(('west_bank_background_pine','estimated_continuous_west_ridge'))]
bpy.data.batch_remove(ids=remove)
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def height(x,z):
 d=-x-194;edge=smooth(d/160)
 peaks=36+22*math.exp(-((z+220)/200)**2)+31*math.exp(-((z-270)/260)**2)
 rolls=5*math.sin(z/99+x/180)+2.5*math.cos(z/43-x/81)
 rear=1-smooth((d-400)/310)
 ends=1-smooth((abs(z)-585)/240)
 # A shallow organic canopy envelope avoids separate rock-like crown blobs.
 leaves=1.7*math.sin(x*.71+math.sin(z*.28))*math.cos(z*.61)+.8*math.sin(x*1.51+z*.84)
 shore=math.exp(-((x+212)/10)**2)*(2.8+.8*math.sin(z*.63)+.5*math.cos(z*.23))
 return .15+ends*(edge*rear*(peaks+rolls+leaves)+shore)
def backdrop(o):
 o['background_only']=True;o['no_shadow']=True;o['no_receive_shadow']=True
 return o
# One packed, original AI-created forest texture. The referenced real photos are
# never embedded; this is visual scenery, not surveyed forest or photogrammetry.
im=bpy.data.images.load(str(R/'assets/deudeulgang/mixed-forest-canopy-v55.png'))
im.pack();mat=bpy.data.materials.new('Background_mixed_woodland_texture');mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=1
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;tex.extension='REPEAT'
mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
background=[]
def forest_mesh(name,vs,fs):
 o=backdrop(g.mesh(name,vs,fs,'#476343',smooth=True));o.data.materials.clear();o.data.materials.append(mat)
 uv=o.data.uv_layers.active
 # A rotated planar projection hides the grid alignment and keeps real-world
 # crown scale consistent across adjoining terrain sections.
 for f in o.data.polygons:
  for li in f.loop_indices:
   v=o.data.vertices[o.data.loops[li].vertex_index].co;x,z=v.x,-v.y
   uv.data[li].uv=((x*.94+z*.342)/145,(-x*.342+z*.94)/145)
 o['background_canopy']=True;background.append(o);return o

def grid(name,x0,x1,z0,z1,step,fn):
 nx=round((x1-x0)/step)+1;nz=round((z1-z0)/step)+1;vs=[];fs=[]
 for j in range(nz):
  z=z0+(z1-z0)*j/(nz-1)
  for i in range(nx):
   x=x0+(x1-x0)*i/(nx-1);vs.append((x,fn(x,z),z))
 for j in range(nz-1):
  for i in range(nx-1):
   a=j*nx+i;fs.append((a,a+1,a+1+nx,a+nx))
 return forest_mesh(name,vs,fs)

# Three contiguous sections allow frustum culling without visible material seams.
for i,(a,b) in enumerate([(-825,-275),(-275,275),(275,825)]):
 grid('background_wooded_ridge_'+str(i),-904,-194,a,b,5,height)

# A second complete hill rolls down to the ground on every side: no floating slab.
def distant_height(x,z):
 across=math.sin(math.pi*max(0,min(1,(x+1400)/820)))**1.35
 ends=1-smooth((abs(z)-630)/380)
 return .1+across*ends*(96+20*math.sin(z/220+.6)+9*math.sin(z/87))
grid('background_distant_ridgeline',-1400,-580,-1010,1010,10,distant_height)

scene.eevee.taa_render_samples=32
bpy.ops.wm.save_as_mainfile(filepath=str(target))
out=R/'public/models/deudeulgang.glb'
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False)
blob=out.read_bytes();n=struct.unpack_from('<I',blob,12)[0];doc=json.loads(blob[20:20+n]);tail=blob[20+n:]
for m in doc['materials']:
 if m.get('name')=='Pine_needles_alpha_clip':m['alphaMode']='MASK';m['alphaCutoff']=.48;m['doubleSided']=True
j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
raw=struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail
out.write_bytes(raw);packed=gzip.compress(raw,compresslevel=9,mtime=0);Path(str(out)+'.gz').write_bytes(packed)
(R/'knowledge/sources/deudeulgang/background-v55-metrics.json').write_text(json.dumps(dict(backgroundMeshes=len(background),backgroundTriangles=sum(len(o.data.loop_triangles) for o in background),texture='Original AI-generated mixed forest canopy; not site photography',glbBytes=len(raw),gzipBytes=len(packed),walkWorldUnchanged=True),indent=2))
print('BACKGROUND EXPORT',len(background),len(raw),len(packed),flush=True)
cam=scene.camera
for name,pos,aim,lens in [('mountain',(-2,80,285),(-380,52,10),35),('riverside',(-28,1.72,15),(-290,36,70),26)]:
 cam.location=g.bp(*pos);cam.rotation_euler=(Vector(g.bp(*aim))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
 scene.render.filepath=str(O/(name+'-v55-finished.png'));bpy.ops.render.render(write_still=True)
print('BACKGROUND COMPLETE',flush=True)
