'use client';
import {useEffect} from 'react';
import {ArrowUpRight,Compass} from 'lucide-react';
import BitgaramOrbit from './bitgaram-orbit';
export default function BitgaramHub(){
  useEffect(()=>{document.title='나주 산책 — 빛가람 장소 선택';},[]);
  const places=[{id:'bitgaram-park',title:'호수공원 · 전망대',detail:'전망대 주변 산책과 내부 전망실',n:'01'},{id:'bitgaram-kepco',title:'한국전력 본사',detail:'입구 주변과 1층 로비',n:'02'},{id:'bitgaram-kentech',title:'KENTECH',detail:'완공 건물 입구와 1층 추정 초안',n:'03'}];
  return <main className="bitgaram-hub">
    <header><a href="/?place=geumseonggwan"><Compass size={26}/>나주 산책</a><span>빛가람 · 장소별 산책</span></header>
    <div className="hub-layout"><section className="hub-map" aria-label="빛가람 조감 안내 지도">
      <BitgaramOrbit/>
      <p className="hub-map-caption">드래그로 회전 · 휠/두 손가락으로 확대 · 푯말을 눌러 산책</p>
    </section><aside className="hub-places"><span className="hub-kicker">BITGARAM</span><h1>어디부터<br/>걸어볼까요?</h1><p>각 장소를 따로 불러와<br/>가까이에서 둘러봅니다.</p>
      {places.map(p=><a className="hub-place" key={p.id} href={`/?place=${p.id}`}><span>{p.n}</span><div><strong>{p.title}</strong><small>{p.detail}</small></div><ArrowUpRight size={20}/></a>)}
      <small className="hub-note">사진·영상 기반 제작 초안입니다. 건물 높이와 내부 치수·배치에는 추정이 포함됩니다.</small>
    </aside></div>
    <footer><a href="https://www.openstreetmap.org/copyright">© OpenStreetMap 기여자 · ODbL</a><a href="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer">Esri 위성사진 참고</a><span>일부 건물 윤곽·높이·식재 추정 · 주변 건물은 전경용</span></footer>
  </main>;
}
