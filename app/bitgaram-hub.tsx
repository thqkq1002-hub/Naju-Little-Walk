'use client';
import {useEffect,useState} from 'react';
import {ArrowUpRight,Compass,CircleHelp,Map} from 'lucide-react';
import BitgaramOrbit from './bitgaram-orbit';
import { FullscreenButton, useScreenMode } from './screen-mode';
import WalkGuide from './walk-guide';
import MapTravel from './map-travel';
export default function BitgaramHub(){
  const [guideOpen,setGuideOpen]=useState(false),[mapOpen,setMapOpen]=useState(false);
  const { touch, portrait }=useScreenMode();
  useEffect(()=>{document.title='나주 산책 — 빛가람 장소 선택';},[]);
  useEffect(()=>{if(portrait){setGuideOpen(false);setMapOpen(false);}},[portrait]);
  const places=[{id:'bitgaram-park',title:'호수공원 · 전망대',detail:'숲길과 전망대 주변',n:'01'},{id:'bitgaram-kepco',title:'한국전력 본사',detail:'앞마당과 1층 로비',n:'02'},{id:'bitgaram-kentech',title:'KENTECH',detail:'캠퍼스와 강의동 1층',n:'03'}];
  return <main className="bitgaram-hub">
    <header><a href="/?place=geumseonggwan"><Compass size={25} strokeWidth={1.5}/>나주 산책<span className="hub-header-place">빛가람동</span></a><div className="topbar-tools"><button className="hub-all-places" onClick={()=>setMapOpen(true)}><Map size={18}/>장소 선택</button><button className="screen-button" onClick={()=>setGuideOpen(true)} aria-label="산책 안내와 화면 설정"><CircleHelp size={19}/></button><FullscreenButton/></div></header>
    <div className="hub-layout"><section className="hub-map" aria-label="빛가람 조감 안내 지도">
      <BitgaramOrbit/>
      <p className="hub-map-caption">{touch?'드래그로 회전 · 두 손가락으로 확대':'드래그로 회전 · 휠로 확대'}<span>푯말을 누르면 산책이 시작됩니다</span></p>
    </section><aside className="hub-places"><span className="hub-kicker">나주 혁신도시</span><h1>빛가람동</h1><p>호수공원과 두 캠퍼스를 둘러보세요.</p><span className="hub-list-label">산책할 곳</span>
      {places.map(p=><a className="hub-place" key={p.id} href={`/?place=${p.id}`}><span>{p.n}</span><div><strong>{p.title}</strong><small>{p.detail}</small></div><ArrowUpRight size={20}/></a>)}
      <a className="hub-interior-link" href="/?place=bitgaram-observatory">전망실에서 도시 바라보기<ArrowUpRight size={16}/></a>
      <small className="hub-note">지도와 사진을 참고해 만든 산책 모형입니다.<button onClick={()=>setGuideOpen(true)}>제작 자료 확인</button></small>
    </aside></div>
    <footer><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap 기여자 · ODbL</a><a href="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer" target="_blank" rel="noreferrer">Esri 위성사진 참고</a><button onClick={()=>setGuideOpen(true)}>자료·제작 정보</button></footer>
    {guideOpen&&<WalkGuide destinationId="bitgaram" onClose={()=>setGuideOpen(false)}/>}
    {mapOpen&&<MapTravel destinationId="bitgaram" world={null} position={[0,0]} onClose={()=>setMapOpen(false)} onTravel={()=>false}/>}
  </main>;
}
