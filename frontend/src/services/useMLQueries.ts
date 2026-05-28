import { useQuery } from "@tanstack/react-query";
import { authApi } from "@/configs/axios";
import { endpoint } from "@/configs/endpoint";
import type {
	MarketStateData,
	AnomalyAlert,
	MLModelInfo,
} from "@/types/Stock";

export function useMarketStateQuery(date?: string) {
	const token = localStorage.getItem("token");

	return useQuery({
		queryKey: ["ml", "market-state", date],
		queryFn: async () => {
			if (!token) throw new Error("Not logged in");
			const params: Record<string, string | number> = {};
			if (date) params.date = date;
			else params.days = 30;
			const res = await authApi(token).get<MarketStateData>(
				endpoint.ml.marketState,
				{ params },
			);
			return res.data;
		},
		enabled: !!token,
		staleTime: 5 * 60 * 1000,
	});
}

export function useAnomalyAlertsQuery(days = 7, date?: string) {
	const token = localStorage.getItem("token");

	return useQuery({
		queryKey: ["ml", "anomalies", days, date],
		queryFn: async () => {
			if (!token) throw new Error("Not logged in");
			const params: Record<string, string | number> = {};
			if (date) params.date = date;
			else params.days = days;
			const res = await authApi(token).get<{ results: AnomalyAlert[] }>(
				endpoint.ml.anomalies,
				{ params },
			);
			return res.data.results ?? res.data;
		},
		enabled: !!token,
		staleTime: 5 * 60 * 1000,
	});
}

export function useMLModelInfoQuery() {
	const token = localStorage.getItem("token");

	return useQuery({
		queryKey: ["ml", "model-info"],
		queryFn: async () => {
			if (!token) throw new Error("Not logged in");
			const res = await authApi(token).get<MLModelInfo>(
				endpoint.ml.modelInfo,
			);
			return res.data;
		},
		enabled: !!token,
		staleTime: 30 * 60 * 1000,
	});
}
