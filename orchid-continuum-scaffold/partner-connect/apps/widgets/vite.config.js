import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    lib: {
      entry: 'src/main.js',
      name: 'OCWWidgets',
      fileName: 'ocw-widgets',
      formats: ['umd']
    },
    rollupOptions: {
      external: [],
      output: {
        globals: {}
      }
    },
    outDir: 'dist'
  },
  define: {
    'process.env.NODE_ENV': '"production"'
  }
});