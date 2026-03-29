import { IChartApiBase, ISeriesApi, SeriesType } from 'lightweight-charts';
import { LineToolPaneView, CompositeRenderer, SegmentRenderer, TextRenderer } from 'lightweight-charts-line-tools-core';
import { LineToolVerticalLine } from '../model/LineToolVerticalLine';
/**
 * Pane View for the Vertical Line tool.
 *
 * **Tutorial Note on Logic:**
 * This view handles the unique requirement of drawing a line that is fixed in Time (X-axis)
 * but infinite in Price (Y-axis).
 *
 * Instead of relying on the renderer's extension logic, this view explicitly calculates
 * the top (Y=0) and bottom (Y=PaneHeight) coordinates of the current viewport and draws
 * a segment between them. This ensures accurate hit-testing and rendering across the full height.
 */
export declare class LineToolVerticalLinePaneView<HorzScaleItem> extends LineToolPaneView<HorzScaleItem> {
    /**
     * Internal renderer for the main vertical line segment.
     * @protected
     */
    protected _lineRenderer: SegmentRenderer<HorzScaleItem>;
    /**
     * Internal renderer for the optional text label.
     * @protected
     */
    protected _textRenderer: TextRenderer<HorzScaleItem>;
    /**
     * Initializes the Vertical Line View.
     *
     * @param source - The specific Vertical Line model instance.
     * @param chart - The Chart API.
     * @param series - The Series API.
     */
    constructor(source: LineToolVerticalLine<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>);
    /**
     * The core update logic.
     *
     * It translates the single logical anchor point into a vertical segment spanning the full height
     * of the chart pane. It also handles the complex logic of rotating text 90 degrees and
     * re-mapping alignment settings (e.g., "Left" alignment becomes "Bottom" on a vertical line).
     *
     * @param height - The height of the pane.
     * @param width - The width of the pane.
     * @protected
     * @override
     */
    protected _updateImpl(height: number, width: number): void;
    /**
     * Adds the single interactive anchor point.
     *
     * We use the `HorizontalResize` cursor because a Vertical Line is fixed in Price (conceptually)
     * and only moves Left/Right in Time.
     *
     * @param renderer - The composite renderer to append the anchor to.
     * @protected
     * @override
     */
    protected _addAnchors(renderer: CompositeRenderer<HorzScaleItem>): void;
}
