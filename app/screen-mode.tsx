'use client';

import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { Maximize, Minimize, RotateCw, Smartphone } from 'lucide-react';
import { enterLandscape, needsLandscape, type GraphicsQuality } from '@/lib/display-mode';

type ScreenMode = {
  initialized: boolean; touch: boolean; touchControls: boolean; portrait: boolean; fullscreen: boolean; quality: GraphicsQuality;
  setQuality: (quality: GraphicsQuality) => void; setTouchControls: (show: boolean) => void; toggleFullscreen: () => Promise<void>;
};
const Context = createContext<ScreenMode | null>(null);
export function useScreenMode() {
  const mode = useContext(Context);
  if (!mode) throw new Error('ScreenMode is required');
  return mode;
}

export default function ScreenMode({ children }: { children: ReactNode }) {
  const [touch, setTouch] = useState(false), [portrait, setPortrait] = useState(false);
  const [initialized,setInitialized]=useState(false);
  const [controlOverride, setControlOverride] = useState<boolean|null>(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [quality, updateQuality] = useState<GraphicsQuality>('balanced');
  const [notice, setNotice] = useState(''), [busy, setBusy] = useState(false);
  const content = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const input = matchMedia('(any-pointer: coarse)');
    const sync = () => {
      const isTouch = input.matches || navigator.maxTouchPoints > 0;
      const isPortrait = needsLandscape(innerWidth, innerHeight, isTouch);
      setTouch(isTouch); setPortrait(isPortrait);
      if (isPortrait) window.dispatchEvent(new Event('naju:pause'));
    };
    const fullscreenChange = () => setFullscreen(!!document.fullscreenElement);
    let saved: string | null = null;
    try { saved = localStorage.getItem('naju-graphics'); } catch { /* private browsing */ }
    try { const savedControls=localStorage.getItem('naju-touch-controls'); if(savedControls==='true'||savedControls==='false')setControlOverride(savedControls==='true'); } catch { /* private browsing */ }
    updateQuality(saved === 'detail' || saved === 'balanced' ? saved : input.matches || navigator.maxTouchPoints > 0 ? 'balanced' : 'detail');
    sync(); fullscreenChange();setInitialized(true);
    window.addEventListener('resize', sync); input.addEventListener('change', sync);
    document.addEventListener('fullscreenchange', fullscreenChange);
    return () => {
      window.removeEventListener('resize', sync); input.removeEventListener('change', sync);
      document.removeEventListener('fullscreenchange', fullscreenChange);
      try { screen.orientation?.unlock?.(); } catch { /* unavailable */ }
    };
  }, []);
  const setQuality = (value: GraphicsQuality) => {
    updateQuality(value);
    try { localStorage.setItem('naju-graphics', value); } catch { /* private browsing */ }
    window.dispatchEvent(new CustomEvent('naju:quality', { detail: value }));
  };
  const setTouchControls = (show: boolean) => {
    setControlOverride(show);
    try { localStorage.setItem('naju-touch-controls', String(show)); } catch { /* private browsing */ }
  };
  const requestLandscape = async () => {
    if (busy) return;
    setBusy(true); setNotice('');
    const orientation = screen.orientation as ScreenOrientation & { lock?: (mode: 'landscape') => Promise<void> };
    const result = await enterLandscape(document.documentElement, orientation, !!document.fullscreenElement);
    setNotice(result === 'locked' ? '' : result === 'rotate' ? '기기를 옆으로 돌려 주세요. 회전 잠금이 켜져 있다면 해제해 주세요.' : '이 브라우저는 전체 화면 전환을 지원하지 않습니다. 기기를 옆으로 돌려 주세요.');
    setBusy(false);
  };
  const toggleFullscreen = async () => {
    if (document.fullscreenElement) {
      try { screen.orientation?.unlock?.(); await document.exitFullscreen(); } catch { /* stays usable */ }
    } else await requestLandscape();
  };
  const showTouch=controlOverride??touch;
  return <Context.Provider value={{ initialized,touch, touchControls:showTouch, portrait, fullscreen, quality, setQuality, setTouchControls, toggleFullscreen }}>
    <div className="app-shell" data-touch={showTouch} data-graphics={quality}>
      <div ref={content} className="app-content" inert={portrait} aria-hidden={portrait || undefined}>{children}</div>
      {portrait && <section className="rotate-screen" aria-labelledby="rotate-title">
        <div className="rotate-mark"><Smartphone size={54} strokeWidth={1.3}/><RotateCw size={22}/></div>
        <span className="rotate-brand">나주 산책</span>
        <h1 id="rotate-title">가로로 돌려 주세요</h1>
        <p>넓은 화면으로 풍경을 보고<br/>양손으로 편하게 걸을 수 있어요.</p>
        <button onClick={requestLandscape} disabled={busy}><Maximize size={18}/>{busy ? '화면 전환 중…' : '가로 전체 화면으로 시작'}</button>
        <small>자동 회전이 안 되면 기기의 회전 잠금을 해제해 주세요.</small>
        {notice && <p className="screen-notice" role="status">{notice}</p>}
      </section>}
      {!portrait && notice && <div className="fullscreen-notice" role="status">{notice}<button aria-label="안내 닫기" onClick={() => setNotice('')}>닫기</button></div>}
    </div>
  </Context.Provider>;
}

export function FullscreenButton() {
  const { fullscreen, toggleFullscreen } = useScreenMode();
  return <button className="screen-button" onClick={toggleFullscreen} aria-label={fullscreen ? '전체 화면 종료' : '전체 화면'} title={fullscreen ? '전체 화면 종료' : '전체 화면'}>
    {fullscreen ? <Minimize size={19}/> : <Maximize size={19}/>}
  </button>;
}
