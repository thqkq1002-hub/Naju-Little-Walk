"""Public photo references for observation only; not included in public assets."""
import urllib.request,re,html,json,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1]
SOURCES={'gallery': 'https://live112.tistory.com/5968', 'neureoji':'https://forme13.tistory.com/3621'}
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req,timeout=30) as response:return response.read()
for key,url in SOURCES.items():
    folder=R/'work/scene-references-v91'/key;folder.mkdir(parents=True,exist_ok=True)
    page=get(url).decode('utf8');(folder/'source.html').write_text(page,encoding='utf8')
    urls=list(dict.fromkeys(html.unescape(u) for u in re.findall(r'data-origin="([^"]+)"',page)))
    if not urls:urls=list(dict.fromkeys(html.unescape(u) for u in re.findall(r'<img[^>]+src="(https://(?:blog.kakaocdn.net|t1.daumcdn.net)/[^"]+)"',page)))
    def save(item):
        i,u=item;path=folder/f'{i+1:02}.jpg'
        try:path.write_bytes(get(u));return {'index':i+1,'file':str(path.relative_to(R)), 'ok':True}
        except Exception as e:return {'index':i+1,'ok':False,'error':str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(save,enumerate(urls)))
    (folder/'manifest.json').write_text(json.dumps({'page':url,'images':results},indent=2),encoding='utf8')
    print(key,json.dumps(results),flush=True)
