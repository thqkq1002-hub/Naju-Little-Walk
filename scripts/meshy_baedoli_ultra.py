"""One Meshy 7.1 Ultra character, with credit guard and resumable submission."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, base64, hashlib, json, urllib.request, urllib.error
import meshy_baedoli_photo_sample as connection

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/baedoli-meshy71-ultra-20261002'
ASSETS = ROOT / 'assets/npc/meshy71-ultra-20261002'
STATE = OUT / 'task-state.json'
REFERENCE = ROOT / 'assets/npc/higgsfield-rebuild-20261002/references/baedoli-front.png'
ESTIMATED_CREDITS = 35
SETTINGS = {
    'model_type': 'standard', 'ai_model': 'meshy-7.1',
    'geometry_resolution': '4k', 'texture_resolution': '4k',
    'should_texture': True, 'enable_pbr': True, 'should_remesh': False,
    'image_enhancement': False, 'pose_mode': '',
    'target_formats': ['glb'], 'multi_view_thumbnails': True,
}

def save(state):
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(state, indent=2), encoding='utf-8')
    temp.replace(STATE)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'balance', 'submit', 'status', 'download'])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    if args.action == 'balance':
        print(json.dumps(connection.call('/balance')))
        return
    if args.action == 'prepare':
        plan = {'character': 'baedoli', 'settings': SETTINGS,
                'estimated_api_credits': ESTIMATED_CREDITS,
                'reference': str(REFERENCE.relative_to(ROOT)),
                'reference_sha256': hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
                'status': 'PREPARED_NOT_SUBMITTED'}
        ASSETS.mkdir(parents=True, exist_ok=True)
        (ASSETS / 'generation-plan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
        print(json.dumps(plan))
        return
    if args.action == 'submit':
        if state:
            print(json.dumps({'submission': state.get('submission'), 'existing_task_id': state.get('task_id')}))
            return
        balance = connection.call('/balance')['balance']
        if balance < ESTIMATED_CREDITS:
            print(json.dumps({'status': 'BLOCKED_INSUFFICIENT_CREDITS', 'balance': balance,
                              'required': ESTIMATED_CREDITS, 'shortfall': ESTIMATED_CREDITS - balance,
                              'submitted': False}))
            return
        source = REFERENCE.read_bytes()
        state = {'submission': 'unknown', 'created_at': datetime.now(timezone.utc).isoformat(),
                 'balance_before': balance, 'settings': SETTINGS,
                 'estimated_credits': ESTIMATED_CREDITS,
                 'reference': str(REFERENCE.relative_to(ROOT)),
                 'reference_sha256': hashlib.sha256(source).hexdigest()}
        save(state)
        try:
            response = connection.call('/image-to-3d', {**SETTINGS,
                'image_url': 'data:image/png;base64,' + base64.b64encode(source).decode()})
        except urllib.error.HTTPError as error:
            state.update(submission='rejected', http_status=error.code)
            save(state)
            raise RuntimeError('Meshy submission rejected: HTTP ' + str(error.code)) from None
        state.update(submission='accepted', task_id=response['result'])
        save(state)
        print(json.dumps({'task_id': state['task_id'], 'submission': 'accepted', 'balance_before': balance}))
        return
    if not state.get('task_id'):
        raise RuntimeError('No task ID: do not resubmit an unknown outcome')
    response = connection.call('/image-to-3d/' + state['task_id'])
    (OUT / 'task-response.json').write_text(json.dumps(response, indent=2), encoding='utf-8')
    state.update(status=response.get('status'), progress=response.get('progress'),
                 balance_after=connection.call('/balance')['balance'])
    save(state)
    print(json.dumps({k: state.get(k) for k in ('task_id', 'status', 'progress', 'balance_before', 'balance_after')}))
    if args.action == 'download' and state['status'] == 'SUCCEEDED':
        ASSETS.mkdir(parents=True, exist_ok=True)
        dest = ASSETS / 'baedoli-meshy71-original.glb'
        if not dest.exists():
            with urllib.request.urlopen(response['model_urls']['glb'], timeout=120) as asset:
                data = asset.read()
            if data[:4] != b'glTF':
                raise RuntimeError('Invalid GLB')
            dest.write_bytes(data)
        (ASSETS / 'generation-record.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
        print(json.dumps({'file': dest.name, 'bytes': dest.stat().st_size}))

if __name__ == '__main__':
    main()
