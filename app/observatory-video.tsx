'use client';
import {useRef,useState} from 'react';
import {Play, X} from 'lucide-react';
const clips=[
  {label:'전망실에서 본 풍경',src:'/media/bitgaram-observatory-interior.mp4',poster:'/media/bitgaram-observatory-interior.png'},
  {label:'전망대 주변 항공 영상',src:'/media/bitgaram-observatory-aerial.mp4',poster:'/media/bitgaram-observatory-aerial.png'},
];
export default function ObservatoryVideo({onOpen}:{onOpen:()=>void}){
  const dialog=useRef<HTMLDialogElement>(null),video=useRef<HTMLVideoElement>(null);
  const [opened,setOpened]=useState(false),[index,setIndex]=useState(0),[error,setError]=useState(false);
  const close=()=>{video.current?.pause();dialog.current?.close();setOpened(false);};
  return <>
    <button className="observatory-video-launch" onClick={()=>{onOpen();setOpened(true);setError(false);dialog.current?.showModal();}}><Play size={18}/>실제 전망 영상 보기</button>
    <dialog ref={dialog} className="observatory-video-dialog" aria-labelledby="observatory-video-title" onCancel={close} onClose={()=>{video.current?.pause();setOpened(false);}}>
      <header><div><h2 id="observatory-video-title">영상으로 보는 빛가람 전망대</h2><p>제공해 주신 실제 촬영 영상입니다.</p></div><button autoFocus aria-label="영상 닫기" onClick={close}><X/></button></header>
      <nav aria-label="촬영 영상 선택">{clips.map((clip,i)=><button key={clip.src} aria-pressed={index===i} onClick={()=>{video.current?.pause();setIndex(i);setError(false);}}>{clip.label}</button>)}</nav>
      {opened&&<video key={clips[index].src} ref={video} controls playsInline preload="metadata" poster={clips[index].poster} src={clips[index].src} onError={()=>setError(true)} aria-label={clips[index].label}/>}
      {error&&<p role="alert">영상을 불러오지 못했습니다. <a href={clips[index].src} target="_blank" rel="noreferrer">원본 영상 열기</a></p>}
      <footer>원본 640 × 360 · 창밖에 합성하지 않은 실제 영상 · 닫은 뒤 산책을 이어갈 수 있어요.</footer>
    </dialog>
  </>;
}
