"""Explicit, resumable Meshy NPC generation. Credentials stay in the environment."""
from pathlib import Path
import argparse, base64, json, os, urllib.request, urllib.error
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/npc-meshy-20261002'
STATE = OUT/'tasks.json'
API = 'https://api.meshy.ai/openapi/v1'
CONFIG = {
    'baedoli': ('배돌이', 12000),
    'beodeuri': ('버들낭자', 15000),
    'hongdoli': ('홍돌이', 12000),
    'teacher': ('선생님', 15000),
}

def request(path, payload=None):
    headers = {'Authorization': 'Bearer '+os.environ['MESHY_API_KEY']}
    if payload is not None: headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(API+path, data=None if payload is None else json.dumps(payload).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        message = e.read().decode(errors='replace')[:1000]
        raise RuntimeError(f'Meshy HTTP {e.code}: {message}') from None

def save(state):
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(STATE)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action', choices=['submit','status','download','balance'])
    parser.add_argument('--character', choices=list(CONFIG))
    args=parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    state=json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    if args.action=='balance':
        print(json.dumps(request('/balance'))); return
    keys=[args.character] if args.character else list(CONFIG)
    for key in keys:
        folder=OUT/key
        folder.mkdir(exist_ok=True)
        if args.action=='submit':
            if key in state:
                print(json.dumps({'character':key,'existing':state[key]},ensure_ascii=True)); continue
            source=OUT/'references'/f'{key}.png'
            if not source.exists(): raise FileNotFoundError(source)
            payload={'image_url':'data:image/png;base64,'+base64.b64encode(source.read_bytes()).decode(),
                     'model_type':'smart-topology','ai_model':'meshy-t2','target_polycount':CONFIG[key][1],
                     'should_texture':False,'target_formats':['glb'], 'pose_mode':''}
            # Mark before the paid POST. An unknown outcome must be recovered, never resubmitted.
            state[key]={'name':CONFIG[key][0],'submission':'unknown','created_at':datetime.now(timezone.utc).isoformat(),
                        'settings':{k:v for k,v in payload.items() if k!='image_url'}}
            save(state)
            try:
                result=request('/image-to-3d',payload)
            except RuntimeError as e:
                state[key]['submission']='rejected';state[key]['error']=str(e);save(state);raise
            state[key].update(task_id=result['result'],submission='accepted')
            save(state)
            print(json.dumps({'character':key,'task_id':result['result'],'submission':'accepted'}))
        else:
            item=state.get(key,{})
            if 'task_id' not in item:
                print(json.dumps({'character':key,'status':'NOT_SUBMITTED'}));continue
            result=request('/image-to-3d/'+item['task_id'])
            # Signed asset links are only saved in ignored outputs, not project knowledge or logs.
            (folder/'task-response.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            item.update(status=result.get('status'),progress=result.get('progress'),task_error=result.get('task_error'))
            save(state)
            print(json.dumps({'character':key,'status':item['status'],'progress':item['progress'],'error':item['task_error']}))
            if args.action=='download' and item['status']=='SUCCEEDED':
                url=result.get('model_urls',{}).get('glb')
                if not url: raise RuntimeError('Successful task without GLB URL')
                dest=folder/'meshy-original.glb'
                if dest.exists():
                    print(json.dumps({'character':key,'file':'existing','bytes':dest.stat().st_size}));continue
                with urllib.request.urlopen(url,timeout=90) as response: data=response.read()
                if data[:4]!=b'glTF':raise RuntimeError('Downloaded asset is not GLB')
                dest.write_bytes(data)
                print(json.dumps({'character':key,'file':str(dest),'bytes':len(data)},ensure_ascii=True))

if __name__=='__main__': main()
