import { IChartApiBase, ISeriesApi, SeriesType } from 'lightweight-charts';
import { LineToolsCorePlugin } from '../core-plugin';
import { BaseLineTool } from '../model/base-line-tool';
import { ToolRegistry } from '../model/tool-registry';
import { Point } from '../utils/geometry';
import { LineToolPoint } from '../api/public-api';
/**
 * Manages all user interactions with line tools, including creation, selection,
 * editing, and event propagation. It acts as the central router for mouse
 * and touch events.
 */
export declare class InteractionManager<HorzScaleItem> {
    private _plugin;
    private _chart;
    private _series;
    private _tools;
    private _toolRegistry;
    private _horzScaleBehavior;
    private _currentToolCreating;
    private _selectedTool;
    private _hoveredTool;
    private _isEditing;
    private _draggedTool;
    private _draggedPointIndex;
    private _originalDragPoints;
    private _dragStartPoint;
    private _activeDragCursor;
    private _isCreationGesture;
    private _creationTool;
    private _mouseDownPoint;
    private _mouseDownTime;
    private _isDrag;
    private _isShiftKeyDown;
    /**
     * Initializes the Interaction Manager, setting up all internal references and subscribing
     * to necessary DOM and Lightweight Charts events.
     *
     * This class serves as the central event handler, converting low-level mouse and touch
     * events into logical interaction commands for line tools (e.g., drag, select, create).
     *
     * @param plugin - The root {@link LineToolsCorePlugin} instance for internal updates and event firing.
     * @param chart - The Lightweight Charts chart API instance.
     * @param series - The primary series API instance.
     * @param tools - The map of all registered line tools.
     * @param toolRegistry - The registry for looking up tool constructors.
     */
    constructor(plugin: LineToolsCorePlugin<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, tools: Map<string, BaseLineTool<HorzScaleItem>>, toolRegistry: ToolRegistry<HorzScaleItem>);
    /**
     * Converts raw screen coordinates (in pixels) to a logical {@link LineToolPoint} (timestamp/price).
     *
     * This conversion is robust, handling interpolation to return a time and price value
     * even if the screen point is over an area of the chart without a data bar (blank logical space).
     *
     * @param screenPoint - The screen coordinates as a {@link Point} object.
     * @returns A {@link LineToolPoint} containing a timestamp and price, or `null` if the conversion fails.
     *
     * @example
     * // Used by LineToolsCorePlugin to position the crosshair
     * const logicalPoint = manager.screenPointToLineToolPoint(new Point(x, y));
     */
    screenPointToLineToolPoint(screenPoint: Point): LineToolPoint | null;
    /**
     * Sets the specific tool instance that is currently being drawn interactively by the user.
     *
     * This is called by the {@link LineToolsCorePlugin.addLineTool} method when initiating an
     * interactive creation gesture. This tool instance becomes the target for subsequent mouse clicks.
     *
     * @param tool - The {@link BaseLineTool} instance currently in creation mode, or `null` to clear.
     * @internal
     */
    setCurrentToolCreating(tool: BaseLineTool<HorzScaleItem> | null): void;
    /**
     * Attaches a line tool primitive to the main series for rendering.
     *
     * This is an internal helper called by the {@link LineToolsCorePlugin} immediately after a tool is constructed.
     *
     * @param tool - The {@link BaseLineTool} to attach.
     * @private
     */
    private attachTool;
    /**
     * Subscribes to all necessary browser DOM events (`mousedown`, `mousemove`, `mouseup`, `keydown`, `keyup`)
     * and Lightweight Charts API events (`subscribeDblClick`, `subscribeCrosshairMove`) to capture user input.
     *
     * @private
     */
    private _subscribeToChartEvents;
    /**
     * Handles global `keydown` and `keyup` events, specifically tracking the state of the 'Shift' key.
     *
     * The Shift key state is critical for enabling constraint-based drawing (e.g., 45-degree angle locking).
     *
     * @param event - The browser's KeyboardEvent.
     * @private
     */
    private _handleKey;
    /**
     * Detaches a line tool primitive from the chart's rendering pipeline and cleans up all internal references to it.
     *
     * This method is called by the {@link LineToolsCorePlugin} when a tool is removed.
     *
     * @param tool - The {@link BaseLineTool} to detach and clean up.
     * @internal
     */
    detachTool(tool: BaseLineTool<HorzScaleItem>): void;
    /**
     * Finalizes the interactive creation of a tool once its required number of points have been placed.
     *
     * This method performs state cleanup, deselects all other tools, selects the new tool,
     * calls the tool's optional `normalize()` method, and fires the `afterEdit` event.
     *
     * @param tool - The {@link BaseLineTool} that has completed its creation.
     * @private
     */
    private _finalizeToolCreation;
    /**
     * Handles the initial `mousedown` event on the chart canvas.
     *
     * This is the crucial entry point for an interaction gesture, determining if the action is:
     * 1. The start of an interactive tool creation.
     * 2. The start of a drag/edit gesture on an existing tool (dragged anchor or body).
     * 3. An initial click that leads to selection.
     *
     * @param event - The browser's MouseEvent.
     * @private
     */
    private _handleMouseDown;
    /**
     * Handles the `mousemove` event, which primarily manages dragging/editing or ghost-point drawing.
     *
     * This logic handles:
     * 1. Applying drag/edit updates to a selected tool's points, including calculating **Shift-key constraints**.
     * 2. Translating the entire tool if the drag started on the body.
     * 3. Updating the "ghost" point of a tool currently in `Creation` phase.
     * 4. Applying the correct custom cursor style during the drag.
     *
     * @param event - The browser's MouseEvent.
     * @private
     */
    private _handleMouseMove;
    /**
     * Handles the `mouseup` event, finalizing any active interaction (creation or editing).
     *
     * This method is responsible for:
     * 1. Committing the final point in a click-click creation sequence.
     * 2. Finalizing a drag-based creation (e.g., Rectangle, Brush).
     * 3. Finalizing an editing drag (resizing or translation) and resetting the editing state.
     * 4. Handling standalone clicks for selection/deselection.
     *
     * @param event - The browser's MouseEvent.
     * @private
     */
    private _handleMouseUp;
    /**
     * Clears flags related only to a one-time mouse gesture (drag state, mouse position/time).
     *
     * This is used during multi-point creation to reset the interaction flags *without* ending the
     * overall `_currentToolCreating` process.
     *
     * @private
     */
    private _resetCreationGestureStateOnly;
    /**
     * Clears flags and state related to an active tool editing/dragging session.
     *
     * This includes clearing the dragged tool reference, clearing the cursor override, and
     * re-enabling the chart's built-in scroll/pan functionality.
     *
     * @private
     */
    private _resetEditingGestureStateOnly;
    /**
     * Clears the most fundamental mouse gesture state variables: drag flag, mouse down point, and time.
     *
     * @private
     */
    private _resetCommonGestureState;
    /**
     * Performs a complete reset of all interaction state flags, including clearing the tool in creation,
     * deselecting all tools, and requesting a chart update.
     *
     * This is typically used as a fallback for unhandled interactions or external API calls (e.g., context menus).
     *
     * @private
     */
    private _resetInteractionStateFully;
    /**
     * Processes a discrete click that occurred outside of an active creation or editing gesture.
     *
     * This logic handles selection: if a tool was clicked, it becomes selected; otherwise, all tools are deselected.
     *
     * @param point - The screen coordinates of the click event.
     * @private
     */
    private _handleStandaloneClick;
    /**
     * Handles the chart's double-click event broadcast.
     *
     * This method checks for two conditions:
     * 1. **Creation Finalization:** Ends the drawing process for tools that use `FinalizationMethod.DoubleClick` (e.g., Path tool).
     * 2. **Event Firing:** Triggers the public `fireDoubleClickEvent` if an existing tool was hit.
     *
     * @param params - The event parameters provided by Lightweight Charts.
     * @private
     */
    private _handleDblClick;
    /**
     * Handles the chart's crosshair move event, used for hover state and ghost-point drawing.
     *
     * This method:
     * 1. Manages the visual state of the tool currently being created (the "ghosting" point), applying Shift-key constraints.
     * 2. Updates the `_hoveredTool` property and sets its hover state, allowing views to draw hover effects.
     *
     * @param params - The event parameters provided by Lightweight Charts.
     * @private
     */
    private _handleCrosshairMove;
    /**
     * Performs a hit test on all visible line tools, iterating them in reverse Z-order (top-most first).
     *
     * @param point - The screen coordinates to test against all tools.
     * @returns An object containing the hit tool, the hit point index, and the suggested cursor type, or `null` if no tool was hit.
     * @private
     */
    private _hitTest;
    /**
     * Clears the selection state of the currently selected tool, if one exists.
     *
     * This is a public utility often called by the {@link LineToolsCorePlugin} or by the `InteractionManager`'s internal logic.
     *
     * @returns void
     */
    deselectAllTools(): void;
    /**
     * Converts a raw browser `MouseEvent` (which uses screen coordinates) into a chart-relative
     * {@link Point} object (CSS pixels relative to the chart canvas).
     *
     * @param event - The browser's MouseEvent.
     * @returns A chart-relative {@link Point} object, or `null` if the chart element bounding box cannot be retrieved.
     * @private
     */
    private _eventToPoint;
}
