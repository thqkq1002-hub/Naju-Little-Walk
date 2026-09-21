"""KENTECH reference-only photos and map; downloaded photos are not deployed."""
from pathlib import Path
import urllib.request, urllib.parse, json, concurrent.futures, subprocess
R=Path(__file__).resolve().parents[1];W=R/'work/kentech-v52';W.mkdir(parents=True,exist_ok=True)
S=R/'knowledge/sources/kentech-v52';S.mkdir(parents=True,exist_ok=True)
def get(url,path):
    req=urllib.request.Request(url,headers={'User-Agent':'NajuWalk reference research'})
    try:
        with urllib.request.urlopen(req,timeout=60) as r:data=r.read()
    except urllib.error.URLError:
        # Windows curl uses the OS certificate store; do not disable TLS verification.
        subprocess.run(['curl.exe','--fail','--silent','--show-error','--location','--max-time','60',url,'--output',str(path)],check=True)
        data=path.read_bytes()
    path.write_bytes(data);print(path.name,len(data),flush=True);return data
def satellite():
    p=dict(bbox='126.799,35.006,126.808,35.014',bboxSR=4326,imageSR=4326,size='1600,1600',format='jpg',f='json')
    d=json.loads(get('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?'+urllib.parse.urlencode(p),S/'satellite-extent.json'))
    get(d['href'],W/'satellite.jpg')
urls={
 'aerial-2025.jpg':'https://gs.kentech.ac.kr/upload/editor/board/4eedb034-24e0-46bd-8a8d-aa3e288a1b42.jpg',
 'facade-2024.jpg':'https://img.seoul.co.kr/img/upload/2024/09/12/SSC_20240912213644_O2.jpg',
 'facade-2026.jpg':'https://img.seoul.co.kr/img/upload/2026/02/10/SSC_20260210164052_O2.jpg',
 'campus-masterplan.jpg':'https://home.kentech.ac.kr/resources/sites/eng/campus/img/temp_1633480837270100.jpg',
}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    jobs=[ex.submit(get,u,W/n) for n,u in urls.items()]+[ex.submit(satellite),ex.submit(get,'https://api.openstreetmap.org/api/0.6/map?bbox=126.798,35.005,126.810,35.014',S/'map.osm')]
    for job in jobs:
        try:job.result()
        except Exception as e:print(type(e).__name__,str(e),flush=True)
