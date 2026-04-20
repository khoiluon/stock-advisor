import { ArrowUpRightIcon } from "@phosphor-icons/react/dist/csr/ArrowUpRight";
import { EraserIcon } from "@phosphor-icons/react/dist/csr/Eraser";
import { LineSegmentIcon } from "@phosphor-icons/react/dist/csr/LineSegment";
import { ListIcon } from "@phosphor-icons/react/dist/csr/List";
import { PaintBrushIcon } from "@phosphor-icons/react/dist/csr/PaintBrush";
import { PaletteIcon } from "@phosphor-icons/react/dist/csr/Palette";
import { RowsIcon } from "@phosphor-icons/react/dist/csr/Rows";
import { TextAaIcon } from "@phosphor-icons/react/dist/csr/TextAa";
import type {
	ILineToolsPlugin,
	LineOptions,
	LineToolExport,
	LineToolsSelectEventParams,
	LineToolType,
} from "lightweight-charts-line-tools-core";
import { useEffect, useState } from "react";
import { cn } from "tailwind-variants";
import useStockChart from "@/hooks/useStockChart";
import type { IndicatorSettings, MALine, StockDataPoint } from "../types/Stock";
import { Button } from "./ui/Button";
import Card from "./ui/Card";

interface StockChartProps {
	data: StockDataPoint[];
	maLines: MALine[];
	indicators: IndicatorSettings;
}

export default function StockChart({
	data,
	maLines,
	indicators,
}: StockChartProps) {
	const { chartContainerRef, lineTools } = useStockChart({
		data,
		maLines,
		indicators,
	});

	return (
		<div className="size-full flex gap-4 relative">
			<ChartTools lineTools={lineTools.current} />

			<ChartDrawSelectedTool
				lineTools={lineTools.current}
				className="absolute bottom-12 z-10 left-1/2 -translate-x-1/2"
			/>

			<div
				ref={chartContainerRef}
				className="relative size-full border rounded-lg overflow-hidden shadow"
			/>
		</div>
	);
}

const defaultToolSetting: Partial<LineOptions> = {
	color: "#2B7FFF",
	width: 3,
};

function ChartTools({
	lineTools,
	className,
}: {
	lineTools: ILineToolsPlugin | null;
	className?: string;
}) {
	const [activeTool, setActiveTool] = useState<LineToolType | null>(null);
	const [activeLineId, setActiveLineId] = useState<string | null>(null);

	// Set activeTool == null sau khi người dùng đã vẽ
	useEffect(() => {
		if (!lineTools) return;

		const handleSelectTool = () => setActiveTool(null);
		lineTools.subscribeLineToolsAfterEdit(handleSelectTool);
		return () => lineTools.unsubscribeLineToolsAfterEdit(handleSelectTool);
	}, [lineTools]);

	const handleSelectTool = (
		toolType: LineToolType,
		options: Partial<LineOptions> = {},
	) => {
		if (activeTool === toolType) {
			activeLineId && lineTools?.removeLineToolsById([activeLineId]);
			setActiveTool(null);
		} else {
			const lineId = lineTools?.addLineTool(toolType, [], {
				line: { ...defaultToolSetting, ...options },
				// biome-ignore lint/suspicious/noExplicitAny: Kệ
			} as any);
			setActiveLineId(lineId ?? null);
			setActiveTool(toolType);
		}
	};

	return (
		<Card
			className={cn(
				"bg-slate-900",
				"absolutex top-4 left-4 flex flex-col gap-2 items-start p-2",
				className,
			)}
		>
			<div className="text-sm font-bold mb-1 pb-2 border-b">Tools:</div>
			<Button
				size="icon"
				variant={activeTool === "TrendLine" ? "primary" : "secondary"}
				onClick={() => handleSelectTool("TrendLine")}
			>
				<LineSegmentIcon size={22} />
			</Button>
			<Button
				size="icon"
				variant={activeTool === "Arrow" ? "primary" : "secondary"}
				onClick={() => handleSelectTool("Arrow")}
			>
				<ArrowUpRightIcon size={22} />
			</Button>
			<Button
				size="icon"
				variant={activeTool === "Brush" ? "primary" : "secondary"}
				onClick={() => handleSelectTool("Brush")}
			>
				<PaintBrushIcon size={22} />
			</Button>
			<Button
				size="icon"
				variant={activeTool === "FibRetracement" ? "primary" : "secondary"}
				onClick={() => handleSelectTool("FibRetracement", { width: 1 })}
			>
				<ListIcon size={22} />
			</Button>
			<Button
				size="icon"
				variant={activeTool === "LongShortPosition" ? "primary" : "secondary"}
				onClick={() => handleSelectTool("LongShortPosition", { width: 1 })}
			>
				<RowsIcon size={22} />
			</Button>
		</Card>
	);
}

function ChartDrawSelectedTool({
	lineTools,
	className,
}: {
	lineTools: ILineToolsPlugin | null;
	className?: string;
}) {
	const [isSelectedDraw, setIsSelectedDraw] =
		useState<LineToolExport<LineToolType> | null>(null);
	const [lineColor, setLineColor] = useState("#2B7FFF");
	const [lineWidth, setLineWidth] = useState(3);

	// Theo dõi người dùng có đang select một draw nào không
	useEffect(() => {
		if (!lineTools) return;

		const handleSelectTool = (e: LineToolsSelectEventParams) => {
			setIsSelectedDraw(e.selectedLineTool);
			if (e.selectedLineTool?.options?.line) {
				setLineColor(e.selectedLineTool.options.line.color || "#2B7FFF");
				setLineWidth(e.selectedLineTool.options.line.width || 3);
			}
		};
		lineTools.subscribeLineToolsSelect(handleSelectTool);
		return () => lineTools.unsubscribeLineToolsSelect(handleSelectTool);
	}, [lineTools]);

	useEffect(() => {
		if (!isSelectedDraw) return;

		const handleDeleteKey = (e: KeyboardEvent) => {
			if (e.key === "Delete") lineTools?.removeSelectedLineTools();
		};

		document.addEventListener("keydown", handleDeleteKey);
		return () => document.removeEventListener("keydown", handleDeleteKey);
	}, [isSelectedDraw, lineTools]);

	const updateLineOptions = (color?: string, width?: number) => {
		if (!isSelectedDraw || !lineTools) return;

		const currentOptions = isSelectedDraw.options || {};
		const newColor = color ?? lineColor;
		const newWidth = width ?? lineWidth;

		lineTools.applyLineToolOptions({
			id: isSelectedDraw.id,
			toolType: isSelectedDraw.toolType,
			points: isSelectedDraw.points || [],
			options: {
				...currentOptions,
				line: {
					...currentOptions.line,
					color: newColor,
					width: newWidth,
				},
			},
			// biome-ignore lint/suspicious/noExplicitAny: Kệ
		} as any);

		if (color) setLineColor(color);
		if (width !== undefined) setLineWidth(width);
	};

	if (!isSelectedDraw) return null;

	return (
		<Card
			className={cn("p-2 flex items-center gap-3 px-3 shadow-2xl", className)}
		>
			<div className="flex items-center gap-2">
				<PaletteIcon size={20} className="text-slate-100" />
				<input
					type="color"
					value={lineColor}
					onChange={(e) => updateLineOptions(e.target.value, undefined)}
					className="size-8 rounded-md cursor-pointer border-0 bg-transparent"
				/>
			</div>

			<div className="w-px h-6 bg-slate-600" />

			<div className="flex items-center gap-2">
				<TextAaIcon size={20} className="text-slate-100" />
				<input
					type="range"
					min={1}
					max={10}
					value={lineWidth}
					onChange={(e) => updateLineOptions(undefined, Number(e.target.value))}
					className="w-20 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
				/>
				<span className="text-sm text-slate-100">{lineWidth}</span>
			</div>

			<div className="w-px h-6 bg-slate-600" />

			<Button
				size="icon-sm"
				rounded="sm"
				variant="secondary"
				onClick={() => lineTools?.removeSelectedLineTools()}
			>
				<EraserIcon size={22} />
			</Button>
		</Card>
	);
}
