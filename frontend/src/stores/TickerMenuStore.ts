import { createStore, useStore } from "zustand";

export type TickerMenuState = {
	isOpen: boolean;
	selectedTicker: string | null;
};

export type TickerMenuActions = {
	setIsOpen: (isOpen: boolean) => void;
	toggleOpen: () => void;
	setSelectedTicker: (selectedTicker: string | null) => void;
};

export const tickerMenuStore = createStore<TickerMenuState & TickerMenuActions>(
	(set) => ({
		isOpen: false,
		selectedTicker: null,

		setIsOpen: (isOpen: boolean) => {
			set({ isOpen });
		},
		toggleOpen: () => {
			set((state) => ({ isOpen: !state.isOpen }));
		},
		setSelectedTicker: (selectedTicker: string | null) => {
			set({ selectedTicker });
		},
	}),
);

export const useTickerMenuStore = <T>(
	selector: (state: TickerMenuState & TickerMenuActions) => T,
): T => useStore(tickerMenuStore, selector);
