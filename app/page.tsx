'use client';

import { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, Footprints, MapPin, Map, RotateCcw, Pause, MoveUpRight, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Compass, MessageCircle, Volume2, VolumeX } from 'lucide-react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { movePlayer, moveOnFloors, reachableFloor, worldObstacles, solidCollider, worldFloors, floorHeight, currentPlace, type World } from '@/lib/world';
import { destinations, destinationFromSearch, type DestinationId } from '@/lib/destinations';
import { batchStaticScene, updateVegetationDetail } from '@/lib/static-scene';
import { createLocalLights } from '@/lib/local-lights';
import { unpackModel } from '@/lib/model-transport';
import { sceneArrival, portalAt, portalHref } from '@/lib/scene-travel';
import { canTravelTo, mapSolids, mapColor } from '@/lib/map-navigation';
import type { Point } from '@/lib/world';
import MapTravel from './map-travel';
import { BoatFleet, type BoatHud } from '@/lib/boat-fleet';
import { NpcTroupe } from '@/lib/npc';
import BitgaramHub from './bitgaram-hub';

type ViewState = { x: number; z: number; yaw: number; place: string; detail: string; indoor: boolean; npc: string | null };
type Talk = { id: string; name: string; lines: string[]; line: number };
type Engine = { start: () => void; pause: () => void; reset: () => void; overview: () => void; key: (key: string, down: boolean) => void; travel: (point: Point, height?:number) => boolean; boatAction: (action:string,id?:string)=>void; talk: () => void };

export default function Home() {
  const [hub,setHub]=useState(false);
  useEffect(()=>setHub(new URLSearchParams(window.location.search).get('place')==='bitgaram'),[]);
  return hub?<BitgaramHub/>:<Explorer/>;
}

function Explorer() {
  const host = useRef<HTMLDivElement>(null);
  const engine = useRef<Engine | null>(null);
  const [world, setWorld] = useState<World | null>(null);
  const [ready, setReady] = useState(false);
  const [active, setActive] = useState(false);
  const [started, setStarted] = useState(false);
  const [overview, setOverview] = useState(true);
  const [mapOpen,setMapOpen] = useState(false);
  const [welcomeExpanded,setWelcomeExpanded] = useState(false);
  const [minimapExpanded,setMinimapExpanded] = useState(false);
  const [error, setError] = useState('');
  const [boatHud,setBoatHud] = useState<BoatHud|null>(null);
  const [talk, setTalk] = useState<Talk | null>(null);
  const [voice, setVoice] = useState(() => {
    if (typeof window === 'undefined') return false;
    try { return window.localStorage.getItem('naju-walk-voice') === '1'; } catch { return false; }
  });
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try { window.localStorage.setItem('naju-walk-voice', voice ? '1' : '0'); } catch { /* private mode */ }
  }, [voice]);
  useEffect(() => {
    if (!voice || !talk || typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    const utterance = new SpeechSynthesisUtterance(talk.lines[talk.line]);
    utterance.lang = 'ko-KR'; utterance.rate = 0.95;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    return () => window.speechSynthesis.cancel();
  }, [voice, talk]);
  const [destinationId, setDestinationId] = useState<DestinationId>('geumseonggwan');
  const destination = destinations[destinationId];
  const [view, setView] = useState<ViewState>({ x: 0, z: 0, yaw: 0, place: '금성관 주변', detail: '', indoor: false, npc: null });

  useEffect(() => {
    const selectedId = destinationFromSearch(window.location.search);
    const selected = destinations[selectedId];
    const optimizedCampus=selectedId==='bitgaram-kepco'||selectedId==='bitgaram-kentech'||selectedId==='naju-arboretum'||selectedId==='deudeulgang';
    setDestinationId(selectedId);
    document.title = `나주 산책 — ${selected.area}`;
    const mount = host.current!;
    let disposed = false, renderer: THREE.WebGLRenderer | undefined, animation = 0;
    const cleanups: (() => void)[] = [];
    const scene = new THREE.Scene();
    const setup = async () => {
      const response = await fetch(selected.worldUrl);
      if (!response.ok) throw new Error('도시 자료를 불러오지 못했습니다.');
      const data: World = await response.json();
      if (disposed) return;
      setWorld(data);
      // Keep centimeter-separated landscape layers stable at city overview distances.
      renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance', logarithmicDepthBuffer: selectedId.startsWith('bitgaram') || selectedId==='deudeulgang' });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, optimizedCampus?1.25:1.75));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFShadowMap;
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = data.lighting?.exposure??1.25;
      const canvas = renderer.domElement;
      canvas.setAttribute('aria-label', `${selected.area} 3D 탐험 화면. 마우스를 끌어서 시선을 움직일 수 있습니다.`);
      canvas.tabIndex = 0;
      mount.appendChild(canvas);
      scene.background = new THREE.Color('#bbd9e6');
      scene.fog = new THREE.Fog('#bbd9e6', selectedId !== 'geumseonggwan' ? 650 : 260, selectedId !== 'geumseonggwan' ? 1350 : 690);
      scene.add(new THREE.HemisphereLight('#e1f3ff', '#918673', data.lighting?.ambient??(data.verticalNavigation ? 1.5 : 2.8)));
      const sun = new THREE.DirectionalLight('#fff0d1', data.lighting?.sun??3.1);
      sun.position.set(-80, 145, 65); sun.castShadow = true;
      sun.shadow.mapSize.set(2048, 2048);
      sun.shadow.camera.left = sun.shadow.camera.bottom = -165;
      sun.shadow.camera.right = sun.shadow.camera.top = 165;
      sun.shadow.camera.far = 420; sun.shadow.normalBias = 0.06;
      if(selectedId==='bitgaram-kentech'){
        sun.position.set(-220,420,220);sun.target.position.set(30,0,20);scene.add(sun.target);
        sun.shadow.camera.left=sun.shadow.camera.bottom=-340;
        sun.shadow.camera.right=sun.shadow.camera.top=340;sun.shadow.camera.far=1000;
      }
      scene.add(sun);
      const localLights=optimizedCampus?createLocalLights(scene,data.lights??[]):undefined;
      for (const fixture of optimizedCampus?[]:data.lights ?? []) {
        const light = new THREE.PointLight(fixture.color, fixture.intensity, fixture.distance, 2);
        light.position.set(...fixture.position);
        scene.add(light);
      }
      const loader=new GLTFLoader();
      const gltf = await (async()=>{
        if(!selected.modelUrl.split('?')[0].endsWith('.gz'))return loader.loadAsync(selected.modelUrl);
        const response=await fetch(selected.modelUrl);
        if(!response.ok)throw new Error('도시 모델을 불러오지 못했습니다.');
        return loader.parseAsync(await unpackModel(await response.arrayBuffer()),'');
      })();
      if (disposed) { gltf.scene.traverse(disposeObject); return; }
      gltf.scene.traverse(o => { if (o instanceof THREE.Mesh) {
        const landscape=selectedId.startsWith('bitgaram')&&/^(context_ground|lake_osm_|estimated_hill|surrounding_park_lawn|surrounding_mapped_paths|surrounding_parking|surrounding_recreation)/.test(o.name);
        const riverSurface=selectedId==='deudeulgang'&&/^(path_|road_|mapped_river_water|water_glint|pine_litter_patch|understory_moss|crop_row|satellite_field)/.test(o.name);
        o.castShadow = !o.name.startsWith('ground')&&!landscape&&!riverSurface&&!o.userData.no_shadow;
        o.receiveShadow = !o.userData.no_receive_shadow && !(landscape && o.name!=='estimated_hill');
        if(o.userData.photo_panorama){
          o.castShadow=false;o.receiveShadow=false;o.renderOrder=-100;
          // Blender exports pure emission as an emissive PBR material in this version.
          const original=Array.isArray(o.material)?o.material:[o.material];
          const unlit=original.map(m=>{
            const p=m as THREE.MeshStandardMaterial;
            const material=new THREE.MeshBasicMaterial({map:p.emissiveMap??p.map,side:m.side});
            m.dispose();return material;
          });
          o.material=Array.isArray(o.material)?unlit:unlit[0];
          for(const material of Array.isArray(o.material)?o.material:[o.material]){
            material.toneMapped=false;material.fog=false;material.depthWrite=false;
          }
        }
      } });
      batchStaticScene(gltf.scene);
      const roofParts: THREE.Object3D[]=[];
      gltf.scene.traverse(o=>{if(o.userData.hide_in_overview)roofParts.push(o);});
      scene.add(gltf.scene);
      if(optimizedCampus){
        gltf.scene.traverse(o=>{o.updateMatrix();o.matrixAutoUpdate=false;});
        renderer.shadowMap.autoUpdate=false;
        renderer.shadowMap.needsUpdate=true;
      }
      const fleet=new BoatFleet(data);
      await fleet.load(scene);
      if(disposed){scene.traverse(disposeObject);return;}
      const npcTroupe=new NpcTroupe(data.npcs??[]);
      await npcTroupe.load(scene);
      if(disposed){scene.traverse(disposeObject);return;}
      const camera = new THREE.PerspectiveCamera(60, 1, 0.12, selectedId !== 'geumseonggwan' ? 1800 : 1000);
      const colliders = data.solids.filter(s => s.collision).map(solidCollider);
      const floors = worldFloors(data.solids);
      const obstacles=data.verticalNavigation?worldObstacles(data.solids):[];
      const arrival=sceneArrival(data,window.location.search);
      let px = arrival.x, pz = arrival.z, yaw = arrival.yaw, pitch = 0;
      let elevation=reachableFloor(px,pz,arrival.height??0,floors)??0;
      let playing = false, bird = true, drag = false, lastX = 0, lastY = 0;
      let orbit: number = selected.overview.angle, orbitElevation: number = selected.overview.elevation, orbitRadius: number = selected.overview.radius;
      const center = selectedId === 'geumseonggwan' ? new THREE.Vector3(data.spawn.x, 0, data.spawn.z - 3) : new THREE.Vector3(selected.overview.center[0], 0, selected.overview.center[1]);
      const keys = new Set<string>();
      const resize = () => {
        if (!renderer) return;
        camera.aspect = mount.clientWidth / mount.clientHeight; camera.updateProjectionMatrix();
        renderer.setSize(mount.clientWidth, mount.clientHeight);
      };
      resize();
      const observer = new ResizeObserver(resize); observer.observe(mount);
      cleanups.push(() => observer.disconnect());
      const listen = (target: EventTarget, name: string, fn: EventListener, options?: AddEventListenerOptions) => {
        target.addEventListener(name, fn, options); cleanups.push(() => target.removeEventListener(name, fn, options));
      };
      const pause = () => {
        fleet.stop();
        playing = false; keys.clear(); drag = false; setActive(false); setTalk(null);
        if (document.pointerLockElement === canvas) document.exitPointerLock();
      };
      const talkAction = () => {
        const npc = npcTroupe.nearest(px, pz);
        if (!npc) return;
        setTalk(prev => (!prev || prev.id !== npc.id) ? { id: npc.id, name: npc.name, lines: npc.lines, line: 0 } : prev.line + 1 < prev.lines.length ? { ...prev, line: prev.line + 1 } : null);
      };
      const start = () => {
        playing = true; bird = false; setActive(true); setStarted(true); setOverview(false);
        canvas.focus({ preventScroll: true });
        // Drag and keyboard controls also work when an embedded browser denies pointer lock.
        // River controls stay clickable; drag-look works alongside the boat dashboard.
        if (!data.boats?.length && window.matchMedia('(pointer:fine)').matches && canvas.requestPointerLock) {
          try { const request = canvas.requestPointerLock(); request?.catch(() => {}); } catch { /* drag fallback */ }
        }
      };
      const alignPassenger=()=>{const p=fleet.eye();if(p){px=p.x;pz=p.z;elevation=p.height;}};
      const boatAction=(action:string,id?:string)=>{
        keys.clear();
        if(action==='board'&&id){
          const vessel=fleet.vessels.find(v=>v.definition.id===id);if(!vessel)return;
          if(fleet.board(id,[px,pz],elevation)){yaw=vessel.state.yaw;pitch=0;alignPassenger();}
          else if(!fleet.passenger){engine.current?.travel(vessel.definition.shore,vessel.definition.shoreHeight);return;}
        }else if(action==='helm'){fleet.drive();if(fleet.passenger)yaw=fleet.passenger.vessel.state.yaw;pitch=0;alignPassenger();}
        else if(action==='deck')fleet.deck();
        else if(action==='dock'){fleet.returnToBerth();alignPassenger();}
        else if(action==='leave'){const p=fleet.leave();if(p){px=p.position[0];pz=p.position[1];elevation=p.height;}}
        start();
      };
      engine.current = {
        start, pause, boatAction, talk: talkAction,
        reset: () => { fleet.reset();setTalk(null);px = data.spawn.x; pz = data.spawn.z; elevation=reachableFloor(px,pz,data.spawn.height??0,floors)??0; yaw = data.spawn.yaw; pitch = 0; start(); },
        overview: () => { pause(); bird = true; setOverview(true); },
        key: (key, down) => { if (down) keys.add(key); else keys.delete(key); },
        travel: (point,height=0) => {
          if(!canTravelTo(point,data,height))return false;
          fleet.leaveForTravel();
          px=point[0];pz=point[1];pitch=0;keys.clear();
          elevation=reachableFloor(px,pz,height,floors)??0;
          const arrival=data.places.find(p=>p.arrival && Math.hypot(p.arrival[0]-px,p.arrival[1]-pz)<.1);
          if(arrival && Math.hypot(arrival.position[0]-px,arrival.position[1]-pz)>1)yaw=Math.atan2(px-arrival.position[0],pz-arrival.position[1]);
          start();
          return true;
        },
      };
      const context = (document as Document & { modelContext?: { registerTool: (tool: { name: string; description: string; inputSchema: object; annotations: object; execute: (input: unknown) => unknown }, options: { signal: AbortSignal }) => void | Promise<void> } }).modelContext;
      if (context?.registerTool) {
        const lifecycle = new AbortController();
        cleanups.push(() => lifecycle.abort());
        const state = () => ({ destination: selected.name, mode: bird ? 'overview' : playing ? 'walking' : 'paused', position: { x: px, z: pz }, source: data.source });
        const registrations = [
          { name: 'get_naju_walk_state', description: 'Read the current Naju exploration view and position.', inputSchema: { type: 'object', properties: {}, additionalProperties: false }, annotations: { readOnlyHint: true }, execute: () => state() },
          { name: 'set_naju_walk_view', description: 'Switch the same exploration view as the visible overview, walk, or pause controls.', inputSchema: { type: 'object', properties: { view: { type: 'string', enum: ['overview', 'walk', 'pause'] } }, required: ['view'], additionalProperties: false }, annotations: { readOnlyHint: false }, execute: async (input: unknown) => {
            if (!input || typeof input !== 'object' || Object.keys(input).some(k => k !== 'view')) throw new Error('Expected only a view field.');
            const requested = (input as { view?: string }).view;
            if (requested === 'overview') engine.current?.overview(); else if (requested === 'walk') start(); else if (requested === 'pause') pause(); else throw new Error('View must be overview, walk, or pause.');
            await new Promise<void>(resolve => requestAnimationFrame(() => resolve())); return state();
          } },
        ];
        for (const tool of registrations) {
          try { void Promise.resolve(context.registerTool(tool, { signal: lifecycle.signal })).catch(() => {}); } catch { /* optional browser capability */ }
        }
      }
      listen(window, 'keydown', ((e: KeyboardEvent) => {
        if (e.target instanceof HTMLButtonElement || e.target instanceof HTMLAnchorElement) return;
        if (e.code === 'Escape') { pause(); return; }
        if (!playing) return;
        if(e.code==='KeyF'&&!e.repeat){e.preventDefault();const hud=fleet.hud([px,pz],elevation);if(hud.mode==='helm')boatAction('deck');else if(hud.aboard)boatAction('helm');else if(hud.near)boatAction('board',hud.near);else talkAction();return;}
        if (['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','KeyQ','KeyE','ShiftLeft','ShiftRight','Space'].includes(e.code)) { e.preventDefault(); keys.add(e.code); }
      }) as EventListener);
      listen(window, 'keyup', ((e: KeyboardEvent) => { keys.delete(e.code); }) as EventListener);
      listen(window, 'blur', pause);
      listen(document, 'visibilitychange', () => { if (document.hidden) pause(); });
      listen(document, 'pointerlockchange', () => { if (document.pointerLockElement !== canvas && playing) pause(); });
      listen(canvas, 'pointerdown', ((e: PointerEvent) => {
        if (!bird && !playing) return;
        drag = true; lastX = e.clientX; lastY = e.clientY;
        if (document.pointerLockElement !== canvas) canvas.setPointerCapture(e.pointerId);
      }) as EventListener);
      listen(window, 'pointerup', () => { drag = false; });
      listen(canvas, 'pointercancel', () => { drag = false; });
      listen(window, 'pointermove', ((e: PointerEvent) => {
        const locked = document.pointerLockElement === canvas;
        if (!locked && !drag) return;
        const dx = locked ? e.movementX : e.clientX - lastX, dy = locked ? e.movementY : e.clientY - lastY;
        lastX = e.clientX; lastY = e.clientY;
        if (bird) { orbit -= dx * 0.005; orbitElevation = THREE.MathUtils.clamp(orbitElevation + dy * 0.003, 0.3, 1.3); }
        else if (playing) { yaw -= dx * 0.0028; pitch = THREE.MathUtils.clamp(pitch - dy * 0.0028, -1.15, 1.15); }
      }) as EventListener);
      listen(canvas, 'wheel', ((e: WheelEvent) => { if (bird) { e.preventDefault(); orbitRadius = THREE.MathUtils.clamp(orbitRadius + e.deltaY * 0.1, 'parent' in selected ? 12 : 85, selectedId !== 'geumseonggwan' ? 800 : 330); } }) as EventListener, { passive: false });
      listen(canvas, 'webglcontextlost', ((e: Event) => { e.preventDefault(); pause(); setError('3D 화면 연결이 끊겼습니다. 새로고침해 다시 열어주세요.'); }) as EventListener);
      setReady(true);
      // Door travel opens at eye level. Pointer lock still waits for a user gesture.
      if(arrival.entered){playing=true;bird=false;setActive(true);setStarted(true);setOverview(false);canvas.focus({preventScroll:true});}
      let changingScene=false;
      let last = performance.now(), lastHud = 0, lastLightUpdate=-Infinity;
      let shadowBird: boolean|undefined;
      const frame = (now: number) => {
        if (disposed || !renderer) return;
        const dt = Math.min((now - last) / 1000, 0.06); last = now;
        if (playing) {
          const forward = Number(keys.has('KeyW') || keys.has('ArrowUp')) - Number(keys.has('KeyS') || keys.has('ArrowDown'));
          const side = Number(keys.has('KeyD')) - Number(keys.has('KeyA'));
          yaw += (Number(keys.has('KeyQ') || (!fleet.passenger?.helm&&keys.has('ArrowLeft'))) - Number(keys.has('KeyE') || (!fleet.passenger?.helm&&keys.has('ArrowRight')))) * dt * 1.6;
          const len = Math.hypot(forward, side) || 1;
          const speed = (keys.has('ShiftLeft') || keys.has('ShiftRight') ? 9 : 4.5) * dt / len;
          const dx=(-Math.sin(yaw) * forward + Math.cos(yaw) * side) * speed, dz=(-Math.cos(yaw) * forward - Math.sin(yaw) * side) * speed;
          const passenger=fleet.update(dt,keys,yaw);
          if(passenger){px=passenger.x;pz=passenger.z;elevation=passenger.height;yaw+=passenger.yawDelta;}
          else{
            const next=data.verticalNavigation?moveOnFloors(px,pz,elevation,dx,dz,obstacles,floors,data.bounds,data.requireFloor):movePlayer(px,pz,dx,dz,colliders,data.bounds);
            px = next.x; pz = next.z;
            if('height' in next)elevation=next.height as number;
          }
          if(!fleet.passenger && !changingScene && (forward || side)){
            const portal=portalAt(data,px,pz,elevation),href=portal&&portalHref(portal);
            if(href){changingScene=true;keys.clear();playing=false;window.location.assign(href);}
          }
        }
        roofParts.forEach(o=>{o.visible=!bird;});
        if (bird) {
          camera.position.set(center.x + Math.sin(orbit) * Math.cos(orbitElevation) * orbitRadius, Math.sin(orbitElevation) * orbitRadius, center.z + Math.cos(orbit) * Math.cos(orbitElevation) * orbitRadius); camera.lookAt(center);
        } else { camera.position.set(px, 1.72 + (data.verticalNavigation?elevation:floorHeight(px, pz, floors)), pz); camera.rotation.order = 'YXZ'; camera.rotation.set(pitch, yaw, 0); }
        if(localLights && now-lastLightUpdate>150){localLights.update(camera.position);lastLightUpdate=now;}
        if((selectedId==='naju-arboretum'||selectedId==='deudeulgang') && updateVegetationDetail(gltf.scene,camera.position))renderer.shadowMap.needsUpdate=true;
        if(optimizedCampus && shadowBird!==bird){renderer.shadowMap.needsUpdate=true;shadowBird=bird;}
        if (now - lastHud > 180) {
          const hud=fleet.hud([px,pz],elevation);if(fleet.vessels.length)setBoatHud(hud);
          const place = currentPlace(px, pz, data.places, data.verticalNavigation?elevation:undefined);
          const doorway=data.portals?.find(p=>Math.hypot(p.position[0]-px,p.position[1]-pz)<4 && Math.abs((p.height??0)-elevation)<.6);
          const npcNear=npcTroupe.nearest(px,pz);
          setTalk(prev=>!prev?prev:(!npcNear||npcNear.id!==prev.id)?null:prev);
          setView({ x: px, z: pz, yaw, place: fleet.passenger?.vessel.definition.name ?? place?.name ?? selected.area, detail: hud.aboard?(hud.mode==='helm'?'W 전진 · S 후진 · A D 방향 · Space 제동':'갑판과 객실을 걸어서 둘러보세요. F를 누르면 운전석으로 이동합니다.'):doorway?doorway.label:npcNear?`${npcNear.name}: F를 눌러 이야기 나누기`:place?.description ?? '길을 따라 천천히 둘러보세요.', indoor: !!hud.aboard || (place?.indoor ?? place?.id === 'interior'), npc: npcNear?.name ?? null }); lastHud = now;
        }
        renderer.render(scene, camera); animation = requestAnimationFrame(frame);
      };
      animation = requestAnimationFrame(frame);
    };
    function disposeObject(o: THREE.Object3D) {
      if (!(o instanceof THREE.Mesh)) return;
      o.geometry?.dispose(); const mats = Array.isArray(o.material) ? o.material : [o.material];
      mats.forEach(m => { Object.values(m).forEach(v => { if (v instanceof THREE.Texture) v.dispose(); }); m.dispose(); });
    }
    setup().catch(e => { if (!disposed) setError(e instanceof Error ? e.message : '3D 화면을 열 수 없습니다.'); });
    return () => {
      disposed = true; cancelAnimationFrame(animation); cleanups.forEach(fn => fn());
      if (document.pointerLockElement === renderer?.domElement) document.exitPointerLock();
      scene.traverse(disposeObject); renderer?.dispose(); renderer?.domElement.remove(); engine.current = null;
    };
  }, []);

  const press = (key: string) => ({
    onPointerDown: (e: React.PointerEvent<HTMLButtonElement>) => { e.preventDefault(); e.currentTarget.setPointerCapture(e.pointerId); engine.current?.key(key, true); },
    onPointerUp: () => engine.current?.key(key, false), onPointerCancel: () => engine.current?.key(key, false), onLostPointerCapture: () => engine.current?.key(key, false),
  });
  const openMap=()=>{engine.current?.pause();setMapOpen(true);};
  return (
    <main className="explorer">
      <div className="scene" ref={host} /><div className="vignette" />
      <header className="topbar">
        <div className="brand"><span className="brand-mark"><Compass size={25} strokeWidth={1.4} /></span><div><strong>나주 산책</strong><span>NAJU, ON FOOT</span></div></div>
        <div className="location-pill"><span className="live-dot" /><span>{destination.area}</span><span className="pill-divider" /><span>{destinationId.startsWith('bitgaram')?'사진·지도 참고':'parent' in destination?'사진 참고 실내':'실제 지도 기반'}</span></div>
        <div className="view-actions"><button className={overview ? 'active' : ''} onClick={() => engine.current?.overview()} disabled={!ready}><MoveUpRight size={16} />전체 보기</button><button className={!overview ? 'active' : ''} onClick={() => boatHud?.aboard?engine.current?.boatAction('deck'):engine.current?.start()} disabled={!ready}><Footprints size={16} />걷기</button></div>
      </header>
      <nav className="destination-nav" aria-label="산책 장소">
        <button onClick={openMap}><Map size={18}/><span>지도로 이동</span><ArrowUpRight size={16}/></button>
      </nav>
      {active && !!world?.sceneLinks?.length && <nav className="scene-signposts" aria-label="장소 이동 푯말">{world.sceneLinks.filter(link=>Object.hasOwn(destinations,link.target)).map(link=><a key={link.target} href={`/?place=${encodeURIComponent(link.target)}`}><MapPin size={18}/><span>{link.label}</span><ArrowUpRight size={16}/></a>)}</nav>}
      {world && !minimapExpanded && <button className="minimap-toggle" aria-expanded={false} aria-controls="location-minimap" onClick={()=>setMinimapExpanded(true)}><Map size={17}/>미니맵 펼치기</button>}
      {world && minimapExpanded && <aside id="location-minimap" className="minimap" aria-label="현재 위치 지도">
        <div className="map-heading"><span>{destinationId.startsWith('bitgaram')?'장소 지도':'parent' in destination?'실내 지도':'동네 지도'}</span><button className="panel-fold" aria-expanded={true} aria-controls="location-minimap" onClick={()=>setMinimapExpanded(false)}>접기 −</button></div>
        <svg viewBox={`${world.bounds[0]} ${world.bounds[2]} ${world.bounds[1] - world.bounds[0]} ${world.bounds[3] - world.bounds[2]}`} role="img" aria-label={`현재 위치: ${view.place}`} onClick={openMap}>
          <rect x={world.bounds[0]} y={world.bounds[2]} width={world.bounds[1] - world.bounds[0]} height={world.bounds[3] - world.bounds[2]} fill="#e5e8df" />
          {mapSolids(world).map((s, i) => <polygon key={i} points={solidCollider(s).map(p => p.join(',')).join(' ')} fill={mapColor(s.name)} stroke={s.kind === 'building' ? '#9aada2' : 'none'} strokeWidth="0.7" />)}
          {boatHud?.boats.map(b=><g key={b.id} transform={`translate(${b.x} ${b.z}) rotate(${-b.yaw*180/Math.PI})`}><path d="M 0,-13 L 4,-7 L 4,11 L -4,11 L -4,-7 Z" fill={boatHud.aboard===b.id?'#d27c32':'#664d33'} stroke="#fff" strokeWidth="1.6"/></g>)}
          <g transform={`translate(${view.x} ${view.z}) scale(${(world.bounds[1]-world.bounds[0])/245})`}>
            <circle r="6" fill="#fff" /><circle r="3.5" fill="#c96734" />
            <path d="M 0,-11 L -3,-6 L 3,-6 Z" fill="#c96734" transform={`rotate(${-view.yaw * 180 / Math.PI})`} />
          </g>
        </svg><div className="map-legend"><span className="you-dot" />내 위치<span>약 {Math.round((world.bounds[1] - world.bounds[0]) / 10) * 10}m 구역</span></div>
        <button className="minimap-travel" onClick={openMap}>지도 열고 이동하기 <ArrowUpRight size={14}/></button>
      </aside>}
      {!active && !boatHud?.aboard && <section className={`welcome${welcomeExpanded?'':' welcome-compact'}`} aria-label="산책 시작">
        <button className="welcome-fold panel-fold" aria-expanded={welcomeExpanded} aria-controls="walk-introduction" onClick={()=>setWelcomeExpanded(v=>!v)}>{welcomeExpanded?'안내 접기 −':'이용 안내 +'}</button>
        {welcomeExpanded && <div id="walk-introduction"><div className="eyebrow"><span />나주 · {destination.name}</div>
        <h1>{started ? '잠시, 쉬어가기.' : <>{destination.heading[0]}<br />{destination.heading[1]}</>}</h1>
        <p>{started ? '산책을 이어가거나, 위에서 동네를 둘러보세요.' : <>{destination.introduction[0]}<br />{destination.introduction[1]}</>}</p></div>}
        <button className="start-button" onClick={() => engine.current?.start()} disabled={!ready || !!error}><Footprints size={20} /><span>{error ? '화면을 열 수 없어요' : !ready ? '동네 불러오는 중…' : started ? '이어서 걷기' : '산책 시작하기'}</span><ArrowUpRight size={21} /></button>
        {welcomeExpanded && <div className="welcome-help"><span><kbd>W A S D</kbd> 이동</span><span>마우스 / 드래그로 둘러보기</span></div>}
        {error && <div className="error-message" role="alert">{error}<button onClick={() => window.location.reload()}>다시 불러오기</button></div>}
      </section>}
      {active && <><div className="crosshair" aria-hidden="true" />{!boatHud?.aboard&&!talk&&<div className="place-card"><span className="place-icon"><MapPin size={21} /></span><div><span>{view.indoor ? '실내에 도착했어요' : '지금 걷는 곳'}</span><strong>{view.place}</strong><p>{view.detail}</p></div></div>}
        {view.npc&&!talk&&!boatHud?.aboard&&<button className="npc-prompt" onClick={()=>engine.current?.talk()}><MessageCircle size={16}/>{view.npc} · F</button>}
        <div className="touch-controls" aria-label="이동 버튼"><button aria-label="앞으로" {...press('KeyW')}><ArrowUp /></button><div><button aria-label="왼쪽으로" {...press('KeyA')}><ArrowLeft /></button><button aria-label="뒤로" {...press('KeyS')}><ArrowDown /></button><button aria-label="오른쪽으로" {...press('KeyD')}><ArrowRight /></button></div><div className="turn-controls"><button aria-label="왼쪽 보기" {...press('KeyQ')}>↶</button><button aria-label="오른쪽 보기" {...press('KeyE')}>↷</button></div></div></>}
      {active && talk && <aside className="npc-panel" aria-label="문화해설사와의 대화">
        <div className="npc-panel-title"><span>{talk.name}</span><div className="npc-panel-title-actions"><button className="npc-voice-toggle" aria-pressed={voice} aria-label={voice?'음성 안내 끄기':'음성으로 듣기'} onClick={()=>setVoice(v=>!v)}>{voice?<Volume2 size={15}/>:<VolumeX size={15}/>}</button><small>{talk.line+1} / {talk.lines.length}</small></div></div>
        <p>{talk.lines[talk.line]}</p>
        <button onClick={()=>engine.current?.talk()}>{talk.line+1<talk.lines.length?'다음 이야기 · F':'마치기 · F'}</button>
      </aside>}
      {boatHud&&(active||!!boatHud.aboard)&&!mapOpen&&<aside className={`boat-panel ${boatHud.aboard?'aboard':'at-shore'}`} aria-label="황포돛배 승선과 조종">
        <div className="boat-panel-title"><span>{boatHud.aboard?view.place:'영산강 황포돛배'}</span>{boatHud.aboard&&<strong>{boatHud.speed.toFixed(1)} <small>km/h</small></strong>}</div>
        {boatHud.aboard?<>
          <p>{boatHud.departing?'출항 중이에요. 선착장에서 떨어진 뒤 직접 조종할 수 있습니다.':boatHud.mode==='helm'?'W 전진 · S 후진 · A D 방향 · Space 제동':'갑판과 객실을 자유롭게 걸어보세요.'}</p>
          <p className="boat-mouse-help">{active?'화면을 드래그해 둘러보기 · Esc 일시정지':'배가 정지했어요. 이어서 탐험하거나 아래에서 선택하세요.'}</p>
          {boatHud.blocked&&<p role="status">강가 또는 다른 배에 가까워 멈췄어요. 반대 방향으로 이동해 주세요.</p>}
          <div className="boat-actions">{!active&&<button onClick={()=>engine.current?.start()}>이어서 탐험</button>}<button onClick={()=>engine.current?.boatAction(boatHud.mode==='helm'?'deck':'helm')}>{boatHud.mode==='helm'?'갑판 둘러보기':'운전석으로 · F'}</button>{boatHud.mode==='helm'&&active&&<button {...press('Space')}>제동</button>}{boatHud.canLeave?<button onClick={()=>engine.current?.boatAction('leave')}>선착장에 내리기</button>:<button onClick={()=>engine.current?.boatAction('dock')}>선착장으로 복귀</button>}</div>
          <small className="boat-dimension">{boatHud.boats.find(b=>b.id===boatHud.aboard)?.note}</small>
        </>:<><p>{boatHud.near?'승선 버튼이나 F를 눌러 배에 올라보세요.':'배를 선택하면 승선 입구로 이동해요.'}</p><div className="boat-actions">{boatHud.boats.map(b=><button key={b.id} onClick={()=>engine.current?.boatAction('board',b.id)}>{b.name} {boatHud.near===b.id?'승선':'선착장'}</button>)}</div></>}
      </aside>}
      <footer className="bottom-bar"><div className="keyboard-guide"><span><kbd>W A S D</kbd> 이동</span><span><kbd>← →</kbd> 시선 회전</span><span><kbd>Shift</kbd> 빠르게</span><span><kbd>Esc</kbd> 쉬기</span></div><div className="bottom-actions"><button onClick={() => engine.current?.reset()} disabled={!ready} aria-label="출발 위치로 돌아가기"><RotateCcw size={16} />처음 위치</button>{active && <button onClick={() => engine.current?.pause()}><Pause size={16} />쉬기</button>}</div></footer>
      <div className="source-note"><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap 기여자 · ODbL</a><span>·</span><a href={destination.sourceUrl} target="_blank" rel="noreferrer">{destination.sourceLabel}</a>{(['dasi','bogam','bogam-museum'].includes(destinationId)) && <><span>·</span><a href="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer" target="_blank" rel="noreferrer">Esri / Vantor 항공사진({destinationId==='dasi'?'2022':'2023'})</a></>}{destinationId==='yeongsanpo'&&<><span>·</span><a href="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer" target="_blank" rel="noreferrer">Esri / Vantor 항공사진 참고</a></>}<span>· {destination.limitation}</span></div>
      {mapOpen&&<MapTravel destinationId={destinationId} world={world} position={[view.x,view.z]} onClose={()=>setMapOpen(false)} onTravel={(point,height)=>engine.current?.travel(point,height)??false}/>}
    </main>
  );
}
