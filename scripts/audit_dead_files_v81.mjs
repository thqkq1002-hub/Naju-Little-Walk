// Read-only import audit. Unknown assets and Blender history are never called dead.
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..');
const scan=dir=>fs.existsSync(dir)?fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?scan(path.join(dir,e.name)):[path.join(dir,e.name)]):[];
const files=['app','lib','components','hooks','tests'].flatMap(d=>scan(path.join(root,d))).filter(p=>/\.(tsx?|mjs)$/.test(p));
files.push(...fs.readdirSync(root).filter(n=>/\.(tsx?|mjs)$/.test(n)).map(n=>path.join(root,n)));
const imports=p=>[...fs.readFileSync(p,'utf8').matchAll(/(?:from\s*|import\s*\(\s*|import\s*)['"]([^'"]+)['"]/g)].map(m=>m[1]);
const resolve=(s,p)=>{
 if(!s.startsWith('.')&&!s.startsWith('@/'))return null;
 const base=s.startsWith('@/')?path.join(root,s.slice(2)):path.resolve(path.dirname(p),s);
 return [base,...['.ts','.tsx','.mjs','/index.ts','/index.tsx'].map(ext=>base+ext)].find(q=>fs.existsSync(q)&&fs.statSync(q).isFile())??null;
};
const entries=['browser-entry.tsx','app/layout.tsx','vite.static.config.ts','vite.config.ts','next.config.ts'].map(p=>path.join(root,p));
entries.push(...files.filter(p=>p.startsWith(path.join(root,'tests'))));
const reachable=new Set(),pending=[...entries];
while(pending.length){const p=pending.pop();if(reachable.has(p)||!fs.existsSync(p)||! /\.(tsx?|mjs)$/.test(p))continue;reachable.add(p);for(const s of imports(p)){const q=resolve(s,p);if(q)pending.push(q);}}
const candidates=files.filter(p=>!reachable.has(p)&&(p.includes(`${path.sep}components${path.sep}ui${path.sep}`)||p===path.join(root,'hooks/use-mobile.ts')||p===path.join(root,'lib/utils.ts')||p===path.join(root,'app/observatory-video.tsx')));
if(candidates.some(p=>p.includes(`${path.sep}components${path.sep}ui${path.sep}`)))candidates.push(path.join(root,'components.json'));
// The removed video panel has no importer. Preserve its user-provided media in
// the local recovery archive. Active panorama generation inputs are retained.
if(candidates.includes(path.join(root,'app/observatory-video.tsx')))candidates.push(...scan(path.join(root,'public/media')));
const npcManifest=JSON.parse(fs.readFileSync(path.join(root,'public/npc-placements.json'),'utf8'));
const activeNpc=new Set(Object.values(npcManifest.assets).map(a=>path.resolve(root,'public'+a.modelUrl)));
const executableText=files.filter(p=>fs.existsSync(p)&&reachable.has(p)).map(p=>fs.readFileSync(p,'utf8')).join('\n');
for(const p of scan(path.join(root,'public/models/npc'))){
 if(/-v[45]\.glb$/.test(p)&&!activeNpc.has(p)&&!executableText.includes(path.basename(p)))candidates.push(p);
}
const report={revision:'v81',date:'2026-10-03',entries:entries.map(p=>path.relative(root,p)),reachableFiles:reachable.size,unusedStarterFiles:candidates.map(p=>({path:path.relative(root,p).replaceAll('\\','/'),bytes:fs.statSync(p).size})),rebuildableCaches:['.next','.vinext','.wrangler','tsconfig.tsbuildinfo'],preserved:'Blender sources, research, generation scripts, other maps, original media and untracked user work are retained; absence of a live import alone does not make these dead.'};
fs.mkdirSync(path.join(root,'outputs/cleanup-v81'),{recursive:true});
fs.writeFileSync(path.join(root,'outputs/cleanup-v81/audit.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({reachable:reachable.size,unusedStarterFiles:candidates.length,unusedBytes:report.unusedStarterFiles.reduce((n,f)=>n+f.bytes,0),caches:report.rebuildableCaches}));
