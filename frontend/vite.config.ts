import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Proxy /api -> FastAPI (backend/) de dev khong vuong CORS; production co the
// serve dist/ sau reverse proxy chung voi API.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
