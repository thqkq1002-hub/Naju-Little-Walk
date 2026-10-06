from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import random,math
R=Path(__file__).resolve().parents[1];O=R/'work/neureoji-v100';O.mkdir(parents=True,exist_ok=True)
palettes=[((82,105,150),(133,163,206)),((97,81,131),(170,145,199)),((124,80,111),(199,149,177))]
for index,(shadow,petal) in enumerate(palettes):
 rng=random.Random(10005+index);n=512;im=Image.new('RGB',(n,n),shadow);draw=ImageDraw.Draw(im)
 for row in range(-1,17):
  for col in range(-1,17):
   cx=(col+.5)*32+rng.uniform(-11,11);cy=(row+.5)*32+rng.uniform(-11,11);angle=rng.random()*math.tau;size=rng.uniform(8,13);vary=rng.uniform(.86,1.13)
   color=tuple(min(255,int(c*vary)) for c in petal)
   for j in range(4):
    a=angle+j*math.pi/2;ux,uy=math.cos(a),math.sin(a);vx,vy=-uy,ux;points=[]
    for q in range(20):
     t=q*math.tau/20;along=size*(.56+.56*math.cos(t));across=size*.43*math.sin(t)
     points.append((cx+ux*along+vx*across,cy+uy*along+vy*across))
    draw.polygon(points,fill=color)
    end=(cx+ux*size*.89,cy+uy*size*.89);draw.line([(cx,cy),end],fill=tuple(min(255,int(c*.86)) for c in color),width=1)
   draw.ellipse((cx-1.2,cy-1.2,cx+1.2,cy+1.2),fill=(198,193,163))
 im.resize((256,256),Image.Resampling.LANCZOS).save(O/f'bloom-volume-{index}.png')
