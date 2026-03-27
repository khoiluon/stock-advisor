import { useQuery } from "@tanstack/react-query";
import { authApi } from "@/configs/axios";
import { endpoint } from "@/configs/endpoint";
import type { StockDataPoint } from "@/types/Stock";

export default function useStockHistoryQuery(ticker: string) {
	const token = localStorage.getItem("token");

	return useQuery({
		queryKey: ["stock-history", ticker],
		queryFn: async () => {
			if (!token) throw new Error("You are not logged in.");

			const response = await authApi(token).get<StockDataPoint[]>(
				endpoint.stockData,
				{
					params: { ticker },
				},
			);

			const sortedHistory = (response.data || []).sort(
				(a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
			);

			return sortedHistory;
		},
		enabled: !!token,
	});
}
