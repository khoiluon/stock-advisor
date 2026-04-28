import { IChartApiBase, ISeriesApi, IHorzScaleBehavior, SeriesType } from 'lightweight-charts';
import { LineToolPoint, LineToolOptionsInternal, LineToolType, DeepPartial, LineToolsCorePlugin, PriceAxisLabelStackingManager } from 'lightweight-charts-line-tools-core';
import { LineToolTrendLine } from './LineToolTrendLine';
/**
 * Concrete implementation of the Ray drawing tool.
 *
 * **Inheritance:**
 * It extends {@link LineToolTrendLine} directly. This is because a Ray shares the exact same
 * 2-point geometry, hit-testing, and user interaction logic as a Trend Line.
 * The only difference is the visual property of extending to infinity on one side.
 */
export declare class LineToolRay<HorzScaleItem> extends LineToolTrendLine<HorzScaleItem> {
    /**
     * The unique identifier for this tool type ('Ray').
     *
     * @override
     */
    readonly toolType: LineToolType;
    /**
     * Defines the number of anchor points required to draw this tool.
     *
     * Like the Trend Line, a Ray is defined by exactly **2 points** (Origin and Direction).
     *
     * @override
     */
    readonly pointsCount: number;
    /**
     * Initializes the Ray tool.
     *
     * **Tutorial Note on Construction:**
     * 1. **Base Defaults:** Start with `TrendLineOptionDefaults`.
     * 2. **Subclass Overrides:** Merge `RaySpecificOverrides` (forcing `extend.right = true`).
     * 3. **User Options:** Merge the `options` passed by the user.
     *
     * **View Assignment:**
     * It assigns the `LineToolRayPaneView`. While this view currently acts just like a TrendLine view,
     * using a specific class allows future customization of how the Ray is rendered (e.g., adding
     * a specific end-cap only to the infinite end) without breaking the standard Trend Line.
     *
     * @param coreApi - The Core Plugin API.
     * @param chart - The Lightweight Charts Chart API.
     * @param series - The Series API this tool is attached to.
     * @param horzScaleBehavior - The horizontal scale behavior.
     * @param options - Configuration overrides.
     * @param points - Initial points.
     * @param priceAxisLabelStackingManager - The manager for label collision.
     */
    constructor(coreApi: LineToolsCorePlugin<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>, options: DeepPartial<LineToolOptionsInternal<'Ray'>>, points: LineToolPoint[] | undefined, priceAxisLabelStackingManager: PriceAxisLabelStackingManager<HorzScaleItem>);
}
