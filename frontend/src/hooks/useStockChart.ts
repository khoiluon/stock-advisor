import {
	CandlestickSeries,
	ColorType,
	createChart,
	HistogramSeries,
	type IChartApi,
	type ISeriesApi,
	LineSeries,
	type Time,
} from "lightweight-charts";
import {
	createLineToolsPlugin,
	type ILineToolsPlugin,
} from "lightweight-charts-line-tools-core";
import { LineToolFibRetracement } from "lightweight-charts-line-tools-fib-retracement";
import {
	LineToolBrush,
	LineToolHighlighter,
} from "lightweight-charts-line-tools-freehand";
import {
	LineToolArrow,
	LineToolCallout,
	LineToolCrossLine,
	LineToolExtendedLine,
	LineToolHorizontalLine,
	LineToolHorizontalRay,
	LineToolRay,
	LineToolTrendLine,
	LineToolVerticalLine,
} from "lightweight-charts-line-tools-lines";
import { useEffect, useRef } from "react";
import type { IndicatorSettings, MALine, StockDataPoint } from "../types/Stock";
import { LineToolLongShortPosition } from "lightweight-charts-line-tools-long-short-position";

function calculateSMA(data: StockDataPoint[], period: number) {
	if (!data || data.length < period) return [];
	const result = [];
	for (let i = period - 1; i < data.length; i++) {
		const sum = data
			.slice(i - period + 1, i + 1)
			.reduce((acc, d) => acc + d.close, 0);
		result.push({
			time: data[i].date,
			value: Number((sum / period).toFixed(2)),
		});
	}
	return result;
}

function calculateBBands(data: StockDataPoint[], period = 20, multiplier = 2) {
	if (!data || data.length < period) return [];
	const result = [];
	for (let i = period - 1; i < data.length; i++) {
		const slice = data.slice(i - period + 1, i + 1);
		const mean = slice.reduce((acc, d) => acc + d.close, 0) / period;
		const variance =
			slice.reduce((acc, d) => acc + (d.close - mean) ** 2, 0) / period;
		const std = Math.sqrt(variance);
		result.push({
			time: data[i].date,
			upper: Number((mean + multiplier * std).toFixed(2)),
			middle: Number(mean.toFixed(2)),
			lower: Number((mean - multiplier * std).toFixed(2)),
		});
	}
	return result;
}

function calculateRSI(data: StockDataPoint[], period = 14) {
	if (!data || data.length < period + 1) return [];
	const result = [];
	let avgGain = 0;
	let avgLoss = 0;

	for (let i = 1; i <= period; i++) {
		const change = data[i].close - data[i - 1].close;
		if (change > 0) avgGain += change;
		else avgLoss += Math.abs(change);
	}
	avgGain /= period;
	avgLoss /= period;

	const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
	result.push({
		time: data[period].date,
		value: Number((100 - 100 / (1 + rs)).toFixed(2)),
	});

	for (let i = period + 1; i < data.length; i++) {
		const change = data[i].close - data[i - 1].close;
		const gain = change > 0 ? change : 0;
		const loss = change < 0 ? Math.abs(change) : 0;
		avgGain = (avgGain * (period - 1) + gain) / period;
		avgLoss = (avgLoss * (period - 1) + loss) / period;
		const rsVal = avgLoss === 0 ? 100 : avgGain / avgLoss;
		result.push({
			time: data[i].date,
			value: Number((100 - 100 / (1 + rsVal)).toFixed(2)),
		});
	}
	return result;
}

function calculateMACD(
	data: StockDataPoint[],
	fast = 12,
	slow = 26,
	signal = 9,
) {
	if (!data || data.length < slow) return []; // Cần đủ dữ liệu để tính toán
	const ema = (closeArr: number[], period: number) => {
		const k = 2 / (period + 1);
		const emaArr = [];
		if (closeArr.length > 0 && closeArr[0] !== undefined) {
			emaArr.push(closeArr[0]);
			for (let i = 1; i < closeArr.length; i++) {
				emaArr.push(closeArr[i] * k + emaArr[i - 1] * (1 - k));
			}
		}
		return emaArr;
	};
	const fastEMA = ema(
		data.map((d) => d.close),
		fast,
	);
	const slowEMA = ema(
		data.map((d) => d.close),
		slow,
	);
	const macdLine = fastEMA.map((val, i) => val - slowEMA[i]);
	const signalLineData = macdLine.map((value, i) => ({
		close: value,
		date: data[i].date,
	}));
	const signalLine = ema(
		signalLineData.map((d) => d.close),
		signal,
	);
	const histogram = macdLine.map((val, i) => val - signalLine[i]);
	return data.map((d, i) => ({
		time: d.date,
		macd: macdLine[i],
		signal: signalLine[i],
		hist: histogram[i],
	}));
}

const toUnixTime = (dateStr: string | Date | number) => {
	// Lấy ra thời gian UNIX theo đúng định dạng giây
	return Math.floor(new Date(dateStr).getTime() / 1000) as Time;
};

/**
 * Hook quản lý logic khởi tạo và điều khiển biểu đồ chứng khoán
 * * @description
 * - Khởi tạo thực thể biểu đồ và quản lý vòng đời (mount/unmount).
 * - Xử lý tính toán và hiển thị các lớp dữ liệu (Candlestick, Volume) và chỉ báo kỹ thuật (MA, MACD, RSI, BBands).
 * - Tự động cập nhật giao diện biểu đồ khi dữ liệu hoặc cấu hình chỉ báo thay đổi.
 */
export default function useStockChart({
	data,
	maLines,
	indicators,
}: {
	data: StockDataPoint[];
	maLines: MALine[];
	indicators: IndicatorSettings;
}) {
	const chartContainerRef = useRef<HTMLDivElement | null>(null);
	const chartRef = useRef<IChartApi | null>(null);
	const seriesRefs = useRef<{
		candle: ISeriesApi<"Candlestick"> | null;
		volume: ISeriesApi<"Histogram"> | null;
		ma: Record<number, ISeriesApi<"Line">>;
		bbands: Record<string, ISeriesApi<"Line">>;
		macd: Record<string, ISeriesApi<"Line"> | ISeriesApi<"Histogram">>;
		rsi: Record<string, ISeriesApi<"Line">>;
	}>({
		candle: null,
		volume: null,
		ma: {},
		bbands: {},
		macd: {},
		rsi: {},
	});
	const lineToolsRef = useRef<ILineToolsPlugin | null>(null);

	// Khởi tạo Chart (chỉ chạy 1 lần)
	useEffect(() => {
		if (!chartContainerRef.current) return;

		chartContainerRef.current.innerHTML = "";

		const chart = createChart(chartContainerRef.current, {
			layout: {
				background: { type: ColorType.Solid, color: "#0F172B" },
				textColor: "#94a3b8",
			},
			grid: {
				vertLines: { color: "#1D293D" },
				horzLines: { color: "#1D293D" },
			},
			timeScale: { borderColor: "#475569", timeVisible: true },
		});

		chartRef.current = chart;

		const candleSeries = chart.addSeries(CandlestickSeries, {
			upColor: "#22c55e",
			downColor: "#ef4444",
			borderVisible: false,
			wickUpColor: "#22c55e",
			wickDownColor: "#ef4444",
		});
		seriesRefs.current.candle = candleSeries;

		const lineTools = createLineToolsPlugin(chart, candleSeries);

		lineTools.registerLineTool("TrendLine", LineToolTrendLine);
		lineTools.registerLineTool("Ray", LineToolRay);
		lineTools.registerLineTool("Arrow", LineToolArrow);
		lineTools.registerLineTool("ExtendedLine", LineToolExtendedLine);
		lineTools.registerLineTool("HorizontalLine", LineToolHorizontalLine);
		lineTools.registerLineTool("HorizontalRay", LineToolHorizontalRay);
		lineTools.registerLineTool("VerticalLine", LineToolVerticalLine);
		lineTools.registerLineTool("CrossLine", LineToolCrossLine);
		lineTools.registerLineTool("Callout", LineToolCallout);

		lineTools.registerLineTool("FibRetracement", LineToolFibRetracement);

		lineTools.registerLineTool("LongShortPosition", LineToolLongShortPosition);

		lineTools.registerLineTool("Brush", LineToolBrush);
		lineTools.registerLineTool("Highlighter", LineToolHighlighter);

		lineToolsRef.current = lineTools;

		const volumeSeries = chart.addSeries(HistogramSeries, {
			priceFormat: { type: "volume" },
			priceScaleId: "volume_scale",
		});
		seriesRefs.current.volume = volumeSeries;

		const handleResize = () => {
			if (chartContainerRef.current && chartRef.current) {
				chartRef.current.applyOptions({
					width: chartContainerRef.current.clientWidth,
				});
			}
		};
		window.addEventListener("resize", handleResize);

		return () => {
			window.removeEventListener("resize", handleResize);
			if (chartRef.current) {
				chartRef.current.remove();
				chartRef.current = null;
			}
			lineToolsRef.current = null;
		};
	}, []);

	// 2. Cập nhật dữ liệu & Indicators
	useEffect(() => {
		// Log removed: log("data, maLines, indicators thay doi", ...)

		if (!chartRef.current || !data || data.length === 0) return;

		const chart = chartRef.current;
		const refs = seriesRefs.current;

		// --- Xử lý dữ liệu ---
		const sortedData = [...data].sort(
			(a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
		);
		const candlestickData = sortedData.map((d) => ({
			// time: d.date,
			time: toUnixTime(d.date),
			open: d.open,
			high: d.high,
			low: d.low,
			close: d.close,
		}));
		const volumeData = sortedData.map((d) => ({
			// time: d.date,
			time: toUnixTime(d.date),
			value: d.volume,
			color:
				d.close >= d.open ? "rgba(34, 197, 94, 0.5)" : "rgba(239, 68, 68, 0.5)",
		}));

		if (refs.candle) refs.candle.setData(candlestickData);
		if (refs.volume) refs.volume.setData(volumeData);

		// --- Moving Averages ---
		const currentMaPeriods = new Set(maLines.map((l) => l.period));
		Object.keys(refs.ma).forEach((periodStr) => {
			const period = Number(periodStr);
			if (!currentMaPeriods.has(period)) {
				chart.removeSeries(refs.ma[period]);
				delete refs.ma[period];
			}
		});

		const maColors = { 20: "#38bdf8", 50: "#a78bfa", 200: "#facc15" };
		maLines.forEach((line) => {
			const period = line.period;
			if (!refs.ma[period]) {
				refs.ma[period] = chart.addSeries(LineSeries, {
					color: maColors[period as keyof typeof maColors] || "#FFFFFF",
					lineWidth: 2,
				});
			}
			const maData = calculateSMA(sortedData, period);
			refs.ma[period].setData(maData);
		});

		// --- Bollinger Bands ---
		if (indicators.bbands?.visible) {
			if (!refs.bbands.upper) {
				refs.bbands.upper = chart.addSeries(LineSeries, {
					color: "rgba(59,130,246,0.5)",
					lineWidth: 1,
				});
				refs.bbands.middle = chart.addSeries(LineSeries, {
					color: "rgba(250, 204, 21, 0.5)",
					lineWidth: 1,
					lineStyle: 2,
				});
				refs.bbands.lower = chart.addSeries(LineSeries, {
					color: "rgba(59,130,246,0.5)",
					lineWidth: 1,
				});
			}
			const bbandsData = calculateBBands(sortedData, 20, 2);
			refs.bbands.upper.setData(
				bbandsData.map((d) => ({ time: d.time, value: d.upper })),
			);
			refs.bbands.middle.setData(
				bbandsData.map((d) => ({ time: d.time, value: d.middle })),
			);
			refs.bbands.lower.setData(
				bbandsData.map((d) => ({ time: d.time, value: d.lower })),
			);
		} else if (refs.bbands.upper) {
			chart.removeSeries(refs.bbands.upper);
			chart.removeSeries(refs.bbands.middle);
			chart.removeSeries(refs.bbands.lower);
			refs.bbands = {};
		}

		// --- MACD ---
		let macdCreated = false;
		if (indicators.macd?.visible) {
			macdCreated = true;
			if (!refs.macd.macdSeries) {
				refs.macd.macdSeries = chart.addSeries(LineSeries, {
					color: "#38bdf8",
					lineWidth: 2,
					priceScaleId: "macd",
				});
				refs.macd.signalSeries = chart.addSeries(LineSeries, {
					color: "#a78bfa",
					lineWidth: 2,
					lineStyle: 2,
					priceScaleId: "macd",
				});
				refs.macd.histSeries = chart.addSeries(HistogramSeries, {
					priceScaleId: "macd",
				});
			}
			const macdData = calculateMACD(
				sortedData,
				indicators.macd.fast,
				indicators.macd.slow,
				indicators.macd.signal,
			);
			refs.macd.macdSeries.setData(
				macdData.map((d) => ({ time: d.time, value: d.macd })),
			);
			refs.macd.signalSeries.setData(
				macdData.map((d) => ({ time: d.time, value: d.signal })),
			);
			refs.macd.histSeries.setData(
				macdData.map((d) => ({
					time: d.time,
					value: d.hist,
					color: d.hist >= 0 ? "#22c55e" : "#ef4444",
				})),
			);
		} else if (refs.macd.macdSeries) {
			chart.removeSeries(refs.macd.macdSeries);
			chart.removeSeries(refs.macd.signalSeries);
			chart.removeSeries(refs.macd.histSeries);
			refs.macd = {};
		}

		// --- RSI ---
		if (indicators.rsi?.visible) {
			if (!refs.rsi.series) {
				refs.rsi.series = chart.addSeries(LineSeries, {
					color: "#fcd34d",
					lineWidth: 2,
					priceScaleId: "rsi",
				});
				refs.rsi.series.createPriceLine({
					price: 70,
					color: "#ef4444",
					lineWidth: 1,
					lineStyle: 2,
					title: "Overbought",
				});
				refs.rsi.series.createPriceLine({
					price: 30,
					color: "#22c55e",
					lineWidth: 1,
					lineStyle: 2,
					title: "Oversold",
				});
			}
			const rsiData = calculateRSI(sortedData, 14);
			refs.rsi.series.setData(rsiData);
		} else if (refs.rsi.series) {
			chart.removeSeries(refs.rsi.series);
			refs.rsi = {};
		}

		// --- Cấu hình layout động ---
		const bbandsVisible = indicators.bbands?.visible;
		const macdVisible = macdCreated;
		const rsiVisible = indicators.rsi?.visible;

		if (macdVisible && rsiVisible) {
			// Price (40%) | Volume (20%) | MACD (20%) | RSI (20%) với 1% khoảng trống
			chart
				.priceScale("right")
				.applyOptions({ scaleMargins: { top: 0.05, bottom: 0.55 } });
			chart.priceScale("volume_scale").applyOptions({
				scaleMargins: { top: 0.46, bottom: 0.34 },
				visible: false,
			});
			chart
				.priceScale("macd")
				.applyOptions({ scaleMargins: { top: 0.67, bottom: 0.17 } });
			chart
				.priceScale("rsi")
				.applyOptions({ scaleMargins: { top: 0.84, bottom: 0.0 } });
		} else if (macdVisible) {
			// Price (40%) | Volume (20%) | MACD (40%) với 1% khoảng trống
			chart
				.priceScale("right")
				.applyOptions({ scaleMargins: { top: 0.05, bottom: 0.55 } });
			chart.priceScale("volume_scale").applyOptions({
				scaleMargins: { top: 0.46, bottom: 0.34 },
				visible: false,
			});
			chart
				.priceScale("macd")
				.applyOptions({ scaleMargins: { top: 0.67, bottom: 0.0 } });
		} else if (rsiVisible) {
			// Price (40%) | Volume (20%) | RSI (40%) với 1% khoảng trống
			chart
				.priceScale("right")
				.applyOptions({ scaleMargins: { top: 0.05, bottom: 0.55 } });
			chart.priceScale("volume_scale").applyOptions({
				scaleMargins: { top: 0.46, bottom: 0.34 },
				visible: false,
			});
			chart
				.priceScale("rsi")
				.applyOptions({ scaleMargins: { top: 0.67, bottom: 0.0 } });
		} else {
			// Layout mặc định
			chart
				.priceScale("right")
				.applyOptions({ scaleMargins: { top: 0.1, bottom: 0.3 } });
			chart.priceScale("volume_scale").applyOptions({
				scaleMargins: { top: 0.8, bottom: 0 },
				visible: false,
			});
		}
	}, [data, maLines, indicators]);

	return { chartContainerRef, lineTools: lineToolsRef };
}
