"""Metadata and inspection views only: all floor/door/collision coordinates retained."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/dasi-v80'
views=[
    dict(id='school-front',label='본관 정면',center=[-18,3.8,-10],radius=60,elevation=.28,angle=-.17,fov=50),
    dict(id='school-gate',label='정문·숲마당',center=[-29,1.8,28],radius=40,elevation=.32,angle=-.05,fov=55),
    dict(id='school-court',label='운동장·코트',center=[26,1.4,9],radius=67,elevation=.40,angle=.72,fov=52),
    dict(id='school-west',label='서쪽 별동',center=[-60,4,-28],radius=59,elevation=.27,angle=-.58,fov=50),
]
stats=[]
for name in ['dasi-neighborhood-world.json','dasi-world.json']:
    p=R/'public'/name;w=json.loads(p.read_text(encoding='utf-8'))
    unchanged={k:w.get(k) for k in ['solids','bounds','spawn','interior','buildings','neighborhood','signs']}
    digest=hashlib.sha256(json.dumps(unchanged,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    w['detailRevision']=dict(version=80,date='2026-10-03',scope='Existing school forms and navigation retained; material, vegetation and joinery refinement only',recentPhotoDates=['2025-10-28','2026-06-08','2026-09-22','2026-10-01'],olderSources='Historic base geometry retained at user request; not verified as a post-remodelling survey',navigationSha256=digest)
    if name.startswith('dasi-neighborhood'):
        w['architectureViews']=views;w['lighting']=dict(exposure=1.04,ambient=1.75,sun=2.35)
    assert unchanged=={k:w.get(k) for k in unchanged}
    p.write_text(json.dumps(w,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
    stats.append(dict(file=name,navigationSha256=digest))
(O/'navigation-preservation.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
print('D80 navigation geometry unchanged',stats)
