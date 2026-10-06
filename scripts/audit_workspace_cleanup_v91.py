"""Identify disposable cache and byte-identical staged model copies, never originals."""
from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[1]
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
def safe(p):
    p=p.resolve()
    if not p.is_relative_to(R) or p==R:raise ValueError(str(p))
    return p
active=[]
for folder in ['public','outputs','assets']:
    for p in (R/folder).rglob('*'):
        if p.is_file() and p.name.endswith(('.glb','.glb.gz')):active.append(p)
by_size={}
for p in active:by_size.setdefault(p.stat().st_size,[]).append(p)
text='\n'.join(p.read_text(encoding='utf8',errors='ignore') for folder in ['scripts','knowledge'] for p in (R/folder).rglob('*') if p.is_file() and p.suffix in ['.py','.mjs','.ps1','.md','.json'])
copies=[];memo={}
for d in (R/'work').iterdir():
    # Staged releases are generated upload copies. Do not traverse tool/dependency,
    # research, current scene build, user character or source archives.
    if not d.is_dir() or not (any(t in d.name for t in ['-stage','-final','-v4','-v5']) or d.name in ['quality-site-publish','tablet-site-source']):continue
    for p in d.rglob('*'):
        if not p.is_file() or not p.name.endswith(('.glb','.glb.gz')):continue
        rel=p.relative_to(R).as_posix()
        if rel in text or rel.replace('/','\\') in text:continue
        matches=by_size.get(p.stat().st_size,[])
        if not matches:continue
        value=digest(p)
        for q in matches:
            if str(q) not in memo:memo[str(q)]=digest(q)
            qsha=memo[str(q)]
            if qsha==value:
                copies.append(dict(path=rel,bytes=p.stat().st_size,sha256=value,retained=q.relative_to(R).as_posix(),reason='Byte-identical generated model copy in an inactive upload stage'))
                break
caches=[]
for rel in ['.next','.vinext','.wrangler','dist','tsconfig.tsbuildinfo','work/npm-cache','work/package-tmp']:
    p=safe(R/rel)
    if p.exists():
        files=[p] if p.is_file() else [f for f in p.rglob('*') if f.is_file()]
        # Local generated output/cache only. A scene source prevents deletion.
        if any(f.suffix in ['.blend','.blend1'] for f in files):continue
        caches.append(dict(path=rel,files=len(files),bytes=sum(f.stat().st_size for f in files),reason='Rebuildable build/package cache'))
for folder in ['scripts','work/scene-references-v91']:
    for p in (R/folder).rglob('__pycache__'):
        if p.is_dir():
            files=[f for f in p.rglob('*') if f.is_file()]
            caches.append(dict(path=p.relative_to(R).as_posix(),files=len(files),bytes=sum(f.stat().st_size for f in files),reason='Python bytecode cache'))
report=dict(revision='workspace-cleanup-v91',auditedAtUTC=datetime.now(timezone.utc).isoformat(),root=str(R),
    duplicateStagedModels=copies,rebuildableCaches=caches,unusedRuntimeCode=0,
    bytesToDelete=sum(p['bytes'] for p in copies+caches),
    preserved=['All .blend/.blend1 files','Active public models and world JSON','Character originals and untracked user work','Research/reference photographs','Generation scripts','At least one identical source model for every removed duplicate'])
out=R/'work/cleanup-v91';out.mkdir(exist_ok=True)
(out/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:len(report[k]) for k in ['duplicateStagedModels','rebuildableCaches']}),flush=True)
print('bytesToDelete',report['bytesToDelete'],flush=True)
