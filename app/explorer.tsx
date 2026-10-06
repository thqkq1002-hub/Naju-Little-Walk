'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowUpRight, Footprints, MapPin, Map, RotateCcw, Pause, MoveUpRight, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Compass, CircleHelp, Plus, Minus, MessageCircle } from 'lucide-react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Sky } from 'three/addons/objects/Sky.js';
import { movePlayer, moveOnFloors, reachableFloor, worldObstacles, solidCollider, worldFloors, floorHeight, currentPlace, type World } from '@/lib/world';
import { destinations, type DestinationId } from '@/lib/destinations';
import { appDestinationFromSearch } from '@/lib/app-destination';
import { batchStaticSceneInSlices, updateVegetationDetail } from '@/lib/static-scene';
import { createLocalLights } from '@/lib/local-lights';
import { fetchModelData } from '@/lib/model-transport';
import { sceneArrival, portalAt, portalHref } from '@/lib/scene-travel';
import { canTravelTo } from '@/lib/map-navigation';
import type { Point } from '@/lib/world';
import MapTravel from './map-travel';
import { PrecinctMapShapes } from './geumseonggwan-map';
import { BoatFleet, type BoatHud } from '@/lib/boat-fleet';
import { MonorailScene, type RailHud } from '@/lib/monorail-scene';
import { FullscreenButton, useScreenMode } from './screen-mode';
import WalkGuide from './walk-guide';
import { pixelRatioFor, type GraphicsQuality } from '@/lib/display-mode';
import { ViewGesture } from '@/lib/view-gesture';
import { RenderDemand } from '@/lib/render-demand';
import { withNpcObstacle, type NpcManifest } from '@/lib/npc-placement';
import { loadNpcGuide } from '@/lib/npc-scene';
import type {NpcAnimation, GuideGesture} from '@/lib/npc-animation';
import NpcConversation from './npc-conversation';

type ViewState = { x: number; z: number; yaw: number; place: string; detail: string; indoor: boolean };
type Engine = { start: () => void; pause: () => void; reset: () => void; overview: () => void; inspect: (id: string) => void; zoom: (scale: number) => void; key: (key: string, down: boolean) => void; travel: (point: Point, height?:number) => boolean; boatAction: (action:string,id?:string)=>void; railAction:(action:string,id?:string)=>void; npcGesture:(gesture:GuideGesture)=>void };

export default function Explorer() {
  const { touch, portrait, quality } = useScreenMode();
  const qualityRef = useRef(quality); qualityRef.current = quality;
  const portraitRef = useRef(portrait); portraitRef.current = portrait;
  const [attempt, setAttempt] = useState(0);
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
  const [guideOpen, setGuideOpen] = useState(false);
  const [npcOpen,setNpcOpen]=useState(false);
  const npcOpenRef=useRef(false);npcOpenRef.current=npcOpen;
  const [npcHud,setNpcHud]=useState<{name:string;near:boolean}|null>(null);
  const [loadStage, setLoadStage] = useState('지도를 준비하고 있습니다');
  const [loadPercent, setLoadPercent] = useState<number|undefined>(undefined);
  const [error, setError] = useState('');
  const [boatHud,setBoatHud] = useState<BoatHud|null>(null);
  const [railHud,setRailHud] = useState<RailHud|null>(null);
  const [destinationId, setDestinationId] = useState<DestinationId>('geumseonggwan');
  const destination = destinations[destinationId];
  const [view, setView] = useState<ViewState>({ x: 0, z: 0, yaw: 0, place: '금성관 주변', detail: '', indoor: false });
  const mapShapes=useMemo(()=>world?<PrecinctMapShapes world={world}/>:null,[world]);

  useEffect(() => {
    if (portrait) { engine.current?.pause(); engine.current?.npcGesture('Idle');setNpcOpen(false);setMapOpen(false); setGuideOpen(false); }
  }, [portrait]);
  useEffect(() => {
    window.dispatchEvent(new CustomEvent('naju:quality', { detail: quality }));
  }, [quality]);

  useEffect(() => {
    const selectedId = appDestinationFromSearch(window.location.search);
    setReady(false); setError(''); setActive(false); setStarted(false); setOverview(true);
    setBoatHud(null);setRailHud(null); setNpcHud(null);setNpcOpen(false);setWorld(null); setLoadStage('지도를 준비하고 있습니다');setLoadPercent(undefined);
    const selected = destinations[selectedId];
    const optimizedCampus=selectedId==='bitgaram-park'||selectedId==='bitgaram-kepco'||selectedId==='bitgaram-kentech'||selectedId==='naju-arboretum'||selectedId==='deudeulgang'||selectedId==='dasi';
    setDestinationId(selectedId);
    document.title = `나주 산책 — ${selected.name}`;
    const mount = host.current!;
    let disposed = false, renderer: THREE.WebGLRenderer | undefined, animation = 0;
    const abort=new AbortController();
    const demand=new RenderDemand();
    let contextLost=false, modelReady=false;
    const cleanups: (() => void)[] = [];
    const scene = new THREE.Scene();
    const setup = async () => {
      const response = await fetch(selected.worldUrl,{signal:abort.signal});
      if (!response.ok) throw new Error('도시 자료를 불러오지 못했습니다.');
      let data: World = await response.json();
      const npcResponse=await fetch('/npc-placements.json?v=terrain-v89',{signal:abort.signal,cache:'no-store'});
      if(!npcResponse.ok)throw new Error('지역 안내 캐릭터 자료를 불러오지 못했습니다.');
      const npcManifest:NpcManifest=await npcResponse.json();
      const npcPlacement=npcManifest.placements[selectedId];
      if(npcPlacement)data=withNpcObstacle(data,npcPlacement);
      if (disposed) return;
      setWorld(data);
      const panoramaRoom=data.viewMode==='panorama';
      if(panoramaRoom)setOverview(false);
      // Keep centimeter-separated landscape layers stable at city overview distances.
      renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance', logarithmicDepthBuffer: selectedId.startsWith('bitgaram') || selectedId==='deudeulgang' || selectedId==='dasi' || selectedId==='neureoji' });
      renderer.setPixelRatio(pixelRatioFor(qualityRef.current, window.devicePixelRatio));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFShadowMap;
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = data.lighting?.exposure??1.25;
      const canvas = renderer.domElement;
      canvas.setAttribute('aria-label', `${selected.area} 3D 탐험 화면. ${panoramaRoom?'화면을 끌어 창밖을 둘러볼 수 있습니다.':'화면을 끌어 시선을 움직이고, 전체 보기에서 확대·축소할 수 있습니다.'}`);
      canvas.tabIndex = 0;
      mount.appendChild(canvas);
      const lost=(event:Event)=>{
        event.preventDefault(); contextLost=true; engine.current?.pause(); setReady(false);
        setError('3D 화면이 잠시 중단됐습니다. 자동 복구를 기다리거나 출발 위치에서 다시 열 수 있습니다.');
      };
      const restored=()=>{
        contextLost=false; demand.invalidate(); renderer!.shadowMap.needsUpdate=true;
        if(modelReady){setError('');setReady(true);}
      };
      canvas.addEventListener('webglcontextlost',lost);canvas.addEventListener('webglcontextrestored',restored);
      cleanups.push(()=>{canvas.removeEventListener('webglcontextlost',lost);canvas.removeEventListener('webglcontextrestored',restored);});
      scene.background = new THREE.Color('#bbd9e6');
      scene.fog = new THREE.Fog('#bbd9e6', selectedId==='neureoji'?2500:selectedId !== 'geumseonggwan' ? 650 : 260, selectedId==='neureoji'?14500:selectedId !== 'geumseonggwan' ? 1350 : 690);
      // One small prefiltered daylight map gives the authored water and glazing
      // real sky reflections without fetching a panorama or rendering probes per frame.
      if(selectedId==='yeongsanpo'||selectedId==='neureoji'){
        const sky=new Sky();sky.scale.setScalar(900);
        sky.material.uniforms.turbidity.value=6;sky.material.uniforms.rayleigh.value=1.4;
        sky.material.uniforms.mieCoefficient.value=.004;sky.material.uniforms.mieDirectionalG.value=.75;
        sky.material.uniforms.sunPosition.value.set(-220,320,110);
        sky.material.uniforms.showSunDisc.value=false;
        const lightingSky=new THREE.Scene();lightingSky.add(sky);
        const pmrem=new THREE.PMREMGenerator(renderer);
        const daylight=pmrem.fromScene(lightingSky,.025,.1,1200,{size:128});
        scene.environment=daylight.texture;scene.environmentIntensity=.045;
        pmrem.dispose();sky.geometry.dispose();sky.material.dispose();
        cleanups.push(()=>{scene.environment=null;daylight.dispose();});
      }
      scene.add(new THREE.HemisphereLight('#e1f3ff', '#918673', data.lighting?.ambient??(data.verticalNavigation ? 1.5 : 2.8)));
      const sun = new THREE.DirectionalLight('#fff0d1', data.lighting?.sun??3.1);
      sun.position.set(-80, 145, 65); sun.castShadow = true;
      sun.shadow.mapSize.set(2048, 2048);
      sun.shadow.camera.left = sun.shadow.camera.bottom = -165;
      sun.shadow.camera.right = sun.shadow.camera.top = 165;
      sun.shadow.camera.far = 420; sun.shadow.normalBias = 0.06;
      if(selectedId==='neureoji'){
        sun.position.set(-150,(data.spawn.height??0)+175,85);
        sun.target.position.set(0,data.spawn.height??0,-40);scene.add(sun.target);
        sun.shadow.camera.left=sun.shadow.camera.bottom=-180;
        sun.shadow.camera.right=sun.shadow.camera.top=180;
        sun.shadow.normalBias=.025;
      }
      if(selectedId==='geumseonggwan'){
        sun.target.position.set(-10,0,-27);scene.add(sun.target);
        sun.shadow.camera.left=sun.shadow.camera.bottom=-115;
        sun.shadow.camera.right=sun.shadow.camera.top=115;
        sun.shadow.normalBias=.018;sun.shadow.bias=-.00006;
        sun.shadow.radius=2;
      }
      if(selectedId==='yeongsanpo'){
        sun.position.set(-250,320,210);sun.target.position.set(-30,0,100);scene.add(sun.target);
        sun.shadow.camera.left=sun.shadow.camera.bottom=-300;
        sun.shadow.camera.right=sun.shadow.camera.top=300;sun.shadow.camera.far=1000;
        sun.shadow.normalBias=.025;sun.shadow.bias=-.00005;
      }
      if(selectedId==='dasi'){
        sun.position.set(-110,185,90);sun.target.position.set(-15,0,4);scene.add(sun.target);
        sun.shadow.camera.left=sun.shadow.camera.bottom=-180;
        sun.shadow.camera.right=sun.shadow.camera.top=180;sun.shadow.camera.far=550;
        sun.shadow.normalBias=.025;sun.shadow.bias=-.00005;
      }
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
      const model=await fetchModelData(selected.modelUrl,{signal:abort.signal,onProgress:progress=>{
        if(disposed)return;
        if(progress.phase==='retry'){setLoadPercent(undefined);setLoadStage('연결을 다시 시도하고 있습니다');return;}
        if(progress.phase==='unpack'){setLoadPercent(undefined);setLoadStage('모델 압축을 풀고 있습니다');return;}
        const mb=(bytes:number)=>(bytes/1_000_000).toFixed(1);
        setLoadPercent(progress.total?Math.min(100,Math.round(progress.received/progress.total*100)):undefined);
        setLoadStage(`건물·산책로 다운로드 · ${mb(progress.received)}${progress.total?` / ${mb(progress.total)}`:''} MB`);
      }});
      if(disposed)return;
      setLoadStage('건물과 산책로를 배치하고 있습니다');
      const gltf=await loader.parseAsync(model,'');
      if (disposed) { gltf.scene.traverse(disposeObject); return; }
      gltf.scene.traverse(o => { if (o instanceof THREE.Mesh) {
        const landscape=selectedId.startsWith('bitgaram')&&/^(context_ground|lake_osm_|estimated_hill|surrounding_park_lawn|mapped_park_lawn_shore|surrounding_mapped_paths|surrounding_parking|surrounding_recreation)/.test(o.name);
        const riverSurface=selectedId==='deudeulgang'&&/^(path_|road_|mapped_river_water|water_glint|pine_litter_patch|understory_moss|crop_row|satellite_field)/.test(o.name);
        // A Blender object with several materials becomes a group of primitives in glTF.
        // Its authored shadow flags belong to that group and apply to every primitive.
        let noShadow=false,noReceiveShadow=false;
        for(let authored:THREE.Object3D|null=o;authored;authored=authored.parent){
          noShadow ||= !!authored.userData.no_shadow;
          noReceiveShadow ||= !!authored.userData.no_receive_shadow;
          if(authored===gltf.scene)break;
        }
        o.castShadow = !o.name.startsWith('ground')&&!landscape&&!riverSurface&&!noShadow;
        o.receiveShadow = !noReceiveShadow && !(landscape && o.name!=='estimated_hill');
        if(o.userData.photo_panorama || o.userData.sky_backdrop){
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
      setLoadStage('산책 화면을 정리하고 있습니다');
      try {
        await batchStaticSceneInSlices(gltf.scene,{signal:abort.signal,onProgress:(done,total)=>setLoadStage(`산책 화면을 정리하고 있습니다${total?` · ${Math.round(done/total*100)}%`:''}`)});
      } catch(error) {gltf.scene.traverse(disposeObject);throw error;}
      if(disposed){gltf.scene.traverse(disposeObject);return;}
      const roofParts: THREE.Object3D[]=[];
      gltf.scene.traverse(o=>{if(o.userData.hide_in_overview)roofParts.push(o);});
      scene.add(gltf.scene);
      let npc:NpcAnimation|undefined;
      if(npcPlacement){
        setLoadStage(`${npcManifest.assets[npcPlacement.character].name} 안내 캐릭터를 준비하고 있습니다`);
        npc=await loadNpcGuide(npcPlacement,npcManifest,abort.signal);
        scene.add(npc.root);cleanups.push(()=>npc?.dispose());
        if(disposed){scene.traverse(disposeObject);return;}
        const motion=matchMedia('(prefers-reduced-motion: reduce)');
        const motionChanged=()=>{if(npc)npc.reducedMotion=motion.matches;demand.invalidate();};
        motionChanged();motion.addEventListener('change',motionChanged);
        cleanups.push(()=>motion.removeEventListener('change',motionChanged));
        setNpcHud({name:npcManifest.assets[npcPlacement.character].name,near:false});
      }
      if(optimizedCampus){
        gltf.scene.traverse(o=>{o.updateMatrix();o.matrixAutoUpdate=false;});
        renderer.shadowMap.autoUpdate=false;
        renderer.shadowMap.needsUpdate=true;
      }
      const fleet=new BoatFleet(data);
      await fleet.load(scene);
      const rail=data.monorail?new MonorailScene(data.monorail):undefined;
      if(rail)await rail.load(scene,abort.signal);
      if(disposed){scene.traverse(disposeObject);return;}
      const camera = new THREE.PerspectiveCamera(60, 1, 0.12, selectedId==='neureoji'?24000:selectedId !== 'geumseonggwan' ? 1800 : 1000);
      const colliders = data.solids.filter(s => s.collision).map(solidCollider);
      const floors = worldFloors(data.solids);
      const obstacles=data.verticalNavigation?worldObstacles(data.solids):[];
      const arrival=sceneArrival(data,window.location.search);
      let px = arrival.x, pz = arrival.z, yaw = arrival.yaw, pitch = 'pitch' in arrival ? (arrival.pitch??0) : 0;
      let elevation=reachableFloor(px,pz,arrival.height??0,floors)??0;
      let playing = false, bird = !panoramaRoom;
      const gesture = new ViewGesture();
      let orbit: number = selected.overview.angle, orbitElevation: number = selected.overview.elevation, orbitRadius: number = selected.overview.radius;
      let inspectingCeiling = false;
      let inspectingArchitecture = false;
      const center = new THREE.Vector3(selected.overview.center[0], selectedId==='neureoji'?(data.spawn.height??0)+7:0, selected.overview.center[1]);
      const keys = new Set<string>();
      const resize = () => {
        if (!renderer) return;
        camera.aspect = mount.clientWidth / mount.clientHeight; camera.updateProjectionMatrix();
        renderer.setSize(mount.clientWidth, mount.clientHeight);
        demand.invalidate();
      };
      resize();
      const observer = new ResizeObserver(resize); observer.observe(mount);
      cleanups.push(() => observer.disconnect());
      const listen = (target: EventTarget, name: string, fn: EventListener, options?: AddEventListenerOptions) => {
        target.addEventListener(name, fn, options); cleanups.push(() => target.removeEventListener(name, fn, options));
      };
      const pause = () => {
        fleet.stop();
        playing = false; keys.clear(); gesture.clear(); setActive(false);
        demand.invalidate();
        if (document.pointerLockElement === canvas) document.exitPointerLock();
      };
      const start = () => {
        if(contextLost)return;
        if (matchMedia('(orientation: portrait)').matches && (matchMedia('(any-pointer: coarse)').matches || navigator.maxTouchPoints > 0)) return;
        playing = true; bird = false; setActive(true); setStarted(true); setOverview(false);
        inspectingCeiling=false;inspectingArchitecture=false;
        camera.fov=60;camera.updateProjectionMatrix();
        demand.invalidate();
        canvas.focus({ preventScroll: true });
        // Drag-look keeps the map, pause and settings buttons reachable while walking.
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
      const railAction=(action:string,id?:string)=>{
        if(!rail)return;
        keys.clear();
        if(action==='station'&&id){
          if(rail.state.aboard)return;
          const station=rail.definition.stations.find(s=>s.id===id);
          if(station)engine.current?.travel(station.arrival,station.height);
        }else if(action==='call'&&id){
          if(rail.hud([px,pz],elevation).near===id&&!rail.state.aboard)rail.request(id);
        }else if(action==='board'){
          if(rail.board([px,pz],elevation)){
            const p=rail.eye()!;px=p.x;pz=p.z;elevation=p.height;
            yaw=(rail.root?.rotation.y??0)+(rail.state.station==='upper'?Math.PI:0);pitch=0;
          }
        }else if(action==='depart'&&id&&rail.state.aboard)rail.request(id);
        else if(action==='leave'){
          const station=rail.leave();if(station){px=station.arrival[0];pz=station.arrival[1];elevation=station.height;pitch=0;}
        }
        setRailHud(rail.hud([px,pz],elevation));start();
      };
      engine.current = {
        start, pause, boatAction,railAction,
        npcGesture:(gesture)=>{npc?.setGesture(gesture);demand.invalidate();},
        reset: () => { npc?.setGesture('Idle');setNpcOpen(false);fleet.reset();rail?.reset();if(rail)setRailHud(rail.hud([data.spawn.x,data.spawn.z],data.spawn.height??0));px = data.spawn.x; pz = data.spawn.z; elevation=reachableFloor(px,pz,data.spawn.height??0,floors)??0; yaw = data.spawn.yaw; pitch = 0; start(); },
        overview: () => {
          if(panoramaRoom){start();return;}
          pause();npc?.setGesture('Idle');setNpcOpen(false);bird=true;setOverview(true);
          inspectingCeiling=false;inspectingArchitecture=false;
          center.set(selected.overview.center[0],selectedId==='neureoji'?(data.spawn.height??0)+7:0,selected.overview.center[1]);
          orbit=selected.overview.angle;orbitElevation=selected.overview.elevation;orbitRadius=selected.overview.radius;demand.invalidate();
          camera.fov=60;camera.updateProjectionMatrix();
        },
        inspect: (id) => {
          const view=data.architectureViews?.find(v=>v.id===id);if(!view)return;
          pause();npc?.setGesture('Idle');setNpcOpen(false);bird=true;setOverview(true);
          inspectingCeiling=view.id==='ceiling';inspectingArchitecture=true;
          center.fromArray(view.center);orbit=view.angle;orbitElevation=view.elevation;orbitRadius=view.radius;demand.invalidate();
          camera.fov=view.fov??60;camera.updateProjectionMatrix();
        },
        zoom: (scale) => { orbitRadius = THREE.MathUtils.clamp(orbitRadius * scale, inspectingCeiling?3:inspectingArchitecture?6:selectedId==='geumseonggwan'?10:selectedId==='neureoji'?12:'parent' in selected ? 12 : 85, inspectingCeiling?6:selectedId==='neureoji'?150:selectedId !== 'geumseonggwan' ? 1100 : 260); demand.invalidate(); },
        key: (key, down) => { if (down) keys.add(key); else keys.delete(key); },
        travel: (point,height=0) => {
          if(rail?.state.aboard)return false;
          if(!canTravelTo(point,data,height))return false;
          fleet.leaveForTravel();
          px=point[0];pz=point[1];pitch=0;keys.clear();
          elevation=reachableFloor(px,pz,height,floors)??0;
          const arrival=data.places.find(p=>p.arrival && Math.hypot(p.arrival[0]-px,p.arrival[1]-pz)<.1);
          if(arrival?.arrivalYaw!==undefined)yaw=arrival.arrivalYaw;
          else if(arrival && Math.hypot(arrival.position[0]-px,arrival.position[1]-pz)>1)yaw=Math.atan2(px-arrival.position[0],pz-arrival.position[1]);
          if(arrival?.arrivalPitch!==undefined)pitch=arrival.arrivalPitch;
          start();
          return true;
        },
      };
      listen(window, 'naju:pause', pause);
      listen(window, 'naju:quality', ((event: CustomEvent<GraphicsQuality>) => {
        if (!renderer) return;
        renderer.setPixelRatio(pixelRatioFor(event.detail, window.devicePixelRatio));
        resize();
      }) as EventListener);
      const frameIntervals:number[]=[];
      const renderDiagnostics=()=>{
        const sorted=[...frameIntervals].sort((a,b)=>a-b);
        return {sampleFrames:sorted.length,meanIntervalMs:sorted.length?frameIntervals.reduce((a,b)=>a+b,0)/sorted.length:null,p95IntervalMs:sorted.length?sorted[Math.ceil(sorted.length*.95)-1]:null,renderedFrames:renderer?.info.render.frame,drawCalls:renderer?.info.render.calls,triangles:renderer?.info.render.triangles,pixelRatio:renderer?.getPixelRatio(),quality:qualityRef.current,contextLost,landscapeBlocked:portraitRef.current,scope:'Recent visible walking frame intervals in this browser; not a GPU-only measurement or hardware certification.'};
      };
      const context = (document as Document & { modelContext?: { registerTool: (tool: { name: string; description: string; inputSchema: object; annotations: object; execute: (input: unknown) => unknown }, options: { signal: AbortSignal }) => void | Promise<void> } }).modelContext;
      if (context?.registerTool) {
        const lifecycle = new AbortController();
        cleanups.push(() => lifecycle.abort());
        const state = () => ({ destination: selected.name, mode: bird ? 'overview' : playing ? 'walking' : 'paused', position: { x: px, z: pz },monorail:rail?.hud([px,pz],elevation)??null, guide:npcPlacement?{character:npcPlacement.character,name:npcManifest.assets[npcPlacement.character].name,position:npcPlacement.position,modelUrl:npcManifest.assets[npcPlacement.character].modelUrl,gesture:npc?.gesture}:null, source: data.source,renderDiagnostics:renderDiagnostics() });
        const registrations = [
          { name: 'get_naju_walk_state', description: 'Read the current Naju exploration view and position.', inputSchema: { type: 'object', properties: {}, additionalProperties: false }, annotations: { readOnlyHint: true }, execute: () => state() },
          { name: 'set_naju_walk_view', description: 'Switch the same exploration view as the visible overview, walk, or pause controls.', inputSchema: { type: 'object', properties: { view: { type: 'string', enum: panoramaRoom?['walk', 'pause']:['overview', 'walk', 'pause'] } }, required: ['view'], additionalProperties: false }, annotations: { readOnlyHint: false }, execute: async (input: unknown) => {
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
        if (e.code === 'Escape') { pause(); return; }
        if (e.target instanceof HTMLElement && e.target.closest('button,a,input,textarea,select,[contenteditable="true"]')) return;
        if (!playing) return;
        if(e.code==='KeyF'&&!e.repeat){e.preventDefault();const hud=fleet.hud([px,pz],elevation);if(hud.mode==='helm')boatAction('deck');else if(hud.aboard)boatAction('helm');else if(hud.near)boatAction('board',hud.near);return;}
        if (['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','KeyQ','KeyE','ShiftLeft','ShiftRight','Space'].includes(e.code)) { e.preventDefault(); keys.add(e.code); }
      }) as EventListener);
      listen(window, 'keyup', ((e: KeyboardEvent) => { keys.delete(e.code); }) as EventListener);
      listen(window, 'blur', pause);
      listen(document, 'visibilitychange', () => { if (document.hidden) pause(); });
      listen(document, 'pointerlockchange', () => { if (document.pointerLockElement !== canvas && playing) pause(); });
      listen(canvas, 'pointerdown', ((e: PointerEvent) => {
        if (!bird && !playing) return;
        if (e.button !== 0 && e.pointerType === 'mouse') return;
        gesture.down(e.pointerId, e.clientX, e.clientY);
        if (document.pointerLockElement !== canvas) canvas.setPointerCapture(e.pointerId);
      }) as EventListener);
      const release = ((e: PointerEvent) => gesture.up(e.pointerId)) as EventListener;
      listen(window, 'pointerup', release);
      listen(canvas, 'pointercancel', release);
      listen(canvas, 'lostpointercapture', release);
      listen(window, 'pointermove', ((e: PointerEvent) => {
        const locked = document.pointerLockElement === canvas;
        const delta = locked ? { dx: e.movementX, dy: e.movementY, scale: 1 } : gesture.move(e.pointerId, e.clientX, e.clientY, bird);
        if (!delta) return;
        const { dx, dy, scale } = delta;
        if (bird && scale !== 1) { engine.current?.zoom(scale); return; }
        if (bird) { orbit -= dx * 0.005; orbitElevation = THREE.MathUtils.clamp(orbitElevation + dy * 0.003, inspectingCeiling?-1.3:inspectingArchitecture?-.1:center.y>0?-.1:.3, inspectingCeiling?-.25:1.3); }
        else if (playing) { yaw -= dx * 0.0028; pitch = THREE.MathUtils.clamp(pitch - dy * 0.0028, -1.15, 1.15); }
        demand.invalidate();
      }) as EventListener);
      listen(canvas, 'wheel', ((e: WheelEvent) => { if (bird) { e.preventDefault(); engine.current?.zoom(Math.exp(e.deltaY * .001)); } }) as EventListener, { passive: false });
      modelReady=true;setReady(!contextLost);if(!contextLost)setError('');
      // A panorama is authored for an interior eye point, including direct links without an arrival.
      if(panoramaRoom || selectedId==='neureoji'&&arrival.entered){setStarted(true);start();}
      else if(arrival.entered)start();
      let changingScene=false;
      let last = performance.now(), lastHud = 0, lastLightUpdate=-Infinity;
      let shadowBird: boolean|undefined;
      const frame = (now: number) => {
        if (disposed || !renderer) return;
        animation = requestAnimationFrame(frame);
        const interval=now-last;
        if(playing&&!document.hidden&&interval>0&&interval<250){frameIntervals.push(interval);if(frameIntervals.length>120)frameIntervals.shift();}
        else frameIntervals.length=0;
        const dt = Math.min(interval / 1000, 0.06); last = now;
        const npcMoving=!!npc&&!bird&&!npc.reducedMotion&&(playing||npcOpenRef.current)&&npc.root.position.distanceTo(new THREE.Vector3(px,elevation,pz))<18;
        if(!demand.take(playing||npcMoving,document.hidden||portraitRef.current||contextLost))return;
        if(npcMoving)npc?.update(dt);
        if (playing) {
          const forward = Number(keys.has('KeyW') || keys.has('ArrowUp')) - Number(keys.has('KeyS') || keys.has('ArrowDown'));
          const side = Number(keys.has('KeyD')) - Number(keys.has('KeyA'));
          yaw += (Number(keys.has('KeyQ') || (!fleet.passenger?.helm&&keys.has('ArrowLeft'))) - Number(keys.has('KeyE') || (!fleet.passenger?.helm&&keys.has('ArrowRight')))) * dt * 1.6;
          const len = Math.hypot(forward, side) || 1;
          const speed = (keys.has('ShiftLeft') || keys.has('ShiftRight') ? 9 : 4.5) * dt / len;
          const dx=(-Math.sin(yaw) * forward + Math.cos(yaw) * side) * speed, dz=(-Math.cos(yaw) * forward - Math.sin(yaw) * side) * speed;
          const railPassenger=rail?.update(dt);
          const passenger=railPassenger?{...railPassenger,yawDelta:0}:fleet.update(dt,keys,yaw);
          if(passenger){px=passenger.x;pz=passenger.z;elevation=passenger.height;yaw+=passenger.yawDelta;}
          else{
            const next=data.verticalNavigation?moveOnFloors(px,pz,elevation,dx,dz,rail?[...obstacles,rail.obstacle()]:obstacles,floors,data.bounds,data.requireFloor):movePlayer(px,pz,dx,dz,colliders,data.bounds);
            px = next.x; pz = next.z;
            if('height' in next)elevation=next.height as number;
          }
          if(!fleet.passenger && !rail?.state.aboard && !changingScene && (forward || side)){
            const portal=portalAt(data,px,pz,elevation),href=portal&&portalHref(portal);
            if(href){changingScene=true;keys.clear();playing=false;window.location.assign(href);}
          }
        }
        roofParts.forEach(o=>{o.visible=!bird;});
        if (bird) {
          camera.position.set(center.x + Math.sin(orbit) * Math.cos(orbitElevation) * orbitRadius, center.y + Math.sin(orbitElevation) * orbitRadius, center.z + Math.cos(orbit) * Math.cos(orbitElevation) * orbitRadius); camera.lookAt(center);
        } else { camera.position.set(px, 1.72 + (data.verticalNavigation?elevation:floorHeight(px, pz, floors)), pz); camera.rotation.order = 'YXZ'; camera.rotation.set(pitch, yaw, 0); }
        if(localLights && now-lastLightUpdate>150){localLights.update(camera.position);lastLightUpdate=now;}
        if(updateVegetationDetail(gltf.scene,camera.position))renderer.shadowMap.needsUpdate=true;
        if(optimizedCampus && shadowBird!==bird){renderer.shadowMap.needsUpdate=true;shadowBird=bird;}
        if (now - lastHud > 180) {
          if(npc&&npcPlacement){
            const near=!bird&&!fleet.passenger&&!rail?.state.aboard&&Math.hypot(px-npcPlacement.position[0],pz-npcPlacement.position[2])<6&&Math.abs(elevation-npcPlacement.position[1])<2;
            if(!near&&npcOpenRef.current){npc.setGesture('Idle');setNpcOpen(false);}
            setNpcHud(current=>current?.near===near?current:{name:npcManifest.assets[npcPlacement.character].name,near});
          }
          const hud=fleet.hud([px,pz],elevation);if(fleet.vessels.length)setBoatHud(hud);
          if(rail)setRailHud(rail.hud([px,pz],elevation));
          const place = currentPlace(px, pz, data.places, data.verticalNavigation?elevation:undefined);
          const doorway=data.portals?.find(p=>Math.hypot(p.position[0]-px,p.position[1]-pz)<4 && Math.abs((p.height??0)-elevation)<.6);
          const nextView={ x: px, z: pz, yaw, place: fleet.passenger?.vessel.definition.name ?? place?.name ?? selected.area, detail: hud.aboard?(hud.mode==='helm'?'방향 버튼으로 조종 · 제동 버튼으로 정지':'갑판과 객실을 걸어서 둘러보세요.'):doorway?doorway.label:place?.description ?? '', indoor: !!hud.aboard || (place?.indoor ?? place?.id === 'interior') };
          setView(current=>current.x===nextView.x&&current.z===nextView.z&&current.yaw===nextView.yaw&&current.place===nextView.place&&current.detail===nextView.detail&&current.indoor===nextView.indoor?current:nextView); lastHud = now;
        }
        renderer.render(scene, camera);
      };
      animation = requestAnimationFrame(frame);
    };
    function disposeObject(o: THREE.Object3D) {
      if (!(o instanceof THREE.Mesh)) return;
      o.geometry?.dispose(); const mats = Array.isArray(o.material) ? o.material : [o.material];
      mats.forEach(m => { Object.values(m).forEach(v => { if (v instanceof THREE.Texture) v.dispose(); }); m.dispose(); });
    }
    setup().catch(e => { if (!disposed) {setReady(false);setError(e instanceof Error ? e.message : '3D 화면을 열 수 없습니다.');} });
    return () => {
      disposed = true; abort.abort(); cancelAnimationFrame(animation); cleanups.forEach(fn => fn());
      if (document.pointerLockElement === renderer?.domElement) document.exitPointerLock();
      scene.traverse(disposeObject); renderer?.dispose(); renderer?.domElement.remove(); engine.current = null;
    };
  }, [attempt]);

  const press = (key: string) => ({
    onPointerDown: (e: React.PointerEvent<HTMLButtonElement>) => { e.preventDefault(); e.currentTarget.setPointerCapture(e.pointerId); engine.current?.key(key, true); },
    onPointerUp: () => engine.current?.key(key, false), onPointerCancel: () => engine.current?.key(key, false), onLostPointerCapture: () => engine.current?.key(key, false),
  });
  const openMap=()=>{engine.current?.pause();engine.current?.npcGesture('Idle');setNpcOpen(false);setMapOpen(true);};
  const openGuide = () => { setNpcOpen(false); engine.current?.npcGesture('Idle'); engine.current?.pause(); setGuideOpen(true); };
  return (
    <main className="explorer">
      <div className="scene" ref={host} /><div className="vignette" />
      <header className="topbar">
        <div className="brand"><span className="brand-mark"><Compass size={25} strokeWidth={1.4} /></span><div><strong>나주 산책</strong><span>{destination.area}</span></div></div>
        <div className="topbar-tools"><div className="view-actions" role="group" aria-label="보기 방식">{world?.viewMode!=='panorama'&&<button aria-pressed={overview} className={overview ? 'active' : ''} onClick={() => engine.current?.overview()} disabled={!ready || !!error}><MoveUpRight size={16} />전체 보기</button>}<button aria-pressed={!overview} className={!overview ? 'active' : ''} onClick={() => boatHud?.aboard?engine.current?.boatAction('deck'):engine.current?.start()} disabled={!ready || !!error}><Footprints size={16} />걷기</button></div><button className="screen-button" onClick={openGuide} aria-label="산책 안내와 화면 설정" title="산책 안내와 화면 설정"><CircleHelp size={19}/></button><FullscreenButton/></div>
      </header>
      <nav className="destination-nav" aria-label="나주 전체 지도와 장소 선택">
        <button onClick={openMap}><Map size={18}/><span>나주 전체 · 장소 선택</span></button>
      </nav>
      {active && !railHud?.aboard && !!world?.sceneLinks?.length && <nav className="scene-signposts" aria-label="장소 이동 푯말">{world.sceneLinks.filter(link=>Object.hasOwn(destinations,link.target)).map(link=><a key={link.target} href={`/?place=${encodeURIComponent(link.target)}`}><MapPin size={18}/><span>{link.label}</span><ArrowUpRight size={16}/></a>)}</nav>}
      {world && !minimapExpanded && <button className="minimap-toggle" aria-expanded={false} aria-controls="location-minimap" onClick={()=>setMinimapExpanded(true)}><Map size={17}/>미니맵 펼치기</button>}
      {world && minimapExpanded && <aside id="location-minimap" className="minimap" aria-label="현재 위치 지도">
        <div className="map-heading"><span>{destination.name}</span><button className="panel-fold" aria-expanded={true} aria-controls="location-minimap" onClick={()=>setMinimapExpanded(false)}>접기 −</button></div>
        <svg viewBox={`${world.bounds[0]} ${world.bounds[2]} ${world.bounds[1] - world.bounds[0]} ${world.bounds[3] - world.bounds[2]}`} role="img" aria-label={`현재 위치: ${view.place}`} onClick={openMap}>
          <rect x={world.bounds[0]} y={world.bounds[2]} width={world.bounds[1] - world.bounds[0]} height={world.bounds[3] - world.bounds[2]} fill="#e5e8df" />
          {mapShapes}
          {boatHud?.boats.map(b=><g key={b.id} transform={`translate(${b.x} ${b.z}) rotate(${-b.yaw*180/Math.PI})`}><path d="M 0,-13 L 4,-7 L 4,11 L -4,11 L -4,-7 Z" fill={boatHud.aboard===b.id?'#d27c32':'#664d33'} stroke="#fff" strokeWidth="1.6"/></g>)}
          <g transform={`translate(${view.x} ${view.z}) scale(${(world.bounds[1]-world.bounds[0])/245})`}>
            <circle r="6" fill="#fff" /><circle r="3.5" fill="#c96734" />
            <path d="M 0,-11 L -3,-6 L 3,-6 Z" fill="#c96734" transform={`rotate(${-view.yaw * 180 / Math.PI})`} />
          </g>
        </svg><div className="map-legend"><span className="you-dot" />내 위치<span>약 {Math.round((world.bounds[1] - world.bounds[0]) / 10) * 10}m 구역</span></div>
        <button className="minimap-travel" onClick={openMap}>지도 열고 이동하기 <ArrowUpRight size={14}/></button>
      </aside>}
      {overview && ready && !error && <div className="overview-zoom" role="group" aria-label="전체 보기 확대 축소"><button aria-label="확대" onClick={() => engine.current?.zoom(.8)}><Plus size={19}/></button><button aria-label="축소" onClick={() => engine.current?.zoom(1.25)}><Minus size={19}/></button></div>}
      {!active && !npcOpen && !boatHud?.aboard && !railHud?.aboard && !error && <section className={`welcome${welcomeExpanded?'':' welcome-compact'}`} aria-label="산책 시작">
        <button className="welcome-fold panel-fold" aria-expanded={welcomeExpanded} aria-controls="walk-introduction" onClick={()=>setWelcomeExpanded(v=>!v)}>{welcomeExpanded?'안내 접기 −':'이용 안내 +'}</button>
        {welcomeExpanded && <div id="walk-introduction"><div className="eyebrow"><span />나주 · {destination.name}</div>
        <h1>{started ? '산책을 잠시 멈췄습니다' : destination.name}</h1>
        <p>{started ? '같은 위치에서 이어서 걸을 수 있습니다.' : destination.introduction[0]}</p></div>}
        {overview && ready && !!world?.architectureViews?.length && <div className="architecture-views" role="group" aria-label="건축 자세히 보기">{world.architectureViews.map(v=><button key={v.id} onClick={()=>engine.current?.inspect(v.id)}>{v.label}</button>)}</div>}
        {ready&&world?.monorail&&<div className="architecture-views" role="group" aria-label="모노레일 승강장으로 이동">{world.monorail.stations.map(s=><button key={s.id} onClick={()=>engine.current?.railAction('station',s.id)}>{s.id==='lower'?'모노레일 하부':'모노레일 상부'}</button>)}</div>}
        <button className="start-button" onClick={() => engine.current?.start()} disabled={!ready || !!error}><Footprints size={20} /><span>{error ? '화면을 열 수 없습니다' : !ready ? '산책 준비 중…' : started ? '이어서 걷기' : '산책 시작'}</span><ArrowUpRight size={21} /></button>
        {!ready && !error && <><div className="load-status" role="status">{loadPercent===undefined?<span className="loading-line"/>:<progress aria-label="3D 모델 다운로드" value={loadPercent} max={100}/>}<span>{loadStage}</span></div><button className="loading-retry" onClick={()=>setAttempt(value=>value+1)}>멈췄다면 다시 불러오기</button></>}
        {welcomeExpanded && <div className="welcome-help">{touch ? '왼쪽 버튼으로 이동 · 화면을 드래그해 둘러보기' : <><span><kbd>W A S D</kbd> 이동</span><span>드래그로 둘러보기</span></>}</div>}
      </section>}
      {error&&<section className="scene-recovery" role="alert" aria-label="3D 화면 복구"><strong>화면을 다시 열어 주세요</strong><p>{error}</p><button onClick={()=>setAttempt(value=>value+1)}>출발 위치에서 다시 불러오기</button></section>}
      {npcHud?.near&&!npcOpen&&!mapOpen&&!guideOpen&&<button className="npc-talk-button" onClick={()=>{engine.current?.pause();engine.current?.npcGesture('Greeting');setNpcOpen(true);}}><MessageCircle size={19}/>{npcHud.name}와 이야기</button>}
      {npcOpen&&npcHud&&<NpcConversation name={npcHud.name} destinationId={destinationId} onGesture={gesture=>engine.current?.npcGesture(gesture)} onClose={()=>{setNpcOpen(false);engine.current?.start();}}/>}
      {active && <><div className="crosshair" aria-hidden="true" />{!boatHud?.aboard&&!railHud?.aboard&&!railHud?.near&&<div className="place-card"><span className="place-icon"><MapPin size={18} /></span><div><span>{view.indoor ? '실내' : '현재 위치'}</span><strong>{view.place}</strong>{view.detail&&<p>{view.detail}</p>}</div></div>}
        {!railHud?.aboard&&<div className="touch-controls" aria-label="이동 버튼"><span className="touch-label">{boatHud?.mode==='helm'?'조종':'이동'}</span><button aria-label="앞으로" {...press('KeyW')}><ArrowUp /></button><div><button aria-label="왼쪽으로" {...press('KeyA')}><ArrowLeft /></button><button aria-label="뒤로" {...press('KeyS')}><ArrowDown /></button><button aria-label="오른쪽으로" {...press('KeyD')}><ArrowRight /></button></div></div>}<div className="turn-controls" aria-label="시선 버튼"><span className="touch-label">시선</span><div><button aria-label="왼쪽 보기" {...press('KeyQ')}>↶</button><button aria-label="오른쪽 보기" {...press('KeyE')}>↷</button></div></div></>}
      {railHud&&(railHud.near||railHud.aboard)&&!overview&&!mapOpen&&<aside className="monorail-panel" aria-label="모노레일 탑승과 운행">
        <strong>{railHud.aboard?'빛가람 모노레일':railHud.stations.find(s=>s.id===railHud.near)?.name}</strong>
        <p>{!active&&railHud.target?'운행을 잠시 멈췄습니다':railHud.target?`${railHud.stations.find(s=>s.id===railHud.target)?.name}으로 ${railHud.speed>0?'운행 중':'출발 준비 중'}`:railHud.door<.98?'문을 열고 있습니다':railHud.station===railHud.near||railHud.aboard?'정차 중 · 탑승문이 열렸습니다':'다른 승강장에 정차 중입니다'}</p>
        {railHud.aboard&&<progress aria-label="모노레일 위치" max={1} value={railHud.progress}/>}
        <div className="boat-actions">
          {!active&&<button onClick={()=>engine.current?.start()}>운행 이어가기</button>}
          {railHud.aboard?railHud.target?<button onClick={()=>engine.current?.pause()} disabled={!active}>운행 잠시 멈추기</button>:<><button disabled={railHud.door<.98} onClick={()=>engine.current?.railAction('depart',railHud.stations.find(s=>s.id!==railHud.station)?.id)}>{railHud.station==='lower'?'전망대로 올라가기':'전시동으로 내려가기'}</button><button disabled={railHud.door<.98} onClick={()=>engine.current?.railAction('leave')}>승강장에 내리기</button></>:railHud.station===railHud.near?<button disabled={railHud.door<.98} onClick={()=>engine.current?.railAction('board')}>모노레일 탑승</button>:<button disabled={!!railHud.target} onClick={()=>engine.current?.railAction('call',railHud.near??undefined)}>모노레일 호출</button>}
        </div><small>화면을 드래그해 창밖을 둘러보세요.</small>
      </aside>}
      {boatHud&&(active||!!boatHud.aboard)&&!mapOpen&&<aside className={`boat-panel ${boatHud.aboard?'aboard':'at-shore'}`} aria-label="황포돛배 승선과 조종">
        <div className="boat-panel-title"><span>{boatHud.aboard?view.place:'영산강 황포돛배'}</span>{boatHud.aboard&&<strong>{boatHud.speed.toFixed(1)} <small>km/h</small></strong>}</div>
        {boatHud.aboard?<>
          <p>{boatHud.departing?'선착장을 벗어나면 직접 조종할 수 있습니다.':boatHud.mode==='helm'?(touch?'왼쪽 버튼으로 전진·후진·방향 조종':'W 전진 · S 후진 · A D 방향 · Space 제동'):'갑판과 객실을 걸어볼 수 있습니다.'}</p>
          <p className="boat-mouse-help">{active?(touch?'화면을 드래그해 둘러보기':'화면을 드래그해 둘러보기 · Esc 일시정지'):'배가 정지했습니다. 이어서 탐험할 수 있습니다.'}</p>
          {boatHud.blocked&&<p role="status">강가 또는 다른 배에 가까워 멈췄어요. 반대 방향으로 이동해 주세요.</p>}
          <div className="boat-actions">{!active&&<button onClick={()=>engine.current?.start()}>이어서 탐험</button>}<button onClick={()=>engine.current?.boatAction(boatHud.mode==='helm'?'deck':'helm')}>{boatHud.mode==='helm'?'갑판 둘러보기':touch?'운전석으로':'운전석으로 · F'}</button>{boatHud.mode==='helm'&&active&&<button {...press('Space')}>제동</button>}{boatHud.canLeave?<button onClick={()=>engine.current?.boatAction('leave')}>선착장에 내리기</button>:<button onClick={()=>engine.current?.boatAction('dock')}>선착장으로 복귀</button>}</div>
          <small className="boat-dimension">{boatHud.boats.find(b=>b.id===boatHud.aboard)?.note}</small>
        </>:<><p>{boatHud.near?'배를 선택하면 승선합니다.':'배를 선택하면 선착장으로 이동합니다.'}</p><div className="boat-actions">{boatHud.boats.map(b=><button key={b.id} onClick={()=>engine.current?.boatAction('board',b.id)}>{b.name} {boatHud.near===b.id?'승선':'선착장'}</button>)}</div></>}
      </aside>}
      <footer className="bottom-bar"><div className="keyboard-guide"><span><kbd>W A S D</kbd> 이동</span><span><kbd>← →</kbd> 시선 회전</span><span><kbd>Shift</kbd> 빠르게</span><span><kbd>Esc</kbd> 쉬기</span></div><div className="bottom-actions"><button onClick={() => engine.current?.reset()} disabled={!ready} aria-label="출발 위치로 돌아가기"><RotateCcw size={16} />처음 위치</button>{active && <button onClick={() => engine.current?.pause()}><Pause size={16} />쉬기</button>}</div></footer>
      <div className="source-note"><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap 기여자 · ODbL</a><button onClick={openGuide}>자료·제작 정보</button></div>
      {mapOpen&&<MapTravel destinationId={destinationId} world={world} position={[view.x,view.z]} onClose={()=>setMapOpen(false)} onTravel={(point,height)=>engine.current?.travel(point,height)??false}/>}
      {guideOpen&&<WalkGuide destinationId={destinationId} onClose={()=>setGuideOpen(false)}/>}
    </main>
  );
}
