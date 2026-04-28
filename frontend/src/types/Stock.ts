export type StockInfo = {
	ticker: string;
	company_name: string;
	exchange: string;
	industry: string | null;
};

/**
 * Định nghĩa cho một điểm dữ liệu lịch sử giá của cổ phiếu.
 * Bao gồm giá OHLC, khối lượng và có thể chứa các giá trị chỉ báo đã được tính
 * toán trước.
 */
export type StockDataPoint = {
	/**
	 * Ngày, định dạng chuỗi (yyyy-mm-dd)
	 */
	date: string;

	/**
	 * Giá mở cửa
	 */
	open: number;

	/**
	 * Giá cao nhất
	 */
	high: number;

	/**
	 * Giá thấp nhất
	 */
	low: number;

	/**
	 * Giá đóng cửa
	 */
	close: number;

	/**
	 * Khối lượng giao dịch
	 */
	volume: number;

	// biome-ignore lint/suspicious/noExplicitAny: Cho phép bất kỳ thuộc tính khác từ API (như RSI, BBands)
	[key: string]: any;
};

/**
 * Một cấu hình đường Moving Average (MA).
 */
export type MALine = {
	id: number;
	period: number;
};

/**
 * Object chứa cấu hình của tất cả các chỉ báo
 */
export type IndicatorSettings = {
	rsi: {
		visible: boolean;
		period: number;
	};
	macd: {
		visible: boolean;
		fast: number;
		slow: number;
		signal: number;
	};
	bbands: {
		visible: boolean;
		period: number;
		std: number;
	};
};

export type UserFavorite = {
	id: number;
	stock: StockInfo;
	added_at: Date;
};

// ── ML Types ──

export type Suggestion = {
	stock: StockInfo;
	analysis_date: string;
	current_price: number;
	target_price: number;
	stop_loss: number;
	timeframe: string;
	confidence: number;
	score: number;
	key_reasons: string[];
	reason: string;
};

export type MarketStateData = {
	current: {
		id: number;
		date: string;
		state: "UPTREND" | "DOWNTREND" | "SIDEWAY";
		confidence: number;
		details: Record<string, unknown> | null;
	} | null;
	history: Array<{
		id: number;
		date: string;
		state: "UPTREND" | "DOWNTREND" | "SIDEWAY";
		confidence: number;
		details: Record<string, unknown> | null;
	}>;
};

export type AnomalyAlert = {
	id: number;
	stock: StockInfo;
	detected_at: string;
	anomaly_type: string;
	anomaly_score: number;
	details: Record<string, unknown>;
};

export type MLModelInfo = {
	total_active_models: number;
	models: Array<{
		id: number;
		name: string;
		model_type: string;
		version: string;
		features_used: string[];
		metrics: Record<string, number>;
		trained_at: string;
		is_active: boolean;
	}>;
};
