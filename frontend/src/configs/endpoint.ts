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
};
