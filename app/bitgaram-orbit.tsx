'use client';
import {useEffect,useRef,useState} from 'react';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {batchStaticScene} from '@/lib/static-scene';
import {unpackModel} from '@/lib/model-transport';

type Pin={id:string;label:string;position:[number,number,number]};
export default function BitgaramOrbit(){
  const host=useRef<HTMLDivElement>(null),reset=useRef<()=>void>(()=>{});
  const [pins,setPins]=useState<Pin[]>([]),[status,setStatus]=useState('3D 지도를 불러오는 중…');
  const links=useRef(new Map<string,HTMLAnchorElement>());
  useEffect(()=>{
    const mount=host.current!;let disposed=false,frame=0;
    let renderer:THREE.WebGLRenderer|undefined,controls:OrbitControls|undefined,observer:ResizeObserver|undefined;
    const scene=new THREE.Scene();scene.background=new THREE.Color('#bbd9e6');
    const camera=new THREE.PerspectiveCamera(45,1,1,12000);
    const dispose=(root:THREE.Object3D)=>root.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose();}});
    async function setup(){
      renderer=new THREE.WebGLRenderer({antialias:true,logarithmicDepthBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));
      renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;
      const canvas=renderer.domElement;canvas.tabIndex=0;canvas.setAttribute('aria-label','빛가람 3D 지도. 드래그로 회전, 휠로 확대·축소, 오른쪽 드래그로 위치 이동');mount.appendChild(canvas);
      scene.add(new THREE.HemisphereLight('#e4f3ff','#787d61',1.5));
      const sun=new THREE.DirectionalLight('#fff4de',2.5);sun.position.set(-1200,2300,800);scene.add(sun);
      controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.enablePan=true;controls.minDistance=350;controls.maxDistance=6500;controls.minPolarAngle=.15;controls.maxPolarAngle=Math.PI*.46;
      const restore=()=>{camera.position.set(1250,1950,2150);controls!.target.set(200,0,-50);controls!.update();};reset.current=restore;restore();
      const resize=()=>{camera.aspect=mount.clientWidth/mount.clientHeight;camera.updateProjectionMatrix();renderer!.setSize(mount.clientWidth,mount.clientHeight);};resize();observer=new ResizeObserver(resize);observer.observe(mount);
      const loadModel=async()=>{
        const parts=await Promise.all(['bitgaram-overview','bitgaram-overview-part2'].map(async name=>{
          const response=await fetch(`/models/${name}.glb.gz?v=palette-v51-20260920`);
          if(!response.ok)throw new Error('3D 지도를 불러오지 못했습니다.');
          return new GLTFLoader().parseAsync(await unpackModel(await response.arrayBuffer()),'');
        }));
        parts[0].scene.add(parts[1].scene);
        return parts[0];
      };
      const [model,response]=await Promise.all([loadModel(),fetch('/bitgaram-orbit.json')]);
      if(disposed){dispose(model.scene);return;}
      if(!response.ok)throw new Error('장소 정보를 불러오지 못했습니다.');
      const data=await response.json() as {pins:Pin[]};if(disposed){dispose(model.scene);return;}
      batchStaticScene(model.scene);scene.add(model.scene);setPins(data.pins);setStatus('');
      const point=new THREE.Vector3();
      const draw=()=>{if(disposed)return;controls!.update();camera.updateMatrixWorld();
        for(const p of data.pins){const el=links.current.get(p.id);if(!el)continue;point.set(...p.position).project(camera);const visible=point.z>-1&&point.z<1&&Math.abs(point.x)<1&&Math.abs(point.y)<1;el.style.visibility=visible?'visible':'hidden';el.style.left=`${(point.x+1)*50}%`;el.style.top=`${(1-point.y)*50}%`;}
        renderer!.render(scene,camera);frame=requestAnimationFrame(draw);
      };draw();
    }
    setup().catch(()=>{if(!disposed)setStatus('3D 지도를 불러오지 못했습니다. 오른쪽 장소 목록으로 이동할 수 있어요.');});
    return()=>{disposed=true;cancelAnimationFrame(frame);observer?.disconnect();controls?.dispose();dispose(scene);renderer?.dispose();renderer?.domElement.remove();};
  },[]);
  return <><div className="hub-orbit" ref={host}/>{pins.map(p=><a ref={el=>{if(el)links.current.set(p.id,el);else links.current.delete(p.id);}} className="hub-pin" key={p.id} href={`/?place=${p.id}`} style={{visibility:'hidden'}}>{p.label} ↗</a>)}<button className="hub-reset" onClick={()=>reset.current()}>처음 각도</button>{status&&<p className="hub-status" role="status">{status}</p>}</>;
}
