import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDebounce } from "@/hooks/useDebounce";
import { useTickerQuery } from "@/services/useTickerQuery";
import { useTickerMenuStore } from "@/stores/TickerMenuStore";
import CommandMenu from "./ui/CommandMenu";
import H3 from "./ui/H3";

export default function TickerSelectCmdk() {
	const navigate = useNavigate();

	const isOpen = useTickerMenuStore((state) => state.isOpen);
	const setIsOpen = useTickerMenuStore((state) => state.setIsOpen);
	const toggleOpen = useTickerMenuStore((state) => state.toggleOpen);

	const [query, setQuery] = useState<string>("");
	const debouncedQuery = useDebounce(query, 300);

	const { data: tickers } = useTickerQuery(debouncedQuery);

	// Xử lý sự kiện "Ctrl + K" để đóng/mở menu
	useEffect(() => {
		const down = (e: KeyboardEvent) => {
			if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
				e.preventDefault();
				toggleOpen();
			}
		};

		document.addEventListener("keydown", down);
		return () => document.removeEventListener("keydown", down);
	}, [toggleOpen]);

	const handleSelect = (ticker: string) => {
		navigate(`/?ticker=${ticker}`);
		setIsOpen(false);
	};

	return (
		<CommandMenu
			isOpen={isOpen}
			onRequestClose={() => setIsOpen(false)}
			className="min-w-xl h-160"
		>
			<H3>Ticker Search</H3>
			<CommandMenu.Input
				placeholder="Search tickers..."
				autoFocus
				value={query}
				onValueChange={setQuery}
			/>
			<CommandMenu.List>
				<CommandMenu.Group>
					{tickers?.map((ticker) => (
						<CommandMenu.Item
							key={ticker.ticker}
							value={ticker.ticker}
							className="flex gap-2 items-center p-2 cursor-pointer"
							onSelect={handleSelect}
						>
							<div className="px-2 py-1 bg-blue-900 border border-slate-600 text-blue-50 rounded-xs font-mono text-sm w-fit">
								{ticker.ticker}
							</div>
							<div>{ticker.company_name}</div>
							<div className="ml-auto text-xs text-slate-400">
								{ticker.exchange}
							</div>
						</CommandMenu.Item>
					))}
				</CommandMenu.Group>
			</CommandMenu.List>
		</CommandMenu>
	);
}
