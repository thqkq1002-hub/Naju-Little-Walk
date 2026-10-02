"""Read-only inventory of the currently saved crown revision."""
import bpy,json,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/quality-v66/naju-arboretum-juniper-budget-v66.blend'))
groups=collections.defaultdict(list)
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.get('reference_habit') in ['meta','broad','broad2']:
  groups[(o.get('reference_habit'),o.get('vegetation_lod'))].append(o)
rows=[]
for (habit,lod),os in groups.items():
 o=os[0];m=o.data
 rows.append(dict(habit=habit,lod=lod,count=len(os),meshes=len({x.data for x in os}),mesh=m.name,vertices=len(m.vertices),triangles=sum(len(p.vertices)-2 for p in m.polygons),bounds=[[min(v.co[a] for v in m.vertices) for a in range(3)],[max(v.co[a] for v in m.vertices) for a in range(3)]],materials=[x.name for x in m.materials],samples=[dict(name=x.name,location=list(x.location),scale=list(x.scale)) for x in os[:3]]))
out=R/'work/arboretum-crowns-inventory-v73.json';out.write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows,indent=2),flush=True)
