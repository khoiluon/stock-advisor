import { createContext, useContext } from "react";
import { createStore, useStore } from "zustand";
import type {
	IndicatorSettings,
	MALine,
	StockDataPoint,
	StockInfo,
} from "@/types/Stock";

export type StockDashboardState = {
	// App state
	ticker: string;
	error: string | null;
	isLoading: boolean;
	isHistoryLoaded: boolean;
	connectionStatus: string;
	pendingMessages: any[]; // Raw WebSocket messages

	// Data state
	stockData: StockDataPoint[];
	stockInfo: Partial<StockInfo>;
	isFavorite: boolean;

	// Indicator state
	maLines: MALine[];
	indicators: IndicatorSettings;
};

export type StockDashboardActions = {
	setTicker: (ticker: string) => void;
	setError: (error: string | null) => void;
	setLoading: (isLoading: boolean) => void;
	setHistoryLoaded: (isLoaded: boolean) => void;
	setConnectionStatus: (status: string) => void;
	addPendingMessage: (message: any) => void;
	clearPendingMessages: () => void;
	processPendingMessages: (processor: (message: any) => void) => void;

	setStockData: (data: StockDataPoint[]) => void;
	updateStockData: (newCandle: StockDataPoint) => void;
	setStockInfo: (info: Partial<StockInfo>) => void;
	setIsFavorite: (isFavorite: boolean) => void;

	setIndicators: (indicators: StockDashboardState["indicators"]) => void;
	addMaLine: () => void;
	updateMaLine: (id: number, period: number) => void;
	removeMaLine: (id: number) => void;
};

// --- STORE CREATION ---

export type StockDashboardStore = ReturnType<typeof createStockDashboardStore>;

export const createStockDashboardStore = (
	initProps?: Partial<StockDashboardState>,
) => {
	const DEFAULT_PROPS: StockDashboardState = {
		ticker: "VIC",
		error: null,
		isLoading: true,
		isHistoryLoaded: false,
		connectionStatus: "Uninstantiated",
		pendingMessages: [],
		stockData: [],
		stockInfo: {},
		isFavorite: false,
		maLines: [],
		indicators: {
			rsi: { visible: false, period: 14 },
			macd: { visible: false, fast: 12, slow: 26, signal: 9 },
			bbands: { visible: false, period: 20, std: 2 },
		},
	};

	return createStore<StockDashboardState & StockDashboardActions>()(
		(set, get) => ({
			...DEFAULT_PROPS,
			...initProps,

			// --- ACTIONS ---
			setTicker: (ticker) =>
				set({
					ticker,
					isHistoryLoaded: false,
					stockData: [],
					pendingMessages: [],
				}),
			setError: (error) => set({ error }),
			setLoading: (isLoading) => set({ isLoading }),
			setHistoryLoaded: (isLoaded) => set({ isHistoryLoaded: isLoaded }),
			setConnectionStatus: (status) => set({ connectionStatus: status }),
			addPendingMessage: (message) =>
				set((state) => ({
					pendingMessages: [...state.pendingMessages, message],
				})),
			clearPendingMessages: () => set({ pendingMessages: [] }),
			processPendingMessages: (processor) => {
				get().pendingMessages.forEach(processor);
				set({ pendingMessages: [] });
			},

			setStockData: (data) => set({ stockData: data }),
			updateStockData: (newCandle) => {
				set((state) => {
					const sortedPrevData = [...state.stockData].sort(
						(a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
					);
					const lastDataPoint = sortedPrevData[sortedPrevData.length - 1];

					if (lastDataPoint && lastDataPoint.date === newCandle.date) {
						const updatedLastPoint = {
							...lastDataPoint,
							high: Math.max(lastDataPoint.high, newCandle.high),
							low: Math.min(lastDataPoint.low, newCandle.low),
							close: newCandle.close,
							volume: (lastDataPoint.volume || 0) + (newCandle.volume || 0),
						};
						return {
							stockData: [...sortedPrevData.slice(0, -1), updatedLastPoint],
						};
					} else if (
						!lastDataPoint ||
						new Date(newCandle.date) > new Date(lastDataPoint.date)
					) {
						return { stockData: [...sortedPrevData, newCandle] };
					}
					return { stockData: sortedPrevData }; // No change
				});
			},
			setStockInfo: (info) => set({ stockInfo: info }),
			setIsFavorite: (isFavorite) => set({ isFavorite }),

			setIndicators: (indicators) => set({ indicators }),
			addMaLine: () =>
				set((state) => ({
					maLines: [...state.maLines, { id: Date.now(), period: 20 }],
				})),
			updateMaLine: (id, period) =>
				set((state) => ({
					maLines: state.maLines.map((line) =>
						line.id === id ? { ...line, period: Number(period) } : line,
					),
				})),
			removeMaLine: (id) =>
				set((state) => ({
					maLines: state.maLines.filter((line) => line.id !== id),
				})),
		}),
	);
};

// --- CONTEXT AND HOOK ---

export const StockDashboardContext = createContext<StockDashboardStore | null>(
	null,
);

export function useStockDashboard<T>(
	selector: (state: StockDashboardState & StockDashboardActions) => T,
): T {
	const store = useContext(StockDashboardContext);
	if (!store) {
		throw new Error(
			"useStockDashboard must be used within a StockDashboardProvider",
		);
	}
	return useStore(store, selector);
}
