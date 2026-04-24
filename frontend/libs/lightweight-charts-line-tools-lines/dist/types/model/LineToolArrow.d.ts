import { IChartApiBase, ISeriesApi, IHorzScaleBehavior, SeriesType } from 'lightweight-charts';
import { LineToolPoint, LineToolOptionsInternal, LineToolType, DeepPartial, LineToolsCorePlugin, PriceAxisLabelStackingManager } from 'lightweight-charts-line-tools-core';
import { LineToolTrendLine } from './LineToolTrendLine';
/**
 * Concrete implementation of the Arrow drawing tool.
 *
 * **Tutorial Note on Inheritance:**
 * The Arrow tool is structurally identical to a standard Trend Line (it connects a start point to an end point).
 * Therefore, instead of rewriting geometry or hit-testing logic, this class simply extends {@link LineToolTrendLine}.
 *
 * The only difference is purely visual: this class forces the "Right End" of the line
 * to be drawn as an Arrow head by default. This demonstrates the power of the plugin architecture:
 * you can create distinct tools just by applying specific option presets to a base class.
 */
export declare class LineToolArrow<HorzScaleItem> extends LineToolTrendLine<HorzScaleItem> {
    /**
     * The unique identifier for this tool type ('Arrow').
     *
     * @override
     */
    readonly toolType: LineToolType;
    /**
     * Defines the number of anchor points required to draw this tool.
     *
     * Like its parent Trend Line, an Arrow is defined by exactly **2 points** (Tail and Head).
     *
     * @override
     */
    readonly pointsCount: number;
    /**
     * Initializes the Arrow tool.
     *
     * **Tutorial Note on Option Merging:**
     * This constructor demonstrates the correct hierarchy for applying options in a derived tool:
     * 1. **Base Defaults:** Start with `TrendLineOptionDefaults` to get standard line/text settings.
     * 2. **Subclass Overrides:** Merge `ArrowSpecificOverrides` (which sets `line.end.right = LineEnd.Arrow`).
     * 3. **User Options:** Merge the `options` passed by the user.
     *
     * This order ensures that the Arrow always looks like an arrow by default, but the user
     * still has the final say (e.g., they could theoretically turn off the arrow tip via options).
     *
     * @param coreApi - The Core Plugin API.
     * @param chart - The Lightweight Charts Chart API.
     * @param series - The Series API this tool is attached to.
     * @param horzScaleBehavior - The horizontal scale behavior.
     * @param options - Configuration overrides.
     * @param points - Initial points.
     * @param priceAxisLabelStackingManager - The manager for label collision.
     */
    constructor(coreApi: LineToolsCorePlugin<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>, options: DeepPartial<LineToolOptionsInternal<'Arrow'>>, points: LineToolPoint[] | undefined, priceAxisLabelStackingManager: PriceAxisLabelStackingManager<HorzScaleItem>);
}
