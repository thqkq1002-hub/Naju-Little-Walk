"""Build the three Naju CI characters (Baedole, Hongdori, Beodeul-nangja) as NPC GLBs.

Run: blender --background --python scripts/build_npc_mascots.py -- [--only baedole,...] [--render]
Original stylised 3D interpretations of the official municipal CI characters;
the manual's artwork itself is never bundled. Local -Z is each character's front.
"""
import bpy, sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from npc_kit import new_scene, ellipsoid, lathe, limb, hand, surface_z, profile_radius, arc, eye, finish

RENDER = '--render' in sys.argv

def baedole():
    scene, g = new_scene('Naju_Baedole')
    GOLD, SKIN, WHITE, VEST, KHAKI, BOOT, BROWN = '#f0c53f', '#f2c84a', '#f7f5ee', '#1f5a48', '#d8b68a', '#1f4a3a', '#8a5a3a'
    # Pear silhouette: narrow crown widening into a round jaw.
    profile = [(.68 + .59 * t, max(.035, .315 * math.sin(math.pi * t ** .58) ** .85)) for t in (i / 28 for i in range(29))]
    SZ = .96
    lathe(g, 'baedole_head', 0, 0, 0, profile, GOLD, sz=SZ, n=40)
    def face_z(y, x=0):
        r = profile_radius(profile, y)
        return -r * SZ * math.sqrt(max(1 - (x / (r + .001)) ** 2, .05)) - .004
    for s in (-1, 1):
        x = s * .10
        ellipsoid(g, f'baedole_eye_{s}', x, .88, face_z(.88, x), .036, .05, .018, '#171216', rings=10, segments=14)
        ellipsoid(g, f'baedole_glint_{s}', x + .01, .905, face_z(.88, x) - .012, .011, .011, .008, '#ffffff', rings=6, segments=8)
        ellipsoid(g, f'baedole_blush_{s}', s * .20, .79, face_z(.79, s * .20) + .004, .05, .034, .012, '#f0975a', rings=8, segments=14)
    arc(g, 'baedole_smile', [(x, .765 - .028 * (1 - (x / .08) ** 2), face_z(.765, x) - .006) for x in [-.08 + .02 * i for i in range(9)]], .008, '#6a3a1c')
    limb(g, 'baedole_stem', [(0, 1.24, 0), (.006, 1.29, 0), (.016, 1.33, 0)], [.019, .015, .012], '#7a5230', n=10)
    ellipsoid(g, 'baedole_leaf', .085, 1.345, 0, .12, .02, .06, '#4a9a3a', roll=.45, rings=10, segments=16)
    ellipsoid(g, 'baedole_leaf_vein', .07, 1.335, -.03, .09, .006, .008, '#8bcf6a', roll=.45, rings=6, segments=10)
    limb(g, 'baedole_neck', [(0, .66, 0), (0, .72, 0)], [.075, .085], SKIN, n=16)
    # Striped vest over a white tee; the collar sits as a shallow V.
    vest = [(.40, .118), (.46, .132), (.56, .138), (.65, .128), (.70, .108), (.725, .07)]
    lathe(g, 'baedole_vest', 0, 0, 0, vest, VEST, sz=.82, n=28)
    def vest_z(y, x):
        r = profile_radius(vest, y)
        return -r * .82 * math.sqrt(max(1 - (x / r) ** 2, .04))
    for k, x in enumerate((-.088, -.031, .031, .088)):
        ellipsoid(g, f'baedole_vest_stripe_{k}', x, .535, vest_z(.535, x) + .003, .017, .105, .011, WHITE, rings=10, segments=12)
    for s in (-1, 1):
        ellipsoid(g, f'baedole_collar_{s}', s * .045, .688, vest_z(.688, s * .045) + .002, .045, .014, .016, WHITE, roll=s * 1.0, rings=8, segments=12)
    ellipsoid(g, 'baedole_badge', .072, .615, vest_z(.615, .072) + .002, .020, .020, .010, '#f0c53f', rings=8, segments=12)
    lathe(g, 'baedole_shorts', 0, 0, 0, [(.30, .10), (.36, .119), (.43, .126), (.47, .12)], KHAKI, sz=.86, n=24)
    for s in (-1, 1):
        side = 'l' if s < 0 else 'r'
        limb(g, f'baedole_leg_{side}', [(s * .062, .33, 0), (s * .062, .24, .002), (s * .062, .17, 0)], [.040, .036, .034], SKIN, n=12)
        lathe(g, f'baedole_boot_{side}', s * .062, 0, 0, [(.005, .046), (.03, .055), (.10, .058), (.155, .052), (.175, .044)], BOOT, sz=1.06, n=20)
        lathe(g, f'baedole_boot_band_{side}', s * .062, 0, 0, [(.130, .0585), (.158, .0575)], WHITE, sz=1.06, n=20)
        ellipsoid(g, f'baedole_boot_toe_{side}', s * .062, .035, -.05, .052, .035, .068, BOOT, rings=8, segments=14)
    # Waving arm (+x reads as image-left in the preview) and a resting arm.
    limb(g, 'baedole_sleeve_wave', [(-.115, .655, -.01), (-.175, .675, -.025)], [.055, .05], WHITE, n=12)
    limb(g, 'baedole_arm_wave', [(-.17, .672, -.024), (-.29, .755, -.04), (-.40, .855, -.05)], [.036, .031, .028], SKIN, n=12)
    hand(g, 'baedole_hand_wave', (-.40, .855, -.05), (-.28, .95, -.05), (.2, .1, .95), .036, SKIN, curl=.1)
    limb(g, 'baedole_sleeve_down', [(.115, .655, -.01), (.17, .63, -.025)], [.055, .05], WHITE, n=12)
    limb(g, 'baedole_arm_down', [(.168, .632, -.024), (.245, .555, -.04), (.295, .485, -.05)], [.036, .032, .029], SKIN, n=12)
    hand(g, 'baedole_hand_down', (.295, .485, -.05), (.05, -.98, -.1), (.98, .05, 0), .034, SKIN, curl=.35)
    limb(g, 'baedole_strap', [(.115, .70, -.055), (.03, .60, -.105), (-.10, .475, -.085)], [.012, .012, .012], '#7a5230', n=8)
    g.box('baedole_bag', -.145, .405, -.035, .10, .085, .062, BROWN, record=False)
    g.box('baedole_bag_flap', -.145, .443, -.035, .106, .030, .068, '#7a4a2c', record=False)
    finish(scene, g, 'npc-baedole', 1.35, RENDER)

def hongdori():
    scene, g = new_scene('Naju_Hongdori')
    WHITE, GREY, PINK, INK = '#fbfbff', '#e2e3ec', '#e796ab', '#171216'
    profile = [(.26, .28), (.34, .38), (.46, .385), (.60, .31), (.74, .22), (.86, .12), (.95, .05), (1.00, .0)]
    SZ = .68
    lathe(g, 'hongdori_body', 0, 0, 0, profile, WHITE, sx=1.08, sz=SZ, n=40)
    ellipsoid(g, 'hongdori_belly', 0, .29, .02, .44, .13, .30, GREY, rings=12, segments=28)
    def face_z(y, x=0):
        r = profile_radius(profile, y)
        return -r * SZ * math.sqrt(max(1 - (x / (r * 1.08 + .001)) ** 2, .05)) - .004
    def on_face(x, y, off=0):
        return (x, y, face_z(y, x) + off)
    ex, ey = .105, .585
    ellipsoid(g, 'hongdori_eye_white', ex, ey, face_z(ey, ex), .064, .08, .02, '#ffffff', rings=10, segments=16)
    ellipsoid(g, 'hongdori_pupil', ex, ey - .006, face_z(ey, ex) - .012, .047, .06, .02, INK, rings=10, segments=16)
    ellipsoid(g, 'hongdori_glint', ex + .016, ey + .026, face_z(ey, ex) - .026, .015, .015, .01, '#ffffff', rings=6, segments=8)
    arc(g, 'hongdori_wink', [on_face(-.115 + .023 * i, .575 + .02 * math.sin(i / 6 * math.pi), -.008) for i in range(7)], .010, INK)
    for s in (-1, 1):
        arc(g, f'hongdori_brow_{s}', [on_face(s * (.06 + .026 * i), .675 + .022 * math.sin(i / 4 * math.pi), -.006) for i in range(5)], .008, INK)
        ellipsoid(g, f'hongdori_blush_{s}', s * .225, .475, face_z(.475, s * .225) + .004, .058, .03, .012, '#f5b3b8', rings=8, segments=14)
    ellipsoid(g, 'hongdori_nose', 0, .515, face_z(.515) - .006, .014, .01, .01, '#e79fae', rings=6, segments=8)
    ellipsoid(g, 'hongdori_mouth', 0, .435, face_z(.435) - .006, .11, .062, .02, '#7d2622', rings=10, segments=18)
    ellipsoid(g, 'hongdori_tongue', 0, .405, face_z(.405) - .016, .072, .034, .014, '#f08a24', rings=8, segments=14)
    # Tail sweeps out of the back of the head, thick at the root.
    limb(g, 'hongdori_tail', [(0, .86, .07), (-.07, .94, .12), (-.17, 1.01, .15), (-.28, 1.06, .155), (-.38, 1.08, .15)],
         [.058, .046, .034, .022, .012], PINK, n=12)
    # Thumbs-up glove.
    limb(g, 'hongdori_arm_thumb', [(-.28, .40, -.05), (-.39, .44, -.12), (-.46, .49, -.17)], [.058, .05, .046], WHITE, n=14)
    ellipsoid(g, 'hongdori_fist', -.50, .525, -.195, .088, .085, .080, WHITE, rings=14, segments=20)
    ellipsoid(g, 'hongdori_curled_fingers', -.535, .505, -.215, .042, .060, .052, WHITE, roll=.12, rings=10, segments=14)
    limb(g, 'hongdori_thumb', [(-.492, .585, -.192), (-.478, .645, -.187), (-.470, .692, -.183)], [.042, .038, .032], WHITE, n=12)
    ellipsoid(g, 'hongdori_thumb_tip', -.470, .695, -.183, .033, .033, .033, WHITE, rings=8, segments=12)
    # Open waving mitten: the cartoon glove reads better than separated fingers.
    limb(g, 'hongdori_arm_wave', [(.28, .44, -.05), (.39, .51, -.09), (.465, .575, -.115)], [.05, .044, .04], WHITE, n=14)
    ellipsoid(g, 'hongdori_mitten', .505, .665, -.135, .082, .098, .072, WHITE, roll=-.22, rings=14, segments=20)
    for k in range(4):
        ellipsoid(g, f'hongdori_mitten_finger_{k}', .452 + k * .037, .752 - abs(k - 1.5) * .014, -.142, .023, .038, .023, WHITE, rings=8, segments=12)
    ellipsoid(g, 'hongdori_mitten_thumb', .582, .655, -.15, .027, .048, .027, WHITE, roll=-.55, rings=8, segments=12)
    ellipsoid(g, 'hongdori_foot_big', -.20, .13, -.16, .095, .15, .11, '#1591d6', roll=.25, rings=12, segments=20)
    ellipsoid(g, 'hongdori_foot_shine', -.225, .17, -.255, .03, .07, .01, '#9fdcf5', roll=.25, rings=8, segments=10)
    ellipsoid(g, 'hongdori_foot_small', .22, .09, -.12, .075, .09, .09, '#5ab9ec', rings=10, segments=16)
    finish(scene, g, 'npc-hongdori', 1.05, RENDER)

def beodeul():
    scene, g = new_scene('Naju_Beodeul')
    SKIN, HAIR, PINK, LAV, INDIGO, GOLD, TURQ, WHITE = '#f6d9bf', '#191920', '#f2a2b8', '#9a9ccc', '#3b3fa0', '#e0b23a', '#3bbcc6', '#f7f5f2'
    # Chima: full bell with pleats that deepen toward the hem.
    skirt = [(.04, .450), (.10, .472), (.26, .446), (.48, .376), (.70, .296), (.86, .236), (.95, .215)]
    lathe(g, 'beodeul_skirt', 0, 0, 0, skirt, LAV, sz=.92, n=44, flutes=14, flute_depth=.035, flute_top=.72)
    # The hem band clears the deepest pleat so the folds never poke through it.
    lathe(g, 'beodeul_skirt_hem', 0, 0, 0, [(.012, .458), (.055, .484), (.105, .497)], INDIGO, sz=.92, n=44)
    for s in (-1, 1):
        ellipsoid(g, f'beodeul_shoe_{s}', s * .075, .035, -.13, .046, .032, .085, '#e8e6f2', rings=8, segments=12)
    # Jeogori: short jacket with a shallow shoulder slope.
    lathe(g, 'beodeul_jeogori', 0, 0, 0, [(.90, .205), (1.00, .215), (1.14, .208), (1.26, .193), (1.34, .155), (1.37, .10)], PINK, sz=.80, n=32)
    lathe(g, 'beodeul_sash', 0, 0, 0, [(.925, .212), (.975, .222), (1.03, .213)], INDIGO, sz=.81, n=32)
    for s in (-1, 1):
        ellipsoid(g, f'beodeul_collar_{s}', s * .052, 1.235, -.152, .098, .024, .032, INDIGO, roll=s * .97, rings=8, segments=14)
        ellipsoid(g, f'beodeul_collar_trim_{s}', s * .047, 1.258, -.150, .086, .012, .026, WHITE, roll=s * .97, rings=8, segments=14)
    limb(g, 'beodeul_goreum', [(.05, 1.14, -.165), (.035, 1.02, -.175), (.05, .90, -.17)], [.016, .014, .011], INDIGO, n=8)
    ellipsoid(g, 'beodeul_goreum_knot', .05, 1.16, -.168, .034, .026, .022, INDIGO, rings=8, segments=12)
    limb(g, 'beodeul_neck', [(0, 1.36, 0), (0, 1.47, 0)], [.045, .042], SKIN, n=16)
    head = (0, 1.60, 0, .102, .122, .106)
    ellipsoid(g, 'beodeul_head', *head, SKIN, rings=18, segments=26)
    ellipsoid(g, 'beodeul_hair_cap', 0, 1.638, .022, .112, .118, .112, HAIR, rings=16, segments=24)
    ellipsoid(g, 'beodeul_hair_back', 0, 1.40, .075, .098, .26, .07, HAIR, rings=14, segments=18)
    for s in (-1, 1):
        limb(g, f'beodeul_hair_side_{s}', [(s * .095, 1.62, -.03), (s * .112, 1.45, -.045), (s * .108, 1.26, -.05), (s * .098, 1.12, -.045)],
             [.030, .030, .026, .018], HAIR, n=10)
        ellipsoid(g, f'beodeul_ear_bead_{s}', s * .101, 1.556, -.012, .012, .012, .012, TURQ, rings=6, segments=10)
        ellipsoid(g, f'beodeul_ear_gem_{s}', s * .101, 1.516, -.012, .016, .024, .012, GOLD, rings=8, segments=10)
    ellipsoid(g, 'beodeul_bun', 0, 1.742, .045, .066, .072, .066, HAIR, rings=12, segments=18)
    limb(g, 'beodeul_hairpin', [(-.085, 1.745, .045), (.085, 1.745, .045)], [.008, .008], GOLD, n=8)
    ellipsoid(g, 'beodeul_ornament', 0, 1.695, -.035, .062, .018, .022, GOLD, rings=8, segments=16)
    for s in (-1, 1):
        eye(g, f'beodeul{s}', *head, s * .042, 1.578, .019, color='#22181a')
        arc(g, f'beodeul_brow_{s}', [(s * (.022 + .015 * i), 1.622 + .004 * math.sin(i / 3 * math.pi), surface_z(*head, s * (.022 + .015 * i), 1.622) - .004) for i in range(4)], .0045, '#2a2020')
        ellipsoid(g, f'beodeul_blush_{s}', s * .065, 1.532, surface_z(*head, s * .065, 1.532) + .003, .024, .013, .007, '#f2a9a2', rings=6, segments=10)
    ellipsoid(g, 'beodeul_nose', 0, 1.548, surface_z(*head, 0, 1.548) - .004, .009, .007, .007, '#e9b79a', rings=6, segments=8)
    arc(g, 'beodeul_smile', [(x, 1.508 - .009 * (1 - (x / .028) ** 2), surface_z(*head, x, 1.508) - .003) for x in [-.028 + .014 * i for i in range(5)]], .0045, '#b0524e')
    # Welcoming arm out, the other resting at her side.
    limb(g, 'beodeul_sleeve_welcome', [(.145, 1.30, -.01), (.28, 1.235, -.075), (.40, 1.19, -.14)], [.068, .060, .052], PINK, n=14)
    limb(g, 'beodeul_cuff_welcome', [(.395, 1.192, -.137), (.435, 1.177, -.158)], [.053, .050], INDIGO, n=12)
    hand(g, 'beodeul_hand_welcome', (.44, 1.175, -.16), (.86, -.06, -.51), (.35, .25, .9), .030, SKIN, curl=.2)
    limb(g, 'beodeul_sleeve_rest', [(-.145, 1.30, -.01), (-.205, 1.14, -.06), (-.195, .99, -.11)], [.068, .058, .050], PINK, n=14)
    limb(g, 'beodeul_cuff_rest', [(-.194, .995, -.108), (-.188, .955, -.118)], [.051, .048], INDIGO, n=12)
    hand(g, 'beodeul_hand_rest', (-.187, .95, -.12), (.1, -.93, -.35), (.97, .1, 0), .030, SKIN, curl=.3)
    finish(scene, g, 'npc-beodeul', 1.80, RENDER)

only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else ['baedole', 'hongdori', 'beodeul']
for name, build in (('baedole', baedole), ('hongdori', hongdori), ('beodeul', beodeul)):
    if name in only:
        build()
