import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'

export default defineConfig({
  plugins: [
    dts({
      insertTypesEntry: true,
    }),
  ],
  build: {
    lib: {
      entry: 'src/main.ts',
      name: 'FCOSOrchidJudge',
      formats: ['umd', 'es'],
      fileName: (format) => `fcos-orchid-judge.${format === 'es' ? 'esm' : format}.js`
    },
    outDir: 'build',
    rollupOptions: {
      external: [],
      output: {
        globals: {}
      }
    }
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'production')
  }
})