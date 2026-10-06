from pathlib import Path
import requests,re,json,html,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[1];W=R/'work/observatory-relief-v96/photos';W.mkdir(parents=True,exist_ok=True)
s=requests.Session();s.headers['User-Agent']='Mozilla/5.0'
page='https://forme13.tistory.com/3621'
h=s.get(page,timeout=40);h.raise_for_status()
urls=[]
for u in re.findall(r'<img[^>]+src="([^"]+)"',h.text):
    u=html.unescape(u)
    if 'kakaocdn.net' in u and u not in urls:urls.append(u)
rows=[]
for i,u in enumerate(urls):
    try:
        response=s.get(u,headers={'Referer':page},timeout=35);response.raise_for_status()
        path=W/f'neureoji-{i:02d}.jpg';path.write_bytes(response.content)
        im=Image.open(path)
        if im.width<500:continue
        rows.append(dict(index=i,file=str(path.relative_to(R)),url=u,size=list(im.size),sha256=hashlib.sha256(response.content).hexdigest()))
    except Exception as e:print(i,str(e),flush=True)
(W/'index.json').write_text(json.dumps(dict(page=page,photos=rows),ensure_ascii=False,indent=2),encoding='utf8')
print('reference photos',len(rows),flush=True)
