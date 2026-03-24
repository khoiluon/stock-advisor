export const endpoint = {
	stockData: "/stock-data/",
	stocks: {
		ticker: (ticker: string) => `/stocks/${ticker}/`,
		search: "/stocks/search/",
	},
	watchlist: {
		list: "/watchlist/",
		delete: (id: string) => `/watchlist/${id}/`,
	},
};
