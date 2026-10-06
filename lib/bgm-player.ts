import {bgmUrl,type BgmTrackId} from './bgm.ts';

/** One looping track per page. Browsers only allow sound after the visitor taps or presses a key. */
export type BgmState={enabled:boolean;playing:boolean;ducked:boolean;track:BgmTrackId|null};

const STORAGE_KEY='naju-bgm';
const VOLUME=.28,DUCKED=.07;

let state:BgmState={enabled:readEnabled(),playing:false,ducked:false,track:null};
const listeners=new Set<()=>void>();
let audio:HTMLAudioElement|null=null,context:AudioContext|null=null,gain:GainNode|null=null;
let unlocked=false,pauseTimer:ReturnType<typeof setTimeout>|undefined;

function readEnabled(){
  try{return typeof localStorage==='undefined'||localStorage.getItem(STORAGE_KEY)!=='off';}catch{return true;}
}
function emit(next:Partial<BgmState>){state={...state,...next};listeners.forEach(listener=>listener());}
export const bgmState=()=>state;
export function subscribeBgm(listener:()=>void){listeners.add(listener);return ()=>{listeners.delete(listener);};}

const target=()=>!state.enabled?0:state.ducked?DUCKED:VOLUME;
/** Web Audio gain, because iPadOS ignores media element volume; fall back to it elsewhere. */
function ramp(value:number,seconds:number){
  if(gain&&context){
    const now=context.currentTime;
    gain.gain.cancelScheduledValues(now);gain.gain.setValueAtTime(gain.gain.value,now);gain.gain.linearRampToValueAtTime(value,now+seconds);
  }else if(audio)audio.volume=value;
}

function ensureAudio(track:BgmTrackId){
  if(audio)return audio;
  audio=new Audio(bgmUrl(track));audio.loop=true;audio.preload='auto';
  audio.addEventListener('playing',()=>emit({playing:true}));
  audio.addEventListener('pause',()=>emit({playing:false}));
  const Context=window.AudioContext??(window as unknown as {webkitAudioContext?:typeof AudioContext}).webkitAudioContext;
  if(Context){
    try{
      context=new Context();gain=context.createGain();gain.gain.value=0;
      context.createMediaElementSource(audio).connect(gain).connect(context.destination);
    }catch{context=null;gain=null;}
  }
  if(!gain)audio.volume=0;
  document.addEventListener('visibilitychange',()=>{
    if(!audio||!unlocked)return;
    if(document.hidden)audio.pause();else if(state.enabled)start();
  });
  return audio;
}

function start(){
  if(!state.track)return;
  clearTimeout(pauseTimer);
  const element=ensureAudio(state.track);
  void context?.resume();
  if(element.paused)ramp(0,0);
  element.play().then(()=>ramp(target(),2.5)).catch(()=>{});
}

/** Choose this scene's loop; it stays silent until the first tap, click or key. */
export function setBgmTrack(track:BgmTrackId){
  if(state.track===track)return;
  emit({track});
  if(!audio)return;
  audio.src=bgmUrl(track);
  if(unlocked&&state.enabled)start();
}

/** Call from a user gesture. */
export function unlockBgm(){
  if(unlocked||!state.track)return;
  unlocked=true;
  if(state.enabled&&!document.hidden)start();
}

export function setBgmEnabled(enabled:boolean){
  try{localStorage.setItem(STORAGE_KEY,enabled?'on':'off');}catch{/* private mode keeps the choice for this page */}
  emit({enabled});
  if(enabled){unlocked=true;start();return;}
  if(!audio)return;
  ramp(0,.6);
  const element=audio;
  pauseTimer=setTimeout(()=>{if(!state.enabled)element.pause();},650);
}

/** Lower the music under a guide's voice and bring it back afterwards. */
export function duckBgm(on:boolean){
  if(state.ducked===on)return;
  emit({ducked:on});
  if(audio&&!audio.paused)ramp(target(),on?.4:1.2);
}
