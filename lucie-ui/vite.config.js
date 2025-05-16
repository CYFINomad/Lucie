import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@components": path.resolve(__dirname, "./src/components"),
      "@chat": path.resolve(__dirname, "./src/components/chat"),
      "@knowledge": path.resolve(__dirname, "./src/components/knowledge"),
      "@agents": path.resolve(__dirname, "./src/components/agents"),
      "@learning": path.resolve(__dirname, "./src/components/learning"),
      "@assistant": path.resolve(__dirname, "./src/components/assistant"),
      "@ai-config": path.resolve(__dirname, "./src/components/ai-config"),
      "@visualizations": path.resolve(
        __dirname,
        "./src/components/visualizations"
      ),
      "@common": path.resolve(__dirname, "./src/components/common"),
      "@pages": path.resolve(__dirname, "./src/pages"),
      "@state": path.resolve(__dirname, "./src/state"),
      "@services": path.resolve(__dirname, "./src/services"),
      "@hooks": path.resolve(__dirname, "./src/hooks"),
      "@contexts": path.resolve(__dirname, "./src/contexts"),
      "@utils": path.resolve(__dirname, "./src/utils"),
    },
  },
  server: {
    port: 5173, // Port par défaut de Vite, change-le si besoin
    open: true,
    proxy: {
      "/api": {
        target: "http://localhost:3000", // Port du backend Node.js
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
  define: {
    "process.env": process.env,
  },
});
