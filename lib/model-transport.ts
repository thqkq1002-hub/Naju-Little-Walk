/** Lossless transport only: decoded bytes are the original Blender GLB. */
export async function unpackModel(data: ArrayBuffer): Promise<ArrayBuffer> {
  const magic=new Uint8Array(data,0,Math.min(4,data.byteLength));
  if(magic[0]===0x1f && magic[1]===0x8b){
    const stream=new Blob([data]).stream().pipeThrough(new DecompressionStream('gzip'));
    return new Response(stream).arrayBuffer();
  }
  // Some hosts transparently decompress Content-Encoding: gzip responses.
  if(magic[0]!==0x67 || magic[1]!==0x6c || magic[2]!==0x54 || magic[3]!==0x46)throw new Error('도시 모델 파일을 읽을 수 없습니다.');
  return data;
}
