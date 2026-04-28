import { TextWidthCache as ITextWidthCache } from '../types';
/**
 * A subset of the `CanvasRenderingContext2D` interface required for text measurement.
 *
 * This type definition allows the cache to work with any object that provides
 * basic text measurement capabilities, facilitating testing or mocking.
 */
export type CanvasCtxLike = Pick<CanvasRenderingContext2D, 'measureText' | 'save' | 'restore' | 'textBaseline'>;
/**
 * A Least Recently Used (LRU) cache for text width measurements.
 *
 * Measuring text on an HTML5 Canvas is an expensive operation. This class caches the
 * results of `measureText` calls to significantly improve rendering performance, especially
 * for axis labels and crosshair values that change frequently but repeat values.
 */
export declare class TextWidthCache implements ITextWidthCache {
    private readonly _maxSize;
    private _actualSize;
    private _usageTick;
    private _oldestTick;
    private _tick2Labels;
    private _cache;
    /**
     * Initializes the cache with a specific capacity.
     *
     * @param size - The maximum number of text metrics to store before evicting the oldest entries. Default is 50.
     */
    constructor(size?: number);
    /**
     * Clears all cached entries and resets the usage tracking.
     *
     * This should be called when font settings change (e.g., font size or family updates),
     * as previous measurements would be invalid.
     */
    reset(): void;
    /**
     * Measures the width of the provided text, using the cache if available.
     *
     * If the text (after optimization replacement) is in the cache, the stored width is returned.
     * Otherwise, the text is measured using the provided context, stored in the cache, and returned.
     *
     * @param ctx - The canvas context to use for measurement if the cache misses.
     * @param text - The text string to measure.
     * @param optimizationReplacementRe - Optional regex to normalize the text (e.g., replacing digits with '0') to increase cache hits.
     * @returns The width of the text in pixels.
     */
    measureText(ctx: CanvasCtxLike, text: string, optimizationReplacementRe?: RegExp): number;
    /**
     * Calculates the vertical offset required to center text accurately.
     *
     * Canvas `textBaseline = 'middle'` often results in slight visual misalignment depending on the font.
     * This method uses `actualBoundingBoxAscent` and `actualBoundingBoxDescent` (if supported)
     * to calculate a pixel-perfect vertical correction.
     *
     * @param ctx - The canvas context.
     * @param text - The text string to measure.
     * @param optimizationReplacementRe - Optional optimization regex.
     * @returns The y-axis offset in pixels.
     */
    yMidCorrection(ctx: CanvasCtxLike, text: string, optimizationReplacementRe?: RegExp): number;
    /**
     * Internal method to retrieve or compute `TextMetrics` for a string.
     *
     * Handles the core LRU logic:
     * 1. Applies the optimization regex to the input text key.
     * 2. Checks the cache. If found, updates the usage tick and returns.
     * 3. If missing, evicts the oldest entry if the cache is full.
     * 4. Measures the text and stores the result.
     *
     * @param ctx - The canvas context.
     * @param text - The text to measure.
     * @param optimizationReplacementRe - Regex for digit normalization.
     * @returns The standard `TextMetrics` object.
     * @private
     */
    private _getMetrics;
}
