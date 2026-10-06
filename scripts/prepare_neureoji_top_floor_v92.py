from pathlib import Path
import math,json,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/python-geo'))
from shapely.geometry import Polygon,box
cx,cz=-.65,-2.4;r=2.8
poly=Polygon([(cx+math.cos(i*math.tau/64)*r,cz+math.sin(i*math.tau/64)*r) for i in range(64)])
# A real stairwell notch leaves the last risers uncovered by the observation floor.
poly=poly.difference(box(1.20,-3.25,4,-1.55))
(R/'work/neureoji-v92/top-floor.json').write_text(json.dumps(list(poly.exterior.coords)[:-1]),encoding='utf8')
