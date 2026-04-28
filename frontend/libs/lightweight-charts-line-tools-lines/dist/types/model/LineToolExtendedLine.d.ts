import { IChartApiBase, ISeriesApi, IHorzScaleBehavior, SeriesType } from 'lightweight-charts';
import { LineToolPoint, LineToolOptionsInternal, LineToolType, DeepPartial, LineToolsCorePlugin, PriceAxisLabelStackingManager } from 'lightweight-charts-line-tools-core';
import { LineToolTrendLine } from './LineToolTrendLine';
/**
 * Concrete implementation of the Extended Line drawing tool.
 *
 * **What is an Extended Line?**
 * Structurally, it is identical to a {@link LineToolTrendLine} (defined by two points).
 * Visually, it draws a line that passes through these two points and continues infinitely
 * in both directions across the chart.
 *
 * **Inheritance:**
 * It extends {@link LineToolTrendLine} to reuse the point handling, hit testing, and normalization logic.
 * The difference is purely configuration (extensions enabled) and the specific View class used.
 */
export declare class LineToolExtendedLine<HorzScaleItem> extends LineToolTrendLine<HorzScaleItem> {
    /**
     * The unique identifier for this tool type ('ExtendedLine').
     *
     * @override
     */
    readonly toolType: LineToolType;
    /**
     * Defines the number of anchor points required to draw this tool.
     *
     * An Extended Line requires exactly **2 points** to define the slope and position of the infinite line.
     *
     * @override
     */
    readonly pointsCount: number;
    /**
     * Initializes the Extended Line tool.
     *
     * **Tutorial Note on Option Merging:**
     * 1. **Base Defaults:** Start with `TrendLineOptionDefaults`.
     * 2. **Subclass Overrides:** Merge `ExtendedLineSpecificOverrides` to force `extend: { left: true, right: true }`.
     * 3. **User Options:** Merge the `options` passed by the user.
     *
     * This setup ensures the line extends infinitely by default, but still allows the user to
     * customize other aspects like color, width, or text.
     *
     * @param coreApi - The Core Plugin API.
     * @param chart - The Lightweight Charts Chart API.
     * @param series - The Series API this tool is attached to.
     * @param horzScaleBehavior - The horizontal scale behavior.
     * @param options - Configuration overrides.
     * @param points - Initial points.
     * @param priceAxisLabelStackingManager - The manager for label collision.
     */
    constructor(coreApi: LineToolsCorePlugin<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>, options: DeepPartial<LineToolOptionsInternal<'ExtendedLine'>>, points: LineToolPoint[] | undefined, priceAxisLabelStackingManager: PriceAxisLabelStackingManager<HorzScaleItem>);
}
