import { useQuery } from "@tanstack/react-query";
import { authApi } from "@/configs/axios";
import { endpoint } from "@/configs/endpoint";
import type { StockInfo } from "@/types/Stock";

export function useTickerQuery(query: string) {
	const token = localStorage.getItem("token");

	return useQuery({
		queryKey: ["tickers", query],
		queryFn: async () => {
			if (!token) throw new Error("You are not logged in.");

			const response = await authApi(token).get<StockInfo[]>(
				endpoint.stocks.search,
				{
					params: { q: query },
				},
			);

			return response.data;
		},
		enabled: !!query || !!token,
	});
}
