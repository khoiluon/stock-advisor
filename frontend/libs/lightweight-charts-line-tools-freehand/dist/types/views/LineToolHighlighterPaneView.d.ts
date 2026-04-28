import { IChartApiBase, ISeriesApi, SeriesType } from 'lightweight-charts';
import { LineToolPaneView, CompositeRenderer, PolygonRenderer, AnchorPoint } from 'lightweight-charts-line-tools-core';
import { LineToolHighlighter } from '../model/LineToolHighlighter';
/**
 * Pane View for the Highlighter tool.
 *
 * **Tutorial Note on Logic:**
 * This view is structurally very similar to the {@link LineToolBrushPaneView}.
 * It converts the stream of logical points into screen coordinates, applies a smoothing
 * algorithm to create fluid strokes, and renders the result using a `PolygonRenderer`.
 *
 * The primary difference lies in the configuration passed from the Model (thicker, translucent lines).
 */
export declare class LineToolHighlighterPaneView<HorzScaleItem> extends LineToolPaneView<HorzScaleItem> {
    /**
     * Internal renderer responsible for drawing the thick, freehand highlighter stroke.
     * @protected
     */
    protected _polygonRenderer: PolygonRenderer<HorzScaleItem>;
    /**
     * Initializes the Highlighter View.
     *
     * @param source - The specific Highlighter model instance.
     * @param chart - The Chart API.
     * @param series - The Series API.
     */
    constructor(source: LineToolHighlighter<HorzScaleItem>, // Accepts the specific Highlighter Model type
    chart: IChartApiBase<any>, series: ISeriesApi<SeriesType, any>);
    /**
     * Smooths the raw path points using an iterative moving average algorithm.
     *
     * This algorithm reduces the "jitter" from raw mouse input, resulting in a cleaner
     * looking highlight stroke. It uses the same logic as the Brush tool to ensure consistent feel.
     *
     * @param points - The raw screen points.
     * @param iterations - Number of smoothing passes (default 2).
     * @returns The smoothed array of points.
     * @protected
     */
    protected _smoothArray(points: AnchorPoint[], iterations?: number): AnchorPoint[];
    /**
     * The core update logic.
     *
     * It manages visibility (culling), coordinate conversion, path smoothing, and finally
     * configuring the renderer with the specific visual options (color, width, opacity).
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
     * **Tutorial Note:**
     * Like the Brush, we calculate the geometric center of the highlight path and place a
     * single "Move Handle" there. This allows the user to reposition the specific highlight
     * annotation without needing to interact with every single point in the path.
     *
     * @param renderer - The composite renderer to append anchors to.
     * @protected
     * @override
     */
    protected _addAnchors(renderer: CompositeRenderer<HorzScaleItem>): void;
}
