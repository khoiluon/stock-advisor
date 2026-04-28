import { IChartApiBase, ISeriesApi, IHorzScaleBehavior, SeriesType, Coordinate } from 'lightweight-charts';
import { BaseLineTool, LineToolPoint, LineToolOptionsInternal, LineToolType, DeepPartial, LineToolsCorePlugin, PriceAxisLabelStackingManager, HitTestResult } from 'lightweight-charts-line-tools-core';
/**
 * Concrete implementation of the Vertical Line drawing tool.
 *
 * **What is a Vertical Line?**
 * It is a line defined by a single anchor point (P0). The line is fixed at this point's
 * Time (X-axis) and spans the entire height of the chart pane.
 *
 * **Inheritance:**
 * Like the Horizontal Line, this tool inherits directly from {@link BaseLineTool} because it
 * represents a fundamental 1-point geometric primitive that doesn't share the 2-point logic
 * of the Trend Line family.
 */
export declare class LineToolVerticalLine<HorzScaleItem> extends BaseLineTool<HorzScaleItem> {
    /**
     * The unique identifier for this tool type ('VerticalLine').
     *
     * @override
     */
    readonly toolType: LineToolType;
    /**
     * Defines the number of anchor points required to draw this tool.
     *
     * A Vertical Line is defined by exactly **1 point** (the position on the time scale).
     *
     * @override
     */
    readonly pointsCount: number;
    /**
     * Initializes the Vertical Line tool.
     *
     * **Tutorial Note on Construction:**
     * 1. **Base Defaults:** We use `TrendLineOptionDefaults` to establish common styling (color, width).
     * 2. **Overrides:** We apply `VerticalLineSpecificOverrides` to configure the axis labels correctly.
     * 3. **View:** We assign `LineToolVerticalLinePaneView`. This view is responsible for taking the
     *    single point and manufacturing a vertical segment that spans from Y=0 to Y=PaneHeight.
     *
     * @param coreApi - The Core Plugin API.
     * @param chart - The Lightweight Charts Chart API.
     * @param series - The Series API this tool is attached to.
     * @param horzScaleBehavior - The horizontal scale behavior.
     * @param options - Configuration overrides.
     * @param points - Initial points.
     * @param priceAxisLabelStackingManager - The manager for label collision.
     */
    constructor(coreApi: LineToolsCorePlugin<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>, options: DeepPartial<LineToolOptionsInternal<'VerticalLine'>>, points: LineToolPoint[] | undefined, priceAxisLabelStackingManager: PriceAxisLabelStackingManager<HorzScaleItem>);
    /**
     * Performs the hit test for the Vertical Line.
     *
     * **Architecture Note:**
     * Because the line extends infinitely vertically, a simple point-to-point distance check on the
     * Model's anchor point is insufficient (the user might click at the very top of the screen while
     * the anchor is in the middle).
     *
     * We delegate this to the `LineToolVerticalLinePaneView`, which knows the exact pixel height
     * of the pane and draws the full vertical segment used for hit detection.
     *
     * @param x - X coordinate in pixels.
     * @param y - Y coordinate in pixels.
     * @returns A hit result if the mouse is over the vertical line or the anchor.
     * @override
     */
    _internalHitTest(x: Coordinate, y: Coordinate): HitTestResult<any> | null;
    /**
     * Updates the coordinates of the single anchor point.
     *
     * **Tutorial Note on Constraints:**
     * A Vertical Line is strictly bound to the **Time Axis**.
     * When the user drags the tool, we update the `timestamp` (X).
     *
     * While the `price` (Y) component technically doesn't affect the *line's* position,
     * we still update it so the anchor handle follows the user's mouse vertically,
     * providing better visual feedback during the drag.
     *
     * @param index - The index of the point (always 0).
     * @param point - The new logical coordinates.
     * @override
     */
    setPoint(index: number, point: LineToolPoint): void;
    /**
     * Explicitly defines the highest valid index for an interactive anchor point.
     *
     * Since `pointsCount` is 1, the only valid index is 0.
     *
     * @override
     * @returns `0`
     */
    maxAnchorIndex(): number;
}
