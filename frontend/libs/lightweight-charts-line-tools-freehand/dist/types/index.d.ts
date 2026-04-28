/**
 * Main entry point for the 'lightweight-charts-line-tools-freehand' plugin.
 * This file registers all contained line tools (starting with Brush)
 * with the core line tools plugin.
 */
import { ILineToolsPlugin } from 'lightweight-charts-line-tools-core';
import { LineToolBrush } from './model/LineToolBrush';
import { LineToolHighlighter } from './model/LineToolHighlighter';
/**
 * Registers the Freehand tools (Brush and Highlighter) with the provided Core Plugin instance.
 *
 * @param corePlugin - The instance of the Core Line Tools Plugin.
 * @returns void
 *
 * @example
 * ```ts
 * registerFreehandPlugin(corePlugin);
 * ```
 */
export declare function registerFreehandPlugin<HorzScaleItem>(corePlugin: ILineToolsPlugin & {
    registerLineTool: <H>(type: string, toolClass: new (...args: any[]) => any) => void;
}): void;
export { LineToolBrush };
export { LineToolHighlighter };
export default registerFreehandPlugin;
