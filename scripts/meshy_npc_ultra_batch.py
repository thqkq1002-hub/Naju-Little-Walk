"""Generate only the three missing Meshy 7.1 characters; resumable, key-free records."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, base64, json, hashlib, urllib.request, urllib.error
from meshy_baedoli_photo_sample import call
from meshy_baedoli_ultra import SETTINGS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/npc-meshy71-rigged-20261002'
ASSETS = ROOT / 'assets/npc/meshy71-rigged-20261002'
CHARS = ('beodeuri', 'hongdoli', 'teacher')

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temp.replace(path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['submit', 'status', 'download', 'balance'])
    args = parser.parse_args()
    if args.action == 'balance':
        print(json.dumps(call('/balance'))); return
    if args.action == 'submit':
        balance = call('/balance')['balance']
        pending = [c for c in CHARS if not (OUT / c / 'state.json').exists()]
        if balance < len(pending) * 35:
            raise RuntimeError('Insufficient credits; no new tasks submitted')
    for character in CHARS:
        path = OUT / character / 'state.json'
        state = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        asset = ASSETS / character
        if args.action == 'submit':
            if state:
                print(json.dumps({'character': character, 'submission': state.get('submission'), 'task_id': state.get('task_id')})); continue
            reference = ROOT / f'assets/npc/higgsfield-rebuild-20261002/references/{character}-front.png'
            source = reference.read_bytes()
            settings = {**SETTINGS, 'pose_mode': 'a-pose' if character != 'hongdoli' else ''}
            state = {'character': character, 'submission': 'unknown', 'settings': settings,
                     'created_at': datetime.now(timezone.utc).isoformat(), 'balance_before': call('/balance')['balance'],
                     'estimated_credits': 35, 'reference': str(reference.relative_to(ROOT)),
                     'reference_sha256': hashlib.sha256(source).hexdigest()}
            save(path, state)
            try:
                response = call('/image-to-3d', {**settings, 'image_url': 'data:image/png;base64,' + base64.b64encode(source).decode()})
            except urllib.error.HTTPError as error:
                state.update(submission='rejected', http_status=error.code); save(path, state)
                raise RuntimeError(f'{character}: Meshy rejected HTTP {error.code}') from None
            state.update(submission='accepted', task_id=response['result']); save(path, state)
        else:
            if not state.get('task_id'):
                raise RuntimeError('Missing task ID: never retry an unknown submission')
            response = call('/image-to-3d/' + state['task_id'])
            save(OUT / character / 'response.json', response)
            state.update(status=response.get('status'), progress=response.get('progress'), consumed_credits=response.get('consumed_credits'))
            save(path, state)
            if args.action == 'download' and state['status'] == 'SUCCEEDED':
                dest = asset / 'meshy71-original.glb'
                if not dest.exists():
                    with urllib.request.urlopen(response['model_urls']['glb'], timeout=150) as remote:
                        data = remote.read()
                    if data[:4] != b'glTF': raise RuntimeError('Invalid GLB')
                    asset.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
                save(asset / 'generation-record.json', state)
        print(json.dumps({k: state.get(k) for k in ('character', 'task_id', 'submission', 'status', 'progress', 'balance_before', 'consumed_credits')}), flush=True)
    print(json.dumps({'balance': call('/balance')['balance']}), flush=True)

if __name__ == '__main__': main()
