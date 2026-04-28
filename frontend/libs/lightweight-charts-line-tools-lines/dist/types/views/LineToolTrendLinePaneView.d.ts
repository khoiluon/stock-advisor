import { IChartApiBase, ISeriesApi, SeriesType } from 'lightweight-charts';
import { LineToolPaneView, CompositeRenderer, SegmentRenderer, TextRenderer } from 'lightweight-charts-line-tools-core';
import { LineToolTrendLine } from '../model/LineToolTrendLine';
import { IPrimitivePaneRenderer } from 'lightweight-charts-line-tools-core';
/**
 * The specific Pane View implementation for the Trend Line tool.
 *
 * **Tutorial Note on Views:**
 * This class demonstrates the standard responsibility of a Pane View in the plugin architecture:
 * 1. **Data Conversion:** It translates the Model's logical points (Time/Price) into Screen points (X/Y pixels).
 * 2. **Culling:** It checks if the tool is actually visible on screen to optimize performance.
 * 3. **Composition:** It configures and combines multiple low-level renderers (Segment, Text, Anchors)
 *    into a single `CompositeRenderer` for the chart to draw.
 */
export declare class LineToolTrendLinePaneView<HorzScaleItem> extends LineToolPaneView<HorzScaleItem> {
    protected _segmentRenderer: SegmentRenderer<HorzScaleItem>;
    protected _textRenderer: TextRenderer<HorzScaleItem>;
    /**
     * Initializes the Trend Line View.
     *
     * @param source - The specific Trend Line model instance.
     * @param chart - The Chart API.
     * @param series - The Series API.
     */
    constructor(source: LineToolTrendLine<HorzScaleItem>, chart: IChartApiBase<any>, series: ISeriesApi<SeriesType, any>);
    /**
     * Retrieves the internal `SegmentRenderer` instance used to draw the main line.
     *
     * This can be useful for derived classes (like `LineToolArrowPaneView`) if they need
     * to inspect or modify the renderer's state directly, though usually configuration is done via options.
     *
     * @returns The active {@link SegmentRenderer}.
     */
    getSegmentRenderer(): SegmentRenderer<HorzScaleItem>;
    /**
     * Retrieves the final `CompositeRenderer` for the current render cycle.
     *
     * **Architecture Note:**
     * This override ensures that `_updateImpl` is called if the view is marked as invalidated.
     * This "lazy update" pattern ensures that expensive geometry calculations (like text rotation
     * or culling) only happen once per frame, just before drawing.
     *
     * @returns The fully configured {@link IPrimitivePaneRenderer}, or `null` if nothing should be drawn.
     * @override
     */
    renderer(): IPrimitivePaneRenderer | null;
    /**
     * The core update logic for the Trend Line View.
     *
     * This method is responsible for translating the tool's data model into visual renderers.
     * It performs visibility checks (culling), coordinates conversion, and configures
     * the sub-renderers (Segment and Text) based on the current options.
     *
     * @param height - The height of the pane.
     * @param width - The width of the pane.
     * @protected
     * @override
     */
    protected _updateImpl(height: number, width: number): void;
    /**
     * Adds the interactive anchor points (handles) to the renderer.
     *
     * For a Trend Line, this places two handles:
     * - One at the Start Point (P0).
     * - One at the End Point (P1).
     *
     * It assigns the `DiagonalNwSeResize` cursor to both, indicating to the user that
     * these points can be dragged freely in 2D space.
     *
     * @param renderer - The composite renderer to append anchors to.
     * @protected
     * @override
     */
    protected _addAnchors(renderer: CompositeRenderer<HorzScaleItem>): void;
}
