import { useContext } from "react";
import { FaStar } from "react-icons/fa";
import { FiStar } from "react-icons/fi";
import { Button } from "@/components/ui/Button";
import { toggleFavoriteStock } from "@/providers/StockDashboardProvider";
import {
	StockDashboardContext,
	useStockDashboard,
} from "@/stores/stockDashboardStore";

export const StockInfoHeader = () => {
	const store = useContext(StockDashboardContext);

	const ticker = useStockDashboard((state) => state.ticker);
	const stockInfo = useStockDashboard((state) => state.stockInfo);
	const isFavorite = useStockDashboard((state) => state.isFavorite);

	const handleToggleFavorite = () => {
		if (store) {
			toggleFavoriteStock(store);
		}
	};

	return (
		<div className="bg-card rounded-xl shadow-lg p-8 flex flex-col md:flex-row items-center justify-between">
			<div className="flex-1">
				<div className="flex items-center mb-2">
					<span className="text-2xl font-bold text-white mr-2">
						{stockInfo.ticker || ticker}
					</span>
					<Button
						variant="secondary"
						size="icon"
						onClick={handleToggleFavorite}
					>
						{isFavorite ? (
							<FaStar color="#FFD700" size={22} />
						) : (
							<FiStar color="#fff" size={22} />
						)}
					</Button>
				</div>
				<div className="text-gray-300 mb-2">
					{stockInfo.company_name || "--"}
				</div>

				<div className="flex space-x-6 mt-4">
					<div className="bg-[#1a2332] rounded-lg px-4 py-2 flex items-center">
						<span className="mr-2 text-blue-400">Exchange</span>
						<div>
							<div className="text-xs text-gray-400">Market</div>
							<div className="font-bold text-white text-lg">
								{stockInfo.exchange || "--"}
							</div>
						</div>
					</div>
					<div className="bg-[#1a2332] rounded-lg px-4 py-2 flex items-center">
						<span className="mr-2 text-green-400">Industry</span>
						<div>
							<div className="text-xs text-gray-400">Sector</div>
							<div className="font-bold text-white text-lg">
								{stockInfo.industry || "--"}
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
};
