'use client';

import {useEffect,useSyncExternalStore} from 'react';
import {Music,VolumeX} from 'lucide-react';
import {bgmForDestination} from '@/lib/bgm';
import {bgmState,setBgmEnabled,setBgmTrack,subscribeBgm,unlockBgm,type BgmState} from '@/lib/bgm-player';
import type {DestinationId} from '@/lib/destinations';

const serverState:BgmState={enabled:true,playing:false,ducked:false,track:null};

/** Picks this place's loop and starts it on the visitor's first tap, click or key. */
export function useBgm(destinationId:DestinationId){
  useEffect(()=>{
    setBgmTrack(bgmForDestination[destinationId]);
    const events=['pointerdown','keydown','touchend'] as const;
    const first=()=>unlockBgm();
    for(const name of events)window.addEventListener(name,first,true);
    return ()=>{for(const name of events)window.removeEventListener(name,first,true);};
  },[destinationId]);
}

export function BgmButton() {
  const {enabled}=useSyncExternalStore(subscribeBgm,bgmState,()=>serverState);
  const label=enabled?'배경음악 끄기':'배경음악 켜기';
  return <button className="screen-button" onClick={()=>setBgmEnabled(!enabled)} aria-pressed={enabled} aria-label={label} title={label}>{enabled?<Music size={19}/>:<VolumeX size={19}/>}</button>;
}
