'use client';

import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import { MapPin, X, ArrowUpRight, Footprints } from 'lucide-react';
import { destinations, type DestinationId } from '@/lib/destinations';
import { canTravelTo, mapArrival, mapColor, mapSolids, regionalPoint, regionalSize } from '@/lib/map-navigation';
import { solidCollider, type Point, type World } from '@/lib/world';

type Region = { paths: { id: number; kind: string; name: string; points: Point[] }[]; labels: { name: string; point: Point }[] };
type Props = { destinationId: DestinationId; world: World | null; position: Point; onClose: () => void; onTravel: (point: Point,height?:number) => boolean };
const mapLabels: Partial<Record<DestinationId,string>> = {neureoji:'느러지 전망대', deudeulgang:'드들강', 'naju-arboretum':'나주수목원', bitgaram:'빛가람동', yeongsanpo:'영산포', dasi:'다시초', bogam:'복암리 고분군', 'bogam-museum':'고분전시관'};

export default function MapTravel({destinationId,world,position,onClose,onTravel}: Props) {
  const dialog=useRef<HTMLDialogElement>(null);
  const [tab,setTab]=useState<'region'|'local'>('region');
  const [region,setRegion]=useState<Region|null>(null);
  const [mapError,setMapError]=useState('');
  const [notice,setNotice]=useState('');
  const arrivals=useMemo(()=>world?world.places.map(p=>({place:p,point:mapArrival(p,world)})).filter(p=>p.point):[],[world]);
  useEffect(()=>{
    const d=dialog.current!;d.showModal();
    const controller=new AbortController();
    fetch('/naju-region-map.json',{signal:controller.signal}).then(r=>{if(!r.ok)throw Error();return r.json() as Promise<Region>;}).then(setRegion).catch(e=>{if(e.name!=='AbortError')setMapError('배경 지도를 불러오지 못했어요. 장소 버튼으로 이동할 수 있어요.');});
    return ()=>{controller.abort();d.close();};
  },[]);
  const travel=(point: Point,height=0)=>{
    if(world && canTravelTo(point,world,height)) {
      // Release the native modal focus trap before focusing the walking canvas.
      dialog.current?.close();
      if(onTravel(point,height)){onClose();return;}
      dialog.current?.showModal();
    }
    setNotice('건물이나 봉분 위에는 이동할 수 없어요. 열린 길을 골라주세요.');
  };
  const span=world?[world.bounds[1]-world.bounds[0],world.bounds[3]-world.bounds[2]]:[1,1];
  return <dialog ref={dialog} className="travel-dialog" aria-labelledby="travel-title" onCancel={e=>{e.preventDefault();onClose();}} onClick={e=>{if(e.target===e.currentTarget)onClose();}}>
    <div className="travel-shell">
      <header className="travel-header"><div><span className="travel-eyebrow">나주 산책</span><h2 id="travel-title">장소 선택</h2></div><button className="map-close" onClick={onClose} aria-label="지도 닫기"><X size={22}/></button></header>
      <div className="travel-tabs" role="tablist" aria-label="지도 범위" onKeyDown={e=>{if(!world||!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const next=e.key==='Home'?'region':e.key==='End'?'local':tab==='region'?'local':'region';setTab(next);setNotice('');document.getElementById(`${next}-tab`)?.focus();}}>
        <button role="tab" id="region-tab" aria-controls="region-panel" aria-selected={tab==='region'} tabIndex={tab==='region'?0:-1} onClick={()=>{setTab('region');setNotice('');}}>나주 전체</button>
        <button role="tab" id="local-tab" aria-controls="local-panel" aria-selected={tab==='local'} tabIndex={tab==='local'?0:-1} onClick={()=>{setTab('local');setNotice('');}} disabled={!world}>현재 장소 안에서</button>
      </div>
      {tab==='region'?<div id="region-panel" role="tabpanel" aria-labelledby="region-tab" className="travel-content">
        <div className="travel-map regional-map" style={{aspectRatio:`${regionalSize[0]} / ${regionalSize[1]}`, '--map-ratio':regionalSize[0]/regionalSize[1]} as CSSProperties}>
          <svg viewBox={`0 0 ${regionalSize[0]} ${regionalSize[1]}`} aria-label="나주 산책 장소와 영산포의 실제 위치 지도" role="img">
            <rect width={regionalSize[0]} height={regionalSize[1]} fill="#e7ebdd"/>
            <defs><pattern id="map-grid" width="50" height="50" patternUnits="userSpaceOnUse"><path d="M 50 0 H 0 V 50" fill="none" stroke="#566e5310" strokeWidth="1"/></pattern></defs>
            <rect width={regionalSize[0]} height={regionalSize[1]} fill="url(#map-grid)"/>
            {region?.paths.filter(p=>p.kind==='water').map(p=><polygon key={p.id} points={p.points.map(p=>regionalPoint(...p).join(',')).join(' ')} fill="#a9cdd0"/>)}
            {region?.paths.filter(p=>p.kind==='river').map(p=><polyline key={p.id} points={p.points.map(p=>regionalPoint(...p).join(',')).join(' ')} fill="none" stroke="#a9cdd0" strokeWidth="19" strokeLinejoin="round" strokeLinecap="round"/>)}
            {region?.paths.filter(p=>!['river','rail','water'].includes(p.kind)).map(p=><polyline key={p.id} points={p.points.map(p=>regionalPoint(...p).join(',')).join(' ')} fill="none" stroke="#fffdf5" strokeWidth={p.kind==='trunk'?9:p.kind==='primary'?7:4} strokeLinejoin="round" strokeLinecap="round"/>)}
            {region?.paths.filter(p=>p.kind==='rail').map(p=><polyline key={p.id} points={p.points.map(p=>regionalPoint(...p).join(',')).join(' ')} fill="none" stroke="#9da595" strokeWidth="2" strokeDasharray="4 4"/>)}
            {region?.labels.map((l,i)=>{const p=regionalPoint(...l.point);return <text key={i} x={p[0]} y={p[1]} className="map-village" textAnchor="middle">{l.name}</text>;})}
            <text x="28" y="38" className="map-north">N ↑</text>
          </svg>
          {(Object.entries(destinations) as [DestinationId,typeof destinations[DestinationId]][]).filter(([,d])=>!('parent' in d)).map(([id,d])=>{const p=regionalPoint(d.coordinates.lon,d.coordinates.lat);return <a className={`region-pin ${id===destinationId?'is-current':''} ${id==='bogam-museum'?'museum-pin':''} ${p[0]<140?'pin-left':p[0]>860?'pin-right':''}`} key={id} href={`/?place=${id}`} aria-label={d.name} aria-current={id===destinationId?'location':undefined} style={{left:`${p[0]/10}%`,top:`${p[1]/regionalSize[1]*100}%`}}><span><MapPin size={22}/></span><strong>{mapLabels[id]??d.name}</strong>{id===destinationId&&<small>현재 장소</small>}</a>;})}
        </div>
        <aside className="travel-list"><p>장소를 선택하면 산책 화면으로 이동합니다.</p>{(Object.entries(destinations) as [DestinationId,typeof destinations[DestinationId]][]).map(([id,d],i)=><a key={id} href={`/?place=${id}`} className={id===destinationId?'selected-place':''} aria-current={id===destinationId?'location':undefined}><span className="travel-index">{String(i+1).padStart(2,'0')}</span><div><strong>{d.name}</strong>{id===destinationId&&<small>현재 장소</small>}</div><ArrowUpRight size={19}/></a>)}{mapError&&<p role="status">{mapError}</p>}<span className="travel-attribution">© OpenStreetMap 기여자 · ODbL 1.0<br/>주요 도로·하천을 표시한 간략 지도</span></aside>
      </div>:world&&<div id="local-panel" role="tabpanel" aria-labelledby="local-tab" className="travel-content">
        <div className="travel-map local-travel-map" style={{aspectRatio:`${span[0]} / ${span[1]}`, '--map-ratio':span[0]/span[1]} as CSSProperties}>
          <svg viewBox={`${world.bounds[0]} ${world.bounds[2]} ${span[0]} ${span[1]}`} role="img" aria-label="열린 길을 누르거나 옆의 장소 목록을 선택해 이동" onClick={e=>{const svg=e.currentTarget,matrix=svg.getScreenCTM();if(!matrix)return;const point=svg.createSVGPoint();point.x=e.clientX;point.y=e.clientY;const local=point.matrixTransform(matrix.inverse());travel([local.x,local.y]);}}>
            <rect x={world.bounds[0]} y={world.bounds[2]} width={span[0]} height={span[1]} fill="#e2e8d8"/>
            {mapSolids(world).map((s,i)=><polygon key={i} points={solidCollider(s).map(p=>p.join(',')).join(' ')} fill={mapColor(s.name)} stroke="#9da992" strokeWidth=".35"/>)}
            <circle cx={position[0]} cy={position[1]} r={span[0]*.008} fill="#cc6c3a" stroke="#fff" strokeWidth={span[0]*.003}/>
          </svg>
          {arrivals.map(({place,point},i)=><button key={place.id} className="local-pin" style={{left:`${(point![0]-world.bounds[0])/span[0]*100}%`,top:`${(point![1]-world.bounds[2])/span[1]*100}%`}} onClick={()=>travel(point!,place.arrivalHeight)} aria-label={`${place.name}로 이동`} title={place.name}>{i+1}</button>)}
          <span className="local-north">장소 지도</span>
        </div>
        <aside className="travel-list"><p>열린 길이나 번호를 누르면 이동합니다. 다른 층은 목록에서 선택하세요.</p>{arrivals.map(({place,point},i)=><button key={place.id} onClick={()=>travel(point!,place.arrivalHeight)}><span className="travel-index">{i+1}</span><div><strong>{place.name}</strong><small>{place.mapLabel ?? (place.arrivalHeight?(place.arrivalHeight<0?'강변 아래 데크':'상부 관람 공간'):place.indoor?'실내':'산책 지점')}</small></div><Footprints size={17}/></button>)}{notice&&<p className="map-notice" role="status">{notice}</p>}</aside>
      </div>}
    </div>
  </dialog>;
}
