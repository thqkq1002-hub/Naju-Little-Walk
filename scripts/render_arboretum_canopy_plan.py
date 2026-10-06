"""Map of interpreted canopy changes against saved public reference imagery."""
import os,sys,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'work/terrain-analysis-libs'))
os.environ.setdefault('MPLCONFIGDIR',str(R/'work/terrain-analysis-mpl-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from PIL import Image,ImageDraw,ImageFont
import numpy as np
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
plt.rcParams.update({'font.family':font_manager.FontProperties(fname='C:/Windows/Fonts/malgun.ttf').get_name(),'axes.unicode_minus':False,'font.size':11})
central='--central-v88' in sys.argv
O=R/('outputs/quality-v88' if central else 'outputs/quality-v87');report=json.loads((R/'knowledge/sources/arboretum/canopy-v87.json').read_text(encoding='utf-8'))
geometry=json.loads((R/'knowledge/sources/arboretum/geometry.json').read_text(encoding='utf-8'))
campus=np.array(next(w['points'] for w in geometry['ways'] if w['id']=='1306096596'))
S=R/'knowledge/sources/arboretum/terrain-analysis-2026-10-03'
sat=json.loads((S/'regional-satellite.json').read_text(encoding='utf-8'));e=sat['response']['extent']
def local(mx,my):
 lon=mx/6378137*180/math.pi;lat=math.atan(math.sinh(my/6378137))*180/math.pi
 return ((lon-126.8256689)*111320*math.cos(math.radians(35.00648)),(lat-35.00648)*111320)
x0,y0=local(e['xmin'],e['ymin']);x1,y1=local(e['xmax'],e['ymax'])
fig,axes=plt.subplots(1,2,figsize=(15,9),layout='constrained',facecolor='#f5f4ee')
fig.suptitle('나주수목원 · 수관과 하층 식재 보강',fontsize=22,fontweight='bold',x=.04,ha='left',color='#234c3f')
axes[0].imshow(Image.open(S/'regional-satellite.jpg'),extent=[x0,x1,y0,y1],origin='upper')
axes[0].set_title('위성사진 · 부지와 길의 기존 윤곽',loc='left',pad=12)
axes[1].set_facecolor('#e8edde');axes[1].set_title('보강 위치 · 수종 배치는 해석',loc='left',pad=12)
for ax in axes:
 ax.plot(*np.vstack([campus,campus[0]]).T*np.array([[1],[-1]]),color='#fff1a7' if ax is axes[0] else '#819572',lw=2)
 for w in geometry['ways']:
  if w['tags'].get('highway'):
   points=np.array(w['points']);ax.plot(points[:,0],-points[:,1],color='white' if ax is axes[0] else '#b4ad98',lw=1.2,alpha=.7)
 ax.set_xlim(-535,205);ax.set_ylim(-265,320);ax.set_aspect('equal');ax.set_xlabel('동쪽 → (m)');ax.set_ylabel('북쪽 → (m)')
 ax.annotate('N',xy=(.94,.95),xytext=(.94,.82),xycoords='axes fraction',ha='center',fontweight='bold',color='#fff' if ax is axes[0] else '#234c3f',arrowprops={'arrowstyle':'-|>','color':'#fff' if ax is axes[0] else '#234c3f'})
for kind,color,label in [('mixed','#55784f','혼합 활엽수 수관 보강 712그루'),('plane','#409b9b','옆 길 플라타너스 표현 359그루 · 위치 추정'),('meta','#cc853c','중앙길 플라타너스 표현 120그루 · 사용자 지정' if central else '중앙 메타세쿼이아 수관 보강 120그루')]:
 points=np.array([v['position'] for v in report['changed_objects'].values() if v['lod']=='near' and v['kind']==kind]);axes[1].scatter(points[:,0],-points[:,1],s=23 if kind!='meta' else 30,c=color,alpha=.65,label=label,linewidths=0)
ground=np.array([v['position'] for v in report['groundcover']]);axes[1].scatter(ground[:,0],-ground[:,1],s=1,c='#376338',alpha=.6,label='맥문동 형태 하층 식재 3,010포기 · 배치 추정')
axes[1].legend(loc='upper left',bbox_to_anchor=(0,-.12),fontsize=10,frameon=False,ncol=1)
fig.text(.04,.025,'Esri World Imagery · 촬영일 미확인 | OSM contributors · ODbL | 개별 나무 위치·치수·수종은 실측 목록이 아닙니다.',fontsize=10,color='#4e6659')
fig.savefig(O/'canopy-plan-map.png',dpi=135);plt.close(fig)

# Comparison sheets keep the entire eye-level frame, identical cameras.
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',27)
for shot in ['avenue','forest','crowns']:
 if not all((O/(shot+'-'+label+'.png')).exists() for label in ['before','after']):continue
 before=Image.open(O/(shot+'-before.png')).convert('RGB');after=Image.open(O/(shot+'-after.png')).convert('RGB')
 sheet=Image.new('RGB',(before.width*2,before.height+66),'#f5f4ee');draw=ImageDraw.Draw(sheet)
 draw.text((25,15),'직전 v87' if central else '기존 v74',font=font,fill='#486052');draw.text((before.width+25,15),'중앙 플라타너스 v88' if central else '보강 v87',font=font,fill='#234c3f')
 sheet.paste(before,(0,66));sheet.paste(after,(before.width,66));sheet.save(O/(shot+'-comparison.jpg'),quality=92)
print('MAP AND COMPARISONS',flush=True)
before_path=O/'avenue-live-before.png';after_path=O/'avenue-app-after.png'
if before_path.exists() and after_path.exists():
 before=Image.open(before_path).convert('RGB');after=Image.open(after_path).convert('RGB')
 assert before.size==after.size,'Browser viewports must match for a comparison'
 sheet=Image.new('RGB',(before.width*2,before.height+66),'#f5f4ee');draw=ImageDraw.Draw(sheet)
 draw.text((25,15),'산책 화면 · 기존',font=font,fill='#486052');draw.text((before.width+25,15),'산책 화면 · 보강 후',font=font,fill='#234c3f')
 sheet.paste(before,(0,66));sheet.paste(after,(before.width,66));sheet.save(O/'app-comparison.jpg',quality=93)
