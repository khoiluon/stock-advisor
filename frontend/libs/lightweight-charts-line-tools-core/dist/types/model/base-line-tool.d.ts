/**
 * This file defines the abstract BaseLineTool class.
 * It serves as the foundation for all individual line drawing tools, encapsulating common
 * properties, state management, and essential methods for coordinate conversion and interaction.
 *
 * It implements the `ISeriesPrimitive` interface, making any of its subclasses a valid
 * plugin for a Lightweight Charts series. Its primary role is to abstract away the
 * complexities of the v5 plugin system, providing a consistent and simpler API for
 * individual tool implementations.
 */
import { IChartApiBase, ISeriesApi, ISeriesPrimitive, SeriesAttachedParameter, SeriesType, Coordinate, PrimitiveHoveredItem, IHorzScaleBehavior, Logical, IPaneApi } from 'lightweight-charts';
import { LineToolExport, LineToolPoint } from '../api/public-api';
import { DeepPartial } from '../utils/helpers';
import { LineToolOptionsInternal, LineToolType, HitTestResult, IPaneView, IUpdatablePaneView, FirstValue, IPriceFormatter, AutoscaleInfo, IPriceAxisView, ITimeAxisView, PaneCursorType, InteractionPhase, ConstraintResult, FinalizationMethod } from '../types';
import { Point } from '../utils/geometry';
import { LineToolsCorePlugin } from '../core-plugin';
import { PriceDataSource } from './price-data-source';
import { PriceAxisLabelStackingManager } from './price-axis-label-stacking-manager';
/**
 * The abstract base class for all line drawing tools in the plugin.
 *
 * This class extends {@link PriceDataSource} and implements the Lightweight Charts `ISeriesPrimitive`
 * interface. It provides a common set of properties, utility methods for coordinate conversion,
 * state management (selection, hover, editing), and hooks for custom behavior (hit-testing, constraints).
 * All custom line tool implementations must extend this class.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item (e.g., `Time` or `number`).
 */
export declare abstract class BaseLineTool<HorzScaleItem> extends PriceDataSource<HorzScaleItem> implements ISeriesPrimitive<HorzScaleItem> {
    /**
     * The unique string identifier for this specific tool's type (e.g., 'TrendLine', 'Rectangle').
     * This is defined by the concrete implementation class.
     * @readonly
     */
    readonly toolType: LineToolType;
    /**
     * The fixed number of logical points this tool requires.
     *
     * - A positive number (e.g., `2` for a TrendLine) means the tool is *bounded*.
     * - A value of `-1` (e.g., for Brush, Path) means the tool is *unbounded* and can have a variable number of points.
     * @readonly
     */
    readonly pointsCount: number;
    protected _priceAxisLabelViews: IPriceAxisView[];
    protected _timeAxisLabelViews: ITimeAxisView[];
    /**
     * Reference to the manager responsible for resolving price axis label collisions.
     * Used to ensure this tool's price labels do not overlap others.
     * @protected
     */
    protected _priceAxisLabelStackingManager: PriceAxisLabelStackingManager<HorzScaleItem>;
    /**
     * Abstract method for the tool's core hit-testing logic.
     *
     * Concrete subclasses must implement this to define the precise geometric area of the tool
     * (lines, backgrounds, anchors) and return a {@link HitTestResult} if the coordinates are inside.
     *
     * @param x - The X coordinate of the mouse pointer (in pixels).
     * @param y - The Y coordinate of the mouse pointer (in pixels).
     * @returns A {@link HitTestResult} containing hit type and index data, or `null`.
     * @internal
     */
    abstract _internalHitTest(x: Coordinate, y: Coordinate): HitTestResult<any> | null;
    /**
     * Provides an array of price axis view components to Lightweight Charts for rendering the tool's labels.
     *
     * This implementation wraps the internal `_priceAxisLabelViews` array.
     *
     * @returns A readonly array of {@link IPriceAxisView} components.
     */
    priceAxisViews(): readonly IPriceAxisView[];
    /**
     * Provides an array of time axis view components to Lightweight Charts for rendering the tool's labels.
     *
     * This implementation wraps the internal `_timeAxisLabelViews` array.
     *
     * @returns A readonly array of {@link ITimeAxisView} components.
     */
    timeAxisViews(): readonly ITimeAxisView[];
    private _overrideCursor;
    /**
     * Temporarily overrides the cursor style displayed over the chart pane, bypassing normal hover detection.
     *
     * This is typically used by the {@link InteractionManager} during an active drag or edit gesture
     * to ensure the cursor stays consistent (e.g., `grabbing`) regardless of where the mouse moves.
     *
     * @param cursor - The {@link PaneCursorType} to enforce, or `null` to revert to default behavior.
     */
    setOverrideCursor(cursor: PaneCursorType | null): void;
    /**
     * The public hit-test method required by the Lightweight Charts `ISeriesPrimitive` interface.
     *
     * This method acts as an adapter, calling `_internalHitTest` and converting its internal
     * result (`HitTestResult`) into the required LWC `PrimitiveHoveredItem` format, including
     * cursor determination and Z-order.
     *
     * @param x - The X coordinate from Lightweight Charts (in pixels).
     * @param y - The Y coordinate from Lightweight Charts (in pixels).
     * @returns A `PrimitiveHoveredItem` if the tool is hit, otherwise `null`.
     */
    hitTest(x: number, y: number): PrimitiveHoveredItem | null;
    protected _chart: IChartApiBase<HorzScaleItem>;
    protected _series: ISeriesApi<SeriesType, HorzScaleItem>;
    protected _horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>;
    protected _coreApi: LineToolsCorePlugin<HorzScaleItem>;
    protected _requestUpdate?: () => void;
    protected _id: string;
    protected _options: LineToolOptionsInternal<LineToolType>;
    protected _points: LineToolPoint[];
    protected _paneViews: IUpdatablePaneView[];
    private _selected;
    private _hovered;
    private _editing;
    private _creating;
    protected _lastPoint: LineToolPoint | null;
    private _editedPointIndex;
    private _currentPoint;
    private _isDestroying;
    private _attachedPane;
    /**
     * Initializes the Base Line Tool instance.
     *
     * Sets up core references, assigns the unique ID, and creates the persistent Price and Time Axis View instances
     * based on the tool's required `pointsCount`.
     *
     * @param coreApi - The core plugin instance.
     * @param chart - The chart API instance.
     * @param series - The series API instance this tool is attached to.
     * @param horzScaleBehavior - The horizontal scale behavior for time conversion utilities.
     * @param finalOptions - The complete and final configuration options for the tool instance.
     * @param points - Initial array of logical points.
     * @param toolType - The specific string identifier for the tool.
     * @param pointsCount - The fixed number of points this tool requires (`-1` for unbounded).
     * @param priceAxisLabelStackingManager - The manager for label collision resolution.
     */
    constructor(coreApi: LineToolsCorePlugin<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>, finalOptions: LineToolOptionsInternal<LineToolType>, points: LineToolPoint[] | undefined, toolType: LineToolType, pointsCount: number, priceAxisLabelStackingManager: PriceAxisLabelStackingManager<HorzScaleItem>);
    /**
     * Lifecycle hook called by Lightweight Charts when the primitive is first attached to a series.
     *
     * This method finalizes the setup by acquiring necessary runtime references:
     * the `IPriceScaleApi`, the `requestUpdate` callback, and the {@link IPaneApi} reference.
     *
     * @param param - The parameters provided by Lightweight Charts upon attachment.
     * @returns void
     */
    attached(param: SeriesAttachedParameter<HorzScaleItem>): void;
    /**
     * OPTIONAL: Defines the maximum index of an interactive anchor point that this tool supports.
     *
     * This is used by the {@link InteractionManager} to correctly determine the total number of anchor
     * points (including virtual ones like the midpoint handle on a Trend Line) to monitor for interaction.
     *
     * @returns The highest index of an anchor point (e.g., 7 for an 8-anchor tool).
     */
    maxAnchorIndex?(): number;
    /**
     * OPTIONAL: Indicates if this tool supports creation via a sequence of discrete mouse clicks.
     *
     * Most bounded tools (e.g., TrendLine) should return `true` or omit this method (defaulting to true).
     * Unbounded tools (e.g., Brush) typically return `false`.
     *
     * @returns `true` if click-click is supported, `false` otherwise.
     */
    supportsClickClickCreation?(): boolean;
    /**
     * OPTIONAL: Indicates if this tool supports creation via a single click-hold-drag-release gesture.
     *
     * This is the common method for drawing tools like Rectangles and the only method for freehand tools like Brush.
     *
     * @returns `true` if click-drag is supported, `false` otherwise.
     */
    supportsClickDragCreation?(): boolean;
    /**
     * OPTIONAL: Indicates if holding the Shift key should apply a geometric constraint (like axis-lock)
     * during a **discrete click-click** creation sequence.
     *
     * This is only relevant if {@link supportsClickClickCreation} is `true`.
     *
     * @returns `true` if the constraint should be applied, `false` otherwise.
     */
    supportsShiftClickClickConstraint?(): boolean;
    /**
     * OPTIONAL: Indicates if holding the Shift key should apply a geometric constraint (like 45-degree lock)
     * during a **click-drag-release** creation gesture.
     *
     * This is only relevant if {@link supportsClickDragCreation} is `true`.
     *
     * @returns `true` if the constraint should be applied, `false` otherwise.
     */
    supportsShiftClickDragConstraint?(): boolean;
    /**
     * Lifecycle hook called by Lightweight Charts when the primitive is detached from a series.
     *
     * This performs crucial cleanup by nullifying references to external Lightweight Charts API objects
     * (chart, series, pane, etc.) to prevent memory leaks and stale closures.
     *
     * @returns void
     */
    detached(): void;
    /**
     * Returns the {@link IPaneApi} instance to which this tool is currently attached.
     *
     * This reference is required for internal operations like detaching the tool primitive.
     *
     * @returns The {@link IPaneApi} for the attached pane.
     * @throws An error if the tool has not been successfully attached to a series/pane yet.
     */
    getPane(): IPaneApi<HorzScaleItem>;
    /**
     * Retrieves the unique string identifier for this tool instance.
     *
     * @returns The unique ID.
     */
    id(): string;
    /**
     * Sets a specific unique ID for this tool instance.
     *
     * This is primarily used during programmatic creation via {@link LineToolsCorePlugin.createOrUpdateLineTool}
     * to ensure a user-defined ID is preserved.
     *
     * @param id - The unique string ID to assign.
     * @returns void
     */
    setId(id: string): void;
    /**
     * Checks if the tool is currently in the selected state.
     *
     * The selected state typically enables anchor handles and border highlighting.
     *
     * @returns `true` if selected, `false` otherwise.
     */
    isSelected(): boolean;
    /**
     * Checks if the mouse cursor is currently hovering over the tool.
     *
     * The hovered state often triggers a temporary visual change, like a different border color.
     *
     * @returns `true` if hovered, `false` otherwise.
     */
    isHovered(): boolean;
    /**
     * Checks if the tool is currently being actively edited (i.e., an anchor point is being dragged).
     *
     * The editing state is distinct from being merely selected.
     *
     * @returns `true` if an anchor is being dragged, `false` otherwise.
     */
    isEditing(): boolean;
    /**
     * Checks if the tool is currently in the process of being created by user interaction.
     *
     * The creating state is active from the moment the tool is initiated until its final point is placed.
     *
     * @returns `true` if in creation mode, `false` otherwise.
     */
    isCreating(): boolean;
    /**
     * Sets the tool's selection state and triggers a view update to reflect the change.
     *
     * @param selected - The new selection state (`true` to select, `false` to deselect).
     * @returns void
     */
    setSelected(selected: boolean): void;
    /**
     * Sets the tool's hovered state and triggers a view update if the state changes.
     *
     * @param hovered - The new hover state.
     * @returns void
     */
    setHovered(hovered: boolean): void;
    /**
     * Sets the tool's editing state (active drag is in progress).
     *
     * This typically happens when the user clicks down on an anchor and moves beyond the drag threshold.
     *
     * @param editing - The new editing state.
     * @returns void
     */
    setEditing(editing: boolean): void;
    /**
     * Sets the tool's creation state.
     *
     * This is used internally by the {@link InteractionManager} to track which tool instance
     * is currently accepting new points from user clicks.
     *
     * @param creating - The new creation state.
     * @returns void
     */
    setCreating(creating: boolean): void;
    /**
     * Returns the index of the anchor point currently being dragged/edited.
     *
     * @returns The zero-based index of the dragged point, or `null` if `isEditing` is false.
     */
    editedPointIndex(): number | null;
    /**
     * Sets the index of the anchor point that is currently the target of an editing drag.
     *
     * @param index - The index of the point, or `null` to clear the reference.
     * @returns void
     */
    setEditedPointIndex(index: number | null): void;
    /**
     * Retrieves the last known screen coordinates of the mouse cursor over the chart.
     *
     * This point is continuously updated by the {@link InteractionManager} and is used by renderers
     * (like the anchor renderer) to draw effects relative to the mouse position (e.g., hover halo).
     *
     * @returns A {@link Point} object with the current mouse screen coordinates.
     */
    currentPoint(): Point;
    /**
     * Sets the last known screen coordinates of the mouse cursor.
     *
     * @param point - The new screen coordinate point.
     * @returns void
     */
    setCurrentPoint(point: Point): void;
    /**
     * Retrieves the full list of points used for drawing the tool.
     *
     * This list includes both the permanent, committed points (`_points`) and, if the tool is in
     * creation mode, the single temporary "ghost" point (`_lastPoint`) currently following the cursor.
     *
     * @returns A composite array of {@link LineToolPoint}s.
     */
    points(): LineToolPoint[];
    /**
     * Retrieves the single temporary "ghost" point used for live preview during tool creation.
     *
     * @returns The last calculated {@link LineToolPoint} of the mouse position, or `null`.
     */
    getLastPoint(): LineToolPoint | null;
    /**
     * Sets or clears the temporary "ghost" point.
     *
     * Used during the tool creation process to show a live preview that follows the user's mouse.
     * Setting this immediately calls `_triggerChartUpdate`.
     *
     * @param point - The temporary {@link LineToolPoint}, or `null` to clear it.
     * @returns void
     */
    setLastPoint(point: LineToolPoint | null): void;
    /**
     * Overwrites the entire array of permanent points defining the tool's geometry.
     *
     * This method is called during programmatic updates or when the entire tool is translated (moved).
     *
     * @param points - The new array of {@link LineToolPoint}s.
     * @returns void
     */
    setPoints(points: LineToolPoint[]): void;
    /**
     * Adds a new, permanent {@link LineToolPoint} to the end of the tool's point array.
     *
     * This is called by the {@link InteractionManager} when a user performs a click to commit a new point during creation.
     *
     * @param point - The {@link LineToolPoint} to add.
     * @returns void
     */
    addPoint(point: LineToolPoint): void;
    /**
     * Retrieves a permanent point from the internal array by its index.
     *
     * @param index - The zero-based index of the point.
     * @returns The requested {@link LineToolPoint}, or `null` if the index is out of bounds.
     */
    getPoint(index: number): LineToolPoint | null;
    /**
     * Updates a specific permanent point in the internal array with new logical coordinates.
     *
     * This method is called during editing (resizing) of a specific anchor point.
     *
     * @param index - The index of the point to modify.
     * @param point - The new {@link LineToolPoint} coordinates.
     * @returns void
     */
    setPoint(index: number, point: LineToolPoint): void;
    /**
     * Returns the number of permanently committed points currently defining the tool.
     *
     * This count excludes any temporary "ghost" point and is used by the {@link InteractionManager}
     * to decide the index of the next point to add.
     *
     * @returns The number of permanent points.
     */
    getPermanentPointsCount(): number;
    /**
     * Retrieves the complete and final configuration options object for this tool instance.
     *
     * This includes both the {@link LineToolOptionsCommon} and the tool-specific options.
     *
     * @returns The full options object.
     */
    options(): LineToolOptionsInternal<any>;
    /**
     * Deeply merges a partial set of new options into the tool's current configuration.
     *
     * This is the core method for updating the tool's appearance programmatically. It automatically
     * triggers a full view update and a chart redraw after the merge is complete.
     *
     * @param options - A deep partial of the tool's options structure containing changes to be merged.
     * @returns void
     */
    applyOptions(options: DeepPartial<LineToolOptionsInternal<any>>): void;
    /**
     * Checks if the tool has acquired its minimum required number of permanent points.
     *
     * For bounded tools (`pointsCount > 0`), this returns true if `_points.length` meets `pointsCount`.
     * For unbounded tools (`pointsCount === -1`), this check typically passes early, deferring finalization to `getFinalizationMethod`.
     *
     * @returns `true` if the tool is ready to exit creation mode, `false` otherwise.
     */
    isFinished(): boolean;
    /**
     * Attempts to transition the tool out of the `creating` state and into the `selected` state.
     *
     * This is called by the {@link InteractionManager} after a point is added. If `isFinished()` is true,
     * the creation state is reset, the selected state is set, and views are updated.
     *
     * @returns void
     */
    tryFinish(): void;
    /**
     * Generates the complete, serializable {@link LineToolExport} object representing the tool's current state.
     *
     * This is the fundamental data output used for API responses, event payloads, and state persistence.
     *
     * @returns The full export data object.
     */
    getExportData(): LineToolExport<LineToolType>;
    /**
     * OPTIONAL: Method used by the {@link InteractionManager} to enforce a tool-specific
     * geometric constraint (like Y-Lock, 45-degree, or Axis-Alignment) when the Shift key is pressed.
     *
     * Concrete tools implement this to define their specific constraint logic.
     *
     * @param pointIndex - The index of the anchor point being dragged.
     * @param rawScreenPoint - The raw, unconstrained screen coordinates of the mouse.
     * @param phase - The current {@link InteractionPhase} (Creation, Editing, or Move).
     * @param originalLogicalPoint - The logical point of the anchor at the start of the gesture.
     * @param allOriginalLogicalPoints - The full array of all anchor points BEFORE the drag started.
     * @returns The {@link ConstraintResult} containing the new constrained screen point and the snap axis hint.
     */
    getShiftConstrainedPoint?(pointIndex: number, rawScreenPoint: Point, phase: InteractionPhase, originalLogicalPoint: LineToolPoint, allOriginalLogicalPoints: LineToolPoint[]): ConstraintResult;
    /**
     * Provides an array of pane view components to Lightweight Charts for rendering the tool's body.
     *
     * This implements the `ISeriesPrimitive` contract.
     *
     * @returns A readonly array of {@link IPaneView} components.
     */
    paneViews(): readonly IPaneView[];
    /**
     * Signals that all associated view components (pane, price axis, time axis) need to update their internal data and caches.
     *
     * This method automatically triggers the synchronous update of the {@link PriceAxisLabelStackingManager}
     * to ensure correct vertical placement of labels before the next render.
     *
     * @returns void
     */
    updateAllViews(): void;
    /**
     * Retrieves the color that should be used for the price axis label background.
     *
     * Concrete tools should override this to return a dynamic color based on the tool's current state (e.g., color of P0).
     *
     * @returns A color string (e.g., '#FF0000') or `null` if the label should not be visible.
     */
    priceAxisLabelColor(): string | null;
    /**
     * Retrieves the color that should be used for the time axis label background.
     *
     * Concrete tools should override this to return a dynamic color based on the tool's current state (e.g., color of P0).
     *
     * @returns A color string (e.g., '#FF0000') or `null` if the label should not be visible.
     */
    timeAxisLabelColor(): string | null;
    /**
     * Retrieves the Lightweight Charts Series API instance this tool is attached to.
     *
     * @returns The `ISeriesApi` instance.
     * @throws An error if the series has not been attached (e.g., in `detached` state).
     */
    getSeries(): ISeriesApi<SeriesType, HorzScaleItem>;
    /**
     * Retrieves the Lightweight Charts Chart API instance associated with this tool.
     *
     * @returns The `IChartApiBase` instance.
     * @throws An error if the chart API is not available.
     */
    getChart(): IChartApiBase<HorzScaleItem>;
    /**
     * Retrieves the chart's horizontal scale behavior instance.
     *
     * This object is critical for correctly converting time values (`Time`, `UTCTimestamp`, etc.)
     * to and from the generic `HorzScaleItem` type used by Lightweight Charts.
     *
     * @returns The `IHorzScaleBehavior` instance.
     * @throws An error if the scale behavior is not attached.
     */
    get horzScaleBehavior(): IHorzScaleBehavior<HorzScaleItem>;
    /**
     * Transforms a logical data point (timestamp/price) into pixel screen coordinates.
     *
     * This utility handles the complex conversion, including interpolation for points
     * that lie in the chart's "blank logical space" (outside the available data bars).
     *
     * @param point - The logical {@link LineToolPoint} to convert.
     * @returns A {@link Point} with screen coordinates, or `null` if conversion fails.
     */
    pointToScreenPoint(point: LineToolPoint): Point | null;
    /**
     * Transforms a pixel screen coordinate into a logical data point (timestamp/price).
     *
     * This method is the inverse of `pointToScreenPoint` and is primarily used by the
     * {@link InteractionManager} to determine the final logical coordinates of a user click or drag.
     *
     * @param point - The {@link Point} with screen coordinates.
     * @returns A logical {@link LineToolPoint}, or `null` if conversion fails.
     */
    screenPointToPoint(point: Point): LineToolPoint | null;
    /**
     * Sets the internal array of pane view components.
     *
     * This protected method is called by the concrete line tool's `constructor` or `updateAllViews`
     * to define what graphical elements (lines, shapes, text, etc.) will be rendered.
     *
     * @param views - An array of {@link IUpdatablePaneView} instances.
     * @protected
     */
    protected _setPaneViews(views: IUpdatablePaneView[]): void;
    /**
     * Assigns the tool's final and complete configuration options.
     *
     * Concrete tool implementations use this during construction, ensuring the base class
     * always holds a unique, finalized options object.
     *
     * @param finalOptions - The complete options object.
     * @protected
     */
    protected _setupOptions(finalOptions: LineToolOptionsInternal<LineToolType>): void;
    /**
     * Cleans up and releases all resources held by the line tool instance.
     *
     * This is the final internal cleanup hook called by the {@link LineToolsCorePlugin} when the tool is removed.
     * It ensures memory safety by:
     * 1. Unregistering all price axis labels from the stacking manager.
     * 2. Clearing all internal view and point references.
     * 3. Nullifying the price scale.
     *
     * @returns void
     */
    destroy(): void;
    /**
     * Triggers a chart update (redraw) via the internal `requestUpdate` callback.
     *
     * This is the standard mechanism for the tool to force the chart to redraw itself
     * after a state change that affects its visual output.
     *
     * @internal
     * @returns void
     */
    _triggerChartUpdate(): void;
    /**
     * Implements the `IDataSource` method for the base value.
     *
     * For line tools, this typically has no meaning and returns 0.
     *
     * @returns The base value (0).
     */
    base(): number;
    /**
     * Provides autoscale information for the primitive, implementing the `IDataSource` contract.
     *
     * By default, line tools do not influence the chart's autoscale range, and this method returns `null`.
     * Tools that need to affect the autoscale (e.g., specialized markers) must override this.
     *
     * @param startTimePoint - The logical index of the start of the visible range.
     * @param endTimePoint - The logical index of the end of the visible range.
     * @returns An {@link AutoscaleInfo} object if the tool affects the scale, or `null`.
     */
    autoscaleInfo(startTimePoint: Logical, endTimePoint: Logical): AutoscaleInfo | null;
    /**
     * Implements the `IDataSource` method for providing the price scale's first value.
     *
     * This is primarily used for features like percentage-based price scales. For general line tools,
     * this is typically not applicable.
     *
     * @returns The {@link FirstValue} object, or `null`.
     */
    firstValue(): FirstValue | null;
    /**
     * Provides an {@link IPriceFormatter} for this tool, implementing the `IDataSource` contract.
     *
     * This is usually a no-op formatter as the underlying series' formatter is preferred.
     *
     * @returns A basic {@link IPriceFormatter} implementation.
     */
    formatter(): IPriceFormatter;
    /**
     * Implements the `IDataSource` method to provide a price line color.
     *
     * This is typically not used for line tools and returns an empty string.
     *
     * @param lastBarColor - The color of the last bar in the series (unused).
     * @returns An empty string.
     */
    priceLineColor(lastBarColor: string): string;
    /**
     * OPTIONAL: Indicates if dragging the first anchor point (index 0) of an unbounded tool (e.g., Brush)
     * should be treated as a full tool translation (move) rather than just a point edit.
     *
     * This is used by the {@link InteractionManager} to distinguish the drag behavior of tools like Brush vs. Path.
     *
     * @returns `true` if dragging anchor 0 should translate the whole tool, `false` otherwise.
     */
    anchor0TriggersTranslation(): boolean;
    /**
     * OPTIONAL: Hook for tools that finalize creation on a double-click (e.g., Path tool).
     *
     * This allows the tool to perform specific cleanup (like removing the last "rogue" point added
     * on the final single click before the double-click) before the creation process concludes.
     *
     * @returns The instance of the tool (for method chaining).
     */
    handleDoubleClickFinalization(): BaseLineTool<HorzScaleItem>;
    /**
     * Returns the method a user must employ to signal the end of the tool's creation process.
     *
     * Concrete tools must override this if they don't finalize automatically when `pointsCount` is reached.
     *
     * @returns The required {@link FinalizationMethod} (e.g., `MouseUp`, `DoubleClick`, or `PointCount`).
     */
    getFinalizationMethod(): FinalizationMethod;
    /**
     * Retrieves the complete array of permanent points that should be translated when the tool is moved.
     *
     * This is used by the {@link InteractionManager} to get a stable snapshot of all points
     * for calculating logical translation vectors.
     *
     * @returns An array of permanent {@link LineToolPoint}s.
     */
    getPermanentPointsForTranslation(): LineToolPoint[];
    /**
     * Clears the temporary "ghost" point (`_lastPoint`), ensuring it is no longer rendered.
     *
     * This is called by the {@link InteractionManager} upon finalization of the tool's creation.
     *
     * @returns void
     */
    clearGhostPoint(): void;
    /**
     * Retrieves the pixel width of the chart pane's central drawing area.
     *
     * This width excludes the left and right price axes, giving the usable horizontal space.
     * It is used for calculating the extent of lines that should span the full width.
     *
     * @returns The pixel width of the drawing area.
     */
    getChartDrawingWidth(): number;
    /**
     * Retrieves the pixel height of the chart pane's central drawing area.
     *
     * This height excludes the top and bottom margins as well as the time scale area,
     * giving the usable vertical space within the pane.
     *
     * @returns The pixel height of the drawing area.
     */
    getChartDrawingHeight(): number;
}
