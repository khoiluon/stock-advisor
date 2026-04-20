import { ReadyState } from "react-use-websocket";

export const connectionStatus = (readyState: ReadyState) => {
	return {
		[ReadyState.CONNECTING]: "Connecting",
		[ReadyState.OPEN]: "Open",
		[ReadyState.CLOSING]: "Closing",
		[ReadyState.CLOSED]: "Closed",
		[ReadyState.UNINSTANTIATED]: "Uninstantiated",
	}[readyState];
};

export const processRealtimeMessage = (message: MessageEvent<any>) => {
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

		if (content.Symbol === ticker) {
			const newCandleData = {
				date: new Date().toISOString().split("T")[0],
				open: parseFloat(content.Open),
				high: parseFloat(content.High),
				low: parseFloat(content.Low),
				close: parseFloat(content.Close),
				volume: parseInt(content.Volume, 10) || 0,
			};

			setStockData((prevData) => {
				// nếu prevData rỗng -> thêm nến đầu tiên
				if (!prevData || prevData.length === 0) return [newCandleData];

				// **LOGIC SỬA LỖI CỐT LÕI**
				// Luôn đảm bảo mảng hiện tại được sắp xếp trước khi thao tác
				const sortedPrevData = [...prevData].sort(
					(a, b) => new Date(a.date) - new Date(b.date),
				);
				const lastDataPoint = sortedPrevData[sortedPrevData.length - 1];

				if (lastDataPoint.date === newCandleData.date) {
					const updatedLastPoint = {
						...lastDataPoint,
						high: Math.max(lastDataPoint.high, newCandleData.high),
						low: Math.min(lastDataPoint.low, newCandleData.low),
						close: newCandleData.close,
						volume: (lastDataPoint.volume || 0) + (newCandleData.volume || 0),
					};
					return [...sortedPrevData.slice(0, -1), updatedLastPoint];
				} else if (
					new Date(newCandleData.date) > new Date(lastDataPoint.date)
				) {
					// Chỉ thêm nến mới nếu nó thực sự mới hơn
					return [...sortedPrevData, newCandleData];
				}
				// Nếu nến mới cũ hơn hoặc cùng ngày không phù hợp => bỏ qua
				return sortedPrevData;
			});
		}
	}
};
