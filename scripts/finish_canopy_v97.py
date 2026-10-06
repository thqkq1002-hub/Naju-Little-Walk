from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
code=(R/'scripts/compact_neureoji_plants_v95.py').read_text(encoding='utf8').replace('knowledge/sources/neureoji-v95/model.json','knowledge/sources/observatory-quality-v97/model.json').replace("('Neureoji95_',","('Neureoji97_', 'Neureoji93_near_trunks_and_branches', 'Neureoji95_',")
exec(compile(code,str(R/'scripts/compact_neureoji_plants_v95.py'),'exec'),{'__file__':str(R/'scripts/compact_neureoji_plants_v95.py')})
k=json.loads((R/'knowledge/sources/observatory-quality-v97/model.json').read_text(encoding='utf8'))
p=R/'public/neureoji-world.json';w=json.loads(p.read_text(encoding='utf8'))
assert hashlib.sha256(json.dumps(w['solids'],sort_keys=True).encode()).hexdigest()==k['navigationSolidsSha256']
w['revision']=k['revision'];w['navigationFromBlend']=k['blend'];w['limitations'].append('v97: 근거리 입체 수관은 사진 참고 추정. 뿌리 높이는 표시 지형에 맞췄으며 개별 수종은 실측하지 않음.')
p.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
