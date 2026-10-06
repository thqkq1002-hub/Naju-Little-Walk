from pathlib import Path
import json,math,hashlib
R=Path(__file__).resolve().parents[1]
source=(R/'scripts/research_observatory_relief_v96.py').read_text(encoding='utf8').split('for key, path in ')[0].replace("observatory-relief-v96","neureoji-polish-v98")
scope={'__file__':str(R/'scripts/research_observatory_relief_v96.py')};exec(source,scope)
origin={'lat':34.9159348,'lon':126.5419381};mx=111320*math.cos(math.radians(origin['lat']))
rows=[]
for x,z in [(0,0),(-30,0),(30,0),(0,-30),(0,30),(-60,0),(60,0),(0,-60),(0,60),(0,100)]:
 lat=origin['lat']-z/111320;lon=origin['lon']+x/mx
 rows.append(dict(x=x,z=z,lat=lat,lon=lon,**scope['elevation'](lat,lon)))
w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'))
d=dict(checked='2026-10-05',originWGS84=origin,terrarium=rows,model=dict(base=w['spawn']['height'],deck=w['topDeckHeightMetres'],towerHeight=w['towerHeightMetres']),sources=['https://registry.opendata.aws/terrain-tiles/','https://live112.tistory.com/5000','https://forme13.tistory.com/3621'],limitations=['DEM product agreement is not a survey or proof of bare-earth accuracy.','Total structure height and occupied deck height are different quantities.','Water is a modeled local plane, not an observed water-level datum.'])
(R/'knowledge/sources/neureoji-polish-v98/elevation-check.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(d['model']),rows[0]['heightMetres'])
