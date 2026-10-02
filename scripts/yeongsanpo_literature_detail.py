"""Photo-informed detailed literature rooms, with a fully closed attic envelope."""
import bpy, math, random
from yeongsanpo_interiors import literature as basic_literature
from yeongsanpo_geometry import Geometry
from yeongsanpo_literature_ground import ground_exhibition

def remove_generated(g,prefixes):
    for obj in list(g.scene.objects):
        if any(obj.name.startswith(name) for name in prefixes):bpy.data.objects.remove(obj,do_unlink=True)
    g.solids[:]=[s for s in g.solids if not any(s['name'].startswith(name) for name in prefixes)]

def texture(g,color,kind):
    """Original packed sRGB materials. No source photographs are redistributed."""
    mat=g.mat(color);bs=mat.node_tree.nodes['Principled BSDF'];n=256
    rgb=[int(color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)];rng=random.Random(761+len(color+kind));pixels=[]
    for j in range(n):
        for i in range(n):
            u=i/n;v=j/n
            if kind=='wood':
                grain=math.sin((v*87+math.sin(u*12)*.3+math.sin(u*4)*.7)*math.tau)
                t=.92+grain*.045+math.sin(v*math.tau*23)*.02+rng.uniform(-.025,.025)
            elif kind=='tatami':t=.93+.025*math.cos(u*math.tau*116)+.025*math.sin(v*math.tau*54)+rng.uniform(-.035,.035)
            else:t=.94+rng.uniform(-.025,.025)
            pixels.extend([*(c*t for c in rgb),1])
    im=bpy.data.images.new('Literature_original_'+kind+'_'+color[1:],width=n,height=n);im.pixels.foreach_set(pixels);im.pack()
    node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.7 if kind=='wood' else .95

def rounded_box(g,name,x,y,z,w,h,d,color,bevel=.015,collision=False):
    obj=g.box(name,x,y,z,w,h,d,color,collision,record=collision)
    modifier=obj.modifiers.new('Soft_joinery_edges','BEVEL');modifier.width=bevel;modifier.segments=3
    return obj

def timber_beam(g,z,top):
    # Continuous irregular rectangular timber, not a chain of round cylinders.
    verts=[];segments=28
    for i in range(segments+1):
        t=i/segments;x=-8.84+t*5.95
        bottom=top+1.92+.25*math.sin(t*math.pi)+.018*math.sin(t*17)
        upper=top+2.43+.018*math.sin(t*8)
        for zz,yy in [(z-.15,bottom),(z+.15,bottom),(z+.15,upper),(z-.15,upper)]:verts.append((x,yy,zz))
    faces=[(3,2,1,0),tuple(range(segments*4,segments*4+4))]
    for j in range(segments):
        for k in range(4):faces.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
    g.mesh('attic_continuous_curved_timber_beam',verts,faces,'#30281f','05_Cutaway_Roof')
    for x in (-8.68,-3.06):
        g.box('attic_beam_joint_block',x,top+2.03,z,.28,.63,.4,'#30281f',group='05_Cutaway_Roof',record=False)
        for y in (top+1.89,top+2.22):g.tube('attic_joinery_peg',(x,y,z-.21),(x,y,z+.21),.016,'#8c7352','05_Cutaway_Roof',n=8)

def chair(g,x,z,top,angle):
    part=Geometry(g.scene,(x,z),angle);dark='#38291f';warm='#8d6947'
    rounded_box(part,'attic_chair_seat',0,top+.085,0,.57,.07,.53,dark,.025)
    rounded_box(part,'attic_chair_cushion',0,top+.14,-.01,.48,.05,.43,'#736147',.022)
    for xx in (-.265,.265):
        rounded_box(part,'attic_chair_back_post',xx,top+.39,.23,.045,.67,.055,dark,.011)
        rounded_box(part,'attic_chair_floor_runner',xx,top+.028,0,.045,.055,.67,dark,.012)
    for y in (.32,.66):rounded_box(part,'attic_chair_back_rail',0,top+y,.24,.57,.047,.055,dark,.009)
    part.box('attic_chair_warm_crossrail',0,top+.38,.275,.48,.065,.022,warm,record=False)
    for sign in (-1,1):part.tube('attic_chair_X_back',(sign*.225,top+.34,.235),(-sign*.225,top+.62,.235),.012,dark,n=4)
    part.collider('attic_chair_collision',[[-.30,-.30],[.30,-.30],[.30,.30],[-.30,.30]],top,.73)
    g.solids+=part.solids

def reading_table(g,x,z,top):
    rounded_box(g,'attic_reading_table_top',x,top+.38,z,2.05,.060,.88,'#b38957',.025,True)
    for dx in (-.87,.87):
        for dz in (-.29,.29):rounded_box(g,'attic_reading_table_leg',x+dx,top+.18,z+dz,.072,.36,.072,'#735133',.008)
    for dz in (-.31,.31):g.box('attic_table_under_apron',x,top+.30,z+dz,1.86,.10,.045,'#936840',record=False)
    for dx in (-.54,.54):
        chair(g,x+dx,z+.85,top,0);chair(g,x+dx,z-.85,top,math.pi)
    # A small light notice appears on a chair back; its original wording is illegible.
    g.box('reading_chair_notice',x+.54,top+.50,z+1.13,.20,.12,.018,'#e8e5d8',record=False)

def cross_lamp(g,x,z,y):
    for dz in (-.22,.22):g.box('wood_cross_lamp_bar',x,y,z+dz,.93,.045,.085,'#b18d5f',group='05_Cutaway_Roof',record=False)
    for dx in (-.23,.23):g.box('wood_cross_lamp_bar',x+dx,y+.04,z,.085,.045,.93,'#b18d5f',group='05_Cutaway_Roof',record=False)
    g.tube('lamp_stem',(x,y+.04,z),(x,y+.20,z),.055,'#6e6049','05_Cutaway_Roof',n=10)
    for dx in (-.23,.23):
        for dz in (-.22,.22):
            g.tube('lamp_socket',(x+dx,y-.02,z+dz),(x+dx,y-.11,z+dz),.04,'#c7bd99','05_Cutaway_Roof',n=12)
            globe=[(.15*(1-math.cos(j*math.pi/16))/2,max(.001,.075*math.sin(j*math.pi/16))) for j in range(17)]
            g.vessel('wood_cross_lamp_globe',x+dx,y-.25,z+dz,1,'#f1ead7',profile=globe)
    bs=g.mat('#f1ead7').node_tree.nodes['Principled BSDF'];bs.inputs['Emission Color'].default_value=(1,.90,.72,1);bs.inputs['Emission Strength'].default_value=.8

def aircon(g,x,z,y,w=1.35,rotation=0):
    part=Geometry(g.scene,(x,z),rotation)
    rounded_box(part,'photo_wall_air_conditioner',0,y,0,w,.36,.23,'#dddcd0',.035)
    part.box('aircon_dark_outlet',0,y-.13,.128,w*.84,.046,.013,'#788178',record=False)
    for i in range(3):part.box('aircon_louver',0,y-.115+i*.016,.14,w*.84,.008,.024,'#c1c7b9',record=False)
    part.box('aircon_indicator',w*.37,y-.05,.127,.035,.012,.012,'#718e74',record=False)

def attic_details(g,top):
    remove_generated(g,('exhibit-case_low_reading_table','reading_table_leg','floor_chair_','attic_high_window','attic_white_bookshelf','attic_bookshelf_divider','attic_curved_dark_beam'))
    # Open cubbies are nearly empty in the reference; the book-filled shelves
    # belong downstairs and must not be copied into this room.
    for z in (-5.65,-1.7,1.2):reading_table(g,-5.60,z,top)
    for z in (-6.3,-1.8,2.35):timber_beam(g,z,top)
    for x in (-8.73,-3.0):
        g.box('attic_wall_head_timber',x,top+2.32,-2.9,.11,.18,12.0,'#30281f',group='05_Cutaway_Roof',record=False)
        g.box('attic_skirting',x,top+.055,-2.9,.07,.11,12.0,'#423727',record=False)
    for z in (-8.80,2.96):
        g.box('attic_end_head_timber',-5.88,top+2.30,z,5.88,.20,.10,'#30281f',group='05_Cutaway_Roof',record=False)
        for y in (.85,1.78):g.box('attic_end_wall_band',-5.88,top+y,z,5.88,.095,.10,'#443427',record=False)
        for x in (-7.0,-4.3):g.box('attic_end_vertical_timber',x,top+1.20,z,.11,2.4,.10,'#352a22',record=False)
    for z in (-6.3,-1.8,2.35):
        g.box('attic_window_wall_post',-8.72,top+1.17,z,.11,2.35,.16,'#30281f',record=False)
    window=Geometry(g.scene,(-8.72,0),-math.pi/2)
    for z,w in [(-7.65,1.72),(-5.25,1.72),(-2.85,1.72),(-.45,1.72),(1.9,1.45)]:
        # True inset casing, sill, glass and a muted exterior behind the glazing.
        window.box('attic_window_exterior_backing',-z,top+1.81,-.016,w,.60,.035,'#88958a',record=False)
        window.box('attic_window_recess',-z,top+1.81,.012,w+.13,.76,.065,'#4c3b2d',record=False)
        window.box('attic_window_daylight',-z,top+1.81,.055,w-.07,.59,.018,'#b5c5bb',record=False)
        for dx in (-w/2,0,w/2):window.box('attic_high_window_stile',-z+dx,top+1.81,.085,.048,.67,.075,'#48382b',record=False)
        for dy in (-.33,.33):window.box('attic_high_window_rail',-z,top+1.81+dy,.085,w+.07,.045,.075,'#48382b',record=False)
        window.box('attic_window_deep_sill',-z,top+1.43,.18,w+.18,.07,.32,'#564230',record=False)
        window.box('attic_window_latch',-z+.055,top+1.77,.14,.035,.07,.024,'#a89f86',record=False)
    g.box('attic_white_bookshelf_back',-2.98,top+1.11,-2.45,.075,2.18,10.4,'#d1d5cb',record=False)
    for row in range(4):g.box('attic_white_bookshelf_shelf',-3.22,top+.08+row*.68,-2.45,.52,.045,10.4,'#e4e7dd',record=False)
    # A taller group of cubbies at the back changes the shelf's top silhouette.
    g.box('attic_white_bookshelf_upper_row',-3.22,top+2.30,-5.9,.52,.04,3.4,'#e4e7dd',record=False)
    for i in range(13):g.box('attic_white_bookshelf_divider',-3.22,top+1.1,-7.65+i*.865,.52,2.1,.033,'#e4e7dd',record=False)
    g.collider('attic_white_bookshelf_collision',[[-3.51,-7.66],[-2.96,-7.66],[-2.96,2.77],[-3.51,2.77]],top,2.15)
    aircon(g,-6.1,-8.72,top+1.95)
    for z in (-4.0,.2):cross_lamp(g,-5.65,z,top+2.24)
    # Broad rectangular tatami, woven surface and patterned dark cloth hems.
    for ix in range(3):
        for iz in range(7):
            x=-7.78+ix*1.96;z=-8.02+iz*1.70
            color=['#aeb080','#a5a778','#b4b486'][(ix+iz)%3]
            g.box('attic_tatami_mat',x,top+.010,z,1.935,.020,1.675,color,record=False)
            for dz in (-.82,.82):
                g.box('attic_tatami_cloth_hem',x,top+.023,z+dz,1.93,.008,.055,'#444c37',record=False)
                for k in range(25):g.box('attic_tatami_hem_stitch',x-.90+k*.075,top+.029,z+dz,.024,.004,.023,'#8b9569',record=False)

def library_book(g,x,y,z,w,h,d,color,rng):
    g.box('library_book_pages',x,y+h/2,z,w*.90,h*.94,d*.91,'#dedbd0',record=False)
    for dx in (-w/2,w/2):g.box('library_book_cover',x+dx,y+h/2,z,.014,h,d,color,record=False)
    g.box('library_book_spine',x,y+h/2,z+d/2,w+.016,h,.018,color,record=False)
    for yy in (.15,.83):g.box('library_book_spine_band',x,y+h*yy,z+d/2+.011,w*.86,.008,.004,'#cec8b4',record=False)
    if rng.random()<.35:
        g.box('library_book_catalogue_label',x,y+h*.20,z+d/2+.013,w*.74,.045,.004,'#ecebe0',record=False)

def ground_details(g):
    rng=random.Random(109)
    remove_generated(g,('exhibit-case_bookshelf','bookshelf_shelf','book_spine','tatami_weave','geometric_transom'))
    remove_generated(g,('ceiling_lamp','label_영산강 문학 서재','label_영산강 문학쉼터'))
    g.signs[:]=[s for s in g.signs if s['text'] not in ('영산강 문학 서재','영산강 문학쉼터')]
    # Full-depth timber uprights, open shelves, books of unequal width, and stacks.
    wall=Geometry(g.scene,(-8.35,0),-math.pi/2)
    for bay,z in enumerate((-5.5,-2.7,.1)):
        cx=-z
        wall.box('library_case_back',cx,1.26,-.32,2.55,2.52,.08,'#382e23',record=False)
        for dx in (-1.24,1.24):rounded_box(wall,'library_case_upright',cx+dx,1.27,0,.09,2.54,.72,'#5c3d27',.018)
        for row in range(6):
            y=.13+row*.46;rounded_box(wall,'library_case_shelf',cx,y,0,2.55,.06,.70,'#755032',.012)
            xx=cx-1.13
            while xx<cx+1.05:
                w=rng.uniform(.055,.11);h=rng.uniform(.29,.41)
                library_book(wall,xx+w/2,y+.034,.09,w,h,rng.uniform(.29,.38),rng.choice(['#d6d5c2','#e3dfd0','#b6bfa3','#869f98','#879faa','#9f815e','#73664d']),rng)
                xx+=w+.014
        for i in range(4):wall.box('library_top_book_stack',cx-.9+i*.015,2.62+i*.06,.02,.40,.054,.30,['#c8c5ad','#eee6cd','#8eaaab','#b6a578'][i],record=False)
        wall.collider('library_case_collision',[[cx-1.30,-.38],[cx+1.30,-.38],[cx+1.30,.38],[cx-1.30,.38]],0,2.6)
    g.solids+=wall.solids
    # Proper room transoms use irregular rectangular geometric joinery.
    for z in (-3,2.8):
        for x in (1.1,3.3,5.5,7.7):
            g.box('transom_dark_backing',x,2.81,z,2.05,.48,.055,'#b3b9a6',record=False)
            for dx in (-1.02,1.02):g.box('transom_end_stile',x+dx,2.81,z+.06,.045,.52,.09,'#604830',record=False)
            for dy in (-.24,.24):g.box('transom_frame_rail',x,2.81+dy,z+.06,2.10,.045,.09,'#604830',record=False)
            for j in range(4):
                xx=x-.78+j*.5;yy=2.77+(.055 if j%2 else -.035)
                for dx in (-.15,.15):g.box('transom_rectangular_pattern',xx+dx,yy,z+.07,.025,.22,.03,'#705339',record=False)
                for dy in (-.11,.11):g.box('transom_rectangular_pattern',xx,yy+dy,z+.07,.32,.025,.03,'#705339',record=False)
    # Dark ceiling panels, white lighting tracks and the shared cross-frame fixture.
    for x in (-6,2,6):
        for z in (-7,-4,-1,2,5):g.box('cutaway_timber_ceiling_panel',x,3.115,z,3.92,.035,2.92,'#352d24',group='05_Cutaway_Roof',record=False)
    for x in (2.1,6.8):
        g.box('white_exhibit_light_track',x,2.99,-.5,.05,.05,12.5,'#d9dace',group='05_Cutaway_Roof',record=False)
        for z in (-6.5,-2.5,1.5,4.5):
            g.tube('white_spot_mount',(x,2.97,z),(x,2.80,z),.018,'#e1dfcf','05_Cutaway_Roof',n=8)
            g.tube('white_spot_cylinder',(x,2.80,z),(x+.10,2.61,z+.06),.06,'#dfdfd1','05_Cutaway_Roof',n=16)
            g.tube('white_spot_lens',(x+.10,2.61,z+.06),(x+.11,2.59,z+.065),.052,'#f1ead7','05_Cutaway_Roof',n=16)
    cross_lamp(g,4,.8,2.9);cross_lamp(g,-5,-3.2,2.9)
    aircon(g,8.72,4.2,2.64,1.5,math.pi/2)
    # A four-pane recessed book display is next to, not inside, the stair opening.
    display=Geometry(g.scene,(.5,-8.75),0)
    display.box('library_recessed_display_back',0,1.58,0,1.6,1.18,.10,'#c3cbbb',record=False)
    for x in (-.78,0,.78):display.box('library_display_vertical',x,1.58,.15,.045,1.22,.34,'#e1e5d5',record=False)
    for y in (.98,1.58,2.18):display.box('library_display_shelf',0,y,.15,1.63,.045,.34,'#e1e5d5',record=False)
    for x,y in [(-.4,1.02),(.4,1.02),(-.4,1.62),(.4,1.62)]:
        display.box('library_display_book',x,y+.17,.10,.23,.34,.07,'#605239',record=False)
        display.label('타오르는 강',x,y+.23,.15,.20,.035,color='#ded3b4')
    display.glass('library_display_glass',0,1.58,.34,1.58,1.16)
    g.signs+=display.signs
    for i in (2,8,14):
        step=g.scene.objects.get('walk-floor_literature_stair_'+str(i))
        if step:
            z=-2.75-i*.28;h=(i+1)*3.36/20
            g.box('stair_tread_nosing',-2,h+.008,z+.14,1.64,.012,.032,'#b0a087',record=False)
    # Close the underside of the upper floor and the lower stair sides, while
    # retaining the existing stair opening and accessible upper landing.
    g.box('cutaway_attic_underside_soffit',-5.88,3.195,-2.9,6.04,.06,12.06,'#352d24',group='05_Cutaway_Roof',record=False)
    for x in (-2.98,-1.02):
        g.box('museum-wall_stair_side_enclosure',x,1.52,-5.4,.13,3.04,5.7,'#e5dfcb',True)
        g.box('stair_door_jamb',x,1.38,-2.5,.14,2.76,.17,'#5c3d27',record=False)
    g.box('stair_opening_lintel',-2,2.79,-2.5,2.10,.15,.17,'#5c3d27',record=False)
    g.box('stair_room_name_plate',-2,2.98,-2.43,1.45,.17,.022,'#e6e4d7',record=False)
    g.label('영산강 문학쉼터',-2,2.98,-2.415,1.36,.10,color='#5a5b4e')
    g.box('stair_caution_plate',-2,1.12,-4.30,.41,.12,.015,'#e1ddcb',record=False)
    g.label('계단 조심',-2,1.12,-4.286,.38,.055,color='#4b4c40')
    # Small photographed furnishings beside the stair, kept clear of its approach.
    g.vessel('library_fire_extinguisher',1.58,.04,-7.95,1,'#a7412e',profile=[(0,.10),(.035,.13),(.42,.13),(.49,.08),(.53,.055)])
    g.box('fire_extinguisher_handle',1.58,.64,-7.95,.18,.04,.075,'#454943',record=False)
    g.tube('fire_extinguisher_hose',(1.67,.54,-7.95),(1.73,.23,-7.95),.016,'#383f37',n=8)
    g.box('fire_extinguisher_label',1.58,.30,-7.811,.12,.19,.01,'#e4dfcd',record=False)
    g.tube('library_notice_stand',(1.52,.02,-7.12),(1.52,1.12,-7.12),.03,'#333e37',n=12)
    g.box('library_notice_plate',1.52,1.16,-7.12,.55,.40,.025,'#303c36',record=False)
    g.box('library_notice_sheet',1.52,1.16,-7.10,.48,.33,.01,'#dfe2d6',record=False)
    g.label('서재 이용 안내',1.52,1.20,-7.088,.42,.055,color='#5e6658')
    # The previous empty graphic strips are enriched with original physical
    # interpretation diagrams, never unreadable scans of the copyrighted panels.
    east=Geometry(g.scene,(8.77,-1),math.pi/2)
    for i in range(6):
        x=-2.4+i*.86;y=.94+.13*math.sin(i)
        east.box('literature_interpretation_card',x,y,.085,.67,.50,.022,'#bcb7a0',record=False)
        east.label(['강','포구','마을','길','기억','문학'][i],x,y+.05,.102,.50,.115,color='#655949')
        if i<5:east.box('literature_interpretation_connector',x+.43,y,.089,.20,.012,.015,'#93866a',record=False)
    g.signs+=east.signs

def literature(scene):
    g,world=basic_literature(scene)
    top=3.36
    # The old 2.1 m wall stopped below the ceiling and its west floor edge
    # stopped short of the wall. Replace the generated pieces as one envelope.
    names={'attic_wall','attic_wall_door_opening','attic_wall_end','attic_white_ceiling','walk-floor_attic_reading'}
    for obj in list(scene.objects):
        if any(obj.name==name or obj.name.startswith(name+'.') for name in names):bpy.data.objects.remove(obj,do_unlink=True)
    g.solids[:]=[s for s in g.solids if s['name'] not in names]
    g.box('walk-floor_attic_reading',-5.88,top-.06,-2.9,6.04,.12,12.06,'#aaa575')
    g.box('attic_wall',-8.85,top+1.22,-2.9,.20,2.44,12.06,'#e3dfd2',True,group='05_Cutaway_Roof')
    g.box('attic_wall_door_opening',-2.9,top+1.22,-2.3,.16,2.44,10.6,'#e3dfd2',True,group='05_Cutaway_Roof')
    for z in (-8.94,3.10):g.box('attic_wall_end',-5.88,top+1.22,z,6.10,2.44,.20,'#e3dfd2',True,group='05_Cutaway_Roof')
    g.box('attic_white_ceiling',-5.88,top+2.43,-2.9,6.12,.18,12.12,'#dddace',group='05_Cutaway_Roof')
    attic_details(g,top);ground_details(g)
    world['groundExhibition']=ground_exhibition(g)
    for color in ('#30281f','#38291f','#504333','#796344','#b38957','#735133','#5c3d27','#755032','#352d24','#423727','#48382b'):texture(g,color,'wood')
    for color in ('#aeb080','#a5a778','#b4b486','#a7a775','#b1af80','#a4a16d'):texture(g,color,'tatami')
    for color in ('#e3dfd2','#dddace','#e5dfcb'):texture(g,color,'plaster')
    for obj in scene.objects:
        if obj.type=='MESH':
            if obj.name.startswith('walk-floor_attic') or all(v.co.z>=top-.13 for v in obj.data.vertices):obj['hide_in_overview']=True
            # Box side faces need a second UV axis for visible wood grain.
            uv=obj.data.uv_layers.active
            if uv:
                for poly in obj.data.polygons:
                    for li in poly.loop_indices:
                        v=obj.data.vertices[obj.data.loops[li].vertex_index].co
                        uv.data[li].uv=(v.y/1.8,v.z/1.8) if abs(poly.normal.x)>.5 else (v.x/1.8,(v.y if abs(poly.normal.z)>.5 else v.z)/1.8)
    # Keep the small room from washing out under three near-ceiling point lights.
    for light in g.lights:
        if light['position'][1]>3.36:light['intensity']=16
    world['arrivals']['reading']=dict(x=-7.50,z=1.95,height=top,yaw=0)
    world['arrivals']['exhibit']=dict(x=5.8,z=3.8,height=0,yaw=.25)
    world['arrivals']['veranda']=dict(x=-5.7,z=7.25,height=0,yaw=-math.pi/2)
    world['detailRevision']='literature-ground-1'
    world['limitations']+=['Attic walls and floor seams are sealed. Furniture counts, room dimensions and shelf heights are photo-proportioned estimates. White attic cubbies are left mostly empty as in reference 149482; dense book collections are downstairs.']
    world['solids']=g.solids
    return g,world
