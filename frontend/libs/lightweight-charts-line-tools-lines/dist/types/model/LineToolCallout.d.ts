import { IChartApiBase, ISeriesApi, IHorzScaleBehavior, SeriesType } from 'lightweight-charts';
import { LineToolPoint, LineToolOptionsInternal, LineToolType, DeepPartial, LineToolsCorePlugin, PriceAxisLabelStackingManager } from 'lightweight-charts-line-tools-core';
import { LineToolTrendLine } from './LineToolTrendLine';
/**
 * Concrete implementation of the Callout drawing tool.
 *
 * **What is a Callout?**
 * A Callout connects a specific point of interest on the chart (P0, the "Pointer")
 * to a text label (P1, the "Anchor"). Unlike a Trend Line, the relationship between
 * these points is directional and semantic, not just geometric.
 *
 * **Inheritance:**
 * It extends {@link LineToolTrendLine} to inherit the underlying 2-point data structure and
 * generic text capability, but uses a specialized View (`LineToolCalloutPaneView`) to render
 * the specific "Stem + Text Box" visual style.
 */
export declare class LineToolCallout<HorzScaleItem> extends LineToolTrendLine<HorzScaleItem> {
    /**
     * The unique identifier for this tool type ('Callout').
     *
     * @override
     */
    readonly toolType: LineToolType;
    /**
     * Defines the number of anchor points required to draw this tool.
     *
     * A Callout requires exactly **2 points**:
     * 1. The target point (where the arrow/line points to).
     * 2. The text box anchor point (where the label sits).
     *
     * @override
     */
    readonly pointsCount: number;
    /**
     * Initializes the Callout tool.
     *
     * **Tutorial Note on Construction:**
     * 1. We start with `TrendLineOptionDefaults` as a base.
     * 2. We apply `CalloutSpecificOverrides` to turn off axis labels and set up the text box styling.
     * 3. We apply user `options` last.
     * 4. Crucially, we assign `LineToolCalloutPaneView` instead of the standard Trend Line view.
     *    This swap is what actually makes the tool look like a Callout on the canvas.
     *
     * @param coreApi - The Core Plugin API.
     * @param chart - The Lightweight Charts Chart API.
     * @param series - The Series API this tool is attached to.
     * @param horzScaleBehavior - The horizontal scale behavior.
     * @param options - Configuration overrides.
     * @param points - Initial points.
     * @param priceAxisLabelStackingManager - The manager for label collision.
     */
    constructor(coreApi: LineToolsCorePlugin<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>, options: DeepPartial<LineToolOptionsInternal<'Callout'>>, points: LineToolPoint[] | undefined, priceAxisLabelStackingManager: PriceAxisLabelStackingManager<HorzScaleItem>);
    /**
     * Overrides the base normalization logic to **prevent** point swapping.
     *
     * **Why override this?**
     * In a standard Trend Line, the order of points doesn't matter visually, so we sort them by time
     * to simplify math. However, a Callout has strict directionality:
     * - Point 0 is *always* the Pointer (Target).
     * - Point 1 is *always* the Text Box location.
     *
     * If we allowed normalization, dragging the text box to the left of the target would swap
     * the points, causing the text box to suddenly jump to the target's position and the pointer
     * to jump to the text's position. Overriding this with an empty function preserves the
     * logical relationship between the two points.
     *
     * @override
     */
    normalize(): void;
}
