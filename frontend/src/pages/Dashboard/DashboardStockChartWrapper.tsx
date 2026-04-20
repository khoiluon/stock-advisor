import LoadingSpinner from "@/components/LoadingSpinner";
import StockChart from "@/components/StockChart";
import Card from "@/components/ui/Card";
import { useDashboardStore } from "@/stores/DashboardStore";

export function DashboardStockChartWrapper() {
	const isLoading = useDashboardStore((state) => state.isLoading);
	const error = useDashboardStore((state) => state.error);
	const stockData = useDashboardStore((state) => state.stockData);
	const maLines = useDashboardStore((state) => state.maLines);
	const indicators = useDashboardStore((state) => state.indicators);

	return (
		<Card className="min-h-0 flex-1">
			{isLoading ? (
				<LoadingSpinner />
			) : error && stockData.length === 0 ? (
				<div className="text-red-400 text-center py-10">{error}</div>
			) : stockData.length > 0 ? (
				<StockChart
					data={stockData}
					maLines={maLines}
					indicators={indicators}
				/>
			) : (
				<div className="text-gray-400 text-center py-10">
					No data to display.
				</div>
			)}
		</Card>
	);
}
