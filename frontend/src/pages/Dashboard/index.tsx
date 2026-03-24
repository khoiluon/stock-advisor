import { useStockDashboard } from "@/stores/stockDashboardStore";
import Header from "./Header";
import { StockChartWrapper } from "./StockChartWrapper";
import { StockInfoHeader } from "./StockInfoHeader";
import TickerSelection from "./TickerSelection";

const Dashboard = () => {
	const error = useStockDashboard((state) => state.error);

	return (
		<div>
			<main className="px-10 pt-4 space-y-4">
				<Header />
				<TickerSelection />

				{error && (
					<div className="bg-red-900/20 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg mb-6">
						{error}
					</div>
				)}

				<StockInfoHeader />
				<StockChartWrapper />
			</main>
		</div>
	);
};

export default Dashboard;
