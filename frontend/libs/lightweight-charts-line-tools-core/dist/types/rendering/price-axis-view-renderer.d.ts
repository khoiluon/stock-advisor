import { IPriceAxisViewRenderer, PriceAxisViewRendererCommonData, PriceAxisViewRendererData, PriceAxisViewRendererOptions, TextWidthCache, CanvasRenderingTarget2D } from '../types';
/**
 * The concrete implementation of a renderer responsible for drawing labels on the Price Axis.
 *
 * This class handles the pixel-level details of drawing the label's background box, border, text,
 * and tick mark according to the provided data and options, correctly accounting for LWC's rendering context.
 */
export declare class PriceAxisViewRenderer implements IPriceAxisViewRenderer {
    private _data;
    private _commonData;
    /**
     * Initializes the renderer with the initial data payloads.
     *
     * @param data - The {@link PriceAxisViewRendererData} containing the text and visibility flags.
     * @param commonData - The {@link PriceAxisViewRendererCommonData} containing coordinate and base style information.
     */
    constructor(data: PriceAxisViewRendererData, commonData: PriceAxisViewRendererCommonData);
    /**
     * Updates the data used by the renderer.
     *
     * @param data - The new {@link PriceAxisViewRendererData}.
     * @param commonData - The new {@link PriceAxisViewRendererCommonData}.
     * @returns void
     */
    setData(data: PriceAxisViewRendererData, commonData: PriceAxisViewRendererCommonData): void;
    /**
     * Draws the price axis label onto the canvas.
     *
     * This method calculates the final layout, applies pixel snapping, draws the background/border/tick mark,
     * and renders the text based on the provided alignment ('left'/'right').
     *
     * @param target - The {@link CanvasRenderingTarget2D} provided by Lightweight Charts.
     * @param rendererOptions - The {@link PriceAxisViewRendererOptions} for styling and dimensions.
     * @param textWidthCache - The {@link TextWidthCache} for accurate text measurement.
     * @param width - The total width of the Price Axis area in pixels.
     * @param align - The horizontal alignment of the axis ('left' for right scale, 'right' for left scale).
     * @returns void
     */
    draw(target: CanvasRenderingTarget2D, // Now directly accepting CanvasRenderingTarget2D
    rendererOptions: PriceAxisViewRendererOptions, textWidthCache: TextWidthCache, width: number, align: 'left' | 'right'): void;
    /**
     * Calculates the total pixel height required to draw the label.
     *
     * This height includes font size and vertical padding defined in the options.
     *
     * @param rendererOptions - The {@link PriceAxisViewRendererOptions} for dimensions.
     * @param useSecondLine - Flag to calculate height for a second line of text (not typically used for price labels).
     * @returns The calculated height in pixels, or 0 if the label is invisible.
     */
    height(rendererOptions: PriceAxisViewRendererOptions, useSecondLine: boolean): number;
}
