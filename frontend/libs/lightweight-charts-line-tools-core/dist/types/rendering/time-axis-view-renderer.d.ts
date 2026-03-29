import { ITimeAxisViewRenderer, TimeAxisViewRendererOptions, TimeAxisViewRendererData, CanvasRenderingTarget2D } from '../types';
/**
 * The concrete implementation of a renderer responsible for drawing labels on the Time Axis.
 *
 * This class calculates the layout, performs necessary position adjustments (to prevent labels
 * from drawing outside the time scale boundary), and draws the background, tick mark, and text.
 */
export declare class TimeAxisViewRenderer implements ITimeAxisViewRenderer {
    private _data;
    private _fallbackTextWidthCache;
    /**
     * Initializes the renderer. Data is set later via `setData`.
     */
    constructor();
    /**
     * Updates the data payload required to draw the time axis label.
     *
     * @param data - The {@link TimeAxisViewRendererData} containing the text, coordinate, and style.
     * @returns void
     */
    setData(data: TimeAxisViewRendererData): void;
    /**
     * Draws the time axis label onto the chart's time scale area.
     *
     * This method calculates the label's required width, adjusts its final X-coordinate to ensure
     * it stays within the visible time scale bounds, and then draws the background, tick mark, and text.
     *
     * @param target - The {@link CanvasRenderingTarget2D} provided by Lightweight Charts.
     * @param rendererOptions - The {@link TimeAxisViewRendererOptions} for styling and dimensions.
     * @returns void
     */
    draw(target: CanvasRenderingTarget2D, // LWC v5 Primitive API signature
    rendererOptions: TimeAxisViewRendererOptions): void;
    /**
     * Calculates the total pixel height required to draw the label.
     *
     * This height includes font size, vertical padding, and border size.
     *
     * @param rendererOptions - The {@link TimeAxisViewRendererOptions} for dimensions.
     * @returns The calculated height in pixels.
     */
    height(rendererOptions: TimeAxisViewRendererOptions): number;
    /**
     * Ensures a fallback {@link TextWidthCache} instance exists if one is not provided in `rendererOptions`.
     *
     * @returns The active {@link ITextWidthCache} instance.
     * @private
     */
    private _ensureFallbackTextWidthCache;
}
