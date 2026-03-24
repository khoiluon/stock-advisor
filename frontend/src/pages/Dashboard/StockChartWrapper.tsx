import LoadingSpinner from "@/components/LoadingSpinner";
import StockChart from "@/components/StockChart";
import { useStockDashboard } from "@/stores/stockDashboardStore";

export function StockChartWrapper() {
	const isLoading = useStockDashboard((state) => state.isLoading);
	const error = useStockDashboard((state) => state.error);
	const stockData = useStockDashboard((state) => state.stockData);
	const ticker = useStockDashboard((state) => state.ticker);
	const maLines = useStockDashboard((state) => state.maLines);
	const indicators = useStockDashboard((state) => state.indicators);

	return (
		<div className="bg-card rounded-xl shadow-lg p-8 min-h-120">
			<div className="text-white font-bold mb-4 text-lg">
				Stock Price Chart with Technical Indicators
			</div>

			{isLoading ? (
				<LoadingSpinner message={`Fetching data for ${ticker}...`} />
			) : error && stockData.length === 0 ? ( // Only show main error if no data
				<div className="text-red-400 text-center py-10">{error}</div>
			) : stockData.length > 0 ? (
				<StockChart
					data={stockData}
					ticker={ticker}
					maLines={maLines}
					indicators={indicators}
				/>
			) : (
				<div className="text-gray-400 text-center py-10">
					No data to display.
				</div>
			)}
		</div>
	);
}
