import { IChartApiBase, ISeriesApi, SeriesType } from 'lightweight-charts';
import { LineToolPaneView, CompositeRenderer, SegmentRenderer } from 'lightweight-charts-line-tools-core';
import { LineToolCrossLine } from '../model/LineToolCrossLine';
/**
 * Pane View for the Cross Line tool.
 *
 * **Tutorial Note on Logic:**
 * The Cross Line is unique because it takes a **Single Point** from the model but renders
 * **Two Infinite Lines** (Horizontal and Vertical).
 *
 * Since the rendering engine draws finite segments, this view is responsible for:
 * 1. Determining the full width and height of the chart pane.
 * 2. Creating a vertical segment from top to bottom at the point's X.
 * 3. Creating a horizontal segment from left to right at the point's Y.
 */
export declare class LineToolCrossLinePaneView<HorzScaleItem> extends LineToolPaneView<HorzScaleItem> {
    protected _horizontalRenderer: SegmentRenderer<HorzScaleItem>;
    protected _verticalRenderer: SegmentRenderer<HorzScaleItem>;
    /**
     * Initializes the Cross Line View.
     *
     * @param source - The specific Cross Line model instance.
     * @param chart - The Chart API.
     * @param series - The Series API.
     */
    constructor(source: LineToolCrossLine<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>);
    /**
     * The core update logic.
     *
     * It translates the single logical anchor point into two full-screen segments
     * (Horizontal and Vertical) and configures separate renderers for each.
     *
     * @param height - The height of the pane.
     * @param width - The width of the pane.
     * @protected
     * @override
     */
    protected _updateImpl(height: number, width: number): void;
    /**
     * Adds the single interactive anchor point at the intersection.
     *
     * We use the `Crosshair` cursor to indicate that this point moves freely in 2D space.
     *
     * @param renderer - The composite renderer to append the anchor to.
     * @protected
     * @override
     */
    protected _addAnchors(renderer: CompositeRenderer<HorzScaleItem>): void;
}
