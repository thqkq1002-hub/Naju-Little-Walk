/** Lossless transport only: decoded bytes are the original Blender GLB. */
export async function unpackModel(data: ArrayBuffer): Promise<ArrayBuffer> {
  const magic=new Uint8Array(data,0,Math.min(4,data.byteLength));
  if(magic[0]===0x1f && magic[1]===0x8b){
    if(typeof DecompressionStream==='undefined')throw new Error('이 브라우저는 3D 모델 압축을 지원하지 않습니다. Chrome을 최신 버전으로 업데이트해 주세요.');
    const stream=new Blob([data]).stream().pipeThrough(new DecompressionStream('gzip'));
    data=await new Response(stream).arrayBuffer();
  }
  // Some hosts transparently decompress Content-Encoding: gzip responses.
  const header=new DataView(data);
  if(data.byteLength<12 || header.getUint32(0,true)!==0x46546c67 || header.getUint32(4,true)!==2 || header.getUint32(8,true)!==data.byteLength)throw new Error('도시 모델 파일이 불완전합니다. 다시 불러와 주세요.');
  return data;
}

export type ModelProgress = {
  phase:'download'|'unpack'|'retry'; received:number; total?:number; attempt:number;
};
type ModelLoadOptions = {
  signal?:AbortSignal; onProgress?:(progress:ModelProgress)=>void;
  idleTimeoutMs?:number; fetcher?:typeof fetch;
};

/** Stop a stalled network operation even if its response body never settles. */
function networkStep<T>(operation:Promise<T>,signal:AbortSignal):Promise<T> {
  return new Promise((resolve,reject)=>{
    const aborted=()=>reject(signal.reason);
    signal.addEventListener('abort',aborted,{once:true});
    operation.then(resolve,reject).finally(()=>signal.removeEventListener('abort',aborted));
    if(signal.aborted)aborted();
  });
}

async function downloadModel(url:string,options:ModelLoadOptions,attempt:number):Promise<ArrayBuffer> {
  const controller=new AbortController();
  const parentAbort=()=>controller.abort(options.signal?.reason);
  options.signal?.throwIfAborted();
  options.signal?.addEventListener('abort',parentAbort,{once:true});
  let timer:ReturnType<typeof setTimeout>;
  const arm=()=>{
    clearTimeout(timer);
    timer=setTimeout(()=>controller.abort(new Error('모델 다운로드가 멈췄습니다. 연결을 확인하고 다시 불러와 주세요.')),options.idleTimeoutMs??30_000);
  };
  let reader:ReadableStreamDefaultReader<Uint8Array>|undefined;
  let complete=false;
  try {
    arm();
    options.onProgress?.({phase:'download',received:0,attempt});
    const response=await networkStep((options.fetcher??fetch)(url,{signal:controller.signal,cache:attempt===1?'default':'reload'}),controller.signal);
    if(!response.ok)throw new Error(`도시 모델을 불러오지 못했습니다. (${response.status})`);
    // Transparent HTTP decompression makes Content-Length a different byte count.
    const length=Number(response.headers.get('content-length'));
    const total=!response.headers.get('content-encoding')&&length>0?length:undefined;
    if(!response.body)return await networkStep(response.arrayBuffer(),controller.signal);
    reader=response.body.getReader();
    const chunks:Uint8Array[]=[];
    let received=0,lastReport=0;
    for(;;){
      const chunk=await networkStep(reader.read(),controller.signal);
      if(chunk.done)break;
      chunks.push(chunk.value);received+=chunk.value.byteLength;arm();
      const now=performance.now();
      if(now-lastReport>150){options.onProgress?.({phase:'download',received,total,attempt});lastReport=now;}
    }
    complete=true;
    options.onProgress?.({phase:'download',received,total,attempt});
    const result=new Uint8Array(received);
    let offset=0;for(const chunk of chunks){result.set(chunk,offset);offset+=chunk.byteLength;}
    return result.buffer;
  } finally {
    clearTimeout(timer!);
    options.signal?.removeEventListener('abort',parentAbort);
    if(reader){if(!complete)void reader.cancel().catch(()=>{});reader.releaseLock();}
  }
}

/** Retry once without cached bytes; preserve the exact authored Blender model. */
export async function fetchModelData(url:string,options:ModelLoadOptions={}):Promise<ArrayBuffer> {
  for(let attempt=1;attempt<=2;attempt++){
    try {
      const bytes=await downloadModel(url,options,attempt);
      options.signal?.throwIfAborted();
      options.onProgress?.({phase:'unpack',received:bytes.byteLength,attempt});
      const data=await unpackModel(bytes);
      options.signal?.throwIfAborted();
      return data;
    } catch(error) {
      options.signal?.throwIfAborted();
      if(attempt===2)throw error;
      options.onProgress?.({phase:'retry',received:0,attempt:2});
    }
  }
  throw new Error('도시 모델을 불러오지 못했습니다.');
}
