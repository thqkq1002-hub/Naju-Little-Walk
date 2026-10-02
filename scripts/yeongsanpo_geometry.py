"""Blender-authored, original geometry for the Yeongsanpo reference model.

Units are metres; local X east, Z south, Y up. Dimensions are estimates.
Source photographs are reference only, never bundled as textures.
"""
import bpy, math, random
from mathutils import Vector
from museum_geometry import MuseumGeometry

class Geometry(MuseumGeometry):
    def __init__(self, scene, center=(0,0), angle=0):
        super().__init__(scene,center,angle)

    def mat(self,color):
        if color not in self.materials:
            existing=bpy.data.materials.get('Museum_'+color.lstrip('#'))
            if existing:self.materials[color]=existing
        return super().mat(color)

    def label(self,text,x,y,z,width,height=.28,rotation=0,color='#e9dbc7',group='02_Photo_Interior'):
        # Hangul advances are approximately one em; avoid global dependency-graph
        # updates for every label in a large editable scene.
        curve=bpy.data.curves.new('Text_'+text,'FONT');curve.body=text;curve.align_x='CENTER';curve.align_y='CENTER';curve.extrude=.001
        curve.size=min(height/.9,width/max(1,max(len(line) for line in text.split('\n'))))
        if self.font:curve.font=self.font
        o=bpy.data.objects.new('label_'+text,curve);self.groups[group].objects.link(o);o.location=self.bp(x,y,z)
        o.rotation_euler=(math.pi/2,0,rotation-self.angle);curve.materials.append(self.mat(color))
        self.signs.append(dict(text=text,position=[*self.point(x,z)[:1],y,self.point(x,z)[1]],width=width,height=height,rotation=rotation-self.angle))
        return o

    def glass(self,name,x,y,z,w,h,d=.025,rotation=0):
        o=self.box(name,x,y,z,w,h,d,'#97b6be',rotation=rotation,record=False)
        m=self.mat('#97b6be');m.surface_render_method='DITHERED';bs=m.node_tree.nodes['Principled BSDF'];bs.inputs['Alpha'].default_value=.2;bs.inputs['Roughness'].default_value=.18
        return o

    def river_material(self,color):
        # Original packed material study: mottled water-floor finish, not a photo.
        n=512;image=bpy.data.images.new('Original_river_floor_material',width=n,height=n)
        pixels=[]
        for j in range(n):
            for i in range(n):
                u=i/n*math.tau;v=j/n*math.tau
                noise=sum(math.sin(u*f+math.sin(v*(f+1))*.8)*math.cos(v*(f-1)+.6)*a for f,a in [(3,.32),(7,.19),(17,.12),(31,.08),(67,.04)])
                t=max(0,min(1,.5+noise));pixels.extend((.025+t*.095,.046+t*.11,.044+t*.09,1))
        image.pixels.foreach_set(pixels);image.pack()
        mat=self.mat(color);bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.28
        node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;mat.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])

    def window(self,name,x,y,z,w,h,rotation=0,lattice=False):
        def at(dx,dy,dz):
            c,s=math.cos(rotation),math.sin(rotation)
            return x+dx*c-dz*s,y+dy,z+dx*s+dz*c
        self.glass(name+'_glass',x,y,z,w,h,rotation=rotation)
        for dx in (-w/2,0,w/2):self.box(name+'_stile',*at(dx,0,-.025),.07,h+.1,.09,'#504336',rotation=rotation,record=False)
        for dy in (-h/2,h*.18,h/2):self.box(name+'_rail',*at(0,dy,-.025),w+.12,.065,.10,'#504336',rotation=rotation,record=False)
        if lattice:
            for i in range(1,max(2,int(w/.18))):self.box(name+'_lattice',*at(-w/2+i*w/max(2,int(w/.18)),0,-.04),.018,h,.025,'#6e563d',rotation=rotation,record=False)

    def roof(self,name,x,y,z,w,d,rise,color='#515d60',axis=False,tiles=True):
        # Hipped, slightly lifted eaves; separate tile ribs retain roof silhouette.
        verts=[(x-w/2,y,z-d/2),(x+w/2,y,z-d/2),(x+w/2,y,z+d/2),(x-w/2,y,z+d/2),(x-w*.28,y+rise,z),(x+w*.28,y+rise,z)]
        self.mesh(name,verts,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],color,'05_Cutaway_Roof')
        self.tube(name+'_ridge',(x-w*.29,y+rise+.06,z),(x+w*.29,y+rise+.06,z),.10,color,'05_Cutaway_Roof',10)
        if tiles:
            for side in (-1,1):
                n=max(8,int(w/.28))
                for i in range(n+1):
                    xx=x-w/2+i*w/n;rx=max(x-w*.28,min(x+w*.28,xx))
                    self.tube(name+'_tile',(xx,y+.025,z+side*d/2),(rx,y+rise+.035,z),.045,color,'05_Cutaway_Roof',6)
                for j in range(1,8):
                    t=j/8;left=x-w/2+(w*.22)*t;right=x+w/2-w*.22*t
                    self.tube(name+'_tile_course',(left,y+rise*t+.02,z+side*d/2*(1-t)),(right,y+rise*t+.02,z+side*d/2*(1-t)),.016,'#687273','05_Cutaway_Roof',5)

    def tree(self,name,x,z,size=1,seed=1):
        rng=random.Random(seed)
        self.tube(name+'_trunk',(x,0,z),(x,3.4*size,z),.14*size,'#726044')
        for i in range(6):
            a=i*math.tau/6;dx=math.cos(a)*size;dz=math.sin(a)*size
            self.tube(name+'_branch',(x,1.8*size,z),(x+dx,3.5*size,z+dz),.055*size,'#726044')
            self.rock(name+'_crown',x+dx,3.6*size,z+dz,2*size,1.8*size,2*size,rng.choice(['#5d7850','#73905d','#84975f']),rng)

    def light(self,x,y,z,power=65):
        self.box('ceiling_lamp',x,y,z,.23,.045,.23,'#fff1cd',record=False,group='05_Cutaway_Roof')
        bs=self.mat('#fff1cd').node_tree.nodes['Principled BSDF'];bs.inputs['Emission Color'].default_value=(1,.87,.64,1);bs.inputs['Emission Strength'].default_value=4
        xx,zz=self.point(x,z);self.lights.append(dict(position=[xx,y-.15,zz],color='#fff1db',intensity=power,distance=10))
        data=bpy.data.lights.new('Photo_room_lighting','AREA');data.energy=power*3;data.size=3
        obj=bpy.data.objects.new('Photo_room_lighting',data);self.scene.collection.objects.link(obj);obj.location=self.bp(x,y-.15,z)

    def boat(self,name,x,z,scale=1,sails=True,base=-.5,flat=False):
        # Timber hull, high pointed bow, battened ochre sails and passenger cabin.
        s=scale
        def p(a,b,c):return x+a*s,base+b*s,z+c*s
        outline=[(-2.7,-9),(-3.2,-6),(-3.1,6),(-1.9,10),(0,12),(1.9,10),(3.1,6),(3.2,-6),(2.7,-9)]
        n=len(outline);verts=[p(a*.78,-1.1,c*.85) for a,c in outline]+[p(a,.9+max(0,c-7)*.12,c) for a,c in outline]
        self.mesh(name+'_timber_hull',verts,[tuple(range(n-1,-1,-1))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],'#67452d')
        self.polygon(name+'_deck',[(x+a*s,z+c*s) for a,c in outline],base+.82*s,.12*s,'#aa7b4a')
        for j in range(-17,22):self.box(name+'_deck_plank',*p(0,.96,j*.5),5*s,.018*s,.022*s,'#715334',record=False)
        for side in (-1,1):
            self.box(name+'_rail',*p(side*2.8,1.8,0),.13*s,.14*s,18*s,'#956335',record=False)
            for j in range(-8,10,2):self.box(name+'_rail_post',*p(side*2.8,1.4,j),.13*s,.85*s,.13*s,'#745234',record=False)
        self.box(name+'_cabin_back',*p(0,2.0,-4.5),3.8*s,2.1*s,.13*s,'#66482f',record=False)
        for side in (-1,1):
            self.box(name+'_cabin_sill',*p(side*1.9,1.3,-1.5),.15*s,.6*s,6*s,'#85603b',record=False)
            for j in range(-4,2):self.window(name+'_cabin_window',*p(side*1.9,2.15,j+.5),.95*s,1.25*s,math.pi/2)
        if flat:
            self.box(name+'_flat_cabin_roof',*p(0,3.3,-1.5),4.7*s,.13*s,7.2*s,'#b39366',record=False)
            self.box(name+'_second_cabin',*p(0,1.85,5),3.9*s,1.9*s,3.2*s,'#80613f',record=False)
            self.box(name+'_second_cabin_roof',*p(0,2.85,5),4.5*s,.14*s,3.6*s,'#b39366',record=False)
        else:self.roof(name+'_cabin_roof',x,base+3.3*s,z-1.5*s,5*s,7.5*s,.65*s,'#626767')
        for c in (-6,5):
            self.tube(name+'_mast',p(0,.9,c),p(0,10.5 if sails else 4.9,c),(.10 if sails else .035)*s,'#745137')
            if sails:
                for anchor in (-2.7,2.7):self.tube(name+'_rigging',p(0,10,c),p(anchor,1,c+2),.014*s,'#c8b486',n=5)
            if sails:
                rows=12;cols=8;sv=[]
                for j in range(rows+1):
                    v=j/rows
                    for i in range(cols+1):
                        u=i/cols;sv.append(p((u-.5)*(4.8-.8*v),4+5.5*v,c+.4+math.sin(u*math.pi)*.7))
                self.mesh(name+'_ochre_sail',sv,[(j*(cols+1)+i,j*(cols+1)+i+1,(j+1)*(cols+1)+i+1,(j+1)*(cols+1)+i) for j in range(rows) for i in range(cols)],'#c89853')
                for j in range(9):
                    v=j/8;w=4.8-.8*v;self.tube(name+'_sail_batten',p(-w/2,4+5.5*v,c+.42),p(w/2,4+5.5*v,c+.42),.028*s,'#866039',n=6)
        self.label('황포돛배',*p(0,1.5,11),3.3*s,.4*s,color='#f4deb1')

def world_data(g,title,bounds,spawn,places,**extra):
    return dict(title='나주 산책',subtitle=title,source='© OpenStreetMap contributors, ODbL 1.0 · 공식 사진 참고',bounds=bounds,spawn=spawn,solids=g.solids,signs=g.signs,lights=g.lights,places=places,**extra)

def place(pid,name,x,z,radius=4,description='',**extra):
    return dict(id=pid,name=name,position=[x,z],arrival=extra.pop('arrival',[x,z]),radius=radius,description=description,**extra)
