import { IChartApiBase, ISeriesApi, IHorzScaleBehavior, SeriesType, Coordinate } from 'lightweight-charts';
import { BaseLineTool, LineToolPoint, LineToolOptionsInternal, LineToolType, DeepPartial, LineToolsCorePlugin, PriceAxisLabelStackingManager, HitTestResult } from 'lightweight-charts-line-tools-core';
/**
 * Concrete implementation of the Cross Line drawing tool.
 *
 * **What is a Cross Line?**
 * Unlike a Trend Line (2 points) or a Ray (2 points), a Cross Line is defined by a
 * **single point** (P0). This point represents the intersection where a vertical line
 * and a horizontal line meet.
 *
 * **Inheritance Note:**
 * Because this is a 1-point tool, it extends the abstract {@link BaseLineTool} directly
 * rather than inheriting from `LineToolTrendLine`. It implements its own simple
 * logic for point updates and hit testing.
 */
export declare class LineToolCrossLine<HorzScaleItem> extends BaseLineTool<HorzScaleItem> {
    /**
     * The unique identifier for this tool type ('CrossLine').
     *
     * @override
     */
    readonly toolType: LineToolType;
    /**
     * Defines the number of anchor points required to draw this tool.
     *
     * A Cross Line is defined by exactly **1 point** (the center of the cross).
     *
     * @override
     */
    readonly pointsCount: number;
    /**
     * Initializes the Cross Line tool.
     *
     * **Tutorial Note:**
     * 1. It merges `CrossLineDefaultOptions` with user options.
     * 2. It sets `pointsCount` to 1 in the `super()` call.
     * 3. It assigns the specialized `LineToolCrossLinePaneView`, which is responsible
     *    for taking that single point and drawing the two intersecting infinite lines.
     *
     * @param coreApi - The Core Plugin API.
     * @param chart - The Lightweight Charts Chart API.
     * @param series - The Series API this tool is attached to.
     * @param horzScaleBehavior - The horizontal scale behavior.
     * @param options - Configuration overrides.
     * @param points - Initial points.
     * @param priceAxisLabelStackingManager - The manager for label collision.
     */
    constructor(coreApi: LineToolsCorePlugin<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>, options: DeepPartial<LineToolOptionsInternal<'CrossLine'>>, points: LineToolPoint[] | undefined, priceAxisLabelStackingManager: PriceAxisLabelStackingManager<HorzScaleItem>);
    /**
     * Performs the hit test for the Cross Line.
     *
     * **Architecture Note:**
     * Even though the Model only holds one point, the View renders lines spanning the whole screen.
     * Therefore, we cannot do simple math here. We **must** delegate to the View's `CompositeRenderer`.
     * The View knows exactly where those infinite lines are drawn on the pixel canvas, ensuring
     * that clicking anywhere on the crosshair lines registers as a hit.
     *
     * @param x - X coordinate in pixels.
     * @param y - Y coordinate in pixels.
     * @returns A hit result if the mouse is over the horizontal or vertical line, or the center anchor.
     * @override
     */
    _internalHitTest(x: Coordinate, y: Coordinate): HitTestResult<any> | null;
    /**
     * Updates the coordinates of the single anchor point (Intersection).
     *
     * **Tutorial Note on Constraints:**
     * Unlike a `VerticalLine` (which locks Time) or `HorizontalLine` (which locks Price),
     * a Cross Line moves freely in both dimensions. Therefore, this method updates
     * both the `timestamp` (X) and `price` (Y) of point 0 whenever the user drags it.
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
