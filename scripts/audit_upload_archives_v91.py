"""Recognize obsolete build-only upload archives; preserve project source archives."""
from pathlib import Path
import tarfile,hashlib,json
R=Path(__file__).resolve().parents[1];items=[]
for p in (R/'work').glob('*.tar.gz'):
    with tarfile.open(p) as t:
        members=t.getmembers()
        names=[m.name.lstrip('./') for m in members]
        if not members or any(m.issym() or m.islnk() for m in members):continue
        if any(n and not (n=='dist' or n.startswith('dist/') or n=='openai' or n.startswith('openai/')) for n in names):continue
        if any(n.endswith(('.blend','.blend1')) for n in names):continue
    items.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,files=len(members),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        reason='Obsolete generated upload archive: only dist/hosting files; current Vercel builds from Git; authoring sources retained'))
(R/'work/cleanup-v91/archive-audit.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('archives',len(items),'bytes',sum(i['bytes'] for i in items),flush=True)
