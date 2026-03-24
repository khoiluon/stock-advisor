import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useSearchParams } from "react-router-dom";
import { useStore } from "zustand";
import { authApi } from "@/configs/axios";
import { endpoint } from "@/configs/endpoint";
import { useStockDataFeed } from "@/hooks/useStockDataFeed";
import {
	createStockDashboardStore,
	StockDashboardContext,
} from "@/stores/stockDashboardStore";

type StockDashboardProviderProps = {
	children: React.ReactNode;
};

export const StockDashboardProvider = ({
	children,
}: StockDashboardProviderProps) => {
	const [searchParams] = useSearchParams();
	const initialTicker = searchParams.get("ticker") || "VIC";

	const [store] = useState(() =>
		createStockDashboardStore({ ticker: initialTicker }),
	);
	const ticker = useStore(store, (state) => state.ticker);
	const setLoading = useStore(store, (state) => state.setLoading);
	const setError = useStore(store, (state) => state.setError);
	const setStockData = useStore(store, (state) => state.setStockData);
	const setStockInfo = useStore(store, (state) => state.setStockInfo);
	const setHistoryLoaded = useStore(store, (state) => state.setHistoryLoaded);
	const setIsFavorite = useStore(store, (state) => state.setIsFavorite);

	useStockDataFeed(store);

	// Effect to fetch initial historical data and stock info
	useEffect(() => {
		const fetchData = async () => {
			const currentTicker = ticker;
			console.log("fetch cổ phiếu:", currentTicker);
			setLoading(true);
			setError(null);
			setHistoryLoaded(false); // Reset history loaded flag

			const token = localStorage.getItem("token");
			if (!token) {
				setError("You are not logged in.");
				setLoading(false);
				return;
			}

			try {
				const [stockRes, infoRes, favRes] = await Promise.all([
					authApi(token).get(endpoint.stockData, {
						params: { ticker: currentTicker },
					}),
					authApi(token).get(endpoint.stocks.ticker(currentTicker)),
					authApi(token).get(endpoint.watchlist.list),
				]);

				// Process and set stock data
				if (stockRes.data && stockRes.data.length > 0) {
					const sortedData = stockRes.data.sort(
						(a: any, b: any) =>
							new Date(a.date).getTime() - new Date(b.date).getTime(),
					);
					setStockData(sortedData);
				} else {
					setStockData([]);
					setError(`No historical data found for ${currentTicker}.`);
				}

				// Process and set stock info
				setStockInfo(infoRes.data || {});

				// Process and set favorite status
				setIsFavorite(
					favRes.data.some(
						(fav: any) =>
							fav.stock &&
							fav.stock.ticker === (infoRes.data.ticker || currentTicker),
					),
				);
			} catch (err: any) {
				setError(
					err.response
						? err.response.data.error || JSON.stringify(err.response.data)
						: "Cannot connect to server.",
				);
				setStockData([]);
				setStockInfo({});
			} finally {
				setLoading(false);
				// CRITICAL: Signal that history is loaded, allowing WebSocket messages to be processed
				setHistoryLoaded(true);
			}
		};

		fetchData();
	}, [
		setLoading,
		setStockData,
		setStockInfo,
		setIsFavorite,
		setError,
		setHistoryLoaded,
		ticker,
	]);

	return (
		<StockDashboardContext.Provider value={store}>
			{children}
		</StockDashboardContext.Provider>
	);
};

// Helper function to be used by components that need to perform favorite action
export const toggleFavoriteStock = async (
	store: ReturnType<typeof createStockDashboardStore>,
) => {
	const { isFavorite, stockInfo, ticker, setIsFavorite } = store.getState();
	const token = localStorage.getItem("token");
	if (!token) {
		toast.error("Please log in to manage favorites.");
		return;
	}

	const stockTicker = stockInfo.ticker || ticker;

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
