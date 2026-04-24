import { IChartApiBase, ISeriesApi, SeriesType } from 'lightweight-charts';
import { LineToolPaneView, CompositeRenderer, SegmentRenderer, TextRenderer } from 'lightweight-charts-line-tools-core';
import { LineToolCallout } from '../model/LineToolCallout';
/**
 * Pane View for the Callout tool.
 *
 * **Tutorial Note on View Logic:**
 * The Callout requires a custom view because its rendering pipeline differs from a simple line.
 * It involves two distinct visual elements:
 * 1. A **Text Box** (the annotation).
 * 2. A **Stem Line** (connecting the target point P0 to the text box P1).
 *
 * This view manages the coordination of these two renderers.
 */
export declare class LineToolCalloutPaneView<HorzScaleItem> extends LineToolPaneView<HorzScaleItem> {
    protected _segmentRenderer: SegmentRenderer<HorzScaleItem>;
    protected _textRenderer: TextRenderer<HorzScaleItem>;
    /**
     * Initializes the Callout View.
     *
     * @param source - The specific Callout model instance.
     * @param chart - The Chart API.
     * @param series - The Series API.
     */
    constructor(source: LineToolCallout<HorzScaleItem>, chart: IChartApiBase<any>, series: ISeriesApi<SeriesType, any>);
    /**
     * Orchestrates the rendering of the line stem and the text box.
     *
     * @param height - The height of the pane.
     * @param width - The width of the pane.
     * @protected
     * @override
     */
    protected _updateImpl(height: number, width: number): void;
    /**
     * Adds the two interactive anchor points.
     *
     * - **P0:** The "Target" point (where the callout points to).
     * - **P1:** The "Text" point (where the annotation sits).
     *
     * @param renderer - The composite renderer to append anchors to.
     * @protected
     * @override
     */
    protected _addAnchors(renderer: CompositeRenderer<HorzScaleItem>): void;
}
