/**
 * Main entry point for the 'lightweight-charts-line-tool-lines' plugin.
 * This file registers all contained line tools (starting with TrendLine)
 * with the core line tools plugin.
 */
import { ILineToolsPlugin } from 'lightweight-charts-line-tools-core';
import { LineToolTrendLine } from './model/LineToolTrendLine';
import { LineToolExtendedLine } from './model/LineToolExtendedLine';
import { LineToolArrow } from './model/LineToolArrow';
import { LineToolRay } from './model/LineToolRay';
import { LineToolHorizontalLine } from './model/LineToolHorizontalLine';
import { LineToolHorizontalRay } from './model/LineToolHorizontalRay';
import { LineToolVerticalLine } from './model/LineToolVerticalLine';
import { LineToolCrossLine } from './model/LineToolCrossLine';
import { LineToolCallout } from './model/LineToolCallout';
/**
 * Registers all standard line tools (Trend Line, Ray, Arrow, Extended Line, Horizontal Line,
 * Horizontal Ray, Vertical Line, Cross Line, and Callout) with the provided Core Plugin instance.
 *
 * This is the primary entry point for enabling the standard suite of drawing tools.
 *
 * @param corePlugin - The instance of the Core Line Tools Plugin (created via `createLineToolsPlugin`).
 * @returns void
 *
 * @example
 * ```ts
 * import { createLineToolsPlugin } from 'lightweight-charts-line-tools-core';
 * import { registerLinesPlugin } from 'lightweight-charts-line-tools-lines';
 *
 * const corePlugin = createLineToolsPlugin(chart, series);
 * registerLinesPlugin(corePlugin);
 * ```
 */
export declare function registerLinesPlugin<HorzScaleItem>(corePlugin: ILineToolsPlugin & {
    registerLineTool: <H>(type: string, toolClass: new (...args: any[]) => any) => void;
}): void;
export { LineToolTrendLine, LineToolExtendedLine, LineToolArrow, LineToolRay, LineToolHorizontalLine, LineToolHorizontalRay, LineToolVerticalLine, LineToolCrossLine, LineToolCallout, };
export default registerLinesPlugin;
