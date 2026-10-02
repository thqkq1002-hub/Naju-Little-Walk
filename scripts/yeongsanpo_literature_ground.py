"""JNFC 149478–149481: framed ground-floor exhibitions and glazed veranda.

Photographs establish the room's visual structure. Panel artwork below is an
original interpretation, not copied exhibition prose or museum photography.
"""
import math,random
from yeongsanpo_geometry import Geometry

def remove(g,prefixes):
    import bpy
    for o in list(g.scene.objects):
        if any(o.name.startswith(p) for p in prefixes):bpy.data.objects.remove(o,do_unlink=True)
    g.solids[:]=[s for s in g.solids if not any(s['name'].startswith(p) for p in prefixes)]

def framed_panel(f,x,width,title,subtitle):
    f.box('ground_exhibition_panel_back',x,1.47,0,width,2.82,.10,'#dad9cd',record=False)
    f.box('ground_exhibition_panel_face',x,1.47,.063,width-.045,2.76,.025,'#e6e4d8',record=False)
    for dx in (-width/2,width/2):f.box('exhibition_panel_edge',x+dx,1.47,.065,.027,2.82,.032,'#a6a598',record=False)
    f.label(title,x,2.57,.094,width-.33,.20,color='#703a32')
    f.label(subtitle,x,2.26,.094,width-.4,.105,color='#665c4a')
    return x

def caption(f,text,x,y,w=1.1):
    f.label(text,x,y,.13,w,.07,color='#5c5b50')

def landscape(f,x,y,w,h):
    # Original sepia river/port line art, made of editable geometry.
    f.box('panel_landscape_paper',x,y,.091,w,h,.018,'#d8d8c9',record=False)
    points=[(x-w/2,y-h*.17,.11),(x-w*.36,y+h*.12,.11),(x-w*.21,y+h*.01,.11),(x-w*.05,y+h*.32,.11),(x+w*.13,y+h*.15,.11),(x+w*.25,y+h*.25,.11),(x+w/2,y-h*.13,.11)]
    f.mesh('panel_original_distant_hills',points+[(x+w/2,y-h*.34,.11),(x-w/2,y-h*.34,.11)],[tuple(range(9))],'#aeb5a4')
    for i in range(8):
        xx=x-w*.43+i*w*.12;hh=h*(.07+.02*(i%3));ww=w*.075
        f.box('panel_port_house',xx,y-h*.2+hh/2,.124,ww,hh,.018,'#8b9487',record=False)
        f.mesh('panel_port_roof',[(xx-ww*.65,y-h*.2+hh,.139),(xx,y-h*.2+hh*1.45,.139),(xx+ww*.65,y-h*.2+hh,.139)],[(0,1,2)],'#737f73')
    for row in range(4):
        pts=[(x-w*.46+i*w*.115,y-h*.34-row*h*.022+math.sin(i*.8+row)*h*.02,.145) for i in range(9)]
        for a,b in zip(pts,pts[1:]):f.tube('panel_river_etched_line',a,b,.003,'#84958a',n=4)

def book(f,x,y,z,color,title='타오르는 강',scale=1):
    f.box('ground_display_book_pages',x,y+.19*scale,z,.25*scale,.37*scale,.065*scale,'#dfdccb',record=False)
    for dz in (-.044,.044):f.box('ground_display_book_cover',x,y+.19*scale,z+dz*scale,.28*scale,.40*scale,.013,color,record=False)
    f.label(title,x,y+.23*scale,z+.053*scale,.23*scale,.045*scale,color='#e6dbb6')

def exhibitions(g):
    remove(g,('exhibit_panel_','exhibit_caption_rule','literary_timeline_','literature_interpretation_'))
    old=('문순태와 타오르는 강','문학과 영산포','소설 속 영산강','이야기를 따라 흐르는 강','강','포구','마을','길','기억','문학')
    remove(g,tuple('label_'+t for t in old))
    g.signs[:]=[s for s in g.signs if s['text'] not in old]
    east=Geometry(g.scene,(8.79,0),math.pi/2)
    # Fit each panel between the structural cross-beams at z=-3 and z=2.8.
    for x,w,title,sub in [(-5.9,5.35,'문순태 · 타오르는 강','영산강과 포구를 배경으로 한 이야기'),(-.1,5.2,'소설을 따라 흐르는 강','강 · 사람 · 마을'),(4.3,2.3,'문학과 영산포','포구의 풍경을 읽다')]:
        framed_panel(east,x,w,title,sub)
        if x<3:landscape(east,x,.50,w-.21,.68)
    # A book display inset and a physical interpretation diagram replace the
    # previous blank strips. Labels are short, original educational captions.
    for i in range(3):
        x=-7.50+i*1.60
        east.box('panel_book_mount',x,1.67,.13,.91,.91,.085,'#c9c7b7',record=False)
        book(east,x,1.32,.22,['#584e46','#8c5d43','#465a55'][i],scale=1.55)
        caption(east,['작품','강의 기억','삶의 이야기'][i],x,1.13,.95)
    for x,y,text in [(-1.65,1.82,'강'),(-.1,1.82,'포구'),(1.45,1.82,'마을'),(-.85,1.22,'사람'),(.65,1.22,'삶')]:
        east.box('panel_story_diagram_card',x,y,.115,.85,.32,.05,'#d4cbb3',record=False)
        east.label(text,x,y,.148,.74,.12,color='#574b3c')
    for a,b in [((-1.23,1.82),(-.53,1.82)),((.33,1.82),(1.02,1.82)),((-.1,1.62),(-.85,1.39)),((-.1,1.62),(.65,1.39))]:
        east.tube('panel_story_diagram_link',(*a,.145),(*b,.145),.009,'#928572',n=5)
    for i in range(3):
        y=1.89-i*.67
        landscape(east,4.3,y,1.90,.45);caption(east,['영산강','옛 포구','골목과 집'][i],4.3,y-.30,1.80)
    # Rear wall: a wide display with layered frames, small exhibits and a low
    # glazed case. Circulation remains to its left at the existing stair route.
    rear=Geometry(g.scene,(4.8,-8.76),0);framed_panel(rear,0,6.50,'문순태와 타오르는 강','문학으로 만나는 영산포')
    landscape(rear,-1.25,1.46,3.30,1.19)
    for i in range(3):
        y=1.12+i*.34;rear.box('panel_label_mount',1.87,y,.13,1.87,.27,.04,'#dbd5c3',record=False)
        rear.label(['영산강의 기억','포구에 머문 사람들','이야기로 남은 삶'][i],1.87,y,.157,1.68,.085,color='#635644')
    for x in (-2.1,0,2.1):
        rear.box('exhibit-case_ground_book_plinth',x,.37,.49,1.62,.66,.68,'#544b3b',True)
        rear.box('ground_book_case_top',x,.72,.49,1.65,.045,.73,'#b0a894',record=False)
        book(rear,x-.26,.75,.43,'#5a5443');book(rear,x+.24,.75,.43,'#925f45')
        rear.glass('ground_book_case_front',x,.95,.87,1.61,.43)
        rear.glass('ground_book_case_back',x,.95,.11,1.61,.43)
        for dx in (-.81,.81):rear.glass('ground_book_case_side',x+dx,.95,.49,.72,.43,rotation=math.pi/2)
        rear.box('ground_case_glass_top',x,1.18,.49,1.64,.018,.77,'#97b6be',record=False)
    g.solids+=rear.solids;g.signs+=rear.signs+east.signs
    # The user-facing blank central partitions have timber stiles and mounted
    # panels on both faces, not freestanding unframed white slabs.
    for z in (-6.8,2):
        for x,angle in ((.075,-math.pi/2),(-.075,math.pi/2)):
            f=Geometry(g.scene,(x,z),angle)
            for dx in (-1.96,1.96):f.box('ground_partition_end_post',dx,1.45,.025,.11,2.90,.13,'#5c3d27',record=False)
            for y in (.12,2.55):f.box('ground_partition_timber_rail',0,y,.025,4.03,.12,.13,'#5c3d27',record=False)
            f.box('ground_partition_panel',0,1.35,.087,1.72,2.12,.045,'#e5e1d1',record=False)
            f.label('문학으로 만나는 영산강',0,2.16,.118,1.49,.13,color='#733e31')
            landscape(f,0,1.43,1.42,.87)
            f.label('강을 따라, 사람의 이야기를 읽다',0,.70,.148,1.49,.072,color='#625b49')
            g.signs+=f.signs
    # Actual warning plates observed above the low timber passage.
    for z in (-3,2.8):
        for side in (-1,1):
            g.box('ground_passage_warning_plate',4.4,2.45,z+side*.095,.65,.125,.018,'#e5e3d9',record=False)
            g.label('머리조심',4.4,2.45,z+side*.11,.58,.075,rotation=0 if side==1 else math.pi,color='#56665d')

def veranda(g):
    remove(g,('garden_corridor_window','corridor_lattice','corridor_plank_joint','corridor_lintel'))
    # Close all areas that are wall rather than glazing; the exit doorway is
    # deliberately open at x=0 and still activates the existing outdoor portal.
    for a,b in [(-9,-1),(1,9)]:
        g.box('veranda_window_white_plinth',(a+b)/2,.21,8.96,b-a,.42,.20,'#e3dfd2',True)
        g.box('veranda_window_head_wall',(a+b)/2,2.95,8.96,b-a,.42,.20,'#e3dfd2',True)
    for x in (-8.96,-6.6,-4.1,-1.03,1.03,4.1,6.6,8.96):
        g.box('veranda_window_main_post',x,1.49,8.91,.105,2.70,.16,'#48382b',record=False)
    for a,b in [(-8.9,-6.65),(-6.55,-4.15),(-4.05,-1.12),(1.12,4.05),(4.15,6.55),(6.65,8.9)]:
        center=(a+b)/2;w=b-a
        g.glass('veranda_clear_garden_glazing',center,1.56,8.90,w,2.24)
        for y in (.44,2.08,2.70):g.box('veranda_window_horizontal_rail',center,y,8.86,w,.065,.12,'#48382b',record=False)
        n=max(2,round(w/.62))
        for i in range(1,n):g.box('veranda_window_narrow_mullion',a+i*w/n,1.56,8.86,.04,2.24,.09,'#48382b',record=False)
        g.box('veranda_deep_window_sill',center,.415,8.80,w+.07,.055,.31,'#5c3d27',record=False)
    g.box('veranda_exit_header',0,2.96,8.96,2.1,.39,.21,'#5c3d27',record=False)
    # Sliding leaves stack beside the three existing openings, preserving the
    # passage through x=-6,0,6 and the tested stair/library route.
    for center in (-7.5,-3.0,3.0,7.5):
        w=2.05;z=5.78
        for dx in (-w/2,w/2):g.box('veranda_sliding_door_stile',center+dx,1.29,z,.065,2.45,.11,'#5c3d27',record=False)
        for y in (.085,1.05,2.47):g.box('veranda_sliding_door_rail',center,y,z,w,.075,.12,'#5c3d27',record=False)
        g.box('veranda_sliding_door_paper',center,.59,z-.018,w-.1,.88,.026,'#d9d8c6',record=False)
        for i in range(15):g.box('veranda_fine_door_lattice',center-w/2+.08+i*(w-.16)/14,1.31,z+.061,.023,2.35,.026,'#735133',record=False)
        for y in (.34,1.73):g.box('veranda_lattice_crossrail',center,y,z+.062,w,.026,.035,'#735133',record=False)
        for dx in (-.78,.78):g.box('veranda_recessed_door_pull',center+dx,1.10,z+.075,.03,.11,.022,'#30281f',record=False)
        g.collider('veranda_sliding_leaf_collision',[[center-w/2,z-.09],[center+w/2,z-.09],[center+w/2,z+.09],[center-w/2,z+.09]],0,2.48)
    for y,h,col in ((2.58,.20,'#5c3d27'),(3.01,.18,'#5c3d27')):g.box('veranda_continuous_lintel',0,y,5.78,18,h,.22,col,record=False)
    # The photographed clerestory is opaque pale backing with dark joinery,
    # never a gap through which the blue scene background can cut across a wall.
    g.box('veranda_transom_infill',0,2.82,5.78,17.9,.31,.10,'#dedbcc',record=False)
    for x in range(-8,9):
        for dx in (-.36,.36):g.box('veranda_transom_pattern',x+dx,2.82,5.85,.025,.23,.04,'#604830',record=False)
        for y in (2.71,2.93):g.box('veranda_transom_pattern',x,y,5.85,.75,.025,.04,'#604830',record=False)
    # Narrow timber floorboards with end joints and subtle grain.
    for row in range(11):
        z=5.97+row*.266
        for col in range(7):
            left=-8.90+col*2.55
            g.box('veranda_timber_floorboard',left+1.263,.013,z,2.526,.026,.25,'#504333',record=False)
            g.box('veranda_plank_end_joint',left+2.538,.028,z,.012,.005,.255,'#30281f',record=False)
    # Door at the end of the corridor is a closed photo-observed furnishing,
    # not an invented second interior or a walk-through wall.
    end=Geometry(g.scene,(8.86,7.33),math.pi/2)
    end.box('veranda_end_door',0,1.16,.03,1.32,2.32,.12,'#8b6743',record=False)
    for dx in (-.56,.56):end.box('veranda_door_recess_stile',dx,1.13,.102,.043,2.02,.024,'#604830',record=False)
    for y in (.14,2.13):end.box('veranda_door_recess_rail',0,y,.102,1.13,.055,.024,'#604830',record=False)
    end.box('veranda_door_nameplate',0,1.99,.116,.49,.14,.015,'#e3e0d3',record=False)
    end.label('화장실',0,1.99,.132,.42,.08,color='#434b40');end.tube('veranda_door_knob',(.48,1.12,.11),(.48,1.12,.19),.042,'#9eaa9d',n=14)
    g.signs+=end.signs

def garden_view(g):
    # Photo-grounded view beyond the veranda. These meshes are a visual context
    # only, outside the indoor walk boundary; the door still opens the main map.
    f=Geometry(g.scene);rng=random.Random(913)
    f.box('window_garden_ground',0,-.10,20,40,.18,25,'#93966a',record=False)
    f.box('window_garden_paved_apron',0,-.006,10.1,19,.05,2.3,'#b7baad',record=False)
    for x,z,w,d in [(-5.7,13.5,5.2,3.4),(5.1,14.3,5,4),(-1.8,20,6,3.7)]:
        f.box('window_garden_gravel_bed',x,.035,z,w,.065,d,'#d7d9cd',record=False)
        for j in range(28):
            px=x+rng.uniform(-w*.45,w*.45);pz=z+rng.uniform(-d*.45,d*.45)
            f.rock('window_garden_gravel',px,.09,pz,.13,.07,.11,'#e0e1d5',rng)
    for i in range(8):
        z=11.2+i*1.40;x=math.sin(i*.63)*1.7
        f.rock('window_garden_stepping_stone',x,.055,z,1.36,.10,.80,'#8b958a',rng)
    for x,z,s in [(-5.7,13.5,.64),(5.1,14.5,.68),(-6.3,19,.80),(5.9,21,.90)]:
        f.tree('window_garden_pruned_tree',x,z,s,seed=int((x+10)*20))
        for dx in (-.35,.35):f.tube('window_garden_tree_stake',(x+dx,.02,z),(x+dx,1.65*s,z),.028,'#93805c',n=7)
    for x in (-5.1,4.6,6.9):
        f.vessel('window_garden_white_pot',x,.06,10.8,.72,'#dedfd3')
        for i in range(7):
            a=i*math.tau/7
            f.mesh('window_garden_pot_leaf',[(x,.75,10.8),(x+.34*math.cos(a),1.25+.14*(i%2),10.8+.34*math.sin(a)),(x+.13*math.cos(a+.7),1.04,10.8+.13*math.sin(a+.7))],[(0,1,2)],'#5e8151',smooth=True)
    for x in (-8.8,8.8):f.box('veranda_outer_white_pier',x,1.55,9.65,.32,3.10,.32,'#dadacf',record=False)
    f.box('window_garden_boundary_wall',0,1.25,25,42,2.5,.28,'#777d71',record=False)
    for x in range(-20,21):f.box('window_garden_fence_batten',x,1.30,24.82,.045,2.35,.06,'#575f50',record=False)
    # Garden-facing eaves enclose the upper field of view through the glazing.
    f.box('veranda_exterior_eave_soffit',0,3.01,10.0,19.6,.15,2.45,'#604830',record=False)
    for x in range(-9,10):f.box('veranda_outer_rafter',x,2.90,10.0,.08,.16,2.43,'#735133',record=False)

def ground_exhibition(g):
    exhibitions(g);veranda(g);garden_view(g)
    return dict(revision='literature-ground-1',sources=['JNFC 149478','149479','149480','149481','149484','149486'],scope='Photo-informed ground-floor exhibitions, framed sliding doors and garden-facing veranda; dimensions and original panel graphics are interpretations.')
