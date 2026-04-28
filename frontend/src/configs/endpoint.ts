export const endpoint = {
	login: "/login/",
	register: "/register/",
	stockData: "/stock-data/",
	chat: "/chat/",
	stocks: {
		ticker: (ticker: string) => `/stocks/${ticker}/`,
		search: "/stocks/search/",
	},
	watchlist: {
		list: "/watchlist/",
		add: "/watchlist/",
		delete: (id: string) => `/watchlist/${id}/`,
	},
<<<<<<< HEAD
	screener: "/screener/",
	ml: {
		predictions: "/ml/predictions/",
		predictionDetail: (ticker: string) => `/ml/predictions/${ticker}/`,
		marketState: "/ml/market-state/",
		anomalies: "/ml/anomalies/",
		modelInfo: "/ml/model-info/",
	},
=======
>>>>>>> hiepdangcode
};
