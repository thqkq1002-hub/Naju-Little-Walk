"""Retrieve bounded public reference data without modifying the earlier source snapshot."""
from pathlib import Path
import urllib.request,urllib.parse,json,math,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];S=R/'knowledge/sources/bitgaram';W=R/'work'
bbox=(126.765,34.998,126.822,35.035)
path=S/'district-2026-09-20.osm'
if not path.exists():
 url='https://api.openstreetmap.org/api/0.6/map?bbox='+','.join(map(str,bbox))
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'NajuWalk-reference/1.0'}),timeout=100) as response:path.write_bytes(response.read())
root=ET.parse(path).getroot();nodes={n.attrib['id']:(float(n.attrib['lon']),float(n.attrib['lat'])) for n in root.findall('node')};ways=[]
origin=(126.790447,35.016925)
for w in root.findall('way'):
 pts=[nodes.get(n.attrib['ref']) for n in w.findall('nd')]
 if None in pts or len(pts)<2:continue
 tags={t.attrib['k']:t.attrib['v'] for t in w.findall('tag')}
 ways.append(dict(id=w.attrib['id'],tags=tags,points=[[round((lon-origin[0])*111320*math.cos(math.radians(origin[1])),3),round((origin[1]-lat)*111320,3)] for lon,lat in pts]))
(S/'district-2026-09-20.json').write_text(json.dumps(dict(source='OpenStreetMap contributors, ODbL',retrieved='2026-09-20',bbox=bbox,ways=ways),ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('ways',len(ways),'buildings',sum('building' in w['tags'] for w in ways),flush=True)
image=W/'bitgaram-district-satellite.jpg'
if not image.exists():
 q=urllib.parse.urlencode(dict(bbox=','.join(map(str,bbox)),bboxSR=4326,imageSR=4326,size='2000,1600',format='jpg',f='image'))
 with urllib.request.urlopen('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?'+q,timeout=90) as response:image.write_bytes(response.read())
print('satellite saved for comparison, acquisition date unknown',flush=True)
