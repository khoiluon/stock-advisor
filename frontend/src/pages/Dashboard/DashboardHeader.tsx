import { StarIcon } from "@phosphor-icons/react/dist/csr/Star";
import { FaSearch } from "react-icons/fa";
import { cn } from "tailwind-variants";
import { Button } from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import useFavoritesQuery from "@/services/useFavoritesQuery";
import useToggleFavoriteMutate from "@/services/useToggleFavoriteMutate";
import { useDashboardStore } from "@/stores/DashboardStore";
import { useTickerMenuStore } from "@/stores/TickerMenuStore";
import IndicatorSettingModal from "./IndicatorSettingModal";

export default function DashboardHeader() {
	const connectionStatus = useDashboardStore((state) => state.connectionStatus);
	const stockInfo = useDashboardStore((state) => state.stockInfo);
	const isLoading = useDashboardStore((state) => state.isLoading);
	const setIsOpen = useTickerMenuStore((state) => state.setIsOpen);

	if (isLoading) return null;

	return (
		<div className="flex gap-4 w-full">
			<Card className="flex gap-3 items-center p-2 flex-1">
				<div className="flex items-center space-x-4 ml-1">
					<button
						type="button"
						onClick={() => setIsOpen(true)}
						className={cn(
							"rounded-full flex items-center justify-between gap-2 pl-4",
							"outline -outline-offset-1 outline-slate-600 bg-slate-900",
							"min-w-56 text-sm cursor-pointer",
						)}
					>
						<div className="flex gap-2 items-baseline">
							<div className="font-bold">Ticker:</div>
							<div className="font-mono text-base text-white bg-slate-800 px-1.5 rounded-sm">
								{stockInfo.ticker || "N/A"}
							</div>
						</div>

						<Button size="icon" className="z-10">
							<FaSearch />
						</Button>
					</button>

					<StockFavoriteButton />
				</div>

				<hr className="h-1/2 border-l mx-3" />

				<div className="bg-slate-900 outline outline-slate-600 py-1 px-2 rounded-sm text-sm">
					<div className="font-old text-purple-400">Company</div>
					<div className="font-mono text-right">
						{stockInfo.company_name || "N/A"}
					</div>
				</div>
				<div className="bg-slate-900 outline outline-slate-600 py-1 px-2 rounded-sm text-sm">
					<div className="font-old text-blue-400">Exchange</div>
					<div className="font-mono text-right">
						{stockInfo.exchange || "N/A"}
					</div>
				</div>
				<div className="bg-slate-900 outline outline-slate-600 py-1 px-2 rounded-sm text-sm">
					<div className="font-old text-green-400">Industry</div>
					<div className="font-mono text-right">
						{stockInfo.industry || "N/A"}
					</div>
				</div>
			</Card>

			<Card className="flex items-center p-3 gap-2">
				<div className="flex items-center space-x-4">
					<IndicatorSettingModal />
					<div className="text-sm text-gray-400">WS: {connectionStatus}</div>
				</div>
			</Card>
		</div>
	);
}

function StockFavoriteButton() {
	const { data: favorites } = useFavoritesQuery();
	const { mutate: toggleFavorite } = useToggleFavoriteMutate();
	const stockInfo = useDashboardStore((state) => state.stockInfo);

	const favorited = favorites?.find(
		(fav) => fav.stock.ticker === stockInfo.ticker,
	);

	const handleToggleFavorite = () => {
		if (!stockInfo.ticker) return;

		toggleFavorite({
			stockTicker: stockInfo.ticker,
			favorited: favorited,
		});
	};

	return (
		<Button size="icon" variant="secondary" onClick={handleToggleFavorite}>
			<StarIcon
				size={18}
				weight={favorited ? "fill" : "regular"}
				className={cn(favorited ? "text-yellow-400" : "text-slate-200")}
			/>
		</Button>
	);
}
