import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
    envDir: ".",
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    build: {
        rollupOptions: {
            output: {
                manualChunks: {
                    vendor: ["react", "react-dom", "react-router-dom"],
                    ui: [
                        "@radix-ui/react-dialog",
                        "@radix-ui/react-dropdown-menu",
                        "@radix-ui/react-select",
                        "@radix-ui/react-tabs",
                        "@radix-ui/react-tooltip",
                        "@radix-ui/react-avatar",
                        "@radix-ui/react-checkbox",
                        "@radix-ui/react-label",
                        "@radix-ui/react-scroll-area",
                        "@radix-ui/react-separator",
                        "@radix-ui/react-switch",
                        "@radix-ui/react-slot",
                    ],
                    charts: ["recharts", "lucide-react"],
                    utils: ["clsx", "tailwind-merge", "date-fns", "class-variance-authority"],
                },
            },
        },
        chunkSizeWarningLimit: 1000,
    },
    server: {
        port: 3000,
        proxy: {
            "/api/v1": {
                target: "http://127.0.0.1:8005",
                changeOrigin: true,
            },
            "/api": {
                target: "http://127.0.0.1:8000",
                changeOrigin: true,
            },
        },
    },
});
