import { useEffect, useState } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { useStore } from "zustand";
import type { StockDashboardStore } from "@/stores/DashboardStore";

export const useStockDataFeed = (store: StockDashboardStore) => {
	const ticker = useStore(store, (state) => state.stockInfo.ticker);
	const isHistoryLoaded = useStore(store, (state) => state.isHistoryLoaded);

	const setConnectionStatus = useStore(
		store,
		(state) => state.setConnectionStatus,
	);
	const updateStockData = useStore(store, (state) => state.updateStockData);
	const processPendingMessages = useStore(
		store,
		(state) => state.processPendingMessages,
	);
	const addPendingMessage = useStore(store, (state) => state.addPendingMessage);

	const [socketUrl, setSocketUrl] = useState<string | null>(null);

	// 1. Update WebSocket URL when ticker changes
	useEffect(() => {
		if (ticker) {
			setSocketUrl(`${import.meta.env.VITE_WS_URL}/stock/${ticker}/`);
		}
	}, [ticker]);

	const { lastMessage, readyState } = useWebSocket(socketUrl, {
		shouldReconnect: () => true, // Automatically reconnect
	});

	// 2. Map ReadyState to a human-readable connection status and update the store
	useEffect(() => {
		const status = {
			[ReadyState.CONNECTING]: "Connecting",
			[ReadyState.OPEN]: "Open",
			[ReadyState.CLOSING]: "Closing",
			[ReadyState.CLOSED]: "Closed",
			[ReadyState.UNINSTANTIATED]: "Uninstantiated",
		}[readyState];
		setConnectionStatus(status);
	}, [readyState, setConnectionStatus]);

	// 3. Define the message processing logic
	const processRealtimeMessage = (message: MessageEvent<any>) => {
		if (!message || !message.data) return;

		let parsed;
		try {
			parsed = JSON.parse(message.data);
		} catch (e) {
			console.error("Invalid realtime message JSON", e);
			return;
		}

		if (parsed.DataType === "B" && parsed.Content) {
			let content;
			try {
				content = JSON.parse(parsed.Content);
			} catch (e) {
				console.error("Invalid Content JSON in realtime message", e);
				return;
			}

			// Ensure the message is for the currently selected ticker
			if (content.Symbol === ticker) {
				const newCandleData = {
					date: new Date().toISOString().split("T")[0],
					open: parseFloat(content.Open),
					high: parseFloat(content.High),
					low: parseFloat(content.Low),
					close: parseFloat(content.Close),
					volume: parseInt(content.Volume, 10) || 0,
				};
				// Use the action from the store to update the state
				console.log("new stock data!!!");
				updateStockData(newCandleData);
			}
		}
	};

	// 4. Process incoming messages, handling the race condition
	useEffect(() => {
		if (lastMessage === null) return;

		if (isHistoryLoaded) {
			// If history is loaded, process any pending messages first, then the current one
			processPendingMessages(processRealtimeMessage);
			processRealtimeMessage(lastMessage);
		} else {
			// If history is not yet loaded, add the message to the pending queue
			addPendingMessage(lastMessage);
		}
		// Dependencies ensure this runs when a new message arrives or when history is loaded
	}, [lastMessage, isHistoryLoaded]);
};
