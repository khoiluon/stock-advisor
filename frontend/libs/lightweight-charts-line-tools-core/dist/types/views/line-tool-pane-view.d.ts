import { IUpdatablePaneView, IPaneRenderer, LineAnchorCreationData } from '../types';
import { AnchorPoint } from '../rendering/line-anchor-renderer';
import { CompositeRenderer } from '../rendering/composite-renderer';
import { IChartApiBase, ISeriesApi, SeriesType } from 'lightweight-charts';
import { BaseLineTool } from '../model/base-line-tool';
import { LineAnchorRenderer } from '../rendering/line-anchor-renderer';
import { RectangleRenderer, TextRenderer } from '../rendering/generic-renderers';
/**
 * Abstract base class for the Pane View of a Line Tool.
 *
 * This view is responsible for rendering the main visual elements of the tool (lines, shapes, text)
 * directly onto the chart pane. It also manages the state and rendering of interactive elements
 * like resize anchors.
 *
 * Concrete tool implementations should extend this class and override `_updateImpl` to define
 * their specific rendering logic.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item.
 */
export declare abstract class LineToolPaneView<HorzScaleItem> implements IUpdatablePaneView {
    /**
     * Reference to the specific line tool model instance this view represents.
     * Provides access to the tool's options, points, and state.
     * @protected
     */
    protected readonly _tool: BaseLineTool<HorzScaleItem>;
    /**
     * Reference to the Lightweight Charts API instance.
     * Used for coordinate conversions and accessing chart options.
     * @protected
     */
    protected readonly _chart: IChartApiBase<HorzScaleItem>;
    /**
     * Reference to the series API instance the tool is attached to.
     * Used for price-to-coordinate conversions.
     * @protected
     */
    protected readonly _series: ISeriesApi<SeriesType, HorzScaleItem>;
    /**
     * Internal cache of the tool's points converted to screen coordinates (pixels).
     * These are recalculated whenever `_updatePoints` is called.
     * @protected
     */
    protected _points: AnchorPoint[];
    /**
     * Dirty flag indicating if the view's data is out of sync with the model.
     * If `true`, `_updateImpl` will be called during the next render cycle.
     * @protected
     */
    protected _invalidated: boolean;
    /**
     * Collection of renderers responsible for drawing the interactive anchor points (handles).
     * These are reused to avoid unnecessary object creation.
     * @protected
     */
    protected _lineAnchorRenderers: LineAnchorRenderer<HorzScaleItem>[];
    /**
     * The main composite renderer for this view.
     * It aggregates all specific renderers (shape, text, anchors) into a single draw call.
     * @protected
     */
    protected _renderer: CompositeRenderer<HorzScaleItem>;
    /**
     * A reusable renderer instance for drawing rectangular shapes or backgrounds.
     * @protected
     */
    protected _rectangleRenderer: RectangleRenderer<HorzScaleItem>;
    /**
     * A reusable renderer instance for drawing text labels.
     * @protected
     */
    protected _labelRenderer: TextRenderer<HorzScaleItem>;
    /**
     * Initializes the Pane View.
     *
     * @param tool - The specific line tool model.
     * @param chart - The chart API instance.
     * @param series - The series API instance.
     */
    constructor(tool: BaseLineTool<any>, chart: IChartApiBase<any>, series: ISeriesApi<SeriesType, any>);
    /**
     * Signals that the view's data or options have changed.
     *
     * Sets the `_invalidated` flag to `true`, forcing a recalculation of geometry
     * and render data during the next paint cycle.
     *
     * @param updateType - The type of update (e.g., 'data', 'options').
     */
    update(updateType?: 'data' | 'other' | 'options'): void;
    /**
     * Retrieves the renderer for the current frame.
     *
     * If the view is invalidated, this method triggers `_updateImpl` to refresh the
     * rendering logic before returning the renderer.
     *
     * @returns The {@link IPaneRenderer} to be drawn, or `null` if nothing should be rendered.
     */
    renderer(): IPaneRenderer | null;
    /**
     * Converts the tool's logical points (Time/Price) into screen coordinates (Pixels).
     *
     * This method accesses the chart's time scale and the series' price scale to perform
     * the conversion. It populates the `_points` array.
     *
     * @returns `true` if all points were successfully converted, `false` if scale data is missing.
     * @protected
     */
    protected _updatePoints(): boolean;
    /**
     * The core update logic for the view.
     *
     * This method is called when the view is invalidated. It is responsible for:
     * 1. Clearing the composite renderer.
     * 2. Updating point coordinates via `_updatePoints`.
     * 3. Constructing the specific renderers (lines, shapes) required for the tool's current state.
     * 4. Adding interaction anchors if applicable.
     *
     * @param height - The current height of the pane in pixels.
     * @param width - The current width of the pane in pixels.
     * @protected
     */
    protected _updateImpl(height: number, width: number): void;
    /**
     * Determines if the tool's interaction anchors (resize handles) should be visible.
     *
     * Anchors are typically shown when the tool is selected, hovered, being edited,
     * or currently being drawn (not finished).
     *
     * @returns `true` if anchors should be drawn.
     * @protected
     */
    protected areAnchorsVisible(): boolean;
    /**
     * Adds anchor renderers to the composite renderer.
     *
     * This method is intended to be overridden or used by subclasses to place
     * resize handles at specific points (e.g., corners of a rectangle, ends of a line).
     *
     * @param renderer - The composite renderer to append anchors to.
     * @protected
     */
    protected _addAnchors(renderer: CompositeRenderer<HorzScaleItem>): void;
    /**
     * Factory method to create or recycle a `LineAnchorRenderer`.
     *
     * It configures the anchor with standard styling (colors, hit test logic) and
     * specific interaction data (index, cursor type).
     *
     * @param data - Configuration data for the anchor (points, cursors).
     * @param index - The index in the internal renderer array (for recycling).
     * @returns A configured {@link LineAnchorRenderer}.
     * @protected
     */
    protected createLineAnchor(data: LineAnchorCreationData, index: number): LineAnchorRenderer<HorzScaleItem>;
    /**
     * Helper to determine the background color for anchor points.
     *
     * By default, it attempts to match the chart's background color to make hollow
     * anchors look transparent or blend in. Subclasses can override this for custom styling.
     *
     * @param points - The list of anchor points.
     * @returns An array of color strings corresponding to each point.
     * @protected
     */
    protected _lineAnchorColors(points: AnchorPoint[]): string[];
}
