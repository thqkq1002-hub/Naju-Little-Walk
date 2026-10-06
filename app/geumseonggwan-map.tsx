'use client';

import {useEffect,useMemo,useRef,useState,type CSSProperties} from 'react';
import {X,Footprints} from 'lucide-react';
import type {DestinationId} from '@/lib/destinations';
import {canTravelTo,mapArrival,mapColor,mapSolids} from '@/lib/map-navigation';
import {solidCollider,type Point,type World} from '@/lib/world';

type Props={destinationId:DestinationId;world:World|null;position:Point;onClose:()=>void;onTravel:(point:Point,height?:number)=>boolean};
type PrecinctWorld=World&{buildings?:{osm_id:string;footprint:Point[]}[];walkRoute?:Point[]};
export function PrecinctMapShapes({world}:{world:World}){
  const order=(name:string)=>name==='ground_floor_precinct_v76'?0:name.startsWith('ground_floor')?1:2;
  const gates=['832423356','832423357'].flatMap(id=>{const p=world.places.find(p=>p.id===id);return p?[p.position]:[];});
  const path=[...gates,...((world as PrecinctWorld).walkRoute??[])];
  return <>
    {[...mapSolids(world)].sort((a,b)=>order(a.name)-order(b.name)).map((s,i)=><polygon key={i} points={solidCollider(s).map(p=>p.join(',')).join(' ')} fill={s.name.startsWith('ground_floor')&&!s.name.includes('lawn')?'#e2d8c2':mapColor(s.name)} stroke="#aaa68e" strokeWidth=".3"/>)}
    <polyline points={path.map(p=>p.join(',')).join(' ')} fill="none" stroke="#f8f5e9" strokeWidth="4.5"/>
    {(world as PrecinctWorld).buildings?.map(b=><polygon key={b.osm_id} points={b.footprint.map(p=>p.join(',')).join(' ')} fill="#577064" stroke="#314c42" strokeWidth=".7"/>)}
  </>;
}
export default function GeumseonggwanMap({world,position,onClose,onTravel}:Props){
  const dialog=useRef<HTMLDialogElement>(null);
  const [notice,setNotice]=useState('');
  const arrivals=useMemo(()=>world?world.places.map(place=>({place,point:mapArrival(place,world)})).filter(p=>p.point):[],[world]);
  useEffect(()=>{const d=dialog.current!;d.showModal();return()=>d.close();},[]);
  const travel=(point:Point,height=0)=>{
    if(world&&canTravelTo(point,world,height)){
      dialog.current?.close();
      if(onTravel(point,height)){onClose();return;}
      dialog.current?.showModal();
    }
    setNotice('담장과 건물은 통과할 수 없습니다. 마당이나 박석길을 선택해 주세요.');
  };
  const span=world?[world.bounds[1]-world.bounds[0],world.bounds[3]-world.bounds[2]]:[1,1];
  return <dialog ref={dialog} className="travel-dialog" aria-labelledby="geum-map-title" onCancel={e=>{e.preventDefault();onClose();}} onClick={e=>{if(e.target===e.currentTarget)onClose();}}>
    <div className="travel-shell">
      <header className="travel-header"><div><span className="travel-eyebrow">금성관 산책</span><h2 id="geum-map-title">경내 안내도</h2></div><button className="map-close" onClick={onClose} aria-label="경내 지도 닫기"><X size={22}/></button></header>
      {world?<div className="travel-content">
        <div className="travel-map local-travel-map" style={{aspectRatio:`${span[0]} / ${span[1]}`,'--map-ratio':span[0]/span[1]} as CSSProperties}>
          <svg viewBox={`${world.bounds[0]} ${world.bounds[2]} ${span[0]} ${span[1]}`} role="img" aria-label="금성관 정청과 문루, 박석길의 위치. 마당을 누르면 이동합니다." onClick={e=>{const svg=e.currentTarget,matrix=svg.getScreenCTM();if(!matrix)return;const p=svg.createSVGPoint();p.x=e.clientX;p.y=e.clientY;const local=p.matrixTransform(matrix.inverse());travel([local.x,local.y]);}}>
            <rect x={world.bounds[0]} y={world.bounds[2]} width={span[0]} height={span[1]} fill="#f1eee3"/>
            <PrecinctMapShapes world={world}/>
            <circle cx={position[0]} cy={position[1]} r={span[0]*.009} fill="#c65f36" stroke="#fff" strokeWidth={span[0]*.003}/>
          </svg>
          {arrivals.map(({place,point},i)=><button key={place.id} className="local-pin" style={{left:`${(point![0]-world.bounds[0])/span[0]*100}%`,top:`${(point![1]-world.bounds[2])/span[1]*100}%`}} onClick={()=>travel(point!,place.arrivalHeight)} aria-label={`${place.name}로 이동`} title={place.name}>{i+1}</button>)}
          <span className="local-north">N ↑</span>
        </div>
        <aside className="travel-list"><p>번호를 선택하거나 마당을 눌러 이동하세요.</p>
          {arrivals.map(({place,point},i)=><button key={place.id} onClick={()=>travel(point!,place.arrivalHeight)}><span className="travel-index">{i+1}</span><div><strong>{place.name}</strong><small>{place.indoor?'정청 마루':'경내 산책 지점'}</small></div><Footprints size={17}/></button>)}
          {notice&&<p className="map-notice" role="status">{notice}</p>}
          <span className="travel-attribution">© OpenStreetMap 기여자 · ODbL 1.0<br/>지도 경계와 사진을 참고한 경내 모형</span>
        </aside>
      </div>:<p role="status">경내 지도를 준비하고 있습니다.</p>}
    </div>
  </dialog>;
}
