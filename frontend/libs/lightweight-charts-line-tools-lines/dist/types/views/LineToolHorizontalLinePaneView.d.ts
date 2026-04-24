import { IChartApiBase, ISeriesApi, SeriesType } from 'lightweight-charts';
import { LineToolPaneView, CompositeRenderer, SegmentRenderer, TextRenderer } from 'lightweight-charts-line-tools-core';
import { LineToolHorizontalLine } from '../model/LineToolHorizontalLine';
/**
 * Pane View for the Horizontal Line tool.
 *
 * **Tutorial Note on Logic:**
 * Unlike a Trend Line which connects two points, a Horizontal Line is defined by a **Single Point**
 * but renders a line that spans the width of the chart (or specific rays based on extension options).
 *
 * This view is responsible for:
 * 1. calculating the visible start and end X-coordinates of the line.
 * 2. Positioning the text label specifically relative to the visible segment (e.g., aligning text to the right edge of the screen).
 */
export declare class LineToolHorizontalLinePaneView<HorzScaleItem> extends LineToolPaneView<HorzScaleItem> {
    /**
     * Internal renderer for the main horizontal line segment.
     * @protected
     */
    protected _lineRenderer: SegmentRenderer<HorzScaleItem>;
    /**
     * Internal renderer for the optional text label.
     * @protected
     */
    protected _textRenderer: TextRenderer<HorzScaleItem>;
    /**
     * Initializes the Horizontal Line View.
     *
     * @param source - The specific Horizontal Line model instance.
     * @param chart - The Chart API.
     * @param series - The Series API.
     */
    constructor(source: LineToolHorizontalLine<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>);
    /**
     * The core update logic.
     *
     * It translates the single logical anchor point into a specific horizontal segment
     * based on the chart's current width and the tool's extension settings.
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
     * We use the `VerticalResize` cursor because a Horizontal Line is typically fixed in Time
     * and only moves up/down in Price.
     *
     * @param renderer - The composite renderer to append the anchor to.
     * @protected
     * @override
     */
    protected _addAnchors(renderer: CompositeRenderer<HorzScaleItem>): void;
}
