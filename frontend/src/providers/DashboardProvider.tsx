import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useSearchParams } from "react-router-dom";
import { useStore } from "zustand";
import { authApi } from "@/configs/axios";
import { endpoint } from "@/configs/endpoint";
import { useStockDataFeed } from "@/hooks/useStockDataFeed";
import {
	createDashboardStore,
	StockDashboardContext,
} from "@/stores/DashboardStore";
import useDashboardDataQuery from "@/services/useStockQuery";

type DashboardProviderProps = {
	children: React.ReactNode;
};

export default function DashboardProvider({
	children,
}: DashboardProviderProps) {
	const [searchParams] = useSearchParams();
	const searchParamTicker = searchParams.get("ticker") || "VIC";

	const [store] = useState(() => createDashboardStore());

	const setLoading = useStore(store, (state) => state.setLoading);
	const setError = useStore(store, (state) => state.setError);
	const setStockData = useStore(store, (state) => state.setStockData);
	const setStockInfo = useStore(store, (state) => state.setStockInfo);
	const setHistoryLoaded = useStore(store, (state) => state.setHistoryLoaded);

	const { data, isLoading, error, isSuccess } =
		useDashboardDataQuery(searchParamTicker);

	useStockDataFeed(store);

	useEffect(() => {
		if (isLoading) {
			setLoading(true);
			setHistoryLoaded(false);
		}

		if (error) {
			setError(error.message || "Cannot connect to server.");
			setLoading(false);
		}

		if (isSuccess && data) {
			setStockData(data.history);
			setStockInfo(data.info);
			setLoading(false);
			setHistoryLoaded(true);
		}
	}, [
		data,
		isLoading,
		error,
		isSuccess,
		setStockData,
		setStockInfo,
		setLoading,
		setError,
		setHistoryLoaded,
	]);

	return (
		<StockDashboardContext.Provider value={store}>
			{children}
		</StockDashboardContext.Provider>
	);
}

// Helper function to be used by components that need to perform favorite action
export const toggleFavoriteStock = async (
	store: ReturnType<typeof createDashboardStore>,
) => {
	const { isFavorite, stockInfo, setIsFavorite } = store.getState();
	const token = localStorage.getItem("token");
	if (!token) {
		toast.error("Please log in to manage favorites.");
		return;
	}

	const stockTicker = stockInfo.ticker;

	try {
		if (!isFavorite) {
			await authApi(token).post(endpoint.watchlist.list, {
				stock_id: stockTicker,
			});
			setIsFavorite(true);
			toast.success(`${stockTicker} was added to your favorites!`);
		} else {
			// To delete, we need the specific watchlist item ID
			const res = await authApi(token).get(endpoint.watchlist.list);
			const favItem = res.data.find(
				(fav: any) => fav.stock && fav.stock.ticker === stockTicker,
			);

			if (favItem) {
				await authApi(token).delete(endpoint.watchlist.delete(favItem.id));
				setIsFavorite(false);
				toast.error(`${stockTicker} was removed from your favorites.`);
			}
		}
	} catch (err) {
		console.error("Failed to update favorites:", err);
		toast.error("Failed to update favorites. Please try again.");
	}
};
