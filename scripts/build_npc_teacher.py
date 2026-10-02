"""Build the Dasi Elementary School teacher NPC GLB (original stylised figure).

Run: blender --background --python scripts/build_npc_teacher.py -- [--render]
Local -Z is the character's front.
"""
import bpy, sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from npc_kit import new_scene, ellipsoid, lathe, limb, hand, surface_z, arc, eye, finish

SKIN, HAIR, CARDI, CARDI_DARK, SHIRT, PANTS, SHOE, BOOK = '#f3d0b3', '#4a3121', '#4f8f7a', '#437c69', '#f7f5ee', '#3d4250', '#5b3d2a', '#c9503a'

scene, g = new_scene('Naju_Dasi_Teacher')

for s in (-1, 1):
    side = 'left' if s < 0 else 'right'
    limb(g, f'teacher_leg_{side}', [(s * .085, .87, 0), (s * .085, .52, -.012), (s * .082, .22, .004), (s * .082, .07, .01)],
         [.078, .068, .058, .055], PANTS, n=14)
    ellipsoid(g, f'teacher_shoe_{side}', s * .083, .038, -.035, .062, .038, .115, SHOE, rings=10, segments=14)

# Cardigan over a collared shirt; the shoulders carry a little volume.
lathe(g, 'teacher_cardigan', 0, 0, 0, [(.76, .168), (.86, .180), (1.02, .188), (1.18, .192), (1.30, .186), (1.365, .15), (1.40, .085)], CARDI, sz=.74, n=32)
for s in (-1, 1):
    ellipsoid(g, f'teacher_shoulder_{s}', s * .135, 1.305, 0, .062, .058, .058, CARDI, rings=10, segments=14)
limb(g, 'teacher_placket', [(0, .80, -.132), (0, 1.05, -.142), (0, 1.30, -.132)], [.012, .013, .012], CARDI_DARK, n=8)
for s in (-1, 1):
    ellipsoid(g, f'teacher_shirt_v_{s}', s * .030, 1.330, -.112, .044, .013, .020, SHIRT, roll=s * .95, rings=8, segments=12)
ellipsoid(g, 'teacher_shirt_chest', 0, 1.318, -.108, .030, .030, .022, SHIRT, rings=10, segments=14)
ellipsoid(g, 'teacher_name_tag', .088, 1.16, -.135, .036, .022, .008, '#f4f0e0', rings=8, segments=12)
limb(g, 'teacher_neck', [(0, 1.365, -.005), (0, 1.47, 0)], [.052, .046], SKIN, n=16)

head = (0, 1.60, 0, .105, .125, .108)
ellipsoid(g, 'teacher_head', *head, SKIN, rings=18, segments=26)
ellipsoid(g, 'teacher_hair_cap', 0, 1.652, .012, .112, .118, .112, HAIR, rings=16, segments=24)
ellipsoid(g, 'teacher_hair_fringe', -.018, 1.702, -.052, .105, .036, .062, HAIR, roll=.16, rings=10, segments=18)
for s in (-1, 1):
    ellipsoid(g, f'teacher_sideburn_{s}', s * .102, 1.605, .008, .022, .052, .032, HAIR, rings=8, segments=12)
    x = s * .045
    eye(g, f'teacher{s}', *head, x, 1.603, .018, color='#22181a')
    circle = [(x + .038 * math.cos(a * math.tau / 16), 1.603 + .038 * math.sin(a * math.tau / 16), surface_z(*head, x, 1.603) - .013) for a in range(17)]
    arc(g, f'teacher_glasses_{s}', circle, .0038, '#2b2b30')
    limb(g, f'teacher_temple_{s}', [(x + s * .036, 1.606, surface_z(*head, x, 1.603) - .013), (s * .10, 1.606, .01)], [.0035, .0035], '#2b2b30', n=6)
    arc(g, f'teacher_brow_{s}', [(x + s * (-.024 + .016 * i), 1.657 + .005 * math.sin(i / 3 * math.pi), surface_z(*head, x, 1.657) - .004) for i in range(4)], .005, '#3a281c')
    ellipsoid(g, f'teacher_blush_{s}', s * .07, 1.552, surface_z(*head, s * .07, 1.552) + .003, .026, .014, .007, '#f2a9a2', rings=6, segments=10)
arc(g, 'teacher_glasses_bridge', [(-.009, 1.612, surface_z(*head, 0, 1.612) - .013), (.009, 1.612, surface_z(*head, 0, 1.612) - .013)], .0038, '#2b2b30')
ellipsoid(g, 'teacher_nose', 0, 1.572, surface_z(*head, 0, 1.572) - .005, .010, .008, .008, '#e6b596', rings=6, segments=8)
arc(g, 'teacher_smile', [(x, 1.532 - .013 * (1 - (x / .036) ** 2), surface_z(*head, x, 1.532) - .003) for x in [-.036 + .018 * i for i in range(5)]], .005, '#b0524e')

# Raised waving arm (+x reads as image-left in the preview).
limb(g, 'teacher_arm_wave', [(.145, 1.30, -.01), (.255, 1.175, -.035), (.298, 1.315, -.065), (.315, 1.425, -.072)],
     [.056, .048, .044, .040], CARDI, n=14)
limb(g, 'teacher_cuff_wave', [(.313, 1.405, -.071), (.317, 1.445, -.073)], [.042, .040], CARDI_DARK, n=12)
hand(g, 'teacher_hand_wave', (.317, 1.45, -.073), (.06, .97, -.22), (.95, -.05, .3), .036, SKIN, curl=.05)

# Book tucked against the other forearm.
limb(g, 'teacher_arm_book', [(-.145, 1.30, -.01), (-.225, 1.145, -.045), (-.185, 1.075, -.145), (-.09, 1.06, -.205)],
     [.056, .048, .044, .040], CARDI, n=14)
limb(g, 'teacher_cuff_book', [(-.105, 1.062, -.195), (-.075, 1.058, -.215)], [.042, .040], CARDI_DARK, n=12)
hand(g, 'teacher_hand_book', (-.072, 1.058, -.218), (.55, .10, -.83), (.2, .95, .2), .034, SKIN, curl=.55)
g.box('teacher_book', -.10, 1.155, -.222, .185, .24, .038, BOOK, rotation=.14, record=False)
g.box('teacher_book_pages', -.10, 1.155, -.202, .168, .222, .014, '#f5efe0', rotation=.14, record=False)
g.box('teacher_book_band', -.10, 1.155, -.243, .026, .238, .006, '#f0d9a0', rotation=.14, record=False)

finish(scene, g, 'npc-dasi-teacher', 1.78, '--render' in sys.argv)
