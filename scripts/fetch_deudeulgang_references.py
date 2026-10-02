"""Read-only source collection for modelling; photos stay out of the deployment."""
import json, urllib.request, urllib.parse, pathlib, concurrent.futures
R=pathlib.Path(__file__).resolve().parents[1]
W=R/'work/deudeulgang';W.mkdir(parents=True,exist_ok=True)
S=R/'knowledge/sources/deudeulgang';S.mkdir(parents=True,exist_ok=True)
def get(url,path):
 req=urllib.request.Request(url,headers={'User-Agent':'NajuWalk-reference-research/1.0'})
 with urllib.request.urlopen(req,timeout=90) as r:data=r.read()
 path.write_bytes(data);print(path.name,len(data),flush=True);return data
def photo(i):
 return get('https://ojsfile.ohmynews.com/STD_IMG_FILE/2025/0816/'+i+'_STD.jpg',W/(i+'.jpg'))
def satellite():
 p=dict(bbox='126.851,35.016,126.860,35.024',bboxSR=4326,imageSR=4326,size='1500,1500',format='jpg',f='json')
 url='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?'+urllib.parse.urlencode(p)
 data=json.loads(get(url,S/'satellite-extent.json'));get(data['href'],W/'satellite.jpg')
def osm():
 get('https://api.openstreetmap.org/api/0.6/map?bbox=126.849,35.014,126.862,35.026',S/'map.osm')
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
 jobs=[ex.submit(photo,i) for i in ['IE003509897','IE003509901','IE003510001']]+[ex.submit(satellite),ex.submit(osm)]
 for j in jobs:
  try:j.result()
  except Exception as e:print(type(e).__name__,str(e),flush=True)
