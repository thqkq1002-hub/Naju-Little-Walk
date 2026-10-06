import json,random,sys,math
from pathlib import Path
from PIL import Image,ImageDraw
R=Path('.');sys.path.insert(0,'work/python-geo')
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
W=R/'work/neureoji-v93';D=json.loads((W/'landscape.json').read_text());K=R/'knowledge/sources/neureoji-v93/landscape.json';record=json.loads(K.read_text());origin=record['mapOrigin'];rng=random.Random(9395)
def world(p):return [(126.515+p[0]/1800*.045-origin['lon'])*91281.58980911358,(origin['lat']-(34.933375-p[1]/1350*.03375))*111320]
woods=[Polygon([world(p) for p in pts]) for pts in [[(819,390),(913,391),(970,423),(1000,495),(992,562),(920,594),(864,577),(843,526),(890,470)],[(854,302),(913,347),(940,399),(912,422),(883,409),(872,369)]]]
fields=unary_union([Polygon(p) for p in record['photoInferredFieldEnvelopes']]);woods=unary_union(woods).difference(fields.buffer(4));existing={(round(p[0]/8),round(p[2]/8)) for p in D['trees']}
for z in range(-1400,-350,8):
 for x in range(-900,-50,8):
  if woods.contains(Point(x,z)) and (round(x/8),round(z/8)) not in existing:D['trees'].append([x+rng.uniform(-2,2),.4,z+rng.uniform(-2,2),rng.uniform(5.5,9),rng.randrange(4)])
parts=[woods] if woods.geom_type=='Polygon' else woods.geoms
record['photoInferredWoodlandEnvelopes']=[list(p.exterior.coords) for p in parts];record['woodlandCrowns']=len(D['trees'])
image=Image.open(R/'assets/neureoji-v93/landcover-original.png');draw=ImageDraw.Draw(image)
for p in parts:draw.polygon([((x+3100)/6200*image.width,(z+2700)/5000*image.height) for x,z in p.exterior.coords],fill='#47623a')
image.save(R/'assets/neureoji-v93/landcover-original.png')
# Small distant roofs are photo/satellite interpretations, not surveyed building footprints.
D['photoContextRoofs']=[]
for px,py in [(657,175),(676,175),(692,181),(709,180),(732,193),(756,205),(788,244),(799,268)]:
 D['photoContextRoofs'].append(dict(points=[world(q) for q in [(px-2,py-1.5),(px+2,py-1.5),(px+2,py+1.5),(px-2,py+1.5)]],ground=3.0))
record['photoInferredRoofCount']=len(D['photoContextRoofs']);record['photoInferredRoofs']=D['photoContextRoofs']
(W/'landscape.json').write_text(json.dumps(D,separators=(',',':')),encoding='utf8');K.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Final woodland crowns',len(D['trees']))
