import { IChartApiBase, ISeriesApi, IHorzScaleBehavior, SeriesType, Coordinate } from 'lightweight-charts';
import { BaseLineTool, LineToolPoint, LineToolOptionsInternal, LineToolType, DeepPartial, LineToolsCorePlugin, PriceAxisLabelStackingManager, HitTestResult } from 'lightweight-charts-line-tools-core';
/**
 * Concrete implementation of the Horizontal Line drawing tool.
 *
 * **What is a Horizontal Line?**
 * It is a line defined by a single anchor point (P0). The line passes through this point's
 * Price level (Y-axis) and spans the entire width of the chart.
 *
 * **Architecture Note:**
 * Unlike 2-point tools (TrendLine, Ray) which share a common ancestor, this class inherits directly
 * from {@link BaseLineTool}. It represents a fundamental base for "1-Point Horizontal" tools,
 * which {@link LineToolHorizontalRay} then extends.
 */
export declare class LineToolHorizontalLine<HorzScaleItem> extends BaseLineTool<HorzScaleItem> {
    /**
     * The unique identifier for this tool type ('HorizontalLine').
     *
     * @override
     */
    readonly toolType: LineToolType;
    /**
     * Defines the number of anchor points required to draw this tool.
     *
     * A Horizontal Line is defined by exactly **1 point**. The time component (X) of this point
     * places the anchor handle, but the line itself is drawn across all time.
     *
     * @override
     */
    readonly pointsCount: number;
    /**
     * Initializes the Horizontal Line tool.
     *
     * **Tutorial Note on Construction:**
     * 1. **Base Defaults:** We borrow `TrendLineOptionDefaults` to get standard styling (colors, widths, text settings).
     * 2. **Overrides:** We apply `HorizontalLineSpecificOverrides` to force infinite left/right extension and enable price labels.
     * 3. **View:** We assign `LineToolHorizontalLinePaneView`. This view is smart enough to take a single point
     *    and draw a line spanning the full calculated width of the chart pane.
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
    /**
     * Performs the hit test for the Horizontal Line.
     *
     * **Architecture Note:**
     * Since the line extends infinitely, we cannot simply check if the mouse is near the anchor point.
     * We must check if the mouse is near the *visible line segment* on screen.
     *
     * The `LineToolHorizontalLinePaneView` calculates the specific start (0) and end (paneWidth)
     * pixel coordinates for the current viewport. By delegating to the View's renderer, we ensure
     * accurate hit detection across the entire width of the chart.
     *
     * @param x - X coordinate in pixels.
     * @param y - Y coordinate in pixels.
     * @returns A hit result if the mouse is over the line or the anchor.
     * @override
     */
    _internalHitTest(x: Coordinate, y: Coordinate): HitTestResult<any> | null;
    /**
     * Updates the coordinates of the single anchor point.
     *
     * **Tutorial Note on 1-Point Logic:**
     * Even though a Horizontal Line is conceptually invariant in Time (it exists at all times),
     * the *Anchor Point* (the handle the user drags) exists at a specific Time.
     *
     * Therefore, we update **both** the `timestamp` (X) and `price` (Y). This allows the user
     * to drag the handle left and right along the line (visual preference) while moving the line
     * up and down (functional change).
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
