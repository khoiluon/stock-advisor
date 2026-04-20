import { useQuery } from "@tanstack/react-query";
import { authApi } from "@/configs/axios";
import { endpoint } from "@/configs/endpoint";
import type { UserFavorite } from "@/types/Stock";

export default function useFavoritesQuery() {
	const token = localStorage.getItem("token");

	return useQuery({
		queryKey: ["favorites"],
		queryFn: async () => {
			if (!token) throw new Error("You are not logged in.");

			const response = await authApi(token).get<UserFavorite[]>(
				endpoint.watchlist.list,
			);

			return response.data;
		},
		enabled: !!token,
	});
}
