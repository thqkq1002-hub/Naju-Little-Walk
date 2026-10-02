'use client';

import { useEffect, useRef } from 'react';
import { X, Footprints, MousePointer2, Hand, Map, Image, Settings2 } from 'lucide-react';
import { destinations, type DestinationId } from '@/lib/destinations';
import { useScreenMode } from './screen-mode';

export default function WalkGuide({ destinationId, onClose }: { destinationId: DestinationId; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const { touch, touchControls, quality, setQuality, setTouchControls, portrait } = useScreenMode();
  const destination = destinations[destinationId];
  useEffect(() => {
    const element = dialog.current!; element.showModal();
    window.dispatchEvent(new Event('naju:pause'));
    return () => element.close();
  }, []);
  useEffect(() => { if (portrait) onClose(); }, [portrait, onClose]);
  return <dialog ref={dialog} className="guide-dialog" aria-labelledby="guide-title" onCancel={e => { e.preventDefault(); onClose(); }} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
    <header><div><span className="dialog-eyebrow">나주 산책 안내</span><h2 id="guide-title">{destination.name}</h2></div><button className="map-close" aria-label="안내 닫기" onClick={onClose}><X size={20}/></button></header>
    <div className="guide-content">
      <section><h3><Footprints size={18}/>산책 방법</h3><dl className="control-list">
        <div><dt>{touch ? <Hand size={17}/> : <MousePointer2 size={17}/>}둘러보기</dt><dd>{touch ? '화면을 한 손가락으로 드래그' : '마우스 버튼을 누른 채 화면을 드래그'}</dd></div>
        <div><dt><Footprints size={17}/>걷기</dt><dd>{touch ? '왼쪽 방향 버튼을 누른 채 이동 · 오른쪽에서 시선 회전' : 'W A S D로 이동 · ← →로 회전 · Shift로 빠르게'}</dd></div>
        <div><dt><Map size={17}/>전체 보기</dt><dd>{touch ? '한 손가락으로 회전 · 두 손가락으로 확대·축소' : '드래그로 회전 · 마우스 휠로 확대·축소'}</dd></div>
      </dl><label className="touch-preference"><input type="checkbox" checked={touchControls} onChange={e=>setTouchControls(e.target.checked)}/>화면에 이동 버튼 표시</label><p className="guide-tip">지도의 장소 목록에서 원하는 곳으로 바로 이동할 수 있습니다. 실내에서는 출구로 걸어가거나 지도에서 다른 장소를 선택하세요.</p></section>
      <section><h3><Settings2 size={18}/>화면 품질</h3><div className="quality-options" role="group" aria-label="화면 품질">
        <button aria-pressed={quality === 'balanced'} onClick={() => setQuality('balanced')}><strong>편하게 걷기</strong><span>태블릿 권장 · 화면 부담 줄이기</span></button>
        <button aria-pressed={quality === 'detail'} onClick={() => setQuality('detail')}><strong>선명하게 보기</strong><span>높은 해상도로 풍경 감상</span></button>
      </div></section>
      <section className="reference-info"><h3><Image size={18}/>제작 자료</h3><p>{destination.limitation}</p><a href={destination.sourceUrl} target="_blank" rel="noreferrer">{destination.sourceLabel} ↗</a><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap 기여자 · ODbL ↗</a><a href="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer" target="_blank" rel="noreferrer">Esri / Vantor 위성·항공사진 참고{destinationId==='dasi'?' · 2022년':['bogam','bogam-museum'].includes(destinationId)?' · 2023년':''} ↗</a><p>실제 지도와 공개 사진을 바탕으로 제작한 산책 모형입니다. 현장의 현재 모습과 차이가 있을 수 있습니다.</p></section>
    </div>
  </dialog>;
}
