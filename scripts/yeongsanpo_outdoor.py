"""One georeferenced Yeongsanpo riverfront, Hong-eo street and museum exteriors."""
import json, math, random
from pathlib import Path
from yeongsanpo_geometry import Geometry,world_data,place
from literature_courtyard import courtyard,paved_outline
from literature_context import build_context
from literature_boundary import add_boundary_detail
from yeongsanpo_street_detail import wharf_detail,roof_form,facade_detail,streets,samhwa
from yeongsanpo_riverfront import frontage,courtyard as frontage_courtyard,finishes as frontage_finishes,paving as frontage_paving

ROOT=Path(__file__).resolve().parents[1]
ORIGIN=[126.7105,35.0008]
def xy(p):return [(p[0]-ORIGIN[0])*111320*math.cos(math.radians(ORIGIN[1])),(ORIGIN[1]-p[1])*111320]

def clip(poly,axis,value,less=True):
    result=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ia=(a[axis]<=value) if less else (a[axis]>=value);ib=(b[axis]<=value) if less else (b[axis]>=value)
        if ia:result.append(a)
        if ia!=ib:
            t=(value-a[axis])/(b[axis]-a[axis]);result.append([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])])
    return result

def clip_line(poly,a,b,inside=True):
    def side(p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
    out=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        sp,sq=side(p),side(q);ip=sp>=0 if inside else sp<=0;iq=sq>=0 if inside else sq<=0
        if ip:out.append(p)
        if ip!=iq:
            t=sp/(sp-sq);out.append([p[k]+(q[k]-p[k])*t for k in (0,1)])
    return out

def subtract(poly,cutter):
    pieces=[];remaining=poly
    for a,b in zip(cutter,cutter[1:]+cutter[:1]):
        outside=clip_line(remaining,a,b,False)
        if len(outside)>2:pieces.append(outside)
        remaining=clip_line(remaining,a,b)
        if not remaining:break
    return pieces

def clipped_segment(a,b,bounds):
    t0,t1=0,1;dx,dz=b[0]-a[0],b[1]-a[1]
    for p,q in [(-dx,a[0]-bounds[0]),(dx,bounds[1]-a[0]),(-dz,a[1]-bounds[2]),(dz,bounds[3]-a[1])]:
        if abs(p)<1e-10:
            if q<0:return None
        else:
            r=q/p
            if p<0:t0=max(t0,r)
            else:t1=min(t1,r)
            if t0>t1:return None
    return [[a[0]+t*dx,a[1]+t*dz] for t in (t0,t1)]

def line_distance(p,a,b):
    dx,dz=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dz)/(dx*dx+dz*dz or 1)))
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dz)

def in_poly(p,pts):
    inside=False
    for a,b in zip(pts,pts[1:]+pts[:1]):
        if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside

def wharf(scene,g):
    level=-6.4;dock=Geometry(scene,(-143,130),-.337)
    dock.box('walk-floor_dock',0,level-.12,-16,85,.24,26,'#9a8060')
    for i in range(169):dock.box('dock_plank_seam',-42.25+i*.5,level+.006,-16,.018,.008,25.9,'#665a49',record=False)
    dock.box('retaining_wall',-6,-3.2,0,73,6.4,.4,'#a4a998',True)
    for x in (-42.45,42.45):dock.box('dock_return_retaining_wall',x,-3.25,-14.5,.32,6.5,29,'#9c9f8e',True)
    dock.box('dock_stair_side_masonry',30.35,-3.4,-7,.3,6.4,14,'#a4a998',True)
    for row in range(11):
        dock.box('retaining_masonry_course',-6,-.5-row*.53,-.225,72.8,.018,.025,'#7c897e',record=False)
    for x in (-41,41):dock.railing('dock_upper_side_guard',(x,-26),(x,-1),0,glass=False)
    route=[dock.point(36,1)]
    for i in range(40):
        z=-.175-i*.35;top=-(i+1)*.16
        dock.box('walk-floor_dock_stair_'+str(i),36,top-.09,z,11,.18,.37,'#b8b8a7');route.append(dock.point(36,z))
        if top>level+.18:dock.box('dock_stair_solid_infill',36,(top-.18+level-.24)/2,z,11,top-.18-level+.24,.37,'#a7aa9b',record=False)
    for x in (30,42):
        dock.tube('dock_stair_handrail',(x,1.0,0),(x,-5.4,-14),.055,'#e2ddc9')
        for i in range(12):dock.tube('dock_stair_post',(x,-i/11*6.4,-i/11*14),(x,1-i/11*6.4,-i/11*14),.035,'#dedac8')
    # The tourism coordinate is a representative marker; photo alignment places
    # the lighthouse immediately against the lower retaining wall.
    lx,lz=0,-2.3
    dock.vessel('yeongsanpo_lighthouse',lx,level,lz,1,'#e2e3d6',profile=[(0,1),(5.4,1),(6.65,1.95),(6.75,1.95),(6.8,1.6),(8.2,1.6),(8.4,1.82),(8.65,1.82)])
    dock.box('lighthouse_lantern_window',lx,level+7.6,lz-1.61,.48,.75,.04,'#719a9d',record=False)
    for i in range(24):
        a=i*math.tau/24;b=(i+1)*math.tau/24
        dock.tube('lighthouse_guard_post',(lx+math.cos(a)*1.98,level+6.7,lz+math.sin(a)*1.98),(lx+math.cos(a)*1.98,level+7.55,lz+math.sin(a)*1.98),.024,'#b6c1b9')
        dock.tube('lighthouse_round_guard',(lx+math.cos(a)*1.98,level+7.55,lz+math.sin(a)*1.98),(lx+math.cos(b)*1.98,level+7.55,lz+math.sin(b)*1.98),.032,'#b6c1b9')
    dock.collider('lighthouse_collision',[[lx-1.1,lz-1.1],[lx+1.1,lz-1.1],[lx+1.1,lz+1.1],[lx-1.1,lz+1.1]],level,8.65)
    dock.label('영산포 등대',lx,level+1.1,lz-1.12,1.75,.25,rotation=math.pi,color='#727464')
    # Moving boats are independently authored GLBs, never part of the static batch.
    for x,name in [(-23,'나주호'),(16,'왕건호')]:
        dock.box('boarding_information',x,level+1.3,-27.7,2.1,.6,.08,'#315451',record=False)
        dock.label(name+' 승선',x,level+1.3,-27.64,1.9,.25,color='#ede1bf')
        for dx in (-.85,.85):dock.box('boarding_sign_post',x+dx,level+.65,-27.7,.05,1.3,.05,'#465a51',record=False)
    dock.box('ticket_house',-33,level+1.5,-9,10,3,4,'#343c3b',True)
    dock.window('ticket_counter',-33,level+1.7,-6.9,7,1.5)
    dock.label('황포돛배 매표소',-33,level+2.75,-6.8,8,.34,color='#ece6d8')
    for x in range(-39,40,5):dock.tube('dock_bollard',(x,level,-28.3),(x,level+.45,-28.3),.16,'#dddcd0')
    dock.box('landing_information_board',-16,1.4,2,10,1.2,.14,'#566858',record=False)
    dock.label('황포돛배 선착장',-16,1.4,2.1,8.9,.55,color='#e5dfc8')
    for x in (-20,-12):dock.box('landing_information_post',x,.8,2,.12,1.6,.12,'#5e6754',record=False)
    dock.railing('promenade_guard',(-42,0),(29,0),0,glass=False)
    # Original diagram, not a copy of the copyrighted mural.
    dock.box('wharf_original_mural',-7,-3.2,-.24,70,5.5,.035,'#7aa4ac',record=False)
    for y,color in [(-2.3,'#c6a365'),(-4.6,'#6c9390')]:dock.box('wharf_mural_band',-7,y,-.265,70,.85,.02,color,record=False)
    for x in (-29,-6,17):
        dock.mesh('wharf_mural_boat',[(x-3,-4,-.285),(x+3,-4,-.285),(x+2,-4.65,-.285),(x-2,-4.65,-.285)],[(0,1,2,3)],'#715848')
        dock.box('wharf_mural_mast',x,-2.85,-.29,.07,2.3,.025,'#685943',record=False)
        dock.box('wharf_mural_sail',x-1,-2.7,-.295,1.7,1.8,.025,'#c4a267',record=False)
    wharf_detail(dock)
    g.solids+=dock.solids;g.signs+=dock.signs
    return dock,route

def exterior(g,kind):
    if kind=='history':
        # White render/timber frame, balcony rings and glass conservatory.
        for x,w in [(-5.05,1.9),(2.05,7.9)]:g.box('photo-building_history_front',x,1.7,6,w,3.4,.2,'#eee8d7',True)
        for x in (-6,6):g.box('photo-building_history_side',x,3.4,0,.22,6.8,12,'#ddd7c6',True)
        g.box('photo-building_history_back',0,3.4,-6,12,6.8,.2,'#e7ddc8',True)
        g.box('history_door_header',-3,2.95,6,2.2,.9,.2,'#e8e1cf')
        g.box('history_recess_dark',0,1.6,-1,11.8,3.2,.1,'#393c35',record=False)
        for x in (-5.8,-4.1,-1.9,1,5.8):g.box('history_exposed_timber',x,1.7,6.13,.14,3.4,.13,'#947b56',record=False)
        for y in (.18,3.28):g.box('history_timber_band',0,y,6.13,12,.18,.16,'#987f5a',record=False)
        g.window('history_front_window',2.8,1.95,6.15,4.4,1.7)
        for x in (-4.04,-1.96):g.box('history_door_frame',x,1.25,6.1,.065,2.5,.1,'#897966',record=False)
        # Leave an open doorway to the interior portal instead of an invisible glass wall.
        g.glass('history_open_door',-4.05,1.2,5.25,1.55,2.3,rotation=math.pi/2)
        g.box('history_signboard',0,3.69,6.13,7.3,.58,.16,'#69503b',record=False)
        g.label('영산포 역사갤러리',0,3.69,6.23,6.7,.36,color='#fff4dd')
        g.box('history_brass_plate',-5,1.98,6.17,1.5,.82,.06,'#9f9560',record=False)
        g.label('영산포\n역사갤러리',-5,1.98,6.22,1.35,.21,color='#302e29')
        g.box('history_balcony',0,3.45,1.5,12,.2,9,'#aaa393',record=False)
        g.box('history_upper_wall',-2,5.2,-1,8,3.4,.16,'#e4decd',record=False)
        for x in (-4,-1):g.window('history_upper_window',x,5.3,-.85,2.2,1.5)
        for x in (-5.8,5.8):g.box('balcony_guard',x,4.13,3,.04,1.2,5.9,'#3d403c',record=False)
        for y in (3.62,4.62):g.box('balcony_guard',0,y,5.9,11.7,.05,.05,'#3d403c',record=False)
        for i in range(43):
            x=-5.75+i*.27;g.box('balcony_vertical',x,4.12,5.9,.018,1,.018,'#3d403c',record=False)
            if i%2==0:
                pts=[(x+.11*math.cos(j*math.tau/12),4.12+.11*math.sin(j*math.tau/12),5.9) for j in range(13)]
                for a,b in zip(pts,pts[1:]):g.tube('balcony_ornamental_ring',a,b,.012,'#3d403c',n=5)
        for x in (1,3,5):g.window('history_conservatory',x,5.35,3.4,1.95,2.9)
        g.box('history_conservatory_roof',3,6.85,1.2,6,.025,4.5,'#97b6be',record=False)
        g.roof('history_upper_roof',-2,6.95,-2.5,8.8,7.4,.6,'#647c72',tiles=False)
        for x in (-5.6,4.6,5.3):g.vessel('entry_planter',x,0,6.65,.46,'#9b9b84')
        return [-3,6.0],[-3,9]
    # Literature house: blue-grey tile roofs, projecting gable wing and garden.
    for x in (-9,9):g.box('photo-building_literature_side',x,1.65,0,.18,3.3,13,'#e5dfce',True)
    g.box('photo-building_literature_back',0,1.65,-6.5,18,3.3,.18,'#dfdac8',True)
    for a,b in [(-9,-1),(1,9)]:g.box('photo-building_literature_front',(a+b)/2,.5,6.5,b-a,1,.15,'#4e453a',True)
    for x in (-8,-6,-4,2,4,6,8):g.window('literature_timber_windows',x,1.93,6.54,1.9,1.75)
    g.box('literature_entry_header',0,2.95,6.5,2,.7,.20,'#5d4c39')
    for x in (-1.1,1.1):g.box('entry_brick_pier',x,1.4,7.4,.28,2.8,.28,'#855e48',True)
    g.box('entry_name_board',0,2.55,7.56,2.15,.4,.08,'#3c3930',record=False)
    g.label('타오르는 강 문학관',0,2.55,7.62,1.94,.20,color='#eee7d3')
    g.roof('literature_main_tile_roof',1,4.8,-.8,18.7,13.5,2.4,'#53616b')
    g.roof('literature_low_eaves',1,3.0,1,19.8,14.3,1.4,'#53616b')
    g.roof('literature_entry_gable',0,3.0,7.5,3.6,3.4,1,'#53616b')
    g.box('photo-building_literature_gable_wing',-6,1.8,7.5,5.5,3.6,6,'#dedbc9',True)
    g.mesh('literature_front_gable',[(-8.75,3.6,10.51),(-3.25,3.6,10.51),(-6,6.2,10.51)],[(0,1,2)],'#958b73')
    for side in (-1,1):g.mesh('literature_gabled_roof',[(-6,6.3,3.5),(-6,6.3,11),(-6+side*3.1,3.6,11),(-6+side*3.1,3.6,3.5)],[(0,1,2,3)],'#52606a','05_Cutaway_Roof')
    g.box('literature_brick_plinth',-6,.45,10.54,5.5,.9,.12,'#7b5947',record=False)
    for row in range(8):
        for i in range(20):g.box('brick_mortar',-8.7+i*.28+(row%2)*.14,.05+row*.105,10.615,.265,.012,.015,'#b9ae97',record=False)
    g.window('gable_wing_door',-6,1.35,10.64,1.7,2.6,lattice=True)
    for i in range(13):g.box('gable_vent',-6.45+i*.075,4.55,10.54,.025,.6,.04,'#4b4940',record=False)
    g.box('literature_open_entry_recess',0,1.15,5.9,1.75,2.3,.06,'#333f37',record=False)
    # A narrow timber clerestory closes the step between the two roof levels.
    g.box('literature_clerestory_front',1,4.05,5.75,17.3,1.5,.10,'#b8b4a4',record=False)
    for x in (-5,-1,3,7):
        g.box('literature_clerestory_dark_pane',x,4.2,5.81,2.8,.58,.04,'#586b66',record=False)
        g.window('literature_clerestory_window',x,4.2,5.85,2.8,.58)
    # Rear details visible in the JNFC exterior photographs.
    for x in (-7,-3,2,6):
        g.box('literature_rear_window_recess',x,1.80,-6.61,2.3,1.8,.06,'#454d43',record=False)
        g.window('literature_rear_timber_window',x,1.80,-6.65,2.3,1.8,rotation=math.pi,lattice=True)
    for x in (-8.8,8.8):g.tube('literature_rear_downpipe',(x,.08,-6.75),(x,3.25,-6.75),.055,'#4d5854',n=10)
    g.box('literature_gutter',0,3.28,-6.85,18.4,.12,.14,'#4d5854',record=False)
    for x in (-1,1):g.box('literature_rear_water_trough_side',x,.30,-7.7,.12,.60,1.1,'#959c91',True)
    for z in (-8.2,-7.2):g.box('literature_rear_water_trough_edge',0,.30,z,2.1,.60,.1,'#959c91',True)
    g.box('literature_rear_water_trough_base',0,.07,-7.7,2.1,.14,1.1,'#788c85',record=False)
    # Under-eave infill and wood soffit make the garden view read as a closed house.
    g.box('literature_closed_roof_core',0,3.4,0,17.8,.8,12.8,'#e5dfce',record=False)
    g.box('literature_front_soffit',1,2.96,7.3,19.4,.10,.8,'#6a5a43',record=False)
    for x in (-8.6,-3.4):g.tube('literature_wing_downpipe',(x,.12,10.62),(x,3.55,10.62),.046,'#525b56',n=8)
    return [0,7.2],[0,10]

def outdoor(scene):
    ref=json.loads((ROOT/'knowledge/sources/yeongsanpo-map-reference.json').read_text(encoding='utf-8'))
    data=json.loads((ROOT/'knowledge/sources/yeongsanpo-osm.geojson').read_text(encoding='utf-8'))
    g=Geometry(scene);rng=random.Random(76);bounds=[-410,395,-315,300]
    river=[xy(p) for p in ref['river']['geometry']['coordinates'][0][:-1]]
    g.polygon('mapped_river_water',river,-7.55,.08,'#527f7c')
    g.mat('#527f7c').node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.23
    # Land follows the mapped south bank. Dock is cut out so stairs can descend.
    land=river[:16]+[[395,300],[-410,300],[-410,river[0][1]]]
    dock,stair_route=wharf(scene,g)
    cutter=[dock.point(x,z) for x,z in [(-42.5,-65),(42.5,-65),(42.5,0),(-42.5,0)]]
    for i,poly in enumerate(subtract(land,cutter)):
        if len(poly)>2:g.polygon('ground_floor_south_bank_'+str(i),poly,-11,11,'#c6c4aa')
    g.box('north_bank_background',0,-5.25,-320,1000,9.5,180,'#95a77e',record=False)
    for a,b in zip(river[:15],river[1:16]):
        if line_distance(dock.point(0,-15),a,b)>65:g.segment('bank_reed_margin',a,b,3.2,7.0,'#8e9970',base=-7.4)
    roads=[]
    for road in ref['roads']:
        points=[xy(p) for p in road['coordinates']];tag=road['tags'];width=7 if tag.get('highway') in ('residential','unclassified') else 13
        if road['osmId']=='way/130634137':width=6
        roads.append(dict(id=road['osmId'],name=tag.get('name',''),points=points,width=width))
        for a,b in zip(points,points[1:]):
            segment=clipped_segment(a,b,bounds)
            if not segment:continue
            a,b=segment
            g.segment('road-edge_'+road['osmId'],a,b,width+3,.025,'#b7ae99',base=.008)
            g.segment('road_'+road['osmId'],a,b,width,.018,'#7e8582',base=.038)
            # Road surfaces also bridge the water; require-floor blocks the river.
            if tag.get('bridge')=='yes':
                g.segment('walk-floor_bridge_'+road['osmId'],a,b,width,.5,'#90978c',base=-.5)
                for j in range(1,max(2,int(math.dist(a,b)/35))):
                    t=j/max(2,int(math.dist(a,b)/35));g.box('bridge_pier',a[0]+(b[0]-a[0])*t,-4,a[1]+(b[1]-a[1])*t,2.4,8,3.2,'#a3aca4',record=False)
            length=math.dist(a,b)
            if width>7:
                for j in range(int(length/9)):
                    t=(j+.5)*9/length;c=[a[k]+(b[k]-a[k])*t for k in (0,1)];u=[(b[k]-a[k])/length for k in (0,1)]
                    g.segment('road_center_mark',[c[k]-u[k]*1.6 for k in (0,1)],[c[k]+u[k]*1.6 for k in (0,1)],.12,.006,'#ded5a9',base=.061,record=False)
    street_details=streets(g,roads)
    frontage_paving_source=json.loads((ROOT/'knowledge/sources/yeongsanpo-riverfront-paving.json').read_text(encoding='utf-8'))
    frontage_apron=frontage_paving(g,frontage_paving_source,roads)
    gallery_center=xy([126.711504,35.000721])
    # Photo GPS lies near the northwest roof corner; align its centre to the
    # visible satellite roof instead of treating a camera point as a centroid.
    literature_center=[223.92,115.07]
    # OSM footprint shells provide the surrounding street's real structure.
    count=0;samhwa_arrival=None
    for feature in data['features']:
        if not feature['properties'].get('building') or feature['geometry']['type']!='Polygon':continue
        pts=[xy(p) for p in feature['geometry']['coordinates'][0][:-1]]
        cx=sum(p[0] for p in pts)/len(pts);cz=sum(p[1] for p in pts)/len(pts)
        if not(-405<cx<390 and -300<cz<290) or math.dist((cx,cz),gallery_center)<22 or math.dist((cx,cz),literature_center)<32:continue
        h=float(feature['properties'].get('building:levels',2))*3.1
        if h>20:h=9
        color=rng.choice(['#c7bda7','#c5c7ba','#b9bcae','#b6a88e'])
        if feature['id']=='way/1120464648':
            # Partial OSM/satellite duplication, not a second 6.2m building.
            # Retain its non-overlapping ground area as the same low annex.
            r=next(r for r in json.loads((ROOT/'knowledge/sources/yeongsanpo-traced-roofs.json').read_text(encoding='utf-8'))['roofs'] if r['id']=='street_west_09')
            for j,piece in enumerate(subtract(pts,[xy(p) for p in r['footprint']])):
                g.polygon('osm-building_way_1120464648_trim_'+str(j),piece,0,4.5,'#d0cab9',True)
                g.polygon('context_roof_4648_annex_'+str(j),piece,4.5,.15,'#9baa9b')
            count+=1
            continue
        if feature['id']=='way/1000416564':h=7.3;color='#d8d9d0';samhwa_arrival=samhwa(g,pts)
        g.polygon('osm-building_'+feature['id'].replace('/','_'),pts,0,h,color,True);g.polygon('context_roof_'+str(count),pts,h,.16,rng.choice(['#6d8d91','#718779','#86857a']))
        count+=1
    # Photo-informed low-rise shop rhythm along the mapped Hong-eo street.
    traced=[];frontage_details=[]
    frontage_source=json.loads((ROOT/'knowledge/sources/yeongsanpo-riverfront-detail.json').read_text(encoding='utf-8'))
    frontage_configs={b['id']:b for b in frontage_source['buildings']}
    frontage_finishes(g)
    roof_source=json.loads((ROOT/'knowledge/sources/yeongsanpo-traced-roofs.json').read_text(encoding='utf-8'))
    for roof in roof_source['roofs']:
        pts=[xy(p) for p in roof['footprint']];pts=pts[:-1] if pts[0]==pts[-1] else pts
        cx=sum(p[0] for p in pts)/len(pts);cz=sum(p[1] for p in pts)/len(pts)
        if not(-405<cx<390 and -300<cz<290):continue
        h=roof['height'];traced.append(pts)
        if roof['id'] in frontage_configs:
            frontage_details.append(frontage(g,pts,frontage_configs[roof['id']]))
            if roof['id']=='street_west_04':frontage_courtyard(g,pts)
            continue
        g.polygon('photo-building_roof_trace_'+str(roof['id']),pts,0,h,roof['wallColor'],True)
        g.polygon('traced_roof_'+str(roof['id']),pts,h,.16,roof['roofColor'])
        facade_detail(g,pts,h,roads,len(traced))
    context_source=json.loads((ROOT/'knowledge/sources/literature-context-traces.json').read_text(encoding='utf-8'))
    context_source['roofs']+=json.loads((ROOT/'knowledge/sources/literature-close-neighbours.json').read_text(encoding='utf-8'))['roofs']
    context_footprints=build_context(g,context_source,xy);traced.extend(context_footprints)
    extra_roofs=json.loads((ROOT/'knowledge/sources/yeongsanpo-round2-roofs.json').read_text(encoding='utf-8'))
    extra_footprints=[]
    for i,roof in enumerate(extra_roofs['roofs']):
        if roof.get('reviewFlags'):continue
        pts=[xy(p) for p in roof['footprint']];pts=pts[:-1] if pts[0]==pts[-1] else pts
        walls=roof_form(g,roof,pts);extra_footprints.append(walls)
        facade_detail(g,walls,roof['height'],roads,100+i)
    traced.extend(extra_footprints)
    lane_source=json.loads((ROOT/'knowledge/sources/yeongsanpo-round2-lanes.json').read_text(encoding='utf-8'))
    extra_lanes=[]
    for lane in lane_source['lanes']:
        if lane.get('reviewFlags'):continue
        points=[xy(p) for p in lane['coordinates']]
        g.polygon('walk-floor_'+lane['id'],paved_outline(points,lane['width']),.014,.033,'#a9aa98')
        extra_lanes.append(dict(id=lane['id'],points=points,width=lane['width']))
    street=next(r for r in roads if r['id']=='way/130634137');shopcount=0
    for a,b in zip(street['points'],street['points'][1:]):
        length=math.dist(a,b);u=[(b[k]-a[k])/length for k in (0,1)];normal=[-u[1],u[0]]
        for j in range(max(1,int(length/12))):
            t=(j+.5)/max(1,int(length/12))
            for side in (-1,1):
                center=[a[k]+(b[k]-a[k])*t+normal[k]*side*8.7 for k in (0,1)]
                if math.dist(center,gallery_center)<20 or math.dist(center,literature_center)<32:continue
                if any(line_distance(center,ra,rb)<r['width']/2+6 for r in roads if r['id']!=street['id'] for ra,rb in zip(r['points'],r['points'][1:])):continue
                corners=[[center[k]+u[k]*dx+normal[k]*dz for k in (0,1)] for dx,dz in [(-4.7,-4.25),(4.7,-4.25),(4.7,4.25),(-4.7,4.25)]]
                if any(any(in_poly(p,pts) for p in corners+[center]) or any(in_poly(p,corners) for p in pts) for pts in traced):continue
                shop=Geometry(scene,center,math.atan2(u[1],u[0])+(math.pi if side==1 else 0))
                h=4.2+(shopcount%3)*1.5;shop.box('photo-building_hongeo_shop_'+str(shopcount),0,h/2,0,9.4,h,8.5,rng.choice(['#d6c6ad','#cdc8b2','#c1b6a4']),True)
                shop.box('hongeo_recessed_storefront',0,1.5,4.26,8.4,2.45,.018,'#334a48',record=False)
                shop.window('hongeo_shopfront',0,1.5,4.3,8.4,2.45)
                for x in (-2.8,-1.4,1.4,2.8):shop.box('hongeo_sliding_mullion',x,1.5,4.34,.042,2.43,.06,'#9ca9a4',record=False)
                for x in (-.35,.35):shop.tube('hongeo_door_pull',(x,1.15,4.41),(x,1.55,4.41),.021,'#c0c7bc',n=7)
                for x in (-4.5,4.5):shop.tube('hongeo_downpipe',(x,.08,4.36),(x,h-.1,4.36),.049,'#778881',n=8)
                shop.box('hongeo_storefront_plinth',0,.13,4.33,9.3,.25,.15,'#898d82',record=False)
                shop.box('hongeo_air_conditioner',3.8,2.38,4.61,.75,.5,.5,'#c7cdc2',record=False)
                for i in range(6):shop.box('hongeo_compressor_grille',3.5+i*.12,2.38,4.87,.024,.34,.02,'#71847b',record=False)
                shop.box('hongeo_signboard',0,3.18,4.4,9.3,.75,.12,rng.choice(['#6a7352','#91664c','#44625a','#93694d']),record=False)
                shop.label(['홍어 · 삼합','영산포 홍어','홍어 이야기','남도 밥상'][shopcount%4],0,3.18,4.49,8.3,.47,color='#fff1da')
                for x in (-3,0,3):shop.box('shop_awning',x,2.8,4.9,2.8,.1,1.1,'#a49776',record=False)
                shop.roof('shop_blue_roof',0,h+.15,0,10,9,1.1,['#668590','#768d82','#8c8980'][shopcount%3],tiles=False)
                if h>5:
                    shop.box('hongeo_upper_recess',0,h-1.05,4.26,6.7,1.2,.018,'#627976',record=False)
                    shop.window('shop_upper_window',0,h-1.05,4.3,6.7,1.2)
                g.solids+=shop.solids;g.signs+=shop.signs;shopcount+=1
    portals=[];arrivals={};places=[];garden_data=None
    arrivals['riverfront-shops']=dict(x=-143,z=143.8,yaw=math.pi)
    places.append(place('riverfront-shops','강변 맞은편 상가와 창고',-143,143.8,5,'상가의 처마와 간판, 뒤편의 푸른 창고 지붕을 둘러보세요.'))
    if samhwa_arrival:
        arrivals['jukjeon-alley']=dict(x=samhwa_arrival[0],z=samhwa_arrival[1],yaw=-1.3)
        places.append(place('jukjeon-alley','죽전골목 · 삼화홍어 외관',*samhwa_arrival,5,'작은 등대 장식과 적벽돌 모서리가 있는 골목 입구입니다.'))
    lane_arrival=extra_lanes[0]['points'][1]
    arrivals['west-lanes']=dict(x=lane_arrival[0],z=lane_arrival[1],yaw=math.pi)
    places.append(place('west-lanes','등대길 뒤편 골목',*lane_arrival,5,'위성사진에서 이어지는 지붕과 골목을 따라 걸어보세요.'))
    for kind,center,angle,title in [('history',gallery_center,-.67,'영산포 역사갤러리'),('literature',literature_center,.15,'타오르는 강 문학관')]:
        building=Geometry(scene,center,angle);entry,out=exterior(building,kind)
        if kind=='literature':
            garden=courtyard(building)
            boundary_detail=add_boundary_detail(building)
            garden_route=[building.point(*p) for p in garden['route']]
            lane=next(r for r in context_source['routes'] if r['id']=='museum_west_lane')
            path=[[190.31,90.22]]+[xy(p) for p in lane['coordinates'][:4]]+[garden_route[0]]
            garden_data=dict(center=center,angle=angle,boundary=[building.point(*p) for p in garden['boundary']],approach=path,walkRoute=garden_route,enclosure=boundary_detail)
            arrival=building.point(*garden['gate']);arrivals['literature-garden']=dict(x=arrival[0],z=arrival[1],yaw=-angle)
            places.append(place('literature-garden','타오르는 강 문학관 마당',*arrival,5,'자갈 화단과 디딤길을 지나 문학관으로 들어가 보세요.',arrival=arrival))
            side=building.point(10.05,3);arrivals['literature-side']=dict(x=side[0],z=side[1],yaw=math.pi/2-angle)
            places.append(place('literature-side','문학관 측면 · 목재 울타리',*side,3,'격자창과 처마, 별채와 경계 울타리를 가까이 둘러보세요.',arrival=side))
        g.solids+=building.solids;g.signs+=building.signs
        p=building.point(*entry);q=building.point(*out)
        portals.append(dict(id=kind+'-entry',position=p,radius=.83,target='yeongsanpo-'+kind,arrival='entry',label=title+' · 문 안으로 걸어가면 실내가 열립니다.'))
        arrivals[kind+'-exit']=dict(x=q[0],z=q[1],yaw=math.pi-angle)
        places.append(place(kind,title,*p,7,'입구로 들어가면 상세 실내가 열립니다.',arrival=q))
        # A narrow entrance path connects the door to the street network.
        nearest=min([p for r in roads for p in r['points']],key=lambda p:math.dist(p,q))
        path=path if kind=='literature' else [nearest,q]
        for a,b in zip(path,path[1:]):g.segment('path_'+kind+'_approach',a,b,2.6,.025,'#b6b3a0',base=.065)
    level=-6.4
    boats=[]
    for boat_id,x,z in [('najuho',-23,-33.7),('wanggeonho',16,-36.0)]:
        spec=json.loads((ROOT/f'knowledge/sources/{boat_id}-navigation.json').read_text(encoding='utf-8'))
        home=dock.point(x,z);shore=dock.point(x,-26)
        boats.append({**spec,'modelUrl':f'/models/{boat_id}.glb.gz?v=detail-1','home':dict(x=home[0],z=home[1],yaw=-(dock.angle+math.pi/2)),'waterY':-7.47,'shore':shore,'shoreHeight':level})
        places.append(place('board-'+boat_id,spec['name']+' 승선 입구',*shore,3,'승선 버튼이나 F를 눌러 배에 올라보세요.',arrivalHeight=level))
        arrivals['board-'+boat_id]=dict(x=shore[0],z=shore[1],height=level,yaw=-(dock.angle+math.pi/2))
        # Closed gangway reaches the side entry; no collision floor extends into water.
        end=z+spec['beam']/2;length=-29-end
        dock.box('boarding_gangway_'+boat_id,x,level-.08,(-29+end)/2,1.65,.16,length+.18,'#897354',record=False)
        for dx in (-.79,.79):dock.tube('gangway_rope',(x+dx,level+.7,-29),(x+dx,level+.7,end),.022,'#c2b18a')
    # Navigation includes the excavated berth and excludes the dock and bridge piers.
    channel=[clip(clip(clip(clip(river,0,bounds[0],False),0,bounds[1]),1,bounds[2],False),1,bounds[3]),[dock.point(x,z) for x,z in [(-42.5,-65),(42.5,-65),(42.5,-29),(-42.5,-29)]]]
    water_obstacles=[s['footprint'] for s in g.solids if s['name'].startswith('walk-floor_dock') and 'stair' not in s['name']]
    # Keep bridge navigation clear of piers and insufficient overhead clearance.
    water_obstacles += [s['footprint'] for s in g.solids if s['name'].startswith('walk-floor_bridge')]
    places.extend([place('landing','황포돛배 선착장',*dock.point(5,-16),15,'계류된 목선과 강변 데크를 둘러보세요.',arrivalHeight=level),place('lighthouse','영산포 등대',*dock.point(4,-4),6,'강변 아래 데크에 남아 있는 흰 등대입니다.',arrivalHeight=level),place('dock-stairs','선착장 내려가는 계단',*stair_route[0],4,'계단을 내려가면 낮은 강변 데크로 이어집니다.'),place('hongeo','영산포 홍어거리',*xy([126.71078,35.0001]),28,'영산3길을 따라 역사갤러리로 이어집니다.'),place('river-view','강변 산책길',-143,138.27,20,'계단을 내려가면 선착장과 등대를 가까이 볼 수 있어요.')])
    # Riverside street furniture, trees and utility poles at estimated spacing.
    for x,z in [(-220,183),(-175,168),(-67,127),(6,60),(51,19),(143,-37),(232,-68),(309,148)]:
        if any(in_poly([x,z],b['footprint']) for b in frontage_details):continue
        g.tree('street_tree',x,z,1.05,int(x+500));g.box('street_bench',x+3,.43,z,2.2,.15,.65,'#827351',True)
        g.tube('street_lamp_pole',(x-3,0,z),(x-3,6,z),.055,'#69726c');g.box('street_lamp_head',x-2.5,6,z,1,.12,.35,'#d6d0ae',record=False)
    for i in range(12):
        x=-280+i*12;z=230+i%3*5
        # Earlier estimated parking must yield to newly traced real alleys.
        if any(line_distance((x,z),a,b)<lane['width']/2+3 for lane in extra_lanes for a,b in zip(lane['points'],lane['points'][1:])):continue
        g.box('parked_vehicle',x,.65,z,2.1,1.3,4.4,['#deded3','#949f9b','#5e747d'][i%3],True)
        g.box('vehicle_window',x,1.32,z,1.83,.65,2.2,'#698488',record=False)
    for obj in scene.objects:
        if 'hide_in_overview' in obj:del obj['hide_in_overview']
    return g,world_data(g,'영산포 · 황포돛배 · 홍어거리',bounds,dict(x=-143,z=138.27,yaw=0),places,origin=dict(lon=ORIGIN[0],lat=ORIGIN[1]),verticalNavigation=True,requireFloor=True,portals=portals,arrivals=arrivals,roads=roads,boats=boats,literatureGarden=garden_data,southContextRoofs=len(context_footprints),additionalSatelliteRoofs=len(extra_footprints),streetDetails=street_details,additionalLanes=extra_lanes,detailRevision='streets-1',riverfrontDetails=dict(revision='riverfront-1',buildings=frontage_details,paving=frontage_apron),navigationWater=dict(polygons=channel,obstacles=water_obstacles),mappedBuildings=count,tracedRoofs=len(traced),photoInformedShops=shopcount,dockHeight=level,dockStairRoute=stair_route,limitations=['Mapped road and river coordinates are OSM. Building heights and unrecorded shop facades are estimated, not individually surveyed storefronts.','Courtyard planting/paving follows JNFC photos; the southwest parcel and added context roofs are aligned to satellite imagery of unknown capture date. Dimensions, materials and building heights remain estimates.','Lighthouse height 8.65m follows archive data. Wharf level -6.4m, stairs, mooring placement and seasonal water level are estimated from photographs.','Wanggeonho length 29.9m and beam 9.9m follow construction reports. Najuho dimensions and both interior layouts are photo-proportioned estimates.','Museum exteriors use official map/photo positions; interiors are separate authored spaces linked at the doors.','Source imagery, original museum films and long copyrighted panels are not redistributed.'])
