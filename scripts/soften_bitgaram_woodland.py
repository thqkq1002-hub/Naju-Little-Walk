"""Blend the square terrain tile into its surrounding lawn; preserve all elevations."""
import bpy,math,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
kind='overview' if '--overview' in sys.argv else 'park'
out=root/f'outputs/bitgaram/bitgaram-{kind}-soft-woodland.blend'
if out.exists():raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/f'outputs/bitgaram/bitgaram-{kind}-shore-finish.blend'))
hill=bpy.data.objects['estimated_hill'];mesh=hill.data
attr=mesh.color_attributes.get('Mapped_woodland')
assert attr and attr.domain=='POINT'
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
lawn=[linear(int('a8b886'[i:i+2],16)/255) for i in (0,2,4)]
for v in mesh.vertices:
    x,z=v.co.x,-v.co.y
    # Rounded, gently irregular contour rather than four straight color boundaries.
    theta=math.atan2(z,x);radius=(abs(x)**4+abs(z)**4)**.25
    inner=102+6*math.sin(3*theta)+4*math.cos(5*theta)
    t=max(0,min(1,(radius-inner)/(145-inner)));t=t*t*(3-2*t)
    old=attr.data[v.index].color
    attr.data[v.index].color=tuple(old[i]*(1-t)+lawn[i]*t for i in range(3))+(1,)
for p in mesh.polygons:p.use_smooth=True
mesh.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out))
bpy.ops.export_scene.gltf(filepath=str(root/f'public/models/bitgaram-{kind}.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
if '--render' in sys.argv:
    s=bpy.context.scene;s.render.resolution_x=1100;s.render.resolution_y=800;s.render.resolution_percentage=100
    s.render.filepath=str(root/'outputs/bitgaram/soft-woodland-review.png');bpy.ops.render.render(write_still=True)
