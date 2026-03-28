import axios from "axios";

export const publicApi = axios.create({
	baseURL: import.meta.env.VITE_API_URL,
	headers: { "Content-Type": "application/json" },
});

export const authApi = (token: string) =>
	axios.create({
		baseURL: import.meta.env.VITE_API_URL,
		headers: {
			Authorization: `Token ${token}`,
			"Content-Type": "application/json",
		},
	});
