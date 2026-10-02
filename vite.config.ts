import { sites } from '@openai/sites-vite-plugin';
import tailwindcss from '@tailwindcss/postcss';
import vinext from 'vinext';
import { defineConfig } from 'vite';

// The walkthrough is entirely client-side: static export avoids an unnecessary
// Worker runtime and keeps the Blender GLB usable without a server database.
export default defineConfig({
  css: { postcss: { plugins: [tailwindcss()] } },
  plugins: [vinext(), sites()],
});
