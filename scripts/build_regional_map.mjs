import fs from 'node:fs';
// Geographic geometry is retained; only sub-metre precision is rounded for delivery.
const input=JSON.parse(fs.readFileSync('knowledge/sources/naju-regional-map-overpass.json','utf8'));
const paths=input.elements.filter(e=>e.type==='way' && e.geometry?.length>1).map(e=>({
  id:e.id, kind:e.tags.waterway==='river'?'river':e.tags.railway==='rail'?'rail':e.tags.highway,
  name:e.tags.name??'', points:e.geometry.map(p=>[+p.lon.toFixed(6),+p.lat.toFixed(6)]),
}));
const labels=input.elements.filter(e=>e.type==='node' && e.tags?.name).map(e=>({name:e.tags.name,point:[e.lon,e.lat]}));
const bitgaramPath='knowledge/sources/bitgaram/geometry.json';
if(fs.existsSync(bitgaramPath)) {
  const data=JSON.parse(fs.readFileSync(bitgaramPath,'utf8'));
  const seen=new Set(paths.map(p=>String(p.id)));
  for(const way of data.ways) {
    if(!way.tags.highway || seen.has(way.id)) continue;
    paths.push({id:Number(way.id),kind:way.tags.highway,name:way.tags.name??'',points:way.coordinates});
    seen.add(way.id);
  }
  labels.push({name:'빛가람동',point:[126.787,35.02]});
}
fs.writeFileSync('public/naju-region-map.json',JSON.stringify({source:'© OpenStreetMap contributors, ODbL 1.0',bounds:[126.625,126.805,34.985,35.044],paths,labels}));
console.log(`Regional map: ${paths.length} ways, ${labels.length} settlement labels`);
