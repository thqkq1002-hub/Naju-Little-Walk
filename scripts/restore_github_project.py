"""Verify or restore downloaded project release packages without overwriting existing files."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, zipfile
from pathlib import Path

def run():
    p=argparse.ArgumentParser();p.add_argument('--packages',type=Path,required=True)
    p.add_argument('--destination',type=Path);p.add_argument('--verify-only',action='store_true');a=p.parse_args()
    base=a.packages.resolve();manifest=json.loads((base/'manifest.json').read_text(encoding='utf8'))
    if not a.verify_only and not a.destination:p.error('Specify an empty destination, or --verify-only')
    dest=a.destination.resolve() if a.destination else None
    if dest:
        if dest.exists() and any(dest.iterdir()):raise RuntimeError('Destination must be empty; existing files will not be overwritten')
        if dest==base or base.is_relative_to(dest):raise RuntimeError('Destination cannot contain the downloaded packages')
        dest.mkdir(parents=True,exist_ok=True)
    files={};timestamps={row['path']:row['mtime_ns'] for row in manifest['files']}
    for row in manifest['files']:files.setdefault(row['sha256'],[]).append(row['path'])
    bundle=manifest['gitHistoryBundle'];files.setdefault(bundle['sha256'],[]).append(bundle['name'])
    objects={o['sha256']:o for o in manifest['objects']};seen=set()
    for package in manifest['packages']:
        path=base/package['name'];h=hashlib.sha256()
        with path.open('rb') as f:
            while block:=f.read(4*1024**2):h.update(block)
        if h.hexdigest()!=package['sha256']:raise RuntimeError('Package checksum mismatch: '+package['name'])
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                sha=member.filename.removeprefix('objects/');obj=objects.get(sha)
                if not obj or obj['package']!=package['name'] or obj['member']!=member.filename or sha in seen:
                    raise RuntimeError('Unexpected or duplicate object')
                targets=[]
                for relative in files.get(sha,[]):
                    logical=Path(relative)
                    if logical.is_absolute() or '..' in logical.parts:raise RuntimeError('Unsafe restore path')
                    if dest:
                        target=(dest/logical).resolve()
                        if not target.is_relative_to(dest):raise RuntimeError('Restore path escapes the destination')
                        target.parent.mkdir(parents=True,exist_ok=True);targets.append(target)
                h=hashlib.sha256();count=0
                # First copy streams from the verified ZIP, then duplicates copy from that restored object.
                out=targets[0].open('xb') if targets else None
                try:
                    with archive.open(member) as stream:
                        while block:=stream.read(4*1024**2):
                            h.update(block);count+=len(block)
                            if out:out.write(block)
                finally:
                    if out:out.close()
                if count!=obj['bytes'] or h.hexdigest()!=sha:raise RuntimeError('Restored object checksum mismatch')
                for target in targets[1:]:shutil.copy2(targets[0],target)
                for target in targets:
                    stamp=timestamps.get(target.relative_to(dest).as_posix())
                    if stamp:os.utime(target,ns=(stamp,stamp))
                seen.add(sha)
        print(f'Verified {package["name"]}: {len(seen)}/{len(objects)} objects',flush=True)
    if seen!=set(objects) or not set(files).issubset(seen):raise RuntimeError('Missing project objects')
    print(json.dumps(dict(allObjectsVerified=True,files=manifest['file_count'],objects=len(seen),restored=bool(dest)),ensure_ascii=False))

if __name__=='__main__':run()
