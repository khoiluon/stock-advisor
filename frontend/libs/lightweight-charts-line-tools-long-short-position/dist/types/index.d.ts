/**
 * This is the main entry point for the 'lightweight-charts-line-tools-long-short-position' plugin.
 * It exports the LineToolLongShortPosition class for registration with the core line tools plugin.
 */
import { ILineToolsPlugin } from 'lightweight-charts-line-tools-core';
import { LineToolLongShortPosition } from './model/LineToolLongShortPosition';
/**
 * Registers the Long/Short Position tool with the provided Core Plugin instance.
 *
 * @param corePlugin - The instance of the Core Line Tools Plugin.
 * @returns void
 *
 * @example
 * ```ts
 * registerLongShortPositionPlugin(corePlugin);
 * ```
 */
export declare function registerLongShortPositionPlugin<HorzScaleItem>(corePlugin: ILineToolsPlugin & {
    registerLineTool: <H>(type: string, toolClass: new (...args: any[]) => any) => void;
}): void;
export { LineToolLongShortPosition };
export default registerLongShortPositionPlugin;
