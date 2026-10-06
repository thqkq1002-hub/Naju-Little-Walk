"""One-page review: same aerial camera, walking view, and height profiles."""
from pathlib import Path
import json,sys,math,os
R=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(R/'work/matplotlib-cache'))
sys.path.insert(0,str(R/'work/terrain-analysis-libs'))
sys.path.insert(0,str(R/'scripts'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image
from bitgaram_terrain_v89 import Terrain
font=FontProperties(fname='C:/Windows/Fonts/malgun.ttf')
plt.rcParams['font.family']=font.get_name();plt.rcParams['axes.unicode_minus']=False
old=json.loads((R/'outputs/terrain-v89/world-before.json').read_text(encoding='utf8'))
T=Terrain(next(s['footprint'] for s in old['solids'] if s['name']=='photo_exhibition_shell'))
oldrail=[(x,y-.95,z) for x,y,z in reversed(T.old['rail_route'])]
distance=[0]
for a,b in zip(oldrail,oldrail[1:]):distance.append(distance[-1]+math.hypot(a[0]-b[0],a[2]-b[2]))
fig=plt.figure(figsize=(16,10),facecolor='#f6f4eb')
gs=fig.add_gridspec(2,2,left=.03,right=.98,top=.87,bottom=.10,hspace=.28,wspace=.10,height_ratios=[1,.88])
for grid,path,title in [(gs[0,0],'aerial-before.png','기존 모델 · 바닥 높이 차이 9.8m'),
                        (gs[0,1],'aerial-after.png','표고 보강 · 바닥 높이 차이 약 34.4m'),
                        (gs[1,0],'walk-after.png','상부에서 내려다본 보강 지형')]:
 ax=fig.add_subplot(grid);ax.imshow(Image.open(R/'outputs/terrain-v89'/path));ax.set_axis_off();ax.set_title(title,fontsize=14,loc='left',pad=10,color='#25483d')
ax=fig.add_subplot(gs[1,1]);ax.set_facecolor('#fffdf6')
ax.plot(distance,[y+.35-6.22 for _,y,_ in oldrail],color='#b2aa97',lw=2,label='기존 객실 바닥')
ax.plot(distance,[T.sample(x,z)+T.datum-T.analysis['adoptedLowerSurfaceMetres'] for x,_,z in T.rail],color='#799d77',lw=1.5,ls='--',label='30m DSM 보간 표면')
ax.plot(distance,[y+.35-T.lower for _,y,_ in T.rail],color='#235843',lw=2.5,label='적용한 객실 바닥')
ax.set_title('같은 평면 경로에서의 높이 비교',fontsize=14,loc='left',pad=10,color='#25483d')
ax.set_xlabel('하부 → 상부 평면 이동 거리 (m)',fontsize=11)
ax.set_ylabel('각 하부 바닥 기준 상대 높이 (m)',fontsize=11)
ax.grid(alpha=.15);ax.legend(frameon=False,fontsize=10,loc='upper left');ax.spines[['top','right']].set_visible(False)
fig.text(.03,.96,'빛가람 전망대 접근 지형 보강',fontsize=22,color='#25483d',weight='bold')
fig.text(.03,.913,'같은 항공 카메라로 비교 · 지형, 숲길, 계단, 모노레일, 식재, NPC 높이 동기화',fontsize=13,color='#55654f')
fig.text(.03,.053,'공개 GLO-30 DSM 적용: 나무·건물을 포함하는 30m 표면 자료. 승강장·궤도 종단은 모델 해석이며 현장 측량값이 아닙니다.',fontsize=11,color='#5b6357')
fig.text(.03,.023,'Blender 검토 화면 · 원관측 주로 2010–2015년 / 2021 배포본 · Copernicus / DLR / Airbus / EU / ESA · 평면 자료 © OpenStreetMap 기여자, ODbL',fontsize=9,color='#747a71')
path=R/'outputs/terrain-v89/terrain-comparison.png';fig.savefig(path,dpi=120);plt.close(fig)
print(path)
