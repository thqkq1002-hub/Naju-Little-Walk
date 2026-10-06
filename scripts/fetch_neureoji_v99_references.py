from pathlib import Path
import requests,re,html,json,hashlib
from PIL import Image,ImageOps,ImageDraw
R=Path(__file__).resolve().parents[1];W=R/'work/neureoji-v99/references';W.mkdir(parents=True,exist_ok=True)
page='https://localm.kr/bbs/board.php?bo_table=news&me_id=4&wr_id=4488';s=requests.Session();r=s.get(page,timeout=35);r.raise_for_status();urls=[]
for u in re.findall(r'<img[^>]+src=[\"\x27]([^\"\x27]+)',r.text):
 u=html.unescape(u)
 if '/data/photo/2607/' in u:
  u=requests.compat.urljoin(page,u)
  if u not in urls:urls.append(u)
rows=[]
for i,u in enumerate(urls[:12]):
 try:
  raw=s.get(u,timeout=30).content;p=W/f'2026-{i:02d}.jpg';p.write_bytes(raw);im=Image.open(p)
  if im.width<400:continue
  rows.append(dict(file=p.relative_to(R).as_posix(),url=u,sha256=hashlib.sha256(raw).hexdigest(),size=list(im.size)))
 except Exception as e:print(i,str(e)[:100])
if rows:
 contact=Image.new('RGB',(420*len(rows),310),'white')
 for i,row in enumerate(rows):
  im=Image.open(R/row['file']).convert('RGB');im.thumbnail((410,280));contact.paste(im,(i*420,25));ImageDraw.Draw(contact).text((i*420+10,5),str(i),fill='black')
 contact.save(W/'contact.jpg')
(W/'index.json').write_text(json.dumps(dict(page=page,published='2026-07-10',photos=rows),ensure_ascii=False,indent=2),encoding='utf8');print(len(rows))

