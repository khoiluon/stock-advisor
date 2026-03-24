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
