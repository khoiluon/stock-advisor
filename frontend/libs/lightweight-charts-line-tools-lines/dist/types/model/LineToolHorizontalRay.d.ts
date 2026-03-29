import { IChartApiBase, ISeriesApi, IHorzScaleBehavior, SeriesType } from 'lightweight-charts';
import { LineToolPoint, LineToolOptionsInternal, LineToolType, DeepPartial, LineToolsCorePlugin, PriceAxisLabelStackingManager } from 'lightweight-charts-line-tools-core';
import { LineToolHorizontalLine } from './LineToolHorizontalLine';
/**
 * Concrete implementation of the Horizontal Ray drawing tool.
 *
 * **Inheritance Hierarchy:**
 * `BaseLineTool` -> `LineToolHorizontalLine` -> `LineToolHorizontalRay`
 *
 * **Why this inheritance?**
 * This tool shares 99% of its DNA with the {@link LineToolHorizontalLine}. It has 1 point,
 * moves the same way (Y-axis logic), and uses similar hit-testing. The only difference
 * is the visual rendering (one-sided extension). By inheriting from `LineToolHorizontalLine`,
 * we reuse all that logic and only override the specific options and View class.
 */
export declare class LineToolHorizontalRay<HorzScaleItem> extends LineToolHorizontalLine<HorzScaleItem> {
    /**
     * The unique identifier for this tool type ('HorizontalRay').
     *
     * @override
     */
    readonly toolType: LineToolType;
    /**
     * Defines the number of anchor points required to draw this tool.
     *
     * Like the Horizontal Line, the Ray is defined by exactly **1 point** (the start of the ray).
     *
     * @override
     */
    readonly pointsCount: number;
    /**
     * Initializes the Horizontal Ray tool.
     *
     * **Tutorial Note on Option Merging:**
     * 1. **Base:** Starts with `TrendLineOptionDefaults` (for font/color structure).
     * 2. **Override:** Merges `HorizontalRaySpecificOverrides` to set `extend.right = true` and `extend.left = false`.
     * 3. **User:** Merges user `options`.
     *
     * **View Construction:**
     * It specifically instantiates `LineToolHorizontalRayPaneView`. Even though the logic is similar
     * to the Horizontal Line view, using a distinct view class allows for cleaner separation if
     * Ray-specific rendering logic is added in the future.
     *
     * @param coreApi - The Core Plugin API.
     * @param chart - The Lightweight Charts Chart API.
     * @param series - The Series API this tool is attached to.
     * @param horzScaleBehavior - The horizontal scale behavior.
     * @param options - Configuration overrides.
     * @param points - Initial points.
     * @param priceAxisLabelStackingManager - The manager for label collision.
     */
    constructor(coreApi: LineToolsCorePlugin<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>, options: DeepPartial<LineToolOptionsInternal<'HorizontalLine'>>, points: LineToolPoint[] | undefined, priceAxisLabelStackingManager: PriceAxisLabelStackingManager<HorzScaleItem>);
}
