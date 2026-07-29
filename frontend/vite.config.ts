import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import {defineConfig} from 'vite';

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      // Do not modify — file watching is disabled to prevent flickering during agent edits.
      hmr: process.env.DISABLE_HMR !== 'true'
        ? {
            // When running Vite directly (not via server.ts), let Vite
            // pick the next available port rather than crashing on 24678.
            port: parseInt(process.env.HMR_PORT ?? '24678', 10),
          }
        : false,
      // Disable file watching when DISABLE_HMR is true to save CPU during agent edits.
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
      // Allow Vite to advance to the next port when the preferred one is taken.
      // This applies both to the HTTP listener (vite CLI) and the HMR socket.
      strictPort: false,
    },
  };
});
