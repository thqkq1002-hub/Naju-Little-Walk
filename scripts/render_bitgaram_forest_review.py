"""Render the authored park revision for visual review, without changing its source."""
import bpy
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-park-forest-detail.blend'))
s=bpy.context.scene;s.camera.location=(76,-164,82)
s.camera.rotation_euler=(Vector((7,-62,12))-s.camera.location).to_track_quat('-Z','Y').to_euler()
s.camera.data.lens=30;s.render.resolution_x=1280;s.render.resolution_y=960;s.render.resolution_percentage=100
s.render.filepath=str(root/'outputs/bitgaram/bitgaram-park-forest-review.png');bpy.ops.render.render(write_still=True)
