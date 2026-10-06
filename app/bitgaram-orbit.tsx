'use client';
import {useEffect,useRef,useState} from 'react';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {batchStaticSceneInSlices} from '@/lib/static-scene';
import {unpackModel} from '@/lib/model-transport';
import { Plus, Minus, RotateCcw } from 'lucide-react';
import { useScreenMode } from './screen-mode';
import { pixelRatioFor, type GraphicsQuality } from '@/lib/display-mode';
import { RenderDemand } from '@/lib/render-demand';

type Pin={id:string;label:string;position:[number,number,number]};
export default function BitgaramOrbit(){
  const host=useRef<HTMLDivElement>(null),reset=useRef<()=>void>(()=>{}),zoom=useRef<(scale:number)=>void>(()=>{});
  const { quality,portrait }=useScreenMode(); const qualityRef=useRef(quality);qualityRef.current=quality;
  const portraitRef=useRef(portrait);portraitRef.current=portrait;
  const [pins,setPins]=useState<Pin[]>([]),[status,setStatus]=useState('3D 지도를 불러오는 중…');
  const [failed,setFailed]=useState(false),[attempt,setAttempt]=useState(0);
  const [contextUnavailable,setContextUnavailable]=useState(false);
  const links=useRef(new Map<string,HTMLAnchorElement>());
  useEffect(()=>{
    const mount=host.current!;let disposed=false,frame=0,gpuLost=false;
    const demand=new RenderDemand();
    const abort=new AbortController();
    setFailed(false);setContextUnavailable(false);setStatus('빛가람 지도를 불러오고 있습니다');setPins([]);
    const cleanups:(()=>void)[]=[];
    let renderer:THREE.WebGLRenderer|undefined,controls:OrbitControls|undefined,observer:ResizeObserver|undefined;
    const scene=new THREE.Scene();scene.background=new THREE.Color('#bbd9e6');
    const camera=new THREE.PerspectiveCamera(45,1,1,12000);
    const dispose=(root:THREE.Object3D)=>root.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();for(const m of Array.isArray(o.material)?o.material:[o.material]){Object.values(m).forEach(value=>{if(value instanceof THREE.Texture)value.dispose();});m.dispose();}}});
    const updateQuality=(event:Event)=>{if(renderer){renderer.setPixelRatio(pixelRatioFor((event as CustomEvent<GraphicsQuality>).detail,devicePixelRatio));renderer.setSize(mount.clientWidth,mount.clientHeight);demand.invalidate();}};
    window.addEventListener('naju:quality',updateQuality);
    async function setup(){
      renderer=new THREE.WebGLRenderer({antialias:true,logarithmicDepthBuffer:true});renderer.setPixelRatio(pixelRatioFor(qualityRef.current,devicePixelRatio));
      renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;
      const canvas=renderer.domElement;canvas.tabIndex=0;canvas.setAttribute('aria-label','빛가람 3D 지도. 드래그로 회전하고, 두 손가락이나 확대·축소 버튼으로 화면 크기를 조절하세요.');mount.appendChild(canvas);
      const lost=(event:Event)=>{event.preventDefault();gpuLost=true;setContextUnavailable(true);};
      const restored=()=>{gpuLost=false;setContextUnavailable(false);demand.invalidate();};
      canvas.addEventListener('webglcontextlost',lost);canvas.addEventListener('webglcontextrestored',restored);
      cleanups.push(()=>{canvas.removeEventListener('webglcontextlost',lost);canvas.removeEventListener('webglcontextrestored',restored);});
      scene.add(new THREE.HemisphereLight('#e4f3ff','#787d61',1.5));
      const sun=new THREE.DirectionalLight('#fff4de',2.5);sun.position.set(-1200,2300,800);scene.add(sun);
      controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.enablePan=true;controls.minDistance=350;controls.maxDistance=6500;controls.minPolarAngle=.15;controls.maxPolarAngle=Math.PI*.46;
      controls.addEventListener('change',()=>demand.invalidate());
      const restore=()=>{camera.position.set(1250,1950,2150);controls!.target.set(200,0,-50);controls!.update();};reset.current=restore;restore();
      zoom.current=(scale)=>{const offset=camera.position.clone().sub(controls!.target);offset.setLength(THREE.MathUtils.clamp(offset.length()*scale,controls!.minDistance,controls!.maxDistance));camera.position.copy(controls!.target).add(offset);controls!.update();demand.invalidate();};
      const resize=()=>{camera.aspect=mount.clientWidth/mount.clientHeight;camera.updateProjectionMatrix();renderer!.setSize(mount.clientWidth,mount.clientHeight);demand.invalidate();};resize();observer=new ResizeObserver(resize);observer.observe(mount);
      const loadModel=async()=>{
        const results=await Promise.allSettled(['bitgaram-overview','bitgaram-overview-part2','bitgaram-access-overview'].map(async name=>{
          const response=await fetch(`/models/${name}.glb.gz?v=bitgaram-access-v101`,{signal:abort.signal});
          if(!response.ok)throw new Error('3D 지도를 불러오지 못했습니다.');
          return new GLTFLoader().parseAsync(await unpackModel(await response.arrayBuffer()),'');
        }));
        const failure=results.find(result=>result.status==='rejected');
        if(failure?.status==='rejected'){
          for(const result of results)if(result.status==='fulfilled')dispose(result.value.scene);
          throw failure.reason;
        }
        const parts=results.map(result=>{if(result.status!=='fulfilled')throw new Error('Incomplete map');return result.value;});
        for(const part of parts.slice(1))parts[0].scene.add(part.scene);
        return parts[0];
      };
      const [modelResult,responseResult]=await Promise.allSettled([loadModel(),fetch('/bitgaram-orbit.json?v=bitgaram-access-v101',{signal:abort.signal})]);
      if(modelResult.status==='rejected')throw modelResult.reason;
      const model=modelResult.value;
      if(responseResult.status==='rejected'){dispose(model.scene);throw responseResult.reason;}
      const response=responseResult.value;
      if(disposed){dispose(model.scene);return;}
      if(!response.ok){dispose(model.scene);throw new Error('장소 정보를 불러오지 못했습니다.');}
      const data=await response.json().catch(error=>{dispose(model.scene);throw error;}) as {pins:Pin[]};if(disposed){dispose(model.scene);return;}
      try {await batchStaticSceneInSlices(model.scene,{signal:abort.signal,onProgress:(done,total)=>setStatus(`지도 화면을 정리하고 있습니다${total?` · ${Math.round(done/total*100)}%`:''}`)});} catch(error){dispose(model.scene);throw error;}
      if(disposed){dispose(model.scene);return;}
      scene.add(model.scene);setPins(data.pins);setStatus('');
      const point=new THREE.Vector3();
      const draw=()=>{if(disposed)return;frame=requestAnimationFrame(draw);if(document.hidden||portraitRef.current||gpuLost)return;const changed=controls!.update();if(!demand.take(!!changed,false))return;camera.updateMatrixWorld();let missing=false;
        const placed:{x:number;y:number;width:number;height:number}[]=[];
        for(const p of data.pins){const el=links.current.get(p.id);if(!el){missing=true;continue;}point.set(...p.position).project(camera);const visible=point.z>-1&&point.z<1&&Math.abs(point.x)<1&&Math.abs(point.y)<1;el.style.visibility=visible?'visible':'hidden';
          const width=el.offsetWidth,height=el.offsetHeight;
          const x=THREE.MathUtils.clamp((point.x+1)*mount.clientWidth/2,width/2+12,mount.clientWidth-width/2-12);
          let y=THREE.MathUtils.clamp((1-point.y)*mount.clientHeight/2,height+80,mount.clientHeight-90);
          for(const other of placed)if(Math.abs(x-other.x)<(width+other.width)/2+8&&Math.abs(y-other.y)<Math.max(height,other.height)+12)y=Math.max(height+80,other.y-height-16);
          if(visible)placed.push({x,y,width,height});
          el.style.left=`${x}px`;el.style.top=`${y}px`;}
        renderer!.render(scene,camera);if(missing)demand.invalidate();
      };draw();
    }
    setup().catch(()=>{if(!disposed){setFailed(true);setStatus('지도를 불러오지 못했습니다. 장소 목록에서 산책을 시작할 수 있습니다.');}});
    return()=>{disposed=true;abort.abort();window.removeEventListener('naju:quality',updateQuality);cancelAnimationFrame(frame);cleanups.forEach(cleanup=>cleanup());observer?.disconnect();controls?.dispose();dispose(scene);renderer?.dispose();renderer?.domElement.remove();};
  },[attempt]);
  return <><div className="hub-orbit" ref={host}/>{pins.map(p=><a ref={el=>{if(el)links.current.set(p.id,el);else links.current.delete(p.id);}} className="hub-pin" key={p.id} href={`/?place=${p.id}`} style={{visibility:'hidden'}}>{p.label} ↗</a>)}<div className="hub-map-tools"><button aria-label="처음 각도로 돌아가기" onClick={()=>reset.current()} disabled={!!status||contextUnavailable}><RotateCcw size={18}/></button><button aria-label="지도 확대" onClick={()=>zoom.current(.8)} disabled={!!status||contextUnavailable}><Plus size={19}/></button><button aria-label="지도 축소" onClick={()=>zoom.current(1.25)} disabled={!!status||contextUnavailable}><Minus size={19}/></button></div>{contextUnavailable?<div className="hub-status" role="alert">3D 화면이 중단됐습니다. 자동 복구를 기다리거나 지도를 다시 열어 주세요.<button onClick={()=>setAttempt(a=>a+1)}>지도 다시 불러오기</button></div>:status&&<div className="hub-status" role="status">{!failed&&<span className="loading-line"/>}{status}{failed&&<button onClick={()=>setAttempt(a=>a+1)}>다시 불러오기</button>}</div>}</>;
}
