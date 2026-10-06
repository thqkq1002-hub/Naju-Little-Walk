import fs from 'node:fs';import {createHash} from 'node:crypto';
const r=JSON.parse(fs.readFileSync('knowledge/sources/history-gallery-v91.json','utf8')),w=JSON.parse(fs.readFileSync('public/yeongsanpo-history-world.json','utf8'));
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
r.navigationSha256=createHash('sha256').update(JSON.stringify(canonical(Object.fromEntries(r.navigationKeys.map(k=>[k,w[k]??null]))))).digest('hex');
fs.writeFileSync('knowledge/sources/history-gallery-v91.json',JSON.stringify(r,null,2)+'\n');
console.log('Final gallery navigation recorded:',r.navigationSha256);
