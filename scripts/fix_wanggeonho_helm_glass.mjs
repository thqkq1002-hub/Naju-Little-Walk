// The v79 refinement classified Wanggeonho's wheelhouse panes as plaster (their object names contain "wall"
// before "glass"), so the export merged them into an opaque, textured Y79_plaster material in the glass colour
// and the helm view showed a painted blue board. The source .blend is not in the repository, so repoint that
// batch to the boat's existing transparent glass material, as on Najuho, and rewrite the gzip transport copy.
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';

const glbUrl=new URL('../public/models/wanggeonho.glb',import.meta.url);
const raw=fs.readFileSync(glbUrl);
const jsonLength=raw.readUInt32LE(12);
const gltf=JSON.parse(raw.toString('utf8',20,20+jsonLength));
const rest=raw.subarray(20+jsonLength);

const glass=gltf.materials.findIndex(m=>m.name==='Museum_97b6be'&&m.alphaMode==='BLEND');
const panes=gltf.nodes.find(n=>n.name==='v79_batch_Y79_plaster_6_0_0');
if(glass<0||!panes)throw new Error('Expected Wanggeonho glass material and wheelhouse pane batch');
const primitives=gltf.meshes[panes.mesh].primitives;
if(primitives.every(p=>p.material===glass)){console.log('already transparent');process.exit(0);}
const previous=gltf.materials[primitives[0].material];
const rgb=m=>m.pbrMetallicRoughness.baseColorFactor.slice(0,3).map(v=>v.toFixed(4)).join();
if(rgb(previous)!==rgb(gltf.materials[glass]))throw new Error(`Unexpected pane material ${previous.name}`);
for(const p of primitives)p.material=glass;

let json=Buffer.from(JSON.stringify(gltf),'utf8');
json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,0x20)]);
const header=Buffer.alloc(20);
header.write('glTF',0,'ascii');header.writeUInt32LE(2,4);header.writeUInt32LE(20+json.length+rest.length,8);
header.writeUInt32LE(json.length,12);header.write('JSON',16,'ascii');
const patched=Buffer.concat([header,json,rest]);
fs.writeFileSync(glbUrl,patched);
fs.writeFileSync(new URL('../public/models/wanggeonho.glb.gz',import.meta.url),gzipSync(patched,{level:9}));
console.log(`wheelhouse panes ${previous.name} -> ${gltf.materials[glass].name}; ${raw.length} -> ${patched.length} bytes`);
