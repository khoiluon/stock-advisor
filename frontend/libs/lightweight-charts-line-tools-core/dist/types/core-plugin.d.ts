import { IChartApiBase, ISeriesApi, SeriesType, IHorzScaleBehavior } from 'lightweight-charts';
import { ILineToolsApi, LineToolExport, LineToolPoint, LineToolsAfterEditEventHandler, LineToolsDoubleClickEventHandler, LineToolsSelectEventHandler } from './api/public-api';
import { LineToolPartialOptionsMap, LineToolType } from './types';
import { BaseLineTool } from './model/base-line-tool';
import { PriceAxisLabelStackingManager } from './model/price-axis-label-stacking-manager';
/**
 * The main implementation of the Line Tools Core Plugin.
 *
 * This class acts as the central controller for adding, managing, and interacting with line tools
 * on a Lightweight Chart. It coordinates between the chart's API, the series, and the internal
 * interaction manager to handle user input, rendering, and state management of drawing tools.
 *
 * While typically initialized via the `createLineToolsPlugin` factory, this class implements
 * the {@link ILineToolsApi} interface which defines the primary methods available to consumers.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item (e.g., `Time`, `UTCTimestamp`, or `number`), matching the chart's configuration.
 */
export declare class LineToolsCorePlugin<HorzScaleItem> implements ILineToolsApi {
    private readonly _chart;
    private readonly _series;
    private readonly _horzScaleBehavior;
    private _tools;
    private readonly _toolRegistry;
    private readonly _interactionManager;
    private readonly _priceAxisLabelStackingManager;
    private readonly _doubleClickDelegate;
    private readonly _afterEditDelegate;
    private readonly _selectDelegate;
    private _stackingUpdateScheduled;
    constructor(chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>, horzScaleBehavior: IHorzScaleBehavior<HorzScaleItem>);
    /**
     * Requests a redraw of the chart.
     *
     * This method is the primary mechanism for internal components (like the {@link InteractionManager} or individual tools)
     * to trigger a render cycle after state changes (e.g., hovering, selecting, or modifying a tool).
     * It effectively calls `chart.applyOptions({})` to signal that the primitives need repainting.
     *
     * @internal
     * @returns void
     */
    requestUpdate(): void;
    /**
     * Registers a custom line tool class with the plugin.
     *
     * Before a specific tool type (e.g., 'Rectangle', 'FibRetracement') can be created via
     * {@link addLineTool} or {@link importLineTools}, its class constructor must be registered here.
     * This maps a string identifier to the actual class implementation.
     *
     * @param type - The unique string identifier for the tool type (e.g., 'Rectangle').
     * @param toolClass - The class constructor for the tool, which must extend {@link BaseLineTool}.
     * @returns void
     *
     * @example
     * import { LineToolRectangle } from './my-tools/rectangle';
     * plugin.registerLineTool('Rectangle', LineToolRectangle);
     */
    registerLineTool(type: LineToolType, toolClass: new (...args: any[]) => BaseLineTool<HorzScaleItem>): void;
    /**
     * Adds a new line tool to the chart.
     *
     * If `points` is provided, the tool is drawn immediately at those coordinates.
     * If `points` is an empty array, `null`, or undefined, the plugin enters
     * **interactive creation mode**, allowing the user to click on the chart to draw the tool.
     *
     * @param type - The type of line tool to create (e.g., 'TrendLine', 'Rectangle').
     * @param points - An array of logical points (timestamp/price) to define the tool. Pass `[]` to start interactive drawing.
     * @param options - Optional configuration object to customize the tool's appearance (line color, width, etc.).
     * @returns The unique string ID of the newly created tool.
     *
     * @example
     * // Start drawing a Trend Line interactively (user clicks to place points)
     * plugin.addLineTool('TrendLine');
     *
     * @example
     * // Programmatically add a Rectangle at specific coordinates
     * plugin.addLineTool('Rectangle', [
     *   { timestamp: 1620000000, price: 100 },
     *   { timestamp: 1620086400, price: 120 }
     * ], {
     *   line: { color: '#ff0000', width: 2 },
     *   background: { color: 'rgba(255, 0, 0, 0.2)' }
     * });
     */
    addLineTool<T extends LineToolType>(type: T, points?: LineToolPoint[] | null, options?: LineToolPartialOptionsMap[T] | undefined): string;
    /**
     * Creates a new line tool with a specific ID, or updates it if that ID already exists.
     *
     * Unlike `addLineTool`, this method requires a specific ID. It is primarily used for
     * state synchronization (e.g., `importLineTools`) where preserving the original tool ID is critical.
     *
     * @param type - The type of the line tool.
     * @param points - The points defining the tool.
     * @param options - The configuration options.
     * @param id - The unique ID to assign to the tool (or the ID of the tool to update).
     * @returns void
     */
    createOrUpdateLineTool<T extends LineToolType>(type: T, points: LineToolPoint[], options: LineToolPartialOptionsMap[T], id: string): void;
    /**
     * Removes one or more line tools from the chart based on their unique IDs.
     *
     * @param ids - An array of unique string IDs representing the tools to remove.
     * @returns void
     *
     * @example
     * plugin.removeLineToolsById(['tool-id-1', 'tool-id-2']);
     */
    removeLineToolsById(ids: string[]): void;
    /**
     * Removes all line tools whose IDs match the provided Regular Expression.
     *
     * This allows for bulk deletion of tools based on naming patterns (e.g., removing all tools tagged with 'temp-').
     *
     * @param regex - The Regular Expression to match against tool IDs.
     * @returns void
     *
     * @example
     * // Remove all tools starting with "drawing-"
     * plugin.removeLineToolsByIdRegex(/^drawing-/);
     */
    removeLineToolsByIdRegex(regex: RegExp): void;
    /**
     * Removes the currently selected line tool(s) from the chart.
     *
     * This is typically wired to a keyboard shortcut (like the Delete key) or a UI button
     * to allow users to delete the specific tool they are interacting with.
     *
     * @returns void
     */
    removeSelectedLineTools(): void;
    /**
     * Removes all line tools managed by this plugin from the chart.
     *
     * This performs a full cleanup, detaching every tool from the chart's series and
     * releasing associated resources.
     *
     * @returns void
     */
    removeAllLineTools(): void;
    /**
     * Retrieves the data for all line tools that are currently selected by the user.
     *
     * @returns A JSON string representing an array of the selected tools' data.
     *
     * @example
     * const selected = JSON.parse(plugin.getSelectedLineTools());
     * console.log(`User has selected ${selected.length} tools.`);
     */
    getSelectedLineTools(): string;
    /**
     * Retrieves the data for a specific line tool by its unique ID.
     *
     * @param id - The unique identifier of the tool to retrieve.
     * @returns A JSON string representing an array containing the single tool's data, or an empty array `[]` if the ID was not found.
     *
     * @remarks
     * The return type is a JSON string to maintain compatibility with the V3.8 API structure.
     * You will typically need to `JSON.parse()` the result to work with the data programmatically.
     */
    getLineToolByID(id: string): string;
    /**
     * Retrieves a list of line tools whose IDs match a specific Regular Expression.
     *
     * This is useful for grouping tools by naming convention (e.g., fetching all tools with IDs starting with 'trend-').
     *
     * @param regex - The Regular Expression to match against tool IDs.
     * @returns A JSON string representing an array of all matching line tools.
     *
     * @example
     * // Get all tools with IDs starting with "fib-"
     * const tools = plugin.getLineToolsByIdRegex(/^fib-/);
     */
    getLineToolsByIdRegex(regex: RegExp): string;
    /**
     * Applies new configuration options or points to an existing line tool.
     *
     * This method is used to dynamically update a tool's appearance or position after it
     * has been created. It performs a partial merge, so you only need to provide the properties
     * you wish to change.
     *
     * Note: If the tool is currently selected, it will be deselected upon update to ensure visual consistency.
     *
     * @param toolData - An object containing the tool's `id`, `toolType`, and the `options` or `points` to update.
     * @returns `true` if the tool was found and updated, `false` otherwise (e.g., ID not found or type mismatch).
     *
     * @example
     * // Change the color of an existing tool to blue
     * plugin.applyLineToolOptions({
     *   id: 'existing-tool-id',
     *   toolType: 'TrendLine',
     *   options: {
     *     line: { color: 'blue' }
     *   },
     *   points: [] // Points can be omitted if not changing
     * });
     */
    applyLineToolOptions<T extends LineToolType>(toolData: LineToolExport<T>): boolean;
    /**
     * Serializes the state of all currently drawn line tools into a JSON string.
     *
     * This export format is compatible with `importLineTools` and the V3.8 line tools plugin,
     * making it suitable for saving chart state to a database or local storage.
     *
     * @returns A JSON string representing an array of all line tools and their current state.
     *
     * @example
     * const savedState = plugin.exportLineTools();
     * localStorage.setItem('my-chart-tools', savedState);
     */
    exportLineTools(): string;
    /**
     * Imports a set of line tools from a JSON string.
     *
     * This method parses the provided JSON (typically generated by {@link exportLineTools}) and
     * creates or updates the tools on the chart.
     *
     * **Note:** This is a non-destructive import. It will not remove existing tools unless
     * the imported data overwrites them by ID. It creates new tools if the IDs do not exist
     * and updates existing ones if they do.
     *
     * @param json - A JSON string containing an array of line tool export data.
     * @returns `true` if the import process completed successfully, `false` if the JSON was invalid.
     */
    importLineTools(json: string): boolean;
    /**
     * Subscribes a callback function to the "Double Click" event.
     *
     * This event fires whenever a user double-clicks on an existing line tool.
     * It is often used to open custom settings modals or perform specific actions on the tool.
     *
     * @param handler - The function to execute when the event fires. Receives {@link LineToolsDoubleClickEventParams}.
     * @returns void
     */
    subscribeLineToolsDoubleClick(handler: LineToolsDoubleClickEventHandler): void;
    /**
     * Unsubscribes a previously registered callback from the "Double Click" event.
     *
     * @param handler - The specific callback function that was passed to {@link subscribeLineToolsDoubleClick}.
     * @returns void
     */
    unsubscribeLineToolsDoubleClick(handler: LineToolsDoubleClickEventHandler): void;
    /**
     * Subscribes a callback function to the "After Edit" event.
     *
     * This event fires whenever a line tool is:
     * 1. Modified (points moved or properties changed).
     * 2. Finished creating (the final point was placed).
     *
     * @param handler - The function to execute when the event fires. Receives {@link LineToolsAfterEditEventParams}.
     * @returns void
     *
     * @example
     * plugin.subscribeLineToolsAfterEdit((params) => {
     *   console.log('Tool edited:', params.selectedLineTool.id);
     *   console.log('Edit stage:', params.stage);
     * });
     */
    subscribeLineToolsAfterEdit(handler: LineToolsAfterEditEventHandler): void;
    /**
     * Unsubscribes a previously registered callback from the "After Edit" event.
     *
     * Use this to stop listening for tool creation or modification events, typically during
     * component cleanup or when the chart is being destroyed.
     *
     * @param handler - The specific callback function that was passed to {@link subscribeLineToolsAfterEdit}.
     * @returns void
     */
    unsubscribeLineToolsAfterEdit(handler: LineToolsAfterEditEventHandler): void;
    /**
     * Subscribes a callback function to the "Select" event.
     *
     * This event fires whenever a line tool is selected or deselected.
     *
     * @param handler - The function to execute when the event fires. Receives {@link LineToolsSelectEventParams}.
     * @returns void
     */
    subscribeLineToolsSelect(handler: LineToolsSelectEventHandler): void;
    /**
     * Unsubscribes a previously registered callback from the "Select" event.
     *
     * @param handler - The specific callback function that was passed to {@link subscribeLineToolsSelect}.
     * @returns void
     */
    unsubscribeLineToolsSelect(handler: LineToolsSelectEventHandler): void;
    /**
     * Sets the crosshair position to a specific pixel coordinate (x, y) on the chart.
     *
     * This method acts as a high-level proxy for the Lightweight Charts API. It converts the
     * provided screen pixel coordinates into the logical time and price values required by the chart
     * to position the crosshair.
     *
     * @param x - The x-coordinate (in pixels) relative to the chart's canvas.
     * @param y - The y-coordinate (in pixels) relative to the chart's canvas.
     * @param visible - Controls the visibility of the crosshair. If `false`, the crosshair is cleared.
     * @returns void
     */
    setCrossHairXY(x: number, y: number, visible: boolean): void;
    /**
     * Clears the chart's crosshair, making it invisible.
     *
     * This acts as a proxy for the underlying Lightweight Charts API `clearCrosshairPosition()`.
     * Use this to programmatically hide the crosshair (e.g., when the mouse leaves a custom container).
     *
     * @returns void
     */
    clearCrossHair(): void;
    /**
     * Broadcasts an event indicating that a line tool has been double-clicked.
     *
     * This method is called internally by the {@link InteractionManager} upon detecting a double-click
     * interaction on a tool. It triggers listeners subscribed via {@link subscribeLineToolsDoubleClick}.
     *
     * @internal
     * @param tool - The tool instance that was double-clicked.
     * @returns void
     */
    fireDoubleClickEvent(tool: BaseLineTool<HorzScaleItem>): void;
    /**
     * Broadcasts an event indicating that a line tool has been selected or deselected.
     *
     * This method is called internally by the {@link InteractionManager} when selection state changes.
     *
     * @internal
     * @param tool - The tool instance that was selected, or null if tools were deselected.
     * @returns void
     */
    fireSelectEvent(tool: BaseLineTool<HorzScaleItem> | null): void;
    /**
     * Broadcasts an event indicating that a line tool has been modified or created.
     *
     * This method is primarily called internally by the {@link InteractionManager} when a user
     * finishes drawing or editing a tool. It triggers any listeners subscribed via
     * {@link subscribeLineToolsAfterEdit}.
     *
     * @internal
     * @param tool - The tool instance that was edited.
     * @param stage - The stage of the edit action (e.g., 'lineToolEdited' for modification, 'lineToolFinished' for creation).
     * @returns void
     */
    fireAfterEditEvent(tool: BaseLineTool<HorzScaleItem>, stage: 'lineToolEdited' | 'pathFinished' | 'lineToolFinished'): void;
    /**
     * Internal factory method to instantiate and register a new tool.
     *
     * This handles the common logic for `addLineTool`, `createOrUpdateLineTool`, and `importLineTools`,
     * including checking the registry, creating the instance, attaching it to the series, and
     * managing interactive state if required.
     *
     * @param type - The tool type identifier.
     * @param points - The initial points for the tool.
     * @param options - Optional configuration options.
     * @param id - Optional specific ID (if not provided, the tool generates its own).
     * @param initiateInteractive - If `true`, sets the tool to "Creating" mode and updates the InteractionManager.
     * @returns The newly created `BaseLineTool` instance.
     * @throws Error if the tool type is not registered.
     * @private
     */
    private _createAndAddTool;
    /**
     * Retrieves the instance of the Price Axis Label Stacking Manager.
     *
     * This manager is responsible for preventing overlap between the price labels of different tools
     * on the Y-axis. This accessor is primarily used internally by {@link BaseLineTool} to register its labels.
     *
     * @internal
     * @returns The shared {@link PriceAxisLabelStackingManager} instance.
     */
    getPriceAxisLabelStackingManager(): PriceAxisLabelStackingManager<HorzScaleItem>;
}
