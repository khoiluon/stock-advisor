import useStockChart from "@/hooks/useStockChart";
import type { IndicatorSettings, MALine, StockDataPoint } from "../types/Stock";

interface StockChartProps {
	data: StockDataPoint[];
	ticker: string;
	maLines: MALine[];
	indicators: IndicatorSettings;
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
		<div className="w-full h-100 max-w-7xl mx-auto">
			<div ref={chartContainerRef} className="relative w-full h-100" />
		</div>
	);
}
