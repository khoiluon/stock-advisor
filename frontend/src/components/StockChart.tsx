import { useStockChart } from "../hooks/use-stock-chart";
import { Indicators, MALine, StockDataPoint } from "../types/Stock";

const StockChart = ({
	data,
	ticker,
	maLines,
	indicators,
}: {
	data: StockDataPoint[];
	ticker: string;
	maLines: MALine[];
	indicators: Indicators;
}) => {
	const chartContainerRef = useStockChart({
		data,
		ticker,
		maLines,
		indicators,
	});

	return (
		<div
			style={{ width: "100%", maxWidth: 1200, margin: "0 auto", height: 400 }}
		>
			<div
				ref={chartContainerRef}
				style={{ position: "relative", width: "100%", height: 400 }}
			/>
		</div>
	);
};

export default StockChart;
