"""Keep satellite reference locally for plan comparison, never deploy imagery."""
import requests,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'work/bitgaram-v101';O.mkdir(exist_ok=True,parents=True)
url='https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export'
p=dict(bbox='126.7890,35.0150,126.7920,35.0178',bboxSR=4326,imageSR=3857,size='1200,1200',format='jpg',f='json')
r=requests.get(url,params=p,timeout=60);r.raise_for_status();d=r.json();assert 'href' in d,d
(O/'satellite-export.json').write_text(json.dumps(d,indent=2),encoding='utf8')
r=requests.get(d['href'],timeout=60);r.raise_for_status();(O/'satellite-native.jpg').write_bytes(r.content)
print('SATELLITE',d['extent'])
metadata=requests.get(url.replace('/export','/9/query'),params=dict(geometry='126.790447,35.016925',geometryType='esriGeometryPoint',inSR=4326,spatialRel='esriSpatialRelIntersects',outFields='*',returnGeometry='false',f='json'),timeout=60)
metadata.raise_for_status();data=metadata.json();assert data.get('features')
K=R/'knowledge/sources/bitgaram/access-v101';K.mkdir(exist_ok=True,parents=True)
(K/'satellite-metadata.json').write_text(json.dumps(data,indent=2),encoding='utf8')
