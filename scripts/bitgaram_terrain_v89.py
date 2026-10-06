"""Shared offline terrain sampler and clearly interpreted civil levels."""
from pathlib import Path
import json,math,bisect
R=Path(__file__).resolve().parents[1]
class Terrain:
 def __init__(self,building):
  self.grid=json.loads((R/'knowledge/sources/bitgaram/terrain-v89/native-surface-grid.json').read_text(encoding='utf8'))
  self.analysis=json.loads((R/'knowledge/sources/bitgaram/terrain-v89/analysis.json').read_text(encoding='utf8'))
  self.old=json.loads((R/'knowledge/sources/bitgaram/access-v69.json').read_text(encoding='utf8'))
  self.origin=self.grid['originWGS84'];self.mx=111320*math.cos(math.radians(self.origin['lat']))
  self.datum=self.grid['modelDatumMetres'];self.upper=self.analysis['adoptedUpperSurfaceMetres']-self.datum
  self.lower=self.analysis['adoptedLowerSurfaceMetres']-self.datum;self.building=building
  oldrail=[(x,y-.95,z) for x,y,z in reversed(self.old['rail_route'])]
  def railheight(i,p):
   t=i/(len(oldrail)-1);p0,p1=oldrail[0],oldrail[-1]
   lo=self.lower-.35-self.sample(p0[0],p0[2]);hi=self.upper-.35-self.sample(p1[0],p1[2])
   return self.sample(p[0],p[2])+(1-t)*lo+t*hi
  self.rail=[(p[0],railheight(i,p),p[2]) for i,p in enumerate(oldrail)]
  self.rail_by_z=sorted(self.rail,key=lambda p:p[2]);self.rail_z=[p[2] for p in self.rail_by_z]
  self.oldrail_by_z=sorted(oldrail,key=lambda p:p[2])
  self.oldslide=self.old['slide_route'];self.slide_z=[p[2] for p in self.oldslide]
  self.slide=[]
  anchor=self.oldslide[27];offset0=self.upper-self.sample(anchor[0],anchor[2]);end=self.oldslide[-1]
  offset1=self.lower-self.sample(end[0],end[2])
  for i,p in enumerate(self.oldslide):
   t=i/(len(self.oldslide)-1)
   height=self.upper if t<=.1125 else self.sample(p[0],p[2])+offset0+(offset1-offset0)*(t-.1125)/.8875
   self.slide.append((p[0],height,p[2]))
  self.stairs=[(x+1.24,y,z) for x,y,z in self.slide]
  self.forest=[(x,self.forest_height(x,z),z) for x,_,z in self.old['forest_route']]
 def sample(self,x,z):
  g=self.grid;lat=self.origin['lat']-z/111320;lon=self.origin['lon']+x/self.mx
  u=(lon-g['sampleOriginLongitude'])/g['longitudeSpacingDegrees'];v=(g['sampleOriginLatitude']-lat)/g['latitudeSpacingDegrees']
  u=max(0,min(g['width']-1.000001,u));v=max(0,min(g['height']-1.000001,v));i,j=math.floor(u),math.floor(v);a,b=u-i,v-j;h=g['heightsMetres']
  return (h[j][i]*(1-a)+h[j][i+1]*a)*(1-b)+(h[j+1][i]*(1-a)+h[j+1][i+1]*a)*b-self.datum
 @staticmethod
 def inside(x,z,poly):
  result=False
  for a,b in zip(poly,poly[1:]+poly[:1]):
   if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:result=not result
  return result
 @staticmethod
 def smooth(t):
  t=max(0,min(1,t));return t*t*(3-2*t)
 @staticmethod
 def at_z(points,z,values=None):
  zs=values or [p[2] for p in points];i=max(0,min(len(points)-2,bisect.bisect_right(zs,z)-1));a,b=points[i:i+2];t=max(0,min(1,(z-a[2])/(b[2]-a[2])))
  return tuple(a[k]+(b[k]-a[k])*t for k in range(3))
 def raw_ground(self,x,z):
  fade=1-self.smooth((max(abs(x),abs(z))-220)/80)
  return max(0,min(self.upper-.18,self.sample(x,z)))*fade if fade>0 else 0
 def forest_height(self,x,z):
  r=math.hypot(x,z);h=self.raw_ground(x,z)+.18
  return self.upper if r<=23 else self.upper+(h-self.upper)*self.smooth((r-23)/11) if r<34 else h
 def ground(self,x,z):
  h=self.raw_ground(x,z)
  # Existing roof terrace is interpreted as a level slab; carve ground below
  # its building, never count the DSM roof height twice as a building base.
  if self.inside(x,z,self.building):h=min(h,self.lower-6.22)
  if self.rail_z[0]<=z<=self.rail_z[-1]:
   p=self.at_z(self.rail_by_z,z,self.rail_z);d=abs(x-p[0]);w=1-self.smooth((d-1.7)/1.2)
   h-=max(0,h-(p[1]-.70))*w
  if self.slide_z[0]<=z<=self.slide_z[-1]:
   p=self.at_z(self.slide,z,self.slide_z);d=abs(x-(p[0]+.4));w=1-self.smooth((d-1.25)/1.2)
   h-=max(0,h-(p[1]-.20))*w
  return h
 def slide_delta(self,z):return self.at_z(self.slide,z,self.slide_z)[1]-self.at_z(self.oldslide,z,self.slide_z)[1]
 def rail_delta(self,z):return self.at_z(self.rail_by_z,z,self.rail_z)[1]-self.at_z(self.oldrail_by_z,z,self.rail_z)[1]
