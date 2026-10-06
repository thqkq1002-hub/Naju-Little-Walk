"""Refine the new generated rigs using texture identity; do not touch Meshy originals."""
from pathlib import Path
import bpy, numpy as np, json, sys

root = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--') + 1:]
character = args[0]
version = args[1] if len(args)>1 else 'v5'
base = root / 'assets/npc/meshy71-baedoli-clean-20261002' if character=='baedoli' and version=='v6' else root / 'assets/npc/meshy71-rigged-20261002' / character
source = base / f'{character}-rigged-{version}.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
mesh = bpy.data.objects[character+'_Body'];rig = bpy.data.objects[character+'_GuideRig']
height = {'baedoli':1.2,'beodeuri':1.65,'hongdoli':1.05,'teacher':1.72}[character]
data = mesh.data
coords = np.empty(len(data.vertices)*3,dtype=np.float32);data.vertices.foreach_get('co',coords)
coords = coords.reshape(-1,3)/height;x,y,z = coords.T
colors = np.zeros((len(coords),3),dtype=np.float32)
image = bpy.data.images['Image_0'].copy();image.scale(512,512)
pixels = np.array(image.pixels[:],dtype=np.float32).reshape(512,512,4)
for loop in data.loops:
    u,v = data.uv_layers.active.data[loop.index].uv
    colors[loop.vertex_index] = pixels[min(511,int(v*512)),min(511,int(u*512)),:3]
bpy.data.images.remove(image)
r,g,b = colors.T
def assign(mask, name):
    indexes = np.flatnonzero(mask).tolist()
    for group in mesh.vertex_groups: group.remove(indexes)
    mesh.vertex_groups[name].add(indexes,1,'REPLACE')
if character == 'baedoli' and version=='v6':
    assign(z>.43,'Head')
    for sign,suffix in [(-1,'R'),(1,'L')]:
        assign((x*sign>.235)&(z>.09)&(z<.29),'Hand.'+suffix)
elif character == 'baedoli':
    # Hat, face and glove must never borrow each other's animation weights.
    assign((z>.43)&(np.abs(x)<.355),'Head')
    assign((z>.62)&(r>g*1.12)&(r>.4),'Head')
    pale = (r>.5)&(g>.45)&(np.abs(r-g)<.11)&(np.abs(g-b)<.10)&(b>r*.80)
    assign((z>.58)&~pale,'Head')
    for sign,suffix in [(-1,'R'),(1,'L')]:
        assign(pale&(x*sign>.30)&(z>.34)&(z<.74),'Hand.'+suffix)
    head_distance = np.linalg.norm((coords-np.array((0,0,.59)))/.30,axis=1)
    fruit_distance = np.linalg.norm((coords-np.array((.41,-.13,.54)))/.14,axis=1)
    fruit = (x>.29)&(z>.42)&(fruit_distance<head_distance)&((r-g>.025)|(g>r*1.1))
    assign(fruit,'Hand.L')
elif character == 'hongdoli':
    # The ray's face is its body: nod the whole upper silhouette, not only its tip.
    assign(z>.34,'Head')
    if version=='v6':assign((z>.10)&(z<.34)&(np.abs(x)>.30),'Chest')
    for sign,suffix,center in [(-1,'R',(-.46,-.06,.28)),(1,'L',(.48,-.06,.47))]:
        distance = np.linalg.norm(coords-np.array(center),axis=1)
        pale = (r>.55)&(g>.5)&(b>.5)&(np.abs(r-b)<.14)
        if version=='v6':
            # Texture shadows do not divide one glove into different bones.
            mask=distance<.23
            influence=np.clip((.23-distance)/.08,0,1)
            influence=influence*influence*(3-2*influence)
            for index in np.flatnonzero(mask):
                previous={g.group:g.weight for g in data.vertices[int(index)].groups}
                for group in mesh.vertex_groups:group.remove([int(index)])
                for group,weight in previous.items():mesh.vertex_groups[group].add([int(index)],float(weight*(1-influence[index])),'REPLACE')
                group=mesh.vertex_groups['Hand.'+suffix]
                group.add([int(index)],float(influence[index]),'ADD')
        else:assign((distance<.17)&(x*sign>.33)&pale,'Hand.'+suffix)
    assign((y>.12)&(z>.42)&(r>g*1.15),'Tail')
elif character == 'beodeuri' and version=='v6':
    # The corrected rest bones align with the actual wrist and shoulder.
    assign((np.max(colors,axis=1)<.32)&(np.abs(x)<.12)&(z>.53),'Head')
    # Blend the cloth seam by mesh adjacency, including duplicated UV vertices.
    # A hard skirt/arm cutoff can stretch a single triangle into a sharp spike.
    names=[group.name for group in mesh.vertex_groups]
    weights=np.zeros((len(coords),len(names)),dtype=np.float32)
    for vertex in data.vertices:
        for group in vertex.groups:weights[vertex.index,group.group]=group.weight
    edges=np.array([edge.vertices[:] for edge in data.edges],dtype=np.int32)
    _,weld=np.unique(np.round(coords,5),axis=0,return_inverse=True)
    weld_count=np.bincount(weld)
    degree=np.bincount(edges.ravel(),minlength=len(coords)).clip(1)
    protected=(z<.34)|(z>.80)|((np.abs(x)>.21)&(z<.49))
    for iteration in range(12):
        sums=np.zeros_like(weights)
        np.add.at(sums,edges[:,0],weights[edges[:,1]])
        np.add.at(sums,edges[:,1],weights[edges[:,0]])
        averaged=sums/degree[:,None]
        weights[~protected]=weights[~protected]*.45+averaged[~protected]*.55
        welded=np.zeros((len(weld_count),len(names)),dtype=np.float32)
        np.add.at(welded,weld,weights)
        weights=(welded/weld_count[:,None])[weld]
    # Meshy can leave near-coincident garment seams disconnected topologically.
    # Sew their deformation weights in space without moving the source vertices.
    from mathutils.kdtree import KDTree
    tree=KDTree(len(coords))
    for index,point in enumerate(coords):tree.insert(tuple(point),index)
    tree.balance()
    pairs=[]
    for index in np.flatnonzero(~protected):
        for _,neighbor,distance in tree.find_range(tuple(coords[index]),.018):
            if neighbor!=index:pairs.append((int(index),neighbor))
    pairs=np.array(pairs,dtype=np.int32)
    counts=np.bincount(pairs[:,0],minlength=len(coords)).clip(1)
    for iteration in range(8):
        sums=np.zeros_like(weights)
        np.add.at(sums,pairs[:,0],weights[pairs[:,1]])
        weights[~protected]=weights[~protected]*.4+(sums/counts[:,None])[~protected]*.6
    # Match glTF's four-influence skinning exactly in the editable source.
    keep=np.argpartition(weights,-4,axis=1)[:,-4:]
    reduced=np.zeros_like(weights)
    np.put_along_axis(reduced,keep,np.take_along_axis(weights,keep,axis=1),axis=1)
    reduced/=np.maximum(reduced.sum(axis=1,keepdims=True),1e-12)
    for group in mesh.vertex_groups:group.remove(list(range(len(coords))))
    for index,row in enumerate(reduced):
        for group in np.flatnonzero(row>.00001):mesh.vertex_groups[int(group)].add([index],float(row[group]),'REPLACE')
    # Broad traditional sleeves need a restrained greeting to keep their drape.
    action=bpy.data.actions['Greeting']
    if not action.get('tailored_sleeve_gesture'):
        from mathutils import Quaternion
        rig.animation_data.action=action
        frames=sorted(set([*range(1,78,2),78]))
        snapshots=[]
        for frame in frames:
            bpy.context.scene.frame_set(frame)
            snapshots.append({name:rig.pose.bones[name].rotation_quaternion.copy() for name in ['UpperArm.R','Forearm.R','Hand.R']})
        for frame,snapshot in zip(frames,snapshots):
            for name,q in snapshot.items():
                pb=rig.pose.bones[name]
                pb.rotation_quaternion=Quaternion((1,0,0,0)).slerp(q,.45 if name=='UpperArm.R' else .65)
                pb.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=name)
        action['tailored_sleeve_gesture']=True
elif character == 'beodeuri':
    # Restore limb weights before isolating the skirt: low hands are not skirt.
    for sign,suffix in [(-1,'R'),(1,'L')]:
        mask=(x*sign>.14)&(z>.34)&(z<.76)
        names=['UpperArm.'+suffix,'Forearm.'+suffix,'Hand.'+suffix]
        distances=[]
        for name in names:
            a=np.array(rig.data.bones[name].head_local)/height
            delta=np.array(rig.data.bones[name].tail_local)/height-a
            t=np.clip(((coords-a)@delta)/np.dot(delta,delta),0,1)
            distances.append(np.linalg.norm(coords-(a+t[:,None]*delta),axis=1))
        w=np.exp(-np.stack(distances,axis=1)/.018)
        w/=np.maximum(w.sum(axis=1,keepdims=True),1e-12)
        indexes=np.flatnonzero(mask).tolist()
        for group in mesh.vertex_groups:group.remove(indexes)
        for i,name in enumerate(names):
            for index in indexes:
                if w[index,i]>.001:mesh.vertex_groups[name].add([index],float(w[index,i]),'REPLACE')
        # Fingers keep their shape; the wrist follows a single hand bone.
        assign((x*sign>.235)&(z>.34)&(z<.50),'Hand.'+suffix)
    assign((z<.515)&((z<.34)|(np.abs(x)<.21)),'Hips')
    assign((z<.63)&(np.abs(x)<.21)&(b>g*1.15)&(b>r*.95),'Hips')
    assign((np.max(colors,axis=1)<.32)&(np.abs(x)<.19)&(z>.53),'Head')
elif character == 'teacher':
    assign((z>.26)&(z<.49)&((np.abs(x)<.115) if version=='v6' else True),'Hips')
# Remove normals tied to the old high density triangulation after decimation.
data.normals_split_custom_set([(0,0,0)]*len(data.loops))
for pb in rig.pose.bones: pb.rotation_quaternion=(1,0,0,0)
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(source))
path = base/'rig-verification.json'
report = json.loads(path.read_text(encoding='utf-8'));report.update(semantic_skin_refinement=True,auto_smooth_normals=True)
path.write_text(json.dumps(report,indent=2),encoding='utf-8')
print('SEMANTIC_SKIN_REFINED '+character)
