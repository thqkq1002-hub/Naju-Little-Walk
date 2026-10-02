"""Blender-authored broadleaf sprays. Original analytic atlas, no source photograph."""
import bpy, math, random
import numpy as np
from mathutils import Vector

def spray_material():
    n=768
    y,x=np.mgrid[0:n,0:n]/(n-1)
    rgba=np.zeros((n,n,4),dtype=np.float32)
    # Color outside the mask prevents black fringes in the texture's mip levels.
    rgba[:,:,:3]=(.25,.36,.12)
    rr=random.Random(581)
    def stroke(a,b,width,color):
        ax,ay=a;bx,by=b;dx=bx-ax;dy=by-ay
        t=np.clip(((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy),0,1)
        mask=(x-ax-t*dx)**2+(y-ay-t*dy)**2<width*width
        rgba[mask,:3]=color;rgba[mask,3]=1
    def blade(base,angle,length,width,tone):
        bx,by=base;dx=math.cos(angle);dy=math.sin(angle)
        t=((x-bx)*dx+(y-by)*dy)/length
        w=-(x-bx)*dy+(y-by)*dx
        curve=np.sin(np.clip(t,0,1)*math.pi)
        shape=(t>0)&(t<1)&(abs(w)<width*curve**.85)
        vein=np.exp(-(w/.0025)**2)
        shade=.86+.15*curve+.07*vein+.025*np.sin(t*48+abs(w)*320)
        for k,c in enumerate(tone):rgba[:,:,k][shape]=(c*shade)[shape]
        rgba[:,:,3][shape]=1
    stem=(.48,.1)
    for j in range(7):
        angle=.40+j*.40
        tip=(.5+.37*math.cos(angle),.28+.51*math.sin(angle))
        stroke(stem,tip,.004,(.24,.24,.10))
        for k in range(5):
            t=.3+k*.135;base=(stem[0]*(1-t)+tip[0]*t,stem[1]*(1-t)+tip[1]*t)
            for side in [-1,1]:
                a=angle+side*rr.uniform(.55,.95)
                tone=rr.choice([(.25,.36,.11),(.31,.43,.14),(.37,.46,.16),(.22,.32,.10)])
                blade(base,a,rr.uniform(.085,.13),rr.uniform(.021,.030),tone)
    image=bpy.data.images.new('Park_original_broadleaf_spray',width=n,height=n,alpha=True)
    image.pixels.foreach_set(rgba.ravel());image.pack()
    mat=bpy.data.materials.new('Park_leaf_spray_cutout');mat.use_nodes=True
    mat.use_backface_culling=False;mat.surface_render_method='DITHERED'
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF')
    bs.inputs['Roughness'].default_value=.83
    tex=nodes.new('ShaderNodeTexImage');tex.image=image
    cutoff=nodes.new('ShaderNodeMath');cutoff.operation='GREATER_THAN';cutoff.inputs[1].default_value=.5
    links.new(tex.outputs['Color'],bs.inputs['Base Color']);links.new(tex.outputs['Alpha'],cutoff.inputs[0]);links.new(cutoff.outputs[0],bs.inputs['Alpha'])
    return mat

def crown_prototype(PlantMesh,bark,spray,variant,near):
    p=PlantMesh();rr=random.Random(5800+variant)
    for j in range(11):
        angle=j*2.399+variant*.57
        height=.60+(j%4)*.072
        spread=.14+rr.random()*.11
        c=Vector((math.cos(angle)*spread,height,math.sin(angle)*spread))
        size=Vector((rr.uniform(.13,.19),rr.uniform(.12,.16),rr.uniform(.13,.19)))
        if near:
            start=Vector((0,.36+(j%2)*.09,0));elbow=start.lerp(c,.6)-Vector((0,.045,0))
            p.tube(start,elbow,.006,.003,0,n=6);p.tube(elbow,c,.003,.001,0,n=5)
        # Unsorted alpha-test sprays remain opaque draw calls and support instancing.
        count=58 if near else 13
        for k in range(count):
            az=rr.random()*math.tau;v=rr.uniform(-1,1);r=math.sqrt(1-v*v)
            offset=Vector((r*math.cos(az),v,r*math.sin(az)))
            pos=c+Vector((offset.x*size.x,offset.y*size.y,offset.z*size.z))*rr.uniform(.30,1)
            normal=Vector((rr.uniform(-1,1),rr.uniform(.1,1),rr.uniform(-1,1))).normalized()
            u=normal.cross(Vector((0,1,0))).normalized();w=normal.cross(u)
            length=rr.uniform(.047,.075) if near else rr.uniform(.12,.15)
            # Two slightly folded halves avoid uniformly flat leaf faces.
            a=pos-u*length-w*length;b=pos+u*length-w*length
            d=pos-u*length+w*length;e=pos+u*length+w*length
            if near:
                mid0=pos-w*length+normal*length*.14;mid1=pos+w*length+normal*length*.14
                p.face([a,mid0,mid1,d],1,[(0,0),(.5,0),(.5,1),(0,1)])
                p.face([mid0,b,e,mid1],1,[(.5,0),(1,0),(1,1),(.5,1)])
            else:p.face([a,b,e,d],1,[(0,0),(1,0),(1,1),(0,1)])
    mesh=p.finish('Park_spray_'+str(variant)+('_near' if near else '_far'),[bark,spray])
    for f in mesh.polygons:f.use_smooth=f.material_index==0
    return mesh
