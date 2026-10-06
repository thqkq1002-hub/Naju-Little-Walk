"""Upload reviewed project packages to the private archive and verify GitHub digests."""
import argparse, hashlib, json, subprocess, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

R=Path(__file__).resolve().parents[1];P=R/'work/github-backup-20261004/packages'
GH=Path('C:/Program Files/GitHub CLI/gh.exe');REPO='reinhardt7177-lab/naju-little-walk-project-archive';TAG='naju-project-v95-20261004'

def gh(*args):
    r=subprocess.run([str(GH),*args],capture_output=True,check=True,encoding='utf8')
    return r.stdout

def checksum(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while block:=f.read(4*1024**2):h.update(block)
    return h.hexdigest()

def run():
    a=argparse.ArgumentParser();a.add_argument('--upload',action='store_true');opts=a.parse_args()
    repository=json.loads(gh('api','repos/'+REPO))
    if not repository['private']:raise RuntimeError('Authoring references must remain in the private archive')
    manifest=json.loads((P/'manifest.json').read_text(encoding='utf8'))
    files=[P/x['name'] for x in manifest['packages']]+[P/'manifest.json',P/'SHA256SUMS',P/'restore_github_project.py',P/'README.md',P/'archive-verification.json']
    expected={p.name:dict(bytes=p.stat().st_size,sha256=checksum(p)) for p in files}
    release=json.loads(gh('api',f'repos/{REPO}/releases/tags/{TAG}'))
    known={x['name']:x for x in release['assets']}
    if opts.upload:
        def upload(path):
            if path.name in known:
                remote=known[path.name]
                if remote.get('digest')!='sha256:'+expected[path.name]['sha256'] or remote['size']!=expected[path.name]['bytes']:
                    raise RuntimeError('Existing asset differs; will not overwrite: '+path.name)
                return path.name+' already matches'
            for attempt in range(3):
                try:
                    gh('release','upload',TAG,str(path),'--repo',REPO)
                    return path.name+' uploaded'
                except subprocess.CalledProcessError:
                    if attempt==2:raise
                    time.sleep(2*(attempt+1))
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(upload,path) for path in files]
            for future in as_completed(futures):print(future.result(),flush=True)
    release=json.loads(gh('api',f'repos/{REPO}/releases/tags/{TAG}'))
    known={x['name']:x for x in release['assets']};checks={}
    for name,expect in expected.items():
        remote=known.get(name)
        if not remote or remote['size']!=expect['bytes'] or remote.get('digest')!='sha256:'+expect['sha256']:
            raise RuntimeError('Remote package verification failed: '+name)
        checks[name]=dict(bytes=remote['size'],sha256=expect['sha256'],githubDigestMatches=True,state=remote['state'])
        if remote['state']!='uploaded':raise RuntimeError('Incomplete asset upload: '+name)
    report=dict(repo=REPO,private=True,releaseURL=release['html_url'],tag=TAG,allRemoteDigestsMatch=True,
                uploadedBytes=sum(x['bytes'] for x in expected.values()),checks=checks,
                snapshotCommit=manifest['snapshotCommit'],files=manifest['file_count'],objects=manifest['object_count'])
    (P.parent/'remote-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':run()
