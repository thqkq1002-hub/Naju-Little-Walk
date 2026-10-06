"""Independent SRTM-derived terrain checks; no claim of surveyed bare ground."""
from pathlib import Path
import json, math, io, requests, hashlib
from PIL import Image

R = Path(__file__).resolve().parents[1]
O = R / 'knowledge/sources/observatory-relief-v96'
W = R / 'work/observatory-relief-v96'
O.mkdir(parents=True, exist_ok=True)
W.mkdir(parents=True, exist_ok=True)
session = requests.Session()
tiles = {}

def elevation(lat, lon):
    zoom = 14
    n = 2 ** zoom
    tx = (lon + 180) / 360 * n
    ty = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    x, y = math.floor(tx), math.floor(ty)
    key = (x, y)
    if key not in tiles:
        url = f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{zoom}/{x}/{y}.png'
        response = session.get(url, timeout=60)
        response.raise_for_status()
        raw = response.content
        (W / f'{zoom}-{x}-{y}.png').write_bytes(raw)
        tiles[key] = (Image.open(io.BytesIO(raw)).convert('RGB'), url, hashlib.sha256(raw).hexdigest())
    image, url, sha = tiles[key]
    # Bilinear sampling at pixel centres, clamped within this comparison tile.
    u, v = (tx-x)*256-.5, (ty-y)*256-.5
    u, v = max(0,min(254.999,u)), max(0,min(254.999,v))
    i, j = math.floor(u), math.floor(v)
    a, b = u-i, v-j
    def h(px,py):
        r,g,blue = image.getpixel((px,py))
        return r*256+g+blue/256-32768
    height = (h(i,j)*(1-a)+h(i+1,j)*a)*(1-b)+(h(i,j+1)*(1-a)+h(i+1,j+1)*a)*b
    return dict(heightMetres=height, tile=url, sha256=sha)

report = dict(dataset='Mapzen/AWS Terrarium terrain tiles, zoom 14',
    documentation='https://registry.opendata.aws/terrain-tiles/',
    limitations=['Independent terrain comparison, mixed source DEM; pixel spacing is not source accuracy.',
                 'SRTM/DSM vegetation, vertical datum and epochs may differ; not a survey.'], sites={})
for key, path in [('neureoji','knowledge/sources/neureoji-v92/native-terrain.json'),
                  ('bitgaram','knowledge/sources/bitgaram/terrain-v89/native-surface-grid.json')]:
    native = json.loads((R/path).read_text(encoding='utf8'))
    origin = native['originWGS84']
    mx = 111320*math.cos(math.radians(origin['lat']))
    coords = [(0,0),(0,30),(0,60),(0,100),(0,180),(-30,0),(30,0),(-70,-40)]
    rows = []
    for x,z in coords:
        lat,lon = origin['lat']-z/111320, origin['lon']+x/mx
        rows.append(dict(x=x,z=z,lat=lat,lon=lon,**elevation(lat,lon)))
    report['sites'][key] = rows
(O/'independent-terrain.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=False),flush=True)
