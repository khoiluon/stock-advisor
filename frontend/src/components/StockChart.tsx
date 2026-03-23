import useStockChart from "@/hooks/use-stock-chart";
import type { Indicators, MALine, StockDataPoint } from "../types/Stock";

interface StockChartProps {
	data: StockDataPoint[];
	ticker: string;
	maLines: MALine[];
	indicators: Indicators;
}

export default function StockChart({
	data,
	ticker,
	maLines,
	indicators,
}: StockChartProps) {
	const chartContainerRef = useStockChart({
		data,
		ticker,
		maLines,
		indicators,
	});

	return (
		<div className="w-full h-[400px] max-w-7xl mx-auto">
			<div ref={chartContainerRef} className="relative w-full h-[400px]" />
		</div>
	);
}
