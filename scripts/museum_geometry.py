"""Editable Blender primitives shared by the Bogam museum authoring script."""
import bpy
import bmesh
import math
import random
from mathutils import Vector
from pathlib import Path

class MuseumGeometry:
    def __init__(self,scene,center,angle):
        self.scene=scene;self.center=center;self.angle=angle
        self.solids=[];self.signs=[];self.lights=[];self.materials={};self.groups={}
        for name in ('01_OSM_Envelope','02_Photo_Interior','03_Report_Burials','04_Estimated_Fixtures','05_Cutaway_Roof'):
            c=bpy.data.collections.new(name);scene.collection.children.link(c);self.groups[name]=c
        path=Path('C:/Windows/Fonts/malgun.ttf')
        self.font=bpy.data.fonts.load(str(path),check_existing=True) if path.exists() else None

    def point(self,x,z):
        c,s=math.cos(self.angle),math.sin(self.angle)
        return [self.center[0]+x*c-z*s,self.center[1]+x*s+z*c]

    def bp(self,x,y,z):
        x,z=self.point(x,z);return (x,-z,y)

    def mat(self,color):
        if color not in self.materials:
            rgb=[int(color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
            rgb=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
            m=bpy.data.materials.new('Museum_'+color.lstrip('#'));m.use_nodes=True;m.diffuse_color=(*rgb,1)
            m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*rgb,1)
            m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.78
            self.materials[color]=m
        return self.materials[color]

    def mesh(self,name,verts,faces,color,group='02_Photo_Interior',smooth=False):
        mesh=bpy.data.meshes.new(name);mesh.from_pydata([self.bp(*p) for p in verts],[],faces);mesh.update()
        bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
        uv=mesh.uv_layers.new(name='Original_Material_UV')
        for face in mesh.polygons:
            face.use_smooth=smooth
            for li in face.loop_indices:
                v=mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv=(v.x/3.2,(v.y if abs(face.normal.z)>.5 else v.z)/3.2)
        o=bpy.data.objects.new(name,mesh);self.groups[group].objects.link(o);mesh.materials.append(self.mat(color))
        o['reference_category']=group
        if group=='05_Cutaway_Roof':o['hide_in_overview']=True
        return o

    def collider(self,name,pts,base,height,color='#ab8060'):
        self.solids.append(dict(name=name,kind='building',position=[0,base,0],size=[1,height,1],footprint=[self.point(*p) for p in pts],color=color,collision=True))

    def box(self,name,x,y,z,w,h,d,color,collision=False,rotation=0,group='02_Photo_Interior',record=True):
        pts=[];c,s=math.cos(rotation),math.sin(rotation)
        for dx,dz in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]:pts.append([x+dx*c-dz*s,z+dx*s+dz*c])
        verts=[(px,yy,pz) for yy in (y-h/2,y+h/2) for px,pz in pts]
        o=self.mesh(name,verts,[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],color,group)
        if record:self.solids.append(dict(name=name,kind='building',position=[0,y-h/2,0],size=[w,h,d],footprint=[self.point(*p) for p in pts],color=color,collision=collision))
        return o

    def polygon(self,name,pts,base,h,color,collision=False,group='02_Photo_Interior'):
        pts=pts[:-1] if pts[0]==pts[-1] else pts;n=len(pts)
        verts=[(x,y,z) for y in (base,base+h) for x,z in pts]
        o=self.mesh(name,verts,[tuple(range(n)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],color,group)
        self.solids.append(dict(name=name,kind='building',position=[0,base,0],size=[1,h,1],footprint=[self.point(*p) for p in pts],color=color,collision=collision))
        return o

    def segment(self,name,a,b,width,h,color,base=0,collision=False,group='02_Photo_Interior',record=True):
        return self.box(name,(a[0]+b[0])/2,base+h/2,(a[1]+b[1])/2,math.dist(a,b),h,width,color,collision,math.atan2(b[1]-a[1],b[0]-a[0]),group,record)

    def tube(self,name,a,b,r,color,group='02_Photo_Interior',n=10):
        p=Vector(a);q=Vector(b);axis=(q-p).normalized();u=axis.cross(Vector((0,1,0)))
        if u.length<.001:u=axis.cross(Vector((1,0,0)))
        u.normalize();v=axis.cross(u).normalized()
        verts=[tuple(center+r*(math.cos(i*math.tau/n)*u+math.sin(i*math.tau/n)*v)) for center in (p,q) for i in range(n)]
        return self.mesh(name,verts,[tuple(range(n)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],color,group,True)

    def label(self,text,x,y,z,width,height=.28,rotation=0,color='#e9dbc7',group='02_Photo_Interior'):
        curve=bpy.data.curves.new('Text_'+text,'FONT');curve.body=text;curve.size=1;curve.align_x='CENTER';curve.align_y='CENTER';curve.extrude=.0015
        if self.font:curve.font=self.font
        o=bpy.data.objects.new('label_'+text,curve);self.groups[group].objects.link(o);o.location=self.bp(x,y,z)
        o.rotation_euler=(math.pi/2,0,rotation-self.angle);o.data.materials.append(self.mat(color));bpy.context.view_layer.update()
        w=max(p[0] for p in o.bound_box)-min(p[0] for p in o.bound_box);h=max(p[1] for p in o.bound_box)-min(p[1] for p in o.bound_box)
        scale=min(width/max(w,.01),height/max(h,.01));o.scale=(scale,scale,scale)
        wx,wz=self.point(x,z);self.signs.append(dict(text=text,position=[wx,y,wz],width=width,height=height,rotation=rotation-self.angle))
        return o

    def vessel(self,name,x,y,z,scale=1,color='#656056',profile=None,rotation=0,horizontal=False):
        profile=profile or [(0,.12),(.08,.35),(.3,.5),(.65,.46),(.84,.26),(.92,.23),(1,.30),(1.05,.30),(1.05,.23),(.93,.18),(.75,.20),(.12,.22)]
        if horizontal:
            # Fine coil ridges and lip transitions remain actual editable geometry.
            refined=[]
            for (a,r),(b,s) in zip(profile,profile[1:]):
                count=max(1,math.ceil(abs(b-a)/.045))
                for j in range(count):
                    t=j/count;yy=a+(b-a)*t
                    refined.append((yy,r+(s-r)*t+.0035*math.sin(yy*155)))
            profile=refined+[profile[-1]]
        n=32;verts=[]
        for yy,rr in profile:
            for i in range(n):
                dx=math.cos(i*math.tau/n)*rr*scale;dz=math.sin(i*math.tau/n)*rr*scale;dy=yy*scale
                if horizontal:dy,dz=dz,dy-scale*.55
                verts.append((x+dx*math.cos(rotation)-dz*math.sin(rotation),y+dy,z+dx*math.sin(rotation)+dz*math.cos(rotation)))
        faces=[]
        for j in range(len(profile)-1):
            for i in range(n):a=j*n+i;b=j*n+(i+1)%n;faces.append((a,b,b+n,a+n))
        faces.append(tuple(range(n)))
        return self.mesh(name,verts,faces,color,'03_Report_Burials',True)

    def rock(self,name,x,y,z,w,h,d,color,rng):
        # Irregular beveled hexahedra; each stone remains an editable Blender object.
        verts=[]
        for yy,inset in [(-h/2,.73),(-h*.30,1),(h*.30,1),(h/2,.76)]:
            for dx,dz in [(-.5,-.32),(-.32,-.5),(.32,-.5),(.5,-.32),(.5,.32),(.32,.5),(-.32,.5),(-.5,.32)]:
                verts.append((x+dx*w*inset*rng.uniform(.87,1.12),y+yy+rng.uniform(-h*.09,h*.09),z+dz*d*inset*rng.uniform(.87,1.12)))
        faces=[tuple(range(8)),tuple(range(24,32))]+[(j*8+i,j*8+(i+1)%8,j*8+(i+1)%8+8,j*8+i+8) for j in range(3) for i in range(8)]
        return self.mesh(name,verts,faces,color,'03_Report_Burials',False)

    def railing(self,name,a,b,height,width=.045,glass=True,start_post=True,end_post=True):
        length=math.dist(a,b);n=max(1,math.ceil(length/1.35))
        self.segment(name+'_collision',a,b,.10,1.05,'#939b99',base=height,collision=True,record=True).hide_render=True
        # Hidden proxy stays in collision JSON only, never in exported visible geometry.
        proxy=self.scene.objects.get(name+'_collision')
        if proxy:bpy.data.objects.remove(proxy,do_unlink=True)
        self.tube(name+'_wood_handrail',(a[0],height+1.06,a[1]),(b[0],height+1.06,b[1]),.045,'#9e784c')
        for i in range(0 if start_post else 1,n+1 if end_post else n):
            t=i/n;x=a[0]+(b[0]-a[0])*t;z=a[1]+(b[1]-a[1])*t
            self.tube(name+'_steel_post',(x,height,z),(x,height+1.03,z),.023,'#a2acab')
        if glass:
            o=self.segment(name+'_glass',a,b,.018,.89,'#92b2b4',base=height+.10,record=False)
            m=self.mat('#92b2b4');m.surface_render_method='DITHERED';bsdf=m.node_tree.nodes['Principled BSDF'];bsdf.inputs['Alpha'].default_value=.17;bsdf.inputs['Roughness'].default_value=.12;m.diffuse_color=(*m.diffuse_color[:3],.17)
