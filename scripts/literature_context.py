"""Satellite-traced surrounding roofs and lanes; facade details are estimates."""
import math, random
from yeongsanpo_geometry import Geometry

def build_context(g,source,xy):
    rng=random.Random(448);footprints=[]
    for roof in source['roofs']:
        if roof.get('reviewFlags'):continue
        pts=[xy(p) for p in roof['footprint']];pts=pts[:-1] if pts[0]==pts[-1] else pts
        h=roof['height'];cx=sum(p[0] for p in pts)/len(pts);cz=sum(p[1] for p in pts)/len(pts)
        # A visible roof outline includes eaves; keep the colliding walls inside.
        walls=[[cx+(x-cx)*.94,cz+(z-cz)*.94] for x,z in pts]
        g.polygon('photo-building_south_'+roof['id'],walls,0,h,roof['wallColor'],True)
        g.polygon('south_context_roof_'+roof['id'],pts,h,.18,roof['roofColor'])
        footprints.append(walls)
        for a,b in zip(pts,pts[1:]+pts[:1]):
            g.segment('context_roof_edge',a,b,.10,.12,'#6c7772',base=h+.18,record=False)
        a,b=max(zip(walls,walls[1:]+walls[:1]),key=lambda e:math.dist(*e));length=math.dist(a,b)
        area=sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(walls,walls[1:]+walls[:1]))
        face=Geometry(g.scene,[(a[0]+b[0])/2,(a[1]+b[1])/2],math.atan2(b[1]-a[1],b[0]-a[0])+(math.pi if area>0 else 0))
        face.box('context_facade_plinth',0,.22,.08,length,.44,.08,'#8c8b7f',record=False)
        for i in range(max(1,int(length/4))):
            x=-length/2+(i+.5)*length/max(1,int(length/4))
            face.box('context_dark_window_recess',x,1.6,.09,1.35,1.2,.06,'#465e5e',record=False)
            face.window('context_estimated_window',x,1.6,.15,1.4,1.25)
            face.box('context_window_sill',x,.92,.25,1.65,.07,.38,'#aeb7af',record=False)
        face.tube('context_rain_downpipe',(length/2-.4,.1,.15),(length/2-.4,h-.1,.15),.055,'#848d89',n=8)
        # Corrugated sheet rhythms are original geometry, not satellite textures.
        if len(pts)==4:
            for i in range(1,max(2,int(math.dist(pts[0],pts[1])/.5))):
                t=i/max(2,int(math.dist(pts[0],pts[1])/.5))
                a=[pts[0][k]+(pts[1][k]-pts[0][k])*t for k in (0,1)]
                b=[pts[3][k]+(pts[2][k]-pts[3][k])*t for k in (0,1)]
                g.segment('context_sheet_roof_seam',a,b,.045,.035,roof['roofColor'],base=h+.18,record=False)
    for surface in source['surfaces']:
        if surface.get('referenceOnly'):continue
        pts=[xy(p) for p in surface['footprint']]
        g.polygon('path_'+surface['id'] if surface['kind']=='paving' else surface['id'],pts,.006,.020,surface['color'])
        if surface['kind']=='mixed_vegetation':
            center=[sum(p[k] for p in pts)/len(pts) for k in (0,1)]
            for j,p in enumerate(pts[:4]):
                point=[center[k]+(p[k]-center[k])*.58 for k in (0,1)]
                g.tree('context_plot_tree',*point,.55+(j%2)*.22,seed=135+j)
    for route in source['routes']:
        if route['id']=='museum_south_entry':continue
        pts=[xy(p) for p in route['coordinates']]
        for a,b in zip(pts,pts[1:]):
            g.segment('path_'+route['id'],a,b,route['width']+.3,.024,'#a2a498',base=.026)
            g.segment('path_surface_'+route['id'],a,b,route['width'],.015,'#939b93',base=.051)
    # Cars were visible on this particular lot; exact spaces/vehicles are estimates.
    for x,z in [(115,108),(121,107),(128,105),(116,121),(122,120),(129,119),(156,132),(152,144)]:
        g.box('context_parked_car',x,.60,z,1.85,1.20,4.0,rng.choice(['#ddded7','#b5c0b9','#647d84']),True,rotation=-.15)
        g.box('context_car_glazing',x,1.18,z,1.72,.52,2.1,'#637d81',rotation=-.15,record=False)
        for dx in (-.95,.95):
            for dz in (-1.25,1.25):g.tube('context_car_tire',(x+dx-.09,.3,z+dz),(x+dx+.09,.3,z+dz),.30,'#394744',n=10)
    for x,z in [(151,153),(165,146),(174,143),(182,137),(122,150)]:g.tree('context_parking_tree',x,z,.9,seed=int(x))
    return footprints
