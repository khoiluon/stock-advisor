import { useQuery } from "@tanstack/react-query";
import { authApi } from "@/configs/axios";
import { endpoint } from "@/configs/endpoint";
import type {
	MarketStateData,
	AnomalyAlert,
	MLModelInfo,
} from "@/types/Stock";

export function useMarketStateQuery() {
	const token = localStorage.getItem("token");

	return useQuery({
		queryKey: ["ml", "market-state"],
		queryFn: async () => {
			if (!token) throw new Error("Not logged in");
			const res = await authApi(token).get<MarketStateData>(
				endpoint.ml.marketState,
			);
			return res.data;
		},
		enabled: !!token,
		staleTime: 5 * 60 * 1000,
	});
}

export function useAnomalyAlertsQuery(days = 7) {
	const token = localStorage.getItem("token");

	return useQuery({
		queryKey: ["ml", "anomalies", days],
		queryFn: async () => {
			if (!token) throw new Error("Not logged in");
			const res = await authApi(token).get<{ results: AnomalyAlert[] }>(
				endpoint.ml.anomalies,
				{ params: { days } },
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
