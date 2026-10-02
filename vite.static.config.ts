import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/postcss';
import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';
import { readFileSync, readdirSync, unlinkSync, existsSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';

// A shared React page with a plain static production entry avoids the Windows
// native crash in the starter's multi-environment RSC production build.
export default defineConfig({
  plugins: [react(),{
    name:'publish-compressed-blender-model',
    apply:'build',
    closeBundle(){
      for(const name of readdirSync(new URL('./dist/client/models/',import.meta.url)).filter(n=>n.endsWith('.glb.gz'))){
      const raw=new URL('./dist/client/models/'+name.slice(0,-3),import.meta.url);
      const compressed=new URL('./dist/client/models/'+name,import.meta.url);
      const decoded=gunzipSync(readFileSync(compressed));
      if(decoded.length<12 || decoded.readUInt32LE(0)!==0x46546c67 || decoded.readUInt32LE(4)!==2 || decoded.readUInt32LE(8)!==decoded.length)throw new Error('Invalid compressed Blender GLB.');
      if(existsSync(raw)&&!decoded.equals(readFileSync(raw)))throw new Error('Compressed Blender model is stale; regenerate it before publishing.');
      // Only omit the redundant build copy. The original GLB stays in public/.
      if(existsSync(raw))unlinkSync(raw);
      }
    },
  }],
  resolve: { alias: { '@': fileURLToPath(new URL('.', import.meta.url)) } },
  // The workspace also stores Blender tools and archived previews. Only scan
  // this site's entry, not unrelated HTML under work/, for dev dependencies.
  optimizeDeps: { entries: ['index.html'] },
  css: { postcss: { plugins: [tailwindcss()] } },
  build: { outDir: 'dist/client', emptyOutDir: true, minify: true },
});
