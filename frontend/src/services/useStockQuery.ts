import { useQuery } from "@tanstack/react-query";
import { authApi } from "@/configs/axios";
import { endpoint } from "@/configs/endpoint";
import type { StockDataPoint, StockInfo } from "@/types/Stock";

export default function useDashboardDataQuery(ticker: string) {
	const token = localStorage.getItem("token");

	return useQuery({
		queryKey: ["stock", ticker],
		queryFn: async () => {
			if (!token) throw new Error("You are not logged in.");

			const [stockRes, infoRes] = await Promise.all([
				authApi(token).get<StockDataPoint[]>(endpoint.stockData, {
					params: { ticker },
				}),
				authApi(token).get<StockInfo>(endpoint.stocks.ticker(ticker)),
			]);

			const sortedHistory = (stockRes.data || []).sort(
				(a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
			);

			return {
				history: sortedHistory,
				info: infoRes.data || {},
			};
		},
		enabled: !!ticker && !!token,
	});
}
