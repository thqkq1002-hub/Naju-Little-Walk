"""Create deduplicated, verifiable project release packages, preserving local originals."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, shutil, subprocess, tarfile, zipfile
from pathlib import Path
import audit_github_backup as audit

ROOT=audit.ROOT;OUT=ROOT/'work/github-backup-20261004/packages'
LIMIT=1800*1024**2

def digest(path):
    with path.open('rb') as f:return audit.inspect_stream(f)

def sanitize_archives(manifest):
    additions=[];notes=[]
    for blocked in manifest['blocked_files']:
        if blocked['finding_types'] or any(x['type']!='private_configuration' for x in blocked['archive_findings']):
            continue
        source=ROOT/blocked['path'];dest=OUT/'sanitized'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
        mode='w:gz' if source.name.endswith(('.tar.gz','.tgz')) else 'w'
        omitted=[]
        with tarfile.open(source,'r|*') as old,tarfile.open(dest,mode) as new:
            for member in old:
                relative=member.name.removeprefix('./')
                category,_=audit.classification(relative)
                if category=='private_configuration':omitted.append(member.name);continue
                # Do not recreate archive links into paths outside this project.
                if member.issym() or member.islnk():omitted.append(member.name);continue
                stream=old.extractfile(member) if member.isfile() else None
                new.addfile(member,stream)
                if stream:stream.close()
        sha,findings=digest(dest)
        if findings or audit.inspect_archive(dest):raise RuntimeError('Sanitized archive failed inspection')
        st=dest.stat();row=dict(path=blocked['path'],bytes=st.st_size,mtime_ns=st.st_mtime_ns,sha256=sha,category='sanitized_legacy_package')
        additions.append((row,dest))
        notes.append(dict(path=blocked['path'],originalSha256=digest(source)[0],backupSha256=sha,omittedMembers=omitted))
    return additions,notes

def package():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'manifest.json').exists():raise RuntimeError('Use the existing manifest, or explicitly choose a new snapshot directory')
    inventory=audit.inventory()
    inv=OUT.parent/'inventory-final.json';inv.write_text(json.dumps(inventory,ensure_ascii=False),encoding='utf8')
    if inventory['errors']:raise RuntimeError('Inventory errors require review')
    manifest=audit.prepare_manifest(inv)
    additions,notes=sanitize_archives(manifest)
    sources={obj['sha256']:ROOT/obj['source'] for obj in manifest['objects']}
    objects={obj['sha256']:obj for obj in manifest['objects']}
    for row,source in additions:
        manifest['files'].append(row)
        if row['sha256'] not in objects:
            objects[row['sha256']]=dict(sha256=row['sha256'],bytes=row['bytes'],source=row['path'],paths=[])
            sources[row['sha256']]=source
        objects[row['sha256']]['paths'].append(row['path'])
    bundle=OUT.parent/'project-history.bundle'
    subprocess.run(['git','bundle','create',str(bundle),'--all'],cwd=ROOT,check=True)
    subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
    sha,_=digest(bundle)
    objects[sha]=dict(sha256=sha,bytes=bundle.stat().st_size,source='project-history.bundle',paths=[])
    sources[sha]=bundle
    ordered=sorted(objects.values(),key=lambda x:x['sha256']);groups=[];group=[];size=0
    for obj in ordered:
        if obj['bytes']>LIMIT:raise RuntimeError('An object exceeds the release segment size')
        if group and size+obj['bytes']>LIMIT:groups.append(group);group=[];size=0
        group.append(obj);size+=obj['bytes']
    if group:groups.append(group)
    packages=[]
    for i,group in enumerate(groups,1):
        dest=OUT/f'naju-project-{i:03d}.zip'
        with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as archive:
            for obj in group:
                source=sources[obj['sha256']];name='objects/'+obj['sha256'];h=hashlib.sha256();count=0
                with source.open('rb') as f,archive.open(name,'w',force_zip64=True) as out:
                    while block:=f.read(4*1024**2):h.update(block);out.write(block);count+=len(block)
                if count!=obj['bytes'] or h.hexdigest()!=obj['sha256']:raise RuntimeError('Source changed while packaging: '+obj['source'])
                obj.update(package=dest.name,member=name)
        size=dest.stat().st_size
        if size>=2*1024**3:raise RuntimeError('Release attachment exceeds GitHub limit')
        packages.append(dict(name=dest.name,bytes=size,sha256=digest(dest)[0],objects=len(group)))
        print(f'Packaged {i}/{len(groups)}: {dest.name}, {size:,} bytes',flush=True)
    manifest.update(created_at=dt.datetime.now(dt.timezone.utc).isoformat(),objects=ordered,packages=packages,
        sanitizedLegacyPackages=notes,source_bytes=sum(r['bytes'] for r in manifest['files']),
        file_count=len(manifest['files']),object_count=len(ordered),unique_bytes=sum(r['bytes'] for r in ordered),
        gitHistoryBundle=dict(sha256=sha,name='project-history.bundle'),
        snapshotCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    shutil.copy2(ROOT/'scripts/restore_github_project.py',OUT/'restore_github_project.py')
    (OUT/'SHA256SUMS').write_text(''.join(p['sha256']+'  '+p['name']+'\n' for p in packages),encoding='utf8')
    print(json.dumps({k:manifest[k] for k in ['file_count','object_count','source_bytes','unique_bytes','snapshotCommit']},ensure_ascii=False),flush=True)

if __name__=='__main__':package()
