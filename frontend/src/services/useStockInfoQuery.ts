import { useQuery } from "@tanstack/react-query";
import { authApi } from "@/configs/axios";
import { endpoint } from "@/configs/endpoint";
import type { StockInfo } from "@/types/Stock";

export default function useStockInfoQuery(ticker: string) {
	const token = localStorage.getItem("token");

	return useQuery({
		queryKey: ["stock-info", ticker],
		queryFn: async () => {
			if (!token) throw new Error("You are not logged in.");

			const response = await authApi(token).get<StockInfo>(
				endpoint.stocks.ticker(ticker),
			);

			return response.data;
		},
		enabled: !!ticker || !!token,
	});
}
