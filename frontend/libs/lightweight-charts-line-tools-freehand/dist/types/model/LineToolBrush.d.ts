import { IChartApiBase, ISeriesApi, IHorzScaleBehavior, SeriesType, Coordinate } from 'lightweight-charts';
import { BaseLineTool, LineToolPoint, LineToolOptionsInternal, LineToolType, LineToolsCorePlugin, DeepPartial, FinalizationMethod, PriceAxisLabelStackingManager, HitTestResult, LineToolHitTestData } from 'lightweight-charts-line-tools-core';
/**
 * Defines the default configuration options for the Brush (Freehand) tool.
 *
 * **Key Defaults:**
 * - **Points:** `pointsCount: -1` indicates an unbounded tool (variable number of points).
 * - **Interaction:** `MouseUp` finalization for continuous drawing.
 * - **Line Style:** `Round` line caps and joins for a smooth, natural brush stroke.
 * - **Color:** Default cyan line, transparent background.
 * - **Labels:** Axis labels are hidden by default as this is an annotation tool.
 * - **Anchors:** Only the center anchor is active for dragging the whole tool.
 */
export declare const BrushOptionDefaults: LineToolOptionsInternal<'Brush'>;
/**
 * Concrete implementation of the Brush (Freehand) drawing tool.
 *
 * **What is a Brush Tool?**
 * A Brush tool allows the user to draw continuous, freehand lines by clicking and dragging
 * the mouse. It captures a stream of points as the mouse moves.
 *
 * **Key Characteristics:**
 * - **Unbounded Points:** `pointsCount: -1` (it can have any number of points).
 * - **MouseUp Finalization:** Drawing ends when the mouse button is released.
 * - **Point Filtering:** Implements `addPoint` override to filter out redundant points
 *   (i.e., points too close to the last one).
 */
export declare class LineToolBrush<HorzScaleItem> extends BaseLineTool<HorzScaleItem> {
    /**
     * The unique identifier for this tool type ('Brush').
     *
     * @override
     */
    readonly toolType: LineToolType;
    /**
     * Defines the number of anchor points required to draw this tool.
     *
     * A Brush tool is **unbounded** and can have any number of points, so `pointsCount` is `-1`.
     *
     * @override
     */
    readonly pointsCount: number;
    /**
     * Explicitly defines the highest valid index for an interactive anchor point.
     *
     * For a Brush tool, typically only one virtual "center" anchor is used to drag
     * the entire shape. Therefore, the maximum index is **0**.
     *
     * @override
     * @returns `0`
     */
    maxAnchorIndex(): number;
    /**
     * Indicates if the tool supports "Click-Click" creation.
     *
     * **Tutorial Note:**
     * Freehand tools (`Brush`, `Highlighter`) are designed for continuous drawing via drag.
     * "Click-Click" is not a natural interaction for them.
     *
     * @override
     * @returns `false`
     */
    supportsClickClickCreation(): boolean;
    /**
     * Confirms that this tool can be created via the "Click-Drag" method.
     *
     * **Interaction Flow:** Press Down -> Draw Continuously -> Release.
     * This is the primary and only way to draw with the Brush tool.
     *
     * @override
     * @returns `true`
     */
    supportsClickDragCreation(): boolean;
    /**
     * Indicates if holding Shift should apply geometric constraints during creation/editing.
     *
     * **Tutorial Note:**
     * For freehand drawing, applying constraints would hinder the natural flow.
     * Therefore, this is disabled.
     *
     * @override
     * @returns `false`
     */
    supportsShiftClickDragConstraint(): boolean;
    /**
     * Initializes the Brush tool.
     *
     * **Tutorial Note on Construction:**
     * 1. **Base Defaults:** Uses `BrushOptionDefaults` (cyan line, transparent background).
     * 2. **User Options:** Merges user provided settings.
     * 3. **Points Count:** Explicitly sets `pointsCount` to `-1` for unbounded drawing.
     * 4. **View:** Assigns `LineToolBrushPaneView`, which handles smoothing the raw mouse input
     *    and rendering the continuous path.
     *
     * @param coreApi - The Core Plugin API.
     * @param chart - The Lightweight Charts Chart API.
     * @param series - The Series API this tool is attached to.
     * @param horzScaleBehavior - The horizontal scale behavior.
     * @param options - Configuration overrides.
     * @param points - Initial points.
     * @param priceAxisLabelStackingManager - The manager for label collision.
     */
    constructor(coreApi: LineToolsCorePlugin<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>, options: DeepPartial<LineToolOptionsInternal<"Brush">> | undefined, points: LineToolPoint[] | undefined, priceAxisLabelStackingManager: PriceAxisLabelStackingManager<HorzScaleItem>);
    /**
     * Overrides the base `addPoint` method to implement **distance-based point filtering**.
     *
     * **Tutorial Note on Smoothing Input:**
     * Freehand drawing captures many points. To prevent jagged lines and reduce data load,
     * this method checks the pixel distance between the new point and the last permanent point.
     * - If the distance is below `DISTANCE_THRESHOLD_PX`, the new point is discarded.
     * - Only significant movements are added, creating a smoother visual path.
     *
     * @param newLogicalPoint - The new point suggested by the `InteractionManager`.
     * @override
     */
    addPoint(newLogicalPoint: LineToolPoint): void;
    /**
     * Specifies how the tool creation should end.
     *
     * For a freehand tool like Brush, drawing continues as long as the mouse button is down.
     * Therefore, creation is finalized on `MouseUp`.
     *
     * @override
     * @returns `FinalizationMethod.MouseUp`
     */
    getFinalizationMethod(): FinalizationMethod;
    /**
     * Explicitly enables full tool translation when dragging the first anchor (index 0).
     *
     * **Tutorial Note:**
     * For unbounded tools like Brush, there isn't really a "point 0" in the traditional sense
     * that you'd resize from. The single anchor that appears for a Brush is intended to
     * let the user **drag the entire shape** around the chart. This override enables that behavior.
     *
     * @override
     * @returns `true`
     */
    anchor0TriggersTranslation(): boolean;
    /**
     * Performs the hit test for the Brush tool by delegating to its associated Pane View.
     *
     * **Architecture Note:**
     * The `LineToolBrushPaneView` uses a `PolygonRenderer` to draw the smoothed, filled path.
     * The `PolygonRenderer` is responsible for the complex `pointInPolygon` hit-testing.
     * This method simply acts as the bridge to that logic.
     *
     * @param x - X coordinate in pixels.
     * @param y - Y coordinate in pixels.
     * @returns A hit result if the mouse is over the brush stroke or its bounding box.
     * @override
     */
    _internalHitTest(x: Coordinate, y: Coordinate): HitTestResult<LineToolHitTestData> | null;
}
