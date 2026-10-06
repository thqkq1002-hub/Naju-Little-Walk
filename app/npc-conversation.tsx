'use client';

import {useEffect, useRef, useState} from 'react';
import {X, Send, Volume2, VolumeX} from 'lucide-react';
import {guideReply} from '@/lib/npc-dialogue';
import type {GuideGesture} from '@/lib/npc-animation';
import type {DestinationId} from '@/lib/destinations';
import './npc-conversation.css';

export default function NpcConversation({name,destinationId,onGesture,onClose}:{name:string;destinationId:DestinationId;onGesture:(gesture:GuideGesture)=>void;onClose:()=>void}) {
  const [input,setInput]=useState('');
  const [reply,setReply]=useState(`안녕하세요! 저는 ${name}예요. 인사하거나 이곳의 안내를 부탁해 보세요.`);
  const [sound,setSound]=useState(true);
  const [speaking,setSpeaking]=useState(false);
  const [voiceNotice,setVoiceNotice]=useState('');
  const ticket=useRef(0);
  const timer=useRef<ReturnType<typeof setTimeout>|null>(null);
  const inputRef=useRef<HTMLInputElement>(null);
  const stop=()=>{
    ticket.current++;
    if(timer.current)clearTimeout(timer.current);
    timer.current=null;
    if('speechSynthesis' in window)window.speechSynthesis.cancel();
    setSpeaking(false);
  };
  useEffect(()=>{
    // Focus without opening the Android soft keyboard over the scenery.
    if('speechSynthesis' in window)window.speechSynthesis.getVoices();
    return ()=>{ticket.current++;if(timer.current)clearTimeout(timer.current);if('speechSynthesis' in window)window.speechSynthesis.cancel();};
  },[]);
  const send=(text:string)=>{
    if(!text.trim())return;
    stop();setVoiceNotice('');setInput('');
    const answer=guideReply(text,destinationId,name);
    setReply(answer.text);onGesture(answer.gesture);
    const current=ticket.current;
    const finish=()=>{if(current!==ticket.current)return;setSpeaking(false);onGesture('Idle');};
    timer.current=setTimeout(finish,Math.min(24000,Math.max(4000,answer.text.length*110)));
    if(!sound)return;
    if(!('speechSynthesis' in window)){setVoiceNotice('이 브라우저에서는 글로 안내해 드릴게요.');return;}
    const voice=window.speechSynthesis.getVoices().find(v=>v.lang.toLowerCase().startsWith('ko'));
    if(!voice){setVoiceNotice('한국어 음성이 없어 글로 안내해 드릴게요.');return;}
    const utterance=new SpeechSynthesisUtterance(answer.text);
    utterance.lang='ko-KR';utterance.voice=voice;utterance.rate=.94;
    utterance.onstart=()=>{if(current===ticket.current)setSpeaking(true);};
    utterance.onend=finish;
    utterance.onerror=()=>{if(current===ticket.current){setVoiceNotice('음성을 재생할 수 없어 글로 안내해 드릴게요.');finish();}};
    window.speechSynthesis.speak(utterance);
  };
  const close=()=>{stop();onGesture('Idle');onClose();};
  return <aside className="npc-conversation" role="dialog" aria-label={`${name}와 대화`} onKeyDown={e=>{if(e.key==='Escape'){e.stopPropagation();close();}}}>
    <header><div><span>지역 안내</span><strong>{name}</strong></div><div><button onClick={()=>{stop();setSound(v=>!v);onGesture('Idle');}} aria-label={sound?'음성 끄기':'음성 켜기'} aria-pressed={sound}>{sound?<Volume2 size={19}/>:<VolumeX size={19}/>}</button><button onClick={close} aria-label="대화 닫기"><X size={19}/></button></div></header>
    <p className="npc-reply" aria-live="polite">{reply}</p>
    {(speaking||voiceNotice)&&<small role="status">{speaking?'이야기하고 있어요':voiceNotice}</small>}
    <div className="npc-prompts">{['안녕!','이곳을 소개해 줘','고개를 끄덕여 줘'].map(text=><button key={text} onClick={()=>send(text)}>{text}</button>)}</div>
    <form onSubmit={e=>{e.preventDefault();send(input);}}><label className="sr-only" htmlFor="npc-message">지역 안내 또는 동작 요청</label><input ref={inputRef} id="npc-message" value={input} onChange={e=>setInput(e.target.value)} placeholder="인사해 줘, 설명해 줘…" maxLength={240}/><button type="submit" disabled={!input.trim()} aria-label="말 걸기"><Send size={18}/></button></form>
  </aside>;
}
