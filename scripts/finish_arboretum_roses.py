"""Round rose rims and correct petal outward normals in a new guarded revision."""
import bpy, bmesh, math, ast, json, sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v61'
P=R/'knowledge/sources/arboretum/garden-quality-v61.json'
report=json.loads(P.read_text(encoding='utf-8'))
soft='--soft' in sys.argv
target=O/('naju-arboretum-garden-v61-soft.blend' if soft else 'naju-arboretum-garden-v61-rounded.blend')
if target.exists():raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']))
tree=ast.parse((R/'scripts/arboretum_botanical_finish.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PlantMesh'],type_ignores=[]),'<PlantMesh>','exec'))
code=(R/'scripts/upgrade_arboretum_garden.py').read_text(encoding='utf-8')
code=code.replace("distance=radius*(.12+.88*t);y=lift*math.sin(t*math.pi/2)-radius*.13*t**4+abs(w)**2*.016", "distance=radius*(.12+.88*math.sin(t*math.pi/2))*(1-.22*w*w);y=lift*(1-math.cos(t*math.pi/2))+.025*w*w*t-.015*(1-w*w)*t**6")
code=code.replace("math.sin(math.pi*t*.96)**.60*radius*.57", "math.sin(math.pi*t/2)**.65*radius*.65")
code=code.replace("rows=5 if detail else 2;cols=4 if detail else 2", "rows=7 if detail else 3;cols=6 if detail else 3")
code=code.replace("[point(a,c),point(b,c),point(b,d),point(a,d)]", "[point(a,d),point(b,d),point(b,c),point(a,c)]")
if soft:code=code.replace("+.025*w*w*t-.015*(1-w*w)*t**6", "-.028*w*w*t+.010*(1-w*w)*t**6")
tree=ast.parse(code)
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['oval_leaf','compound','blossom']],type_ignores=[]),'<curved petals>','exec'))
stem=bpy.data.materials['Garden_live_canes'];leaf=bpy.data.materials['Garden_compound_leaf'];bud=bpy.data.materials['Garden_rose_calyx'];pollen=bpy.data.materials['Garden_pollen']
protos={}
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.get('garden_kind')!='rose':continue
 color=o.data.materials[2];lod=o.get('vegetation_lod');key=(color.name,lod)
 if key not in protos:
  mesh=blossom('rose',color,lod=='near')
  if soft:
   bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(mesh);bm.free();mesh.update()
  protos[key]=mesh
 o.data=protos[key]
report['output']=str(target.relative_to(R));report['petal_revision']='Convex petal rims and welded curved surfaces; outward-facing normals; draft revisions retained' if soft else 'Rounded cup rims; outward-facing petal normals; v61 draft retained'
bpy.context.view_layer.update();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(O/('naju-arboretum-v61-soft.glb' if soft else 'naju-arboretum-v61-rounded.glb')),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
P.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('ROUNDED ROSES',len(protos),flush=True)
