"""Version only the refined region; keep all collision/navigation envelopes intact."""
from pathlib import Path
import json,hashlib,re
R=Path(__file__).resolve().parents[1];O=R/'outputs/yeongsanpo-v79'
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
results=[]
for id in ['yeongsanpo','yeongsanpo-history','yeongsanpo-literature']:
    p=R/f'public/{id}-world.json';d=json.loads(p.read_text(encoding='utf-8'));backup=O/f'{id}-world-before.json'
    if not backup.exists():backup.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    before=json.loads(backup.read_text(encoding='utf-8'))
    d['detailVersion']='yeongsanpo-v79-20261003'
    d.setdefault('limitations',[])
    note='v79 authored PBR maps and leaf silhouettes are original. Fine joinery/finish dimensions and seasonal colors are photo-informed interpretations; mapped footprints, floor heights, museum portals and boat navigation remain unchanged.'
    if note not in d['limitations']:d['limitations'].append(note)
    if id=='yeongsanpo':
        d['lighting']={'exposure':1.12,'ambient':1.65,'sun':2.25}
        d['architectureViews']=[
            dict(id='wharf',label='선착장 전경',center=[-147,-2,120],radius=130,elevation=.43,angle=3.55,fov=52),
            dict(id='lighthouse',label='등대·계단',center=[-144,-2.2,127.8],radius=19,elevation=.30,angle=3.6,fov=52),
            dict(id='frontage',label='홍어거리',center=[-132,2.1,149],radius=82,elevation=.16,angle=3.5,fov=55),
            dict(id='garden',label='문학관 마당',center=[223,1.6,131],radius=46,elevation=.45,angle=.12,fov=52)]
        for boat in d.get('boats',[]):boat['modelUrl']=boat['modelUrl'].split('?')[0]+'?v=quality-v79-20261003'
    navigation=['solids','spawn','bounds','arrivals','portals','navigationWater','dockStairRoute','literatureGarden']
    for k in navigation:
        if d.get(k)!=before.get(k):raise RuntimeError('Unexpected navigation change: '+id+' '+k)
    for current,old in zip(d.get('boats',[]),before.get('boats',[])):
        if {k:v for k,v in current.items() if k!='modelUrl'}!={k:v for k,v in old.items() if k!='modelUrl'}:raise RuntimeError('Boat envelope changed')
    results.append(dict(scene=id,navigationSha256=digest({k:d.get(k) for k in navigation}),unchanged=True))
    p.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
p=R/'lib/destinations.ts';t=p.read_text(encoding='utf-8')
for id in ['yeongsanpo','yeongsanpo-history','yeongsanpo-literature']:
    for path in [f'/{id}-world.json',f'/models/{id}.glb.gz']:
        t=re.sub(re.escape(path)+r"\?[^']*",path+'?v=quality-v79-20261003',t)
t=t.replace('overview:{center:[40,45],radius:620,elevation:.86,angle:-.45}','overview:{center:[-30,95],radius:490,elevation:.82,angle:3.4}')
p.write_text(t,encoding='utf-8');(O/'navigation-verification.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Verified unchanged navigation:',len(results),'scenes and both boats')
