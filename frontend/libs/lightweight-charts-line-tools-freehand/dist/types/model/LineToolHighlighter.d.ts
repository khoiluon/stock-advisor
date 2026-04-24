import { IChartApiBase, ISeriesApi, IHorzScaleBehavior, SeriesType, Coordinate } from 'lightweight-charts';
import { BaseLineTool, LineToolPoint, LineToolOptionsInternal, LineToolType, LineToolsCorePlugin, DeepPartial, FinalizationMethod, PriceAxisLabelStackingManager, HitTestResult, LineToolHitTestData } from 'lightweight-charts-line-tools-core';
/**
 * Defines the default configuration options for the Highlighter tool.
 *
 * **Tutorial Note:**
 * The Highlighter is functionally identical to the Brush but differs in its visual defaults:
 * - **Width:** Much thicker (20px) to cover text or bars.
 * - **Color:** Translucent yellow (`rgba(255, 255, 0, 0.4)`) to simulate a real highlighter marker.
 * - **End Caps:** Round caps for smooth strokes.
 */
export declare const HighlighterOptionDefaults: LineToolOptionsInternal<'Highlighter'>;
/**
 * Concrete implementation of the Highlighter drawing tool.
 *
 * **What is a Highlighter?**
 * It is a freehand drawing tool designed to overlay chart data with a thick, translucent stroke.
 *
 * **Inheritance:**
 * It extends {@link BaseLineTool} directly. While it shares almost all logic with {@link LineToolBrush}
 * (unbounded points, mouse-up finalization, point filtering), it is implemented as a separate class
 * to allow for distinct type identification (`toolType: 'Highlighter'`) and specific default styling.
 */
export declare class LineToolHighlighter<HorzScaleItem> extends BaseLineTool<HorzScaleItem> {
    /**
     * The unique identifier for this tool type ('Highlighter').
     *
     * @override
     */
    readonly toolType: LineToolType;
    /**
     * Defines the number of anchor points required to draw this tool.
     *
     * Like the Brush, the Highlighter is **unbounded** (`-1`), allowing an unlimited number of points
     * to define the freehand path.
     *
     * @override
     */
    readonly pointsCount: number;
    /**
     * Explicitly defines the highest valid index for an interactive anchor point.
     *
     * We only use a single center anchor (index 0) to allow dragging the entire highlight shape.
     *
     * @override
     * @returns `0`
     */
    maxAnchorIndex(): number;
    /**
     * Indicates if the tool supports "Click-Click" creation.
     *
     * **Tutorial Note:**
     * Highlighter drawing is a continuous drag operation. Discrete clicks are not supported.
     *
     * @override
     * @returns `false`
     */
    supportsClickClickCreation(): boolean;
    /**
     * Confirms that this tool is created via the "Click-Drag" method.
     *
     * **Interaction Flow:** Press Down -> Highlight Area -> Release.
     *
     * @override
     * @returns `true`
     */
    supportsClickDragCreation(): boolean;
    /**
     * Indicates if holding Shift should apply geometric constraints.
     *
     * Disabled (`false`) for freehand tools to allow natural movement.
     *
     * @override
     * @returns `false`
     */
    supportsShiftClickDragConstraint(): boolean;
    /**
     * Initializes the Highlighter tool.
     *
     * **Tutorial Note on Construction:**
     * 1. **Base Defaults:** Uses `HighlighterOptionDefaults` (thick yellow line).
     * 2. **User Options:** Merges user settings.
     * 3. **Points Count:** Sets `-1` for unbounded drawing.
     * 4. **View:** Assigns `LineToolHighlighterPaneView`, which handles the rendering of the thick, smoothed path.
     *
     * @param coreApi - The Core Plugin API.
     * @param chart - The Lightweight Charts Chart API.
     * @param series - The Series API this tool is attached to.
     * @param horzScaleBehavior - The horizontal scale behavior.
     * @param options - Configuration overrides.
     * @param points - Initial points.
     * @param priceAxisLabelStackingManager - The manager for label collision.
     */
    constructor(coreApi: LineToolsCorePlugin<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>, options: DeepPartial<LineToolOptionsInternal<"Highlighter">> | undefined, points: LineToolPoint[] | undefined, priceAxisLabelStackingManager: PriceAxisLabelStackingManager<HorzScaleItem>);
    /**
     * Overrides the base `addPoint` method to implement **distance-based point filtering**.
     *
     * **Tutorial Note on Optimization:**
     * Just like the Brush tool, the Highlighter filters out points that are too close (within `DISTANCE_THRESHOLD_PX`)
     * to the previous point. This keeps the data array smaller and the rendering performance higher
     * without sacrificing visual quality.
     *
     * @param newLogicalPoint - The new point suggested by the `InteractionManager`.
     * @override
     */
    addPoint(newLogicalPoint: LineToolPoint): void;
    /**
     * Specifies how the tool creation should end.
     *
     * Highlighting ends immediately when the user releases the mouse button.
     *
     * @override
     * @returns `FinalizationMethod.MouseUp`
     */
    getFinalizationMethod(): FinalizationMethod;
    /**
     * Explicitly enables full tool translation when dragging the first anchor (index 0).
     *
     * This allows the user to reposition the entire highlight mark by dragging its single handle.
     *
     * @override
     * @returns `true`
     */
    anchor0TriggersTranslation(): boolean;
    /**
     * Performs the hit test for the Highlighter tool.
     *
     * **Architecture Note:**
     * Delegates to the `LineToolHighlighterPaneView`. The view's `PolygonRenderer` handles the complex
     * geometry check to see if the mouse is hovering over the thick stroke of the highlighter.
     *
     * @param x - X coordinate in pixels.
     * @param y - Y coordinate in pixels.
     * @returns A hit result if the mouse is over the highlight.
     * @override
     */
    _internalHitTest(x: Coordinate, y: Coordinate): HitTestResult<LineToolHitTestData> | null;
}
