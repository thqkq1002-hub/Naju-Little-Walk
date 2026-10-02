"""Update asset cache keys and geographic navigation for the colour revision."""
import json,re,gzip
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'lib/destinations.ts';t=p.read_text(encoding='utf-8')
t=re.sub(r"(modelUrl:\s*'/models/(?!deudeulgang)[^'?]+)(?:\?[^']*)?'",r"\1?v=palette-20260920'",t)
t=re.sub(r"(modelUrl:\s*'/models/[^'?]+\.glb)(\?)",r"\1.gz\2",t)
t=re.sub(r"(worldUrl:\s*'/[^'?]+)(?:\?[^']*)?'",r"\1?v=palette-20260920'",t);p.write_text(t,encoding='utf-8')
p=R/'app/bitgaram-orbit.tsx';t=p.read_text(encoding='utf-8').replace('district-color-fix-v50-20260920','palette-v51-20260920');p.write_text(t,encoding='utf-8')
region=R/'public/naju-region-map.json';d=json.loads(region.read_text(encoding='utf-8'));ids={str(p['id']) for p in d['paths']}
osm=json.loads((R/'knowledge/sources/deudeulgang/geometry.json').read_text(encoding='utf-8'))
for w in osm['ways']:
 tags=w['tags'];kind=tags.get('highway')
 if kind in ['tertiary','secondary'] and w['id'] not in ids:
  d['paths'].append(dict(id=int(w['id']),kind='secondary',name=tags.get('name',''),points=w['points']));ids.add(w['id'])
# Simplified river centre line follows the inspected imagery, with coordinates kept geographic.
if -51001 not in [p['id'] for p in d['paths']]:
 d['paths'].append(dict(id=-51001,kind='river',name='지석천',points=[[126.8557,35.024],[126.8545,35.021],[126.8537,35.019],[126.8531,35.017],[126.8533,35.015]]))
region.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
# Existing interiors have carefully placed lighting. Only formerly over-bright outdoor defaults change.
for name in ['yeongsanpo-world.json','city-world.json','dasi-neighborhood-world.json','bogam-world.json','bitgaram-kentech-world.json','bitgaram-park-world.json']:
 p=R/'public'/name;d=json.loads(p.read_text(encoding='utf-8'))
 if 'lighting' not in d:d['lighting']=dict(exposure=1.12,ambient=1.85,sun=2.6)
 p.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
# All model downloads now use the already-supported lossless gzip loader.
for p in (R/'public/models').glob('*.glb'):
 with gzip.open(str(p)+'.gz','wb',compresslevel=9) as f:f.write(p.read_bytes())
p=R/'public/yeongsanpo-world.json';d=json.loads(p.read_text(encoding='utf-8'))
for boat in d.get('boats',[]):boat['modelUrl']=boat['modelUrl'].split('?')[0]+'?v=palette-20260920'
p.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
