// Derives the Bitgaram stone-slide ride from the v101 slide centreline recorded by refine_bitgaram_access_v101.py.
// Output: public/bitgaram-slide-ride.json (route on the granite trough floor, landing mat, its walkable floor).
import fs from 'node:fs';

const read=path=>JSON.parse(fs.readFileSync(new URL('../'+path,import.meta.url),'utf8'));
const route=read('knowledge/sources/bitgaram/access-v101/navigation-profiles.json').slide_route;
const round=v=>Math.round(v*1000)/1000;

// Exit frame: `a` runs along the last stretch of trough, `s` to its left.
const end=route.at(-1),before=route.at(-8);
const along=[end[0]-before[0],end[2]-before[2]],length=Math.hypot(...along),f=[along[0]/length,along[1]/length],side=[-f[1],f[0]];
const at=(a,s)=>[round(end[0]+f[0]*a+side[0]*s),round(end[2]+f[1]*a+side[1]*s)];

// The mat top is level with the trough lip and 5 cm above the stair-landing deck it overlaps, so visitors step off.
const MAT_TOP=19.26;
const onMat=(a,s)=>{const [x,z]=at(a,s);return [x,MAT_TOP,z];};
const [matX,matZ]=at(1.65,-.05);

// The visitor can stand 0.5–2 m above the trough mouth; the ride starts from just there.
const [x0,y0,z0]=route[0],[x6,,z6]=route[6],up=Math.hypot(x6-x0,z6-z0);

const ride={
  id:'bitgaram-stone-slide',
  name:'돌미끄럼틀',
  route:[...route.filter((_,i)=>i%4===0||i===route.length-1).map(p=>p.map(round)),onMat(.6,-.05),onMat(2.1,-.05)],
  entry:{x:round(x0-(x6-x0)/up*.7),z:round(z0-(z6-z0)/up*.7),height:round(y0),radius:3.2},
  mat:{modelUrl:'/models/props/slide-landing-mat.glb',position:[matX,MAT_TOP,matZ],yaw:round(Math.atan2(f[0],f[1])),floor:[at(.1,-1.05),at(3.2,-1.05),at(3.2,.95),at(.1,.95)],height:MAT_TOP},
  estimated:'경로는 v101 Blender 미끄럼틀 중심선(위성영상·현장 사진 해석)이며, 탑승 속도와 착지 매트는 체험을 위한 가상 요소입니다.',
};
fs.writeFileSync(new URL('../public/bitgaram-slide-ride.json',import.meta.url),JSON.stringify(ride)+'\n');
console.log('SLIDE_RIDE',ride.route.length,'points; entry',JSON.stringify(ride.entry),'mat',JSON.stringify(ride.mat.position));
