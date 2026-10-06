"""Preserve v79 artist scene; complete photograph-observed first-floor exhibits.

Panel illustrations and craft motifs are original interpretations. Unmeasured
positions/dimensions are explicitly inferred; no unobserved second floor is invented.
"""
import bpy,math,random,json,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from yeongsanpo_geometry import Geometry,place
from yeongsanpo_gallery_detail import town_relief
from scene_export_v91 import surface,export
O=R/'outputs/history-gallery-v91';O.mkdir(parents=True,exist_ok=True)
S=R/'outputs/yeongsanpo-v79/yeongsanpo-history-detail-v79.blend'
TARGET=O/'yeongsanpo-history-complete-v91.blend'
WP=R/'public/yeongsanpo-history-world.json'
rng=random.Random(9104)
def keep(o):o['keep_web']=True;return o
def delete(prefixes):
    for o in list(bpy.context.scene.objects):
        if any(o.name.startswith(p) for p in prefixes):bpy.data.objects.remove(o,do_unlink=True)
def ceramic(g,name,x,y,z,r=.2,h=.12,color='#c6d1c8'):
    return g.vessel(name,x,y,z,1,color,profile=[(0,r*.52),(h*.12,r*.58),(h*.65,r*.93),(h,r),(h*1.03,r),(h*.99,r*.86),(h*.28,r*.45)])
def dish(g,kind,x,y,z):
    ceramic(g,'v91_food_plate',x,y,z,.51,.07,'#ebeadb')
    if kind==0:
        ceramic(g,'v91_soup_bowl',x,y+.035,z,.34,.18,'#171d19')
        g.vessel('v91_soup_surface',x,y+.182,z,1,'#a69f73',profile=[(0,.294),(.009,.299)])
        for i in range(35):
            a=rng.random()*math.tau;r=.27*math.sqrt(rng.random())
            g.rock('v91_soup_greens',x+math.cos(a)*r,y+.20,z+math.sin(a)*r,.04,.02,.12,rng.choice(['#526e3c','#68874e','#d1c590']),rng)
    elif kind==1:
        for i in range(22):
            a=(i/21)*math.pi*1.35+math.pi*.3;r=.29
            g.rock('v91_samhap_skate' if i<11 else 'v91_samhap_pork',x+math.cos(a)*r,y+.095,z+math.sin(a)*r,
                .13,.035,.17,'#b08a82' if i<11 else '#d2bba0',rng)
        for i in range(15):
            a=rng.random()*math.tau;r=.13*math.sqrt(rng.random())
            g.rock('v91_samhap_kimchi',x+math.cos(a)*r,y+.1+i%3*.01,z+math.sin(a)*r,.10,.025,.12,rng.choice(['#b46833','#af7c30','#9d552b']),rng)
    else:
        verts=[(x-.37,y+.08,z-.30),(x+.37,y+.08,z-.3),(x+.4,y+.10,z+.19),(x,y+.17,z+.35),(x-.4,y+.10,z+.19)]
        g.mesh('v91_steamed_skate',verts,[(0,1,2,3,4)],'#a0a377')
        for i in range(34):
            a=rng.random()*math.tau;r=.31*math.sqrt(rng.random())
            g.tube('v91_steamed_skate_garnish',(x+math.cos(a)*r,y+.155,z+math.sin(a)*r),(x+math.cos(a)*r+.04,y+.16,z+math.sin(a)*r+.1),.009,'#738348',n=6)
    ceramic(g,'v91_side_sauce_bowl',x+.39,y,z+.58,.13,.10)
    ceramic(g,'v91_side_sauce_bowl',x+.4,y,z-.59,.13,.10)
    g.vessel('v91_sauce',x+.39,y+.078,z+.58,1,'#69492a',profile=[(0,.10),(.003,.105)])
def cloth(g,name,x,y,z,w,d,color):
    n,m=24,20;v=[]
    for j in range(m+1):
        for i in range(n+1):
            u=i/n;vv=j/m;yy=y+.015*math.sin(u*25+vv*6)+.012*math.sin(vv*32)
            v.append((x+(u-.5)*w,yy,z+(vv-.5)*d))
    ob=g.mesh(name,v,[(j*(n+1)+i,j*(n+1)+i+1,(j+1)*(n+1)+i+1,(j+1)*(n+1)+i) for j in range(m) for i in range(n)],color,smooth=True)
    ob.data.materials[0].use_nodes=True;ob.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.96
    return ob
def folded_scarf(g,x,y,z,color):
    n,m=40,16;v=[]
    for j in range(m+1):
        vv=j/m
        for i in range(n+1):
            a=i/n*math.tau*1.25;r=.13+.11*vv
            v.append((x+math.cos(a)*r,y+.07+.065*math.sin(a*3)+.04*vv,z+math.sin(a)*r+.08*vv))
    g.mesh('v91_craft_folded_scarf',v,[(j*(n+1)+i,j*(n+1)+i+1,(j+1)*(n+1)+i+1,(j+1)*(n+1)+i) for j in range(m) for i in range(n)],color,smooth=True)
def case(g,name,x,z,w,d):
    keep(g.box('v91_craft_case_'+name,x,.49,z,w,.98,d,'#474540',True))
    g.box('v91_craft_linen_base',x,.99,z,w-.07,.025,d-.07,'#d5d1bf',record=False)
    for xx in (x-w/2,x+w/2):g.glass('v91_craft_side_glass',xx,1.32,z,d,.65,.012,math.pi/2)
    for zz in (z-d/2,z+d/2):g.glass('v91_craft_end_glass',x,1.32,zz,w,.65,.012)
    keep(g.box('v91_craft_glass_lid_'+name,x,1.65,z,w,.012,d,'#97b6be',record=False))
    for xx in (x-w/2,x+w/2):
        for zz in (z-d/2,z+d/2):g.tube('v91_case_glass_seam',(xx,1,zz),(xx,1.655,zz),.008,'#b8c7bd',n=6)
    # Plate faces the open gallery, rather than hovering inside the case.
    g.box('v91_case_label_card',x,1.36,z-d*.27,.37,.27,.018,'#eeeee4',record=False)
    g.label(name,x,1.36,z-d*.27-.011,.33,.058,rotation=math.pi,color='#3a4845')
def original_round_landscape(g,x,y,z,r,index):
    ob=keep(g.tube('v91_river_eight_scene_'+str(index),(x,y,z),(x,y,z+.026),r,'#99b3a7',n=64))
    # Original layered landscape reliefs, not unlicensed photographic scans.
    for j,col in enumerate(['#a8b7ad','#7d9690','#59776e']):
        for k in range(9):
            xx=x-r*.86+k*r*.215;yy=y-r*.06+j*r*.18+r*.13*math.sin(k*.8+index)
            g.box('v91_scene_hill',xx,yy,z+.045+j*.006,r*.22,r*.25,.014,col,record=False)
    g.box('v91_scene_water',x,y-r*.27,z+.08,r*1.5,r*.24,.015,'#729a9b',record=False)
    g.label(str(index+1),x,y-r*.65,z+.09,r*.7,.10,color='#f4ede1')

if '--export-only' not in sys.argv:
    if TARGET.exists():raise RuntimeError('Saved artist revision already exists; use export-only or a fresh revision')
    source_sha=hashlib.sha256(S.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(S))
    before=WP.read_bytes();(O/'world-before.json').write_bytes(before);world=json.loads(before);g=Geometry(bpy.context.scene)
    original_names={o.name for o in bpy.context.scene.objects}
    # Remove generic rule placeholders and duplicated generic dishes, retaining observed exhibits.
    delete(['interpretation_rule','food_slice','food_ceramic_plate','food_small_bowl','label_홍어회','label_홍어 삼합','label_홍어찜'])
    world['signs']=[s for s in world['signs'] if s['text'] not in ['홍어회','홍어 삼합','홍어찜']]
    for k,z in enumerate((2,3.8,5.6)):
        dish(g,k,4.82,1.053,z)
        g.box('v91_food_label_card',4.82,1.83,z-.57,.50,.29,.017,'#edeade',record=False)
        g.label(['홍어애국','홍어삼합','홍어찜'][k],4.82,1.83,z-.582,.46,.08,rotation=math.pi,color='#344039')
    # Add the two documented banks/transport/history subjects with legible original short captions.
    west=Geometry(bpy.context.scene,(-5.62,0),-math.pi/2)
    for x,title,body in [(-4.65,'운송수단의 발달','강을 오가던 배와 사람들'),(-1.35,'개폐식 목교','포구를 연결하던 다리'),(1.9,'영산포 등대','강변에 남아 있는 등대')]:
        west.label(title,x,2.89,.05,2.5,.15,color='#e5dfce');west.label(body,x,2.69,.05,2.5,.095,color='#c5cfca')
    for i,(x,title,body) in enumerate([(5.5,'호남 3대 근대도시 영산포','포구를 따라 모였던 시장과 건축'),(7.2,'문학으로 읽는 영산포','강과 마을을 기록한 사람들의 이야기')]):
        west.label(title,x,1.47,.38,1.48,.105);west.label(body,x,1.32,.38,1.48,.065)
    east=Geometry(bpy.context.scene,(5.72,0),math.pi/2)
    entries=[(-6.6,'영산포 지명 유래','영산강과 포구, 정착과 교역의 기억'),(-2.5,'영산포 홍어','흑산도와 영산포를 잇던 강의 길'),(1.6,'홍어 삭히는 방법','옹기에 담아 숙성하던 포구의 음식'),(5.6,'영산포 홍어축제','지역의 음식과 삶이 함께하는 축제')]
    for x,title,body in entries:
        east.label(title,x,2.56,.07,3.4,.16,color='#f1e0c3');east.label(body,x,2.33,.07,3.4,.11,color='#d0c8b5')
    # Food-related raised display illustrations retain the rhythm of framed plates in photographs.
    for i,x in enumerate([-3.2,.5,3.1]):
        keep(east.box('v91_food_wall_picture_'+str(i),x,1.74,.10,1.0,.77,.085,'#ccc6af',record=False))
        for j in range(9):
            xx=x-.34+(j%3)*.32;yy=1.48+(j//3)*.20
            east.rock('v91_food_wall_relief',xx,yy,.155,.21,.12,.045,['#b77970','#a7854e','#b7b39d'][i],rng)
    east.label('젓갈의 종류',-6.5,1.20,.1,2.4,.14)
    east.label('포구의 맛과 생활',-6.5,.96,.1,2.4,.10,color='#cfc8b8')
    # Two landscape panels, eight circular illustrations, documented near the craft displays.
    front=Geometry(bpy.context.scene,(1.45,9.29),math.pi)
    for i in range(2):
        cx=-1.5+i*3
        keep(front.box('v91_eight_views_panel_'+str(i),cx,2.04,0,2.90,2.54,.07,'#765965',record=False))
        front.label('영산강의 8경' if i==0 else '강을 따라 만나는 풍경',cx,3.01,.05,2.6,.17)
    circles=[(-2.36,2.40,.44),(-1.37,2.32,.52),(-1.9,1.26,.50),(.72,2.4,.40),(1.68,2.42,.39),(2.47,1.79,.43),(.85,1.32,.37),(1.64,1.31,.36)]
    names=['영산호','느러지','황포돛배','죽산보','나주평야','송촌보','풍영정','담양 대나무숲']
    for i,(x,y,r) in enumerate(circles):original_round_landscape(front,x,y,.05,r,i);front.label(names[i],x,y-r-.10,.15,.95,.084)
    # Photographed craft vitrines: bags, scarves, patchwork mats, dyed blue garments.
    configs=[('자미공방',-4.78,7.82,1.58,1.34),('어울리기공방',-.60,8.29,1.94,1.46),('목사골공방',1.40,8.29,1.94,1.46),('최현공방',3.40,8.29,1.94,1.46)]
    for k,(name,x,z,w,d) in enumerate(configs):
        case(g,name,x,z,w,d)
        if k==0:
            for j,c in enumerate(['#98724c','#c7b895','#725f85']):
                xx=x-.46+j*.43
                g.vessel('v91_craft_pouch',xx,1.015,z-.16,.28,c,profile=[(0,.4),(.35,.6),(.62,.46),(.75,.22),(.80,.2)])
                for n in range(12):
                    a=n*math.tau/12;g.tube('v91_pouch_gather',(xx+math.cos(a)*.065,1.23,z-.16+math.sin(a)*.065),(xx+math.cos(a)*.125,1.14,z-.16+math.sin(a)*.125),.005,'#d5c5a0',n=5)
        elif k==1:
            folded_scarf(g,x-.40,1.02,z-.22,'#577f9d');folded_scarf(g,x+.39,1.02,z+.04,'#c49a4c')
            g.box('v91_craft_flower_art_board',x,1.28,z+.51,.58,.47,.02,'#d7afbd',record=False)
            for j in range(10):
                a=j*.67;g.tube('v91_pressed_flower_stem',(x-.05,1.09,z+.49),(x+math.sin(a)*.18,1.40+j%3*.05,z+.49),.004,'#7b7850',n=5)
        elif k==2:
            for j in range(4):
                for i in range(6):cloth(g,'v91_craft_patchwork',x-.68+i*.24,1.02,z-.36+j*.19,.237,.187,['#efeddb','#4f7995','#c98b5e','#c1586b','#bfa942'][(i+j*3)%5])
            ceramic(g,'v91_craft_celadon_cup',x-.56,1.025,z+.43,.12,.12)
            for j in range(3):g.box('v91_craft_wood_stand',x+.13+j*.25,1.07+j*.05,z+.42,.16,.09+j*.1,.21,'#63513c',record=False)
        else:
            cloth(g,'v91_indigo_garment_left',x-.29,1.04,z-.10,.53,.93,'#425b88')
            cloth(g,'v91_indigo_garment_right',x+.28,1.04,z-.10,.53,.93,'#5b7c9b')
            for dx in (-.68,.68):cloth(g,'v91_indigo_sleeve',x+dx,1.044,z+.1,.29,.53,'#425b88')
            for side in (-1,1):g.tube('v91_indigo_garment_ties',(x,1.09,z+.26),(x+side*.16,1.083,z-.07),.009,'#293d62',n=8)
            folded_scarf(g,x-.46,1.05,z+.43,'#718ba5')
    # The entry introduction mentions a lighthouse model; its exact position/scale is inferred.
    keep(g.vessel('yeongsanpo_lighthouse_gallery_model',-3.73,.05,-7.65,1,'#c4c6b7',profile=[(0,.22),(.12,.24),(.86,.16),(.99,.23),(1.04,.23),(1.04,.16),(1.32,.16),(1.34,.21)]))
    g.collider('v91_exhibit_lighthouse',[[-4.02,-7.98],[-3.44,-7.98],[-3.44,-7.32],[-4.02,-7.32]],0,1.4)
    g.label('영산포 등대 모형',-3.73,.05,-7.20,.8,.085)
    # Wall skirting and glass corner seams improve close-up scale without false rooms.
    for x in [-5.83,5.83]:g.box('v91_wall_skirting',x,.055,0,.06,.11,18.9,'#1e2423',record=False)
    for x in [-4.12,5.6]:
        for z in [-8.5,-4.5,0,4,8]:g.box('v91_ceiling_aimed_light_recess',x,3.35,z,.16,.06,.29,'#121718',record=False)
    world['solids']+=g.solids
    world['signs']+=g.signs+west.signs+east.signs+front.signs
    world['places']+=[place('history-crafts','지역 공예 전시',.9,6.8,1.5,indoor=True),place('history-landscapes','영산강 8경',2.3,6.8,1.2,indoor=True)]
    world['arrivals'].update(crafts=dict(x=.9,z=6.6,yaw=math.pi),landscapes=dict(x=2.3,z=6.6,yaw=math.pi),boat=dict(x=-2.5,z=-6,yaw=-.42))
    world['walkRoute']=[[-3,7.4],[-2,5],[-2,0],[-2.5,0],[-2.5,-6],[-2.5,0],[2.7,0],[2.7,4],[2.7,6.6],[.9,6.6],[-3,6.6],[-3,7.4],[-3,9.85]]
    world['viewMode']='panorama';world['lighting']=dict(exposure=1.25,ambient=.65,sun=.06)
    world['galleryRevision']='history-complete-v91';world['exhibitSections']=['origin','timeline','transport','modern-city','literature','boat-screen','skate-food','onggi','salted-seafood','eight-river-scenes','four-local-crafts']
    world['limitations']=['2026-09 KTO description cross-checked with 2024-03-24 visitor photographs and undated official interior photographs.',
        'First-floor photographed exhibit subjects are represented; complete present-day floor plan and second-floor use are unverified.',
        'Room size 12 x 19m retained from v79 estimates. Fixture positions, craft motifs and short panel captions are original interpretations; not museum scans.']
    bpy.context.scene['research_revision']='history-complete-v91: photo-observed exhibit subjects; inferred physical dimensions and layout'
    new=[o for o in bpy.context.scene.objects if o.name not in original_names]
    for ob in new:
        if ob.type=='MESH' and any(s in ob.name for s in ['wood_stand','lighthouse_gallery']):surface(ob,'wood' if 'wood' in ob.name else 'concrete')
        ob['reference_basis']='Observed object category, inferred scale/position; original artwork'
    for f in bpy.data.fonts:
        if f.filepath and Path(f.filepath).is_file() and not f.packed_file:f.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
    assert hashlib.sha256(S.read_bytes()).hexdigest()==source_sha
    WP.write_text(json.dumps(world,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
    refs=json.loads((R/'knowledge/sources/yeongsanpo-v79-verification.json').read_text(encoding='utf8'))
    ref=next(n for n in refs['navigation'] if n['scene']=='yeongsanpo-history');keys=ref['navigationKeys']
    nav={k:world.get(k) for k in keys}
    def canonical(v):return {k:canonical(v[k]) for k in sorted(v)} if isinstance(v,dict) else [canonical(x) for x in v] if isinstance(v,list) else v
    report=dict(revision=world['galleryRevision'],sourceBlend=str(S.relative_to(R)).replace('\\','/'),editedBlend=str(TARGET.relative_to(R)).replace('\\','/'),
        sourceSha256=source_sha,sourcePreserved=True,legacyNavigationSha256=ref['navigationSha256'],navigationKeys=keys,
        navigationSha256=hashlib.sha256(json.dumps(canonical(nav),ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),
        sections=world['exhibitSections'],craftCases=4,riverScenes=8,foodDishes=['홍어애국','홍어삼합','홍어찜'],
        unchangedDoorwayAndSpawn=world['spawn']==json.loads(before)['spawn'] and world['portals']==json.loads(before)['portals'],
        assumptions=world['limitations'])
else:
    report=json.loads((R/'knowledge/sources/history-gallery-v91.json').read_text(encoding='utf8'));bpy.ops.wm.open_mainfile(filepath=str(TARGET))
report['export']=export('yeongsanpo-history',O)
(R/'knowledge/sources/history-gallery-v91.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('HISTORY_V91_COMPLETE',json.dumps(report['export']),flush=True)
