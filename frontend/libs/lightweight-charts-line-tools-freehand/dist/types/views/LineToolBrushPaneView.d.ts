import { IChartApiBase, ISeriesApi, SeriesType } from 'lightweight-charts';
import { LineToolPaneView, CompositeRenderer, PolygonRenderer, AnchorPoint } from 'lightweight-charts-line-tools-core';
import { LineToolBrush } from '../model/LineToolBrush';
/**
 * Pane View for the Brush tool.
 *
 * **Tutorial Note on View Logic:**
 * The Brush View is responsible for two critical transformations:
 * 1. **Data Conversion:** Converting the unbounded stream of logical points into screen coordinates.
 * 2. **Path Smoothing:** Applying a post-processing algorithm (`_smoothArray`) to the raw screen points
 *    to create a fluid, natural-looking curve instead of a jagged polyline.
 * 3. **Rendering:** Using the `PolygonRenderer` to draw the final smoothed path.
 */
export declare class LineToolBrushPaneView<HorzScaleItem> extends LineToolPaneView<HorzScaleItem> {
    /**
     * Internal renderer responsible for drawing the continuous freehand line.
     * @protected
     */
    protected _polygonRenderer: PolygonRenderer<HorzScaleItem>;
    /**
     * Initializes the Brush View.
     *
     * @param source - The specific Brush model instance.
     * @param chart - The Chart API.
     * @param series - The Series API.
     */
    constructor(source: LineToolBrush<HorzScaleItem>, chart: IChartApiBase<any>, series: ISeriesApi<SeriesType, any>);
    /**
     * Smooths the raw path points using an iterative moving average algorithm.
     *
     * **Algorithm Details:**
     * It uses a simple box blur kernel (window size 3: [prev, current, next]).
     * The smoothing is applied iteratively (default 2 passes) to progressively reduce high-frequency
     * jitter from the mouse input without significantly distorting the original shape.
     *
     * @param points - The raw screen points captured from mouse movements.
     * @param iterations - The number of smoothing passes to apply (default: 2).
     * @returns A new array of smoothed {@link AnchorPoint}s.
     * @protected
     */
    protected _smoothArray(points: AnchorPoint[], iterations?: number): AnchorPoint[];
    /**
     * The core update logic.
     *
     * It orchestrates the pipeline: Culling -> Coordinate Conversion -> Smoothing -> Rendering.
     *
     * @param height - The height of the pane.
     * @param width - The width of the pane.
     * @protected
     * @override
     */
    protected _updateImpl(height: number, width: number): void;
    /**
     * Adds the interactive anchor point.
     *
     * **Tutorial Note on Anchors:**
     * A freehand drawing has hundreds of points. Showing handles for all of them would be unusable.
     * Instead, we calculate the **geometric center** of the drawing and place a single
     * "Move Handle" there. This allows the user to grab and translate the entire drawing easily.
     *
     * @param renderer - The composite renderer to append anchors to.
     * @protected
     * @override
     */
    protected _addAnchors(renderer: CompositeRenderer<HorzScaleItem>): void;
}
