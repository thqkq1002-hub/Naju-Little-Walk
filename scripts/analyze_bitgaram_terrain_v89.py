"""Clip native GLO-30 surface samples; no invented survey precision.

PIL reads this floating-point GeoTIFF with PixelIsPoint georeferencing. Retain
native samples, not a 4 m interpolation masquerading as a 4 m measurement.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,math
import numpy as np
from PIL import Image

R=Path(__file__).resolve().parents[1]
T=R/'work/bitgaram-terrain-v89/Copernicus_DSM_COG_10_N35_00_E126_00_DEM.tif'
O=R/'knowledge/sources/bitgaram/terrain-v89';O.mkdir(parents=True,exist_ok=True)
origin=json.loads((R/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf8'))['origin']
im=Image.open(T);a=np.asarray(im);dx,dy,_=im.tag_v2[33550];_,_,_,lon,lat,_=im.tag_v2[33922]
keys=im.tag_v2[34735];geo={keys[i]:keys[i+3] for i in range(4,len(keys),4)}
assert geo[1025]==2 and geo[2048]==4326, 'Requires WGS84 PixelIsPoint raster'
mx=111320*math.cos(math.radians(origin['lat']));mz=111320
def uv(x,z):return ((origin['lon']+x/mx-lon)/dx,(lat-origin['lat']+z/mz)/dy)
u0,v0=uv(-360,-360);u1,v1=uv(360,360)
left,top=math.floor(u0)-1,math.floor(v0)-1
right,bottom=math.ceil(u1)+1,math.ceil(v1)+1
crop=a[top:bottom+1,left:right+1]
grid=dict(dataset='Copernicus DEM GLO-30 Public, AWS 2021 release',nativeResolutionMetres=30,
 originWGS84=origin,coordinateConvention='x east / z south, existing OSM equirectangular metres',
 sampleOriginLongitude=lon+left*dx,sampleOriginLatitude=lat-top*dy,
 longitudeSpacingDegrees=dx,latitudeSpacingDegrees=dy,pixelIsPoint=True,
 heightsMetres=crop.tolist(),width=crop.shape[1],height=crop.shape[0],
 verticalReference='EGM2008 orthometric metres, dataset reference; no local benchmark survey',
 sourceUrl='https://copernicus-dem-30m.s3.amazonaws.com/'+T.stem+'/'+T.name,
 sourceSha256=hashlib.sha256(T.read_bytes()).hexdigest(),retrievedAtUTC=datetime.now(timezone.utc).isoformat(),
 modelDatumMetres=25.5,modelDatumBasis='Median DSM sample of existing OSM lake boundary. Local display reference, not a water-level survey.',
 measurement='DSM: includes vegetation/buildings; not a surveyed bare-earth DEM',
 attribution='Contains modified Copernicus Service information 2021. Produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.',
 limitations=['Native grid about 25 m east-west / 31 m north-south here; 30 m nominal. Smaller structures and steps unresolved.',
 'Observations mainly 2010-2015; edited 2021 release does not guarantee present grading or station surfaces.',
 'Public NEINS 2022 NGII 5 m analysis returned elevation class 50-100 m, not numeric ground heights. It is only a cross-check.',
 'Platform levelling, building cut/fill, rail clearances and slide profiles are modelling interpretations. Obtain current NGII contours/DEM or as-built survey to replace them.'])
(O/'native-surface-grid.json').write_text(json.dumps(grid,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sample(x,z):
 u,v=uv(x,z);i,j=math.floor(u),math.floor(v);p,q=u-i,v-j
 return float((a[j,i]*(1-p)+a[j,i+1]*p)*(1-q)+(a[j+1,i]*(1-p)+a[j+1,i+1]*p)*q)
pts=[('summit',0,0),('upper-platform-location',12,16),('lower-platform-location',16,108),('forest-start',70.547,170.13)]
report=dict(samples=[dict(label=n,x=x,z=z,elevationMetres=sample(x,z)) for n,x,z in pts],
 adoptedUpperSurfaceMetres=sample(0,0),adoptedLowerSurfaceMetres=sample(16,108),
 interpretedPlatformDifferenceMetres=sample(0,0)-sample(16,108),previousPlatformDifferenceMetres=9.78,
 officialCrossCheck={'url':'https://webgis.neins.go.kr/map.do','dataset':'2022 NGII 5 m classified elevation','summitClass':'50-100 m'},
 officialSummitDescription={'url':'https://korean.visitkorea.or.kr/detail/rem_detail.do?con_type=11300&cotid=9bcea016-ebf7-4cec-ae02-4d67ce2d49fe','describedHillMetres':80},
 userDecision='30m 자료로 우선 보강하고 정밀도 한계 기록')
(O/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=False),flush=True)
