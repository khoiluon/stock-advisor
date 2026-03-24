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
});
