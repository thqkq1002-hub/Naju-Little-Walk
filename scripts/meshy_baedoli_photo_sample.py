"""One resumable image-to-3D sample. Never prints keys, image data or signed URLs."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, base64, hashlib, json, os, urllib.request, urllib.error

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/baedoli-photo-sample-20261002'
STATE = OUT / 'task-state.json'
ASSETS = ROOT / 'assets/npc/meshy-photo-sample-20261002'
SOURCE = ROOT / 'assets/npc/higgsfield-rebuild-20261002/references/baedoli-front.png'
API = 'https://api.meshy.ai/openapi/v1'

def call(path, payload=None):
    headers = {'Authorization': 'Bearer ' + os.environ['MESHY_API_KEY']}
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(API + path, headers=headers,
        data=None if payload is None else json.dumps(payload).encode())
    with urllib.request.urlopen(req, timeout=90) as response:
        return json.loads(response.read())

def save(state):
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(state, indent=2), encoding='utf-8')
    temp.replace(STATE)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['submit', 'status', 'download', 'balance'])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    if args.action == 'balance':
        print(json.dumps(call('/balance')))
        return
    if args.action == 'submit':
        if state:
            print(json.dumps({'existing_task': state.get('task_id'), 'submission': state.get('submission')}))
            return
        balance = call('/balance')['balance']
        if balance < 5:
            raise RuntimeError('Insufficient Meshy credits for the 5-credit mesh-only sample')
        source = SOURCE.read_bytes()
        settings = {'model_type': 'smart-topology', 'ai_model': 'meshy-t2',
                    'target_polycount': 15000, 'should_texture': False,
                    'target_formats': ['glb'], 'pose_mode': '', 'multi_view_thumbnails': True}
        state = {'submission': 'unknown', 'created_at': datetime.now(timezone.utc).isoformat(),
                 'balance_before': balance, 'estimated_credits': 5, 'settings': settings,
                 'reference': str(SOURCE.relative_to(ROOT)), 'reference_sha256': hashlib.sha256(source).hexdigest()}
        save(state)
        try:
            response = call('/image-to-3d', {**settings, 'image_url': 'data:image/png;base64,' + base64.b64encode(source).decode()})
        except urllib.error.HTTPError as error:
            state.update(submission='rejected', http_status=error.code)
            save(state)
            raise RuntimeError('Meshy submission rejected: HTTP ' + str(error.code)) from None
        state.update(task_id=response['result'], submission='accepted')
        save(state)
        print(json.dumps({'task_id': state['task_id'], 'submission': 'accepted', 'balance_before': balance, 'estimated_credits': 5}))
        return
    if not state.get('task_id'):
        raise RuntimeError('No recoverable task ID; do not resubmit an unknown outcome')
    response = call('/image-to-3d/' + state['task_id'])
    # Raw signed asset URLs remain in ignored outputs only.
    (OUT / 'task-response.json').write_text(json.dumps(response, indent=2), encoding='utf-8')
    state.update(status=response.get('status'), progress=response.get('progress'),
                 balance_after=call('/balance')['balance'])
    save(state)
    print(json.dumps({k: state.get(k) for k in ('task_id', 'status', 'progress', 'balance_before', 'balance_after')}))
    if args.action == 'download' and state['status'] == 'SUCCEEDED':
        ASSETS.mkdir(parents=True, exist_ok=True)
        glb = ASSETS / 'baedoli-photo-original.glb'
        if not glb.exists():
            with urllib.request.urlopen(response['model_urls']['glb'], timeout=90) as result:
                data = result.read()
            if data[:4] != b'glTF':
                raise RuntimeError('Invalid GLB download')
            glb.write_bytes(data)
        (ASSETS / 'generation-record.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
        print(json.dumps({'downloaded': glb.name, 'bytes': glb.stat().st_size}))

if __name__ == '__main__':
    main()
