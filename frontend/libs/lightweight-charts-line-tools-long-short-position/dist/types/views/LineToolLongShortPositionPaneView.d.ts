/**
 * The Pane View for the LineToolLongShortPosition tool.
 * It coordinates the rendering of the two rectangles (Risk and Reward) and the
 * associated dynamic text labels, managed by the core plugin's renderers.
 */
import { IChartApiBase, ISeriesApi, SeriesType } from 'lightweight-charts';
import { RectangleRenderer, TextRenderer, CompositeRenderer, LineToolPaneView } from 'lightweight-charts-line-tools-core';
import { LineToolLongShortPosition } from '../model/LineToolLongShortPosition';
/**
 * The Pane View for the Long/Short Position tool.
 *
 * **Tutorial Note on Logic:**
 * This view coordinates a complex multi-part visualization:
 * 1. **Risk Rectangle:** Red box defining the loss zone (Entry to Stop).
 * 2. **Reward Rectangle:** Green box defining the profit zone (Entry to Target).
 * 3. **Dynamic Labels:** Two separate text renderers that auto-calculate and display
 *    prices, distances, and R:R ratios based on the current geometry.
 *
 * It manages independent culling for the two halves to optimize performance when zooming.
 */
export declare class LineToolLongShortPositionPaneView<HorzScaleItem> extends LineToolPaneView<HorzScaleItem> {
    /**
     * Internal renderer for the Stop Loss (Risk) rectangle.
     * @protected
     */
    protected _riskRenderer: RectangleRenderer<HorzScaleItem>;
    /**
     * Internal renderer for the Profit Target (Reward) rectangle.
     * @protected
     */
    protected _rewardRenderer: RectangleRenderer<HorzScaleItem>;
    /**
     * Internal renderer for the text statistics in the Risk zone.
     * @protected
     */
    protected _riskLabelRenderer: TextRenderer<HorzScaleItem>;
    /**
     * Internal renderer for the text statistics in the Reward zone.
     * @protected
     */
    protected _rewardLabelRenderer: TextRenderer<HorzScaleItem>;
    /**
     * Initializes the Position Tool View.
     *
     * @param tool - The specific Long/Short model instance.
     * @param chart - The Chart API.
     * @param series - The Series API.
     */
    constructor(tool: LineToolLongShortPosition<HorzScaleItem>, chart: IChartApiBase<any>, series: ISeriesApi<SeriesType, any>);
    /**
     * The core update logic.
     *
     * This method calculates the geometry for both rectangles, performs granular culling,
     * and generates the dynamic text strings for the labels.
     *
     * @param height - The height of the pane.
     * @param width - The width of the pane.
     * @protected
     * @override
     */
    protected _updateImpl(height: number, width: number): void;
    /**
     * Adds the three interactive anchor points (Entry, Stop, Target).
     *
     * We assign `VerticalResize` cursors to all three because the primary interaction mode
     * for adjusting this tool is dragging the price levels up and down.
     *
     * @param renderer - The composite renderer to append anchors to.
     * @protected
     * @override
     */
    protected _addAnchors(renderer: CompositeRenderer<any>): void;
    /**
     * Helper to determine visibility of a specific rectangle component (Risk or Reward).
     *
     * It constructs a bounding box from the two defining logical points and uses
     * `getToolCullingState` with specific sub-segment checks to handle infinite extensions
     * properly if they are enabled in the options.
     *
     * @param pA - Start point of the rectangle part.
     * @param pB - End point of the rectangle part.
     * @param rectOptions - The options containing extension settings.
     * @returns `true` if this part of the tool is visible.
     * @private
     */
    private _isRectangleVisible;
}
