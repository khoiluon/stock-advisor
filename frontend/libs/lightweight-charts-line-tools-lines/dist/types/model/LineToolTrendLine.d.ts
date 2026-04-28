import { IChartApiBase, ISeriesApi, IHorzScaleBehavior, SeriesType, Coordinate } from 'lightweight-charts';
import { BaseLineTool, LineToolPoint, LineToolOptionsInternal, LineToolType, LineToolsCorePlugin, DeepPartial, HitTestResult, LineToolHitTestData, Point, InteractionPhase, PriceAxisLabelStackingManager, ConstraintResult } from 'lightweight-charts-line-tools-core';
/**
 * Defines the default configuration options for the Trend Line tool.
 *
 * These defaults serve as the baseline for the Trend Line itself, but are also exported
 * and reused by derived tools (like Ray, Arrow, and Extended Line) to ensure visual consistency
 * across all 2-point line tools.
 *
 * Key defaults include:
 * - Color: Blue (`#2962ff`)
 * - Width: 1px
 * - Style: Solid
 * - Extensions: None (a finite segment)
 * - End Caps: Normal (no arrows)
 */
export declare const TrendLineOptionDefaults: LineToolOptionsInternal<'TrendLine'>;
/**
 * Concrete implementation of the standard Trend Line drawing tool.
 *
 * A Trend Line is the fundamental 2-point geometry tool. It connects a start point (P1)
 * and an end point (P2) with a straight line.
 *
 * **Tutorial Note on Inheritance:**
 * This class is designed to be extended. Tools like `LineToolRay`, `LineToolArrow`, and
 * `LineToolExtendedLine` inherit from this class because they share the exact same
 * input logic (2 points) and interaction rules. They only differ in their visual
 * options (e.g., `extend.right = true` for a Ray).
 */
export declare class LineToolTrendLine<HorzScaleItem> extends BaseLineTool<HorzScaleItem> {
    /**
     * The unique identifier for this tool type ('TrendLine').
     *
     * @override
     */
    readonly toolType: LineToolType;
    /**
     * Defines the number of anchor points required to draw this tool.
     *
     * A Trend Line always consists of exactly **2 points** (Start and End).
     *
     * @override
     */
    readonly pointsCount: number;
    /**
     * Explicitly defines the highest valid index for an interactive anchor point.
     *
     * Since `pointsCount` is 2, the valid indices are 0 and 1. Therefore, the maximum index is 1.
     * The `InteractionManager` uses this to ensure it tracks drag gestures for both ends of the line.
     *
     * @override
     * @returns `1`
     */
    maxAnchorIndex(): number;
    /**
     * Confirms that this tool can be created via the "Click-Click" method.
     *
     * **Interaction Flow:**
     * 1. User clicks once to set the Start Point (P1).
     * 2. User moves the mouse (ghost line follows).
     * 3. User clicks again to set the End Point (P2).
     *
     * @override
     * @returns `true`
     */
    supportsClickClickCreation(): boolean;
    /**
     * Confirms that this tool can be created via the "Click-Drag" method.
     *
     * **Interaction Flow:**
     * 1. User presses mouse down to set the Start Point (P1).
     * 2. User drags the mouse while holding the button.
     * 3. User releases the mouse button to set the End Point (P2).
     *
     * @override
     * @returns `true`
     */
    supportsClickDragCreation(): boolean;
    /**
     * Enables geometric constraints (Shift key) during "Click-Click" creation.
     *
     * If `true`, holding Shift while hovering to place the second point will lock the line
     * to specific angles (e.g., horizontal, vertical, or 45-degree increments).
     *
     * @override
     * @returns `true`
     */
    supportsShiftClickClickConstraint(): boolean;
    /**
     * Enables geometric constraints (Shift key) during "Click-Drag" creation.
     *
     * If `true`, holding Shift while dragging to place the second point will lock the line
     * to specific angles.
     *
     * @override
     * @returns `true`
     */
    supportsShiftClickDragConstraint(): boolean;
    /**
     * Initializes the Trend Line tool.
     *
     * **Tutorial Note on Logic:**
     * 1. It starts with the `TrendLineOptionDefaults`.
     * 2. It merges any user-provided `options` on top.
     * 3. It instantiates the specific `LineToolTrendLinePaneView`, which handles the actual canvas rendering.
     *
     * @param coreApi - The Core Plugin API.
     * @param chart - The Lightweight Charts Chart API.
     * @param series - The Series API this tool is attached to.
     * @param horzScaleBehavior - The horizontal scale behavior for time conversion.
     * @param options - Configuration overrides.
     * @param points - Initial points (if restoring state).
     * @param priceAxisLabelStackingManager - The manager for label collision.
     */
    constructor(coreApi: LineToolsCorePlugin<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>, options: DeepPartial<LineToolOptionsInternal<'TrendLine'>>, points: LineToolPoint[] | undefined, priceAxisLabelStackingManager: PriceAxisLabelStackingManager<HorzScaleItem>);
    /**
     * Implements the specific geometric constraint logic when the user holds the Shift key while drawing or editing.
     *
     * **Tutorial Note:**
     * For a standard Trend Line, holding Shift triggers a **Price Lock** (Horizontal Lock).
     * 1. It identifies the "Anchor Point" (the point *not* being moved).
     * 2. It takes the Y-coordinate (Price) of that anchor.
     * 3. It forces the point being moved to align with that Y-coordinate.
     *
     * This allows users to easily draw perfectly horizontal lines by holding Shift.
     *
     * @param pointIndex - The index of the point being moved (0 or 1).
     * @param rawScreenPoint - The actual mouse position on screen.
     * @param phase - Whether we are creating the tool or editing an existing one.
     * @param originalLogicalPoint - The logical position of the point being moved before the drag started.
     * @param allOriginalLogicalPoints - The state of all points before the drag started.
     * @returns A result containing the constrained screen point and a hint ('price') that we snapped to a specific price level.
     * @override
     */
    getShiftConstrainedPoint(pointIndex: number, rawScreenPoint: Point, phase: InteractionPhase, originalLogicalPoint: LineToolPoint, // This is the *dragged* point's original logical state
    allOriginalLogicalPoints: LineToolPoint[]): ConstraintResult;
    /**
     * Re-orders the internal points so that the start point (P0) is always chronologically earlier
     * (to the left) than the end point (P1).
     *
     * **Why is this needed?**
     * Many rendering calculations (especially for Rays or Extended Lines) assume directionality.
     * By ensuring P0 is always the "left" point, we simplify the math for drawing extensions "to the right".
     *
     * @remarks
     * If the points share the exact same time, the Price is used as a tie-breaker to ensure
     * deterministic ordering.
     */
    normalize(): void;
    /**
     * Updates the logical coordinates of a specific anchor point.
     *
     * While this implementation currently delegates directly to the base class, overriding it here
     * allows the Trend Line to intercept point updates if custom validation logic were needed in the future.
     *
     * @param index - The index of the point to update (0 or 1).
     * @param point - The new logical coordinates.
     * @override
     */
    setPoint(index: number, point: LineToolPoint): void;
    /**
     * Performs the hit test to see if the mouse is hovering over this tool.
     *
     * **Architecture Note:**
     * The **Model** (this class) knows *data* (time/price), but it doesn't know *pixels* (where lines are drawn).
     * The **View** (`LineToolTrendLinePaneView`) knows pixels.
     *
     * Therefore, this method retrieves the active Pane View and asks its **Composite Renderer**
     * to perform the hit test. This ensures that what the user *sees* is exactly what they *click*.
     *
     * @param x - X coordinate in pixels.
     * @param y - Y coordinate in pixels.
     * @returns A hit result if the mouse is over the line or an anchor, otherwise `null`.
     * @override
     */
    _internalHitTest(x: Coordinate, y: Coordinate): HitTestResult<LineToolHitTestData> | null;
}
