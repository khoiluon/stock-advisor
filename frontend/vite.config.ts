import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
	plugins: [react(), tailwindcss()],
	server: {
		watch: {
			usePolling: true,
		},
		host: true,
		strictPort: true,
		port: 5173,
	},
	resolve: {
		alias: [{ find: "@", replacement: "/src" }],
	},
	// optimizeDeps: {
	// 	// Loại trừ khỏi pre-bundling để Vite xử lý như code dự án
	// 	exclude: [
	// 		"lightweight-charts-line-tools-core",
	// 		"lightweight-charts-line-tools-fib-retracement",
	// 		"lightweight-charts-line-tools-lines",
	// 	],
	// },
});
