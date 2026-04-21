export const endpoint = {
	stockData: "/stock-data/",
	stocks: {
		ticker: (ticker: string) => `/stocks/${ticker}/`,
		search: "/stocks/search/",
	},
	watchlist: {
		list: "/watchlist/",
		add: "/watchlist/",
		delete: (id: string) => `/watchlist/${id}/`,
	},
	screener: "/screener/",
	ml: {
		predictions: "/ml/predictions/",
		predictionDetail: (ticker: string) => `/ml/predictions/${ticker}/`,
		marketState: "/ml/market-state/",
		anomalies: "/ml/anomalies/",
		modelInfo: "/ml/model-info/",
	},
};
