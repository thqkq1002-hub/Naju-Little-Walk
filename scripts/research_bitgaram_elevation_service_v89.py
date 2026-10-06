"""Read public official terrain-analysis implementation to identify its query API.
Research only: no map/app mutation and no credentials copied or reused.
"""
import concurrent.futures,re,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'work/bitgaram-terrain-v89';O.mkdir(exist_ok=True)
paths=['customDraw.js','customSingleMap.js']
def fetch(name):
 url='https://webgis.neins.go.kr/assets/js/user/gis/'+name
 with urllib.request.urlopen(url,timeout=40) as r:raw=r.read()
 (O/name).write_bytes(raw);return name,len(raw)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for result in pool.map(fetch,paths):print(result)
