import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { resolve, join } from "path";
import tailwindcss from "tailwindcss";
import autoprefixer from "autoprefixer";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '~' : resolve(join(__dirname, 'src'))
    },
  },
  css: {
    postcss: {
      plugins: [tailwindcss(), autoprefixer()],
    },
  }
})