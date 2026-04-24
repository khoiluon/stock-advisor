import { IChartApiBase, ISeriesApi, IHorzScaleBehavior, SeriesType, Coordinate } from 'lightweight-charts';
import { BaseLineTool, LineToolPoint, LineToolType, LineToolOptionsInternal, TextOptions, DeepPartial, LineToolsCorePlugin, PriceAxisLabelStackingManager, HitTestResult, Point, InteractionPhase, ConstraintResult } from 'lightweight-charts-line-tools-core';
/**
 * Defines the default configuration options for the Long/Short Position tool.
 *
 * **Tutorial Note:**
 * This tool is visually composed of two distinct zones:
 * 1. **Risk Zone (Stop Loss):** Red rectangle (`entryStopLossRectangle`) + Text.
 * 2. **Reward Zone (Profit Target):** Green rectangle (`entryPtRectangle`) + Text.
 *
 * The defaults configure these with standard trading colors (Red/Green) and enable
 * the "Auto Text" feature (`showAutoText: true`) which automatically calculates and displays
 * the Risk/Reward ratio and price levels.
 */
export declare const LongShortPositionOptionDefaults: LineToolOptionsInternal<'LongShortPosition'>;
/**
 * Concrete implementation of the Long/Short Position drawing tool.
 *
 * **What is a Position Tool?**
 * It is a risk management tool defined by **3 logical points**:
 * 1. **Entry Price (P0):** The start of the trade.
 * 2. **Stop Loss (P1):** The invalidation point.
 * 3. **Profit Target (P2):** The target exit point.
 *
 * **Complex Logic:**
 * Unlike simple shapes, this tool has "Business Logic":
 * - It detects direction (Long if Stop < Entry, Short if Stop > Entry).
 * - It calculates Risk:Reward ratios.
 * - It handles "Flipping" (changing colors/direction when Entry crosses Stop).
 */
export declare class LineToolLongShortPosition<HorzScaleItem> extends BaseLineTool<HorzScaleItem> {
    /**
     * The unique identifier for this tool type ('LongShortPosition').
     *
     * @override
     */
    readonly toolType: LineToolType;
    /**
     * Defines the number of anchor points required to draw this tool.
     *
     * A Position tool requires exactly **3 points** (Entry, Stop, Target). User defines 2 points on creation, the 3rd point
     * which is the target is generated on creation and can be modified after creation
     *
     * @override
     */
    readonly pointsCount: number;
    /**
     * Explicitly defines the highest valid index for an interactive anchor point.
     *
     * We support 3 interactive handles:
     * - **0:** Entry Price.
     * - **1:** Stop Loss.
     * - **2:** Profit Target.
     *
     * @override
     * @returns `2`
     */
    maxAnchorIndex(): number;
    private _clickCount;
    private _isLong;
    private _flipModeActive;
    /**
     * Confirms that this tool is created via the "Click-Click" method.
     *
     * **Interaction Flow:**
     * 1. Click Entry.
     * 2. Click Stop Loss.
     * 3. (Auto) Profit Target is initially generated at 3R (3x Risk) automatically.
     *
     * @override
     * @returns `true`
     */
    supportsClickClickCreation(): boolean;
    /**
     * Indicates if the tool supports "Click-Drag" creation.
     *
     * We disable this (`false`) to enforce precision. Placing Entry and Stop Loss
     * usually requires exact clicking rather than a sweeping drag motion.
     *
     * @override
     * @returns `false`
     */
    supportsClickDragCreation(): boolean;
    /**
     * Enables geometric constraints (Shift key) during creation.
     *
     * If `true`, holding Shift while placing points will apply the logic defined in
     * {@link getShiftConstrainedPoint} (typically locking the price level to prevent drift).
     *
     * @override
     * @returns `true`
     */
    supportsShiftClickClickConstraint(): boolean;
    /**
     * Indicates if holding Shift should apply geometric constraints during drag creation.
     *
     * Not applicable as `supportsClickDragCreation` is false.
     *
     * @override
     * @returns `false`
     */
    supportsShiftClickDragConstraint(): boolean;
    /**
     * Initializes the Long/Short Position tool.
     *
     * **Tutorial Note on Logic:**
     * 1. **Defaults:** Merges defaults with user options.
     * 2. **Legacy Handling:** Checks if `points` contains only 2 points (Entry/Stop). If so,
     *    it auto-calculates and pushes a 3rd point (Profit Target) to ensure the tool is valid.
     * 3. **Direction Inference:** Determines if the tool is "Long" or "Short" based on P0 vs P1.
     * 4. **View:** Assigns `LineToolLongShortPositionPaneView` for complex multi-rect rendering.
     *
     * @param coreApi - The Core Plugin API.
     * @param chart - The Lightweight Charts Chart API.
     * @param series - The Series API this tool is attached to.
     * @param horzScaleBehavior - The horizontal scale behavior.
     * @param options - Configuration overrides.
     * @param points - Initial points.
     * @param priceAxisLabelStackingManager - The manager for label collision.
     */
    constructor(coreApi: LineToolsCorePlugin<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>, options: DeepPartial<LineToolOptionsInternal<'LongShortPosition'>>, points: LineToolPoint[] | undefined, priceAxisLabelStackingManager: PriceAxisLabelStackingManager<HorzScaleItem>);
    /**
     * Determines the current direction of the trade based on the geometry.
     *
     * @returns `true` if Entry Price > Stop Price (Long), `false` otherwise (Short).
     */
    isCurrentLong(): boolean;
    /**
     * Helper to retrieve the base text styling options for the auto-generated labels.
     *
     * Used internally or by views to ensure consistency when rendering the dynamic text stats.
     *
     * @returns A deep copy of the `entryStopLossText` options.
     */
    getAutoTextBaseOptions(): TextOptions;
    /**
     * Retrieves the internally cached direction state.
     *
     * This state helps track if a "Flip" has occurred during a drag operation.
     *
     * @returns `true` (Long), `false` (Short), or `null` (Uninitialized).
     */
    getStoredDirection(): boolean | null;
    /**
     * Updates the internally cached direction state.
     *
     * @param isLong - The new direction (`true` for Long).
     */
    setStoredDirection(isLong: boolean): void;
    /**
     * Safely rounds a raw price value to the nearest tick mark (`minMove`).
     *
     * **Why is this needed?**
     * Floating point math and mouse positions can result in prices like `100.0000001`.
     * This helper ensures values align with the instrument's precision (e.g., 0.01) while
     * guarding against division-by-zero errors if `minMove` is invalid.
     *
     * @param price - The raw price.
     * @returns The rounded price.
     * @private
     */
    private _roundPrice;
    /**
     * Calculates the Profit Target (P2) price based on the Entry (P0) and Stop Loss (P1).
     *
     * **Logic (3R Rule):**
     * 1. Calculates the Risk distance: `|Entry - Stop|`.
     * 2. Multiplies Risk by 3 to get the Reward distance.
     * 3. Adds/Subtracts Reward from Entry based on direction (Long/Short).
     * 4. Enforces a minimum distance (1 tick) to prevent the PT from overlapping the Entry.
     *
     * @param entryPoint - The entry point P0.
     * @param stopPoint - The stop loss point P1.
     * @param ptPointTimestamp - The X-coordinate for the new PT (usually synced to P1).
     * @returns A new {@link LineToolPoint} for the Profit Target.
     */
    calculateProfitTarget(entryPoint: LineToolPoint, stopPoint: LineToolPoint, ptPointTimestamp: number): LineToolPoint;
    /**
     * Detects if the trade direction has flipped (Entry crossed Stop Loss).
     *
     * @param newEntryPrice - The new entry price.
     * @param newStopPrice - The new stop price.
     * @returns `true` if the direction changed (Long -> Short or vice versa), `false` otherwise.
     * @private
     */
    private _checkForFlip;
    /**
     * The central state machine logic for the tool.
     *
     * **Tutorial Note:**
     * This method handles the complex behavior when dragging points:
     * 1. **Flip Detection:** If Entry crosses Stop, it flags `_flipModeActive`.
     * 2. **Forced 3R:** If flipping or creating, it forces the PT to stay at exactly 3x Risk.
     * 3. **Custom Mode:** If the user drags the PT explicitly, it respects that distance but ensures
     *    it doesn't cross back over the Entry price (min 1 tick distance).
     *
     * This runs after every drag event to keep the 3 points geometrically valid.
     *
     * @private
     */
    private _updateAndNormalizeToolState;
    /**
     * Overrides the base method to inject a virtual Profit Target during creation.
     *
     * **Why override?**
     * During creation, the user only clicks P0 (Entry) and P1 (Stop). The P2 (Target) hasn't
     * been created yet. This override dynamically calculates where P2 *would* be (at 3R)
     * and returns it as part of the array. This allows the View to render the full Green/Red
     * shape while the user is still just dragging the Stop Loss ghost point.
     *
     * @returns The array of points, potentially including a virtual P2.
     * @override
     */
    points(): LineToolPoint[];
    /**
     * Retrieves a point from the (potentially augmented) points array.
     *
     * Delegates to the overridden {@link points} method to ensure virtual points are returned correctly.
     *
     * @param index - The point index.
     * @returns The point or `null`.
     * @override
     */
    getPoint(index: number): LineToolPoint | null;
    /**
     * Handles complex drag logic for Entry, Stop, and Target points.
     *
     * **Logic:**
     * - **Index 2 (Target):** Constrains the drag so the Target cannot cross the Entry price.
     *   It allows "Custom R:R" mode (user sets specific target).
     * - **Index 0/1 (Entry/Stop):** Updates the point and then triggers `_updateAndNormalizeToolState`.
     *   This might cause the Target to jump (if in 3R mode) to maintain the ratio.
     *
     * @param index - The anchor index.
     * @param point - The new logical position.
     * @override
     */
    setPoint(index: number, point: LineToolPoint): void;
    /**
     * Orchestrates the creation flow (Click 1 -> Entry, Click 2 -> Stop + Auto PT).
     *
     * **Tutorial Note:**
     * 1. **Click 1:** Adds Entry.
     * 2. **Click 2:** Adds Stop. Crucially, it **also** creates and pushes the permanent Profit Target (P2)
     *    calculated at 3R. It then immediately finalizes the tool (`tryFinish()`).
     *
     * @param point - The raw mouse point.
     * @override
     */
    addPoint(point: LineToolPoint): void;
    /**
     * Legacy/No-op method.
     *
     * The core plugin handles ghosting via `setLastPoint`. This override exists to satisfy
     * internal contracts or legacy patterns but performs no action.
     */
    updatePreviewPoints(point: LineToolPoint): void;
    /**
     * Performs the hit test for the Position tool.
     *
     * **Architecture Note:**
     * Delegates to `LineToolLongShortPositionPaneView`. The view composites multiple renderers
     * (Risk Rect, Reward Rect, Labels). Hitting any of them selects the tool.
     *
     * @param x - X coordinate.
     * @param y - Y coordinate.
     * @returns A hit result, or `null`.
     * @override
     */
    _internalHitTest(x: Coordinate, y: Coordinate): HitTestResult<any> | null;
    /**
     * Resets transient state flags at the end of an interaction (MouseUp).
     *
     * Specifically, it clears `_flipModeActive`, marking the end of a dynamic flip operation.
     * The geometric order of points is **not** sorted here because P0/P1/P2 have fixed roles
     * (Entry/Stop/Target) regardless of their price values.
     *
     * @override
     */
    normalize(): void;
    /**
     * Implements Shift key constraints for editing.
     *
     * **Constraint Logic:**
     * - **Entry/Stop (0, 1):** Locks the **Price** (Horizontal move only). This allows the user
     *   to slide the trade setup forward/backward in time without accidentally changing the price levels.
     * - **Target (2):** No extra constraint applied (handled by `setPoint` limits).
     *
     * @param pointIndex - Anchor index.
     * @param rawScreenPoint - Mouse position.
     * @param phase - Interaction phase.
     * @param originalLogicalPoint - Start position.
     * @param allOriginalLogicalPoints - Full state snapshot.
     * @returns The constrained point result.
     * @override
     */
    getShiftConstrainedPoint(pointIndex: number, rawScreenPoint: Point, phase: InteractionPhase, originalLogicalPoint: LineToolPoint, allOriginalLogicalPoints: LineToolPoint[]): ConstraintResult;
}
