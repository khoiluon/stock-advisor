/**
 * This is the main entry point for the Lightweight Charts Line Tools Core plugin.
 * It provides the factory function to initialize the plugin and exports all necessary
 * public-facing types and interfaces for consumption by an application.
 */
import { IChartApiBase, ISeriesApi, SeriesType } from 'lightweight-charts';
import { BaseLineTool } from './model/base-line-tool';
import { ILineToolsApi } from './api/public-api';
import { LineToolType } from './types';
/**
 * The main interface for the Line Tools Plugin instance.
 *
 * This interface combines the standard runtime API methods (defined in {@link ILineToolsApi})
 * with the setup methods required to register specific tool types. This is the object
 * returned by {@link createLineToolsPlugin}.
 */
export interface ILineToolsPlugin extends ILineToolsApi {
    /**
     * Registers a custom line tool class constructor with the plugin.
     *
     * You must register a tool class before you can create instances of it using {@link addLineTool}
     * or {@link importLineTools}. This mechanism allows the plugin to remain lightweight by only
     * including the logic for the tools you actually use.
     *
     * @typeParam HorzScaleItem - The type of the horizontal scale (e.g., Time or number).
     * @param type - The unique string identifier for the tool (e.g., 'Rectangle', 'TrendLine').
     * @param toolClass - The class constructor for the tool, which must extend {@link BaseLineTool}.
     * @returns void
     *
     * @example
     * ```ts
     * import { LineToolRectangle } from './tools/line-tool-rectangle';
     *
     * // Register the tool
     * lineToolsPlugin.registerLineTool('Rectangle', LineToolRectangle);
     *
     * // Now you can use it
     * lineToolsPlugin.addLineTool('Rectangle');
     * ```
     */
    registerLineTool<HorzScaleItem>(type: LineToolType, toolClass: new (...args: any[]) => BaseLineTool<HorzScaleItem>): void;
}
/**
 * The main factory function to create and initialize the Line Tools Core Plugin.
 *
 * This function validates the provided chart and series, initializes the core logic,
 * and returns the API interface needed to interact with the plugin.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale (e.g., `Time`, `UTCTimestamp`, or `number`).
 * @param chart - The Lightweight Charts chart instance (must be created via `createChart`).
 * @param series - The specific series instance to which the drawing tools will be attached.
 * @returns An {@link ILineToolsPlugin} instance providing the API for tool management.
 *
 * @remarks
 * If the chart or series is invalid, this function will log an error and return a "dummy"
 * no-op API to prevent your application from crashing.
 *
 * @example
 * ```ts
 * const chart = createChart(document.body, { ... });
 * const series = chart.addCandlestickSeries();
 *
 * const lineTools = createLineToolsPlugin(chart, series);
 * ```
 */
export declare function createLineToolsPlugin<HorzScaleItem>(chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>): ILineToolsPlugin;
export * from './api/public-api';
export * from './types';
export * from './utils/helpers';
export * from './utils/geometry';
export * from './utils/canvas-helpers';
export * from './utils/text-helpers';
export * from './utils/culling-helpers';
export { BaseLineTool } from './model/base-line-tool';
export { AnchorPoint, LineAnchorRenderer, LineAnchorRendererData } from './rendering/line-anchor-renderer';
export { SegmentRenderer, SegmentRendererData, PolygonRenderer, PolygonRendererData, RectangleRenderer, RectangleRendererData, TextRenderer, CircleRenderer, CircleRendererData, BoxSize, LinesInfo, FontInfo, InternalData, } from './rendering/generic-renderers';
export { CompositeRenderer } from './rendering/composite-renderer';
export { LineToolPaneView } from './views/line-tool-pane-view';
export { DataSource } from './model/data-source';
export { PriceDataSource } from './model/price-data-source';
export { PriceAxisLabelStackingManager } from './model/price-axis-label-stacking-manager';
export { LineToolsCorePlugin } from './core-plugin';
export { InteractionManager } from './interaction/interaction-manager';
export { ToolRegistry } from './model/tool-registry';
