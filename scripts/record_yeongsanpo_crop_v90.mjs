import fs from 'node:fs';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(fs.readFileSync(new URL(p,root),'utf8'));
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const hash=v=>createHash('sha256').update(JSON.stringify(canonical(v))).digest('hex');
const before=read('outputs/yeongsanpo-crop-v90/world-before.json'),after=read('public/yeongsanpo-world.json');
const refs=read('knowledge/sources/yeongsanpo-v79-verification.json').navigation.find(n=>n.scene==='yeongsanpo');
const report=read('knowledge/sources/yeongsanpo-crop-v90.json');
const nav=w=>Object.fromEntries(refs.navigationKeys.map(k=>[k,w[k]??null]));
report.legacyNavigationSha256=hash(nav(before));
if(report.legacyNavigationSha256!==refs.navigationSha256)throw Error('Unexpected pre-existing navigation change; do not replace the baseline');
report.navigationSha256=hash(nav(after));
report.preservedNavigation={};
for(const k of ['spawn','arrivals','portals','places','boats','literatureGarden','dockStairRoute','dockHeight','architectureViews']){
 const a=hash(before[k]??null),b=hash(after[k]??null);
 if(a!==b)throw Error('Required riverfront content changed: '+k);
 report.preservedNavigation[k]={beforeSha256:a,afterSha256:b,unchanged:true};
}
const retained=s=>!s.footprint||s.footprint.every(p=>p[1]>=report.northCutMetres);
report.uncroppedSolidsSha256=hash(before.solids.filter(retained));
const beforeNames=before.solids.filter(retained).map(s=>s.name);
const afterOriginal=after.solids.filter((s,i)=>retained(before.solids[i]));
if(before.solids.length!==after.solids.length||hash(afterOriginal)!==report.uncroppedSolidsSha256)throw Error('Uncropped floor/wall information changed');
report.uncroppedSolidCount=beforeNames.length;
fs.writeFileSync(new URL('knowledge/sources/yeongsanpo-crop-v90.json',root),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({preservedNavigation:Object.keys(report.preservedNavigation),uncroppedSolidCount:report.uncroppedSolidCount,newBounds:report.newBounds}));
