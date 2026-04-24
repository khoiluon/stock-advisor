import { TextRendererData } from '../types';
/**
 * Internal constant defining a hard-coded minimum padding in pixels.
 *
 * This ensures that text does not bleed into the border or background edges,
 * providing a baseline "breathing room" regardless of user configuration.
 */
export declare const MINIMUM_PADDING_PIXELS = 5;
/**
 * A shared, off-screen canvas context used strictly for text measurement operations.
 *
 * This prevents the overhead of creating a new canvas element every time text needs
 * to be measured or wrapped. It is initialized lazily via {@link createCacheCanvas}.
 */
export declare let cacheCanvas: CanvasRenderingContext2D | null;
/**
 * Lazily initializes the shared {@link cacheCanvas} if it does not already exist.
 *
 * It creates a 0x0 pixel canvas element (to minimize memory footprint) and retrieves
 * its 2D context. This function should be called before any operation requiring
 * `measureText`.
 */
export declare function createCacheCanvas(): void;
/**
 * Calculates the total width of the text box container.
 *
 * The width includes the widest line of text, plus scaled horizontal padding and
 * background inflation.
 *
 * @param data - The text renderer data containing box styling options.
 * @param maxLineWidth - The pixel width of the longest line of text.
 * @returns The total calculated width in pixels.
 */
export declare function getBoxWidth(data: TextRendererData, maxLineWidth: number): number;
/**
 * Calculates the total height of the text box container.
 *
 * The height accounts for the number of lines, font size, line spacing (padding between lines),
 * vertical box padding, and background inflation.
 *
 * @param data - The text renderer data containing box styling options.
 * @param linesCount - The number of text lines to render.
 * @returns The total calculated height in pixels.
 */
export declare function getBoxHeight(data: TextRendererData, linesCount: number): number;
/**
 * Calculates the effective vertical padding for the text box.
 *
 * This combines the user-defined `text.box.padding.y` with the internal {@link MINIMUM_PADDING_PIXELS},
 * scaling the result based on the font-aware scale factor.
 *
 * @param data - The text renderer data.
 * @returns The final vertical padding in pixels.
 */
export declare function getScaledBoxPaddingY(data: TextRendererData): number;
/**
 * Calculates the effective horizontal padding for the text box.
 *
 * This combines the user-defined `text.box.padding.x` with the internal {@link MINIMUM_PADDING_PIXELS},
 * scaling the result based on the font-aware scale factor.
 *
 * @param data - The text renderer data.
 * @returns The final horizontal padding in pixels.
 */
export declare function getScaledBoxPaddingX(data: TextRendererData): number;
/**
 * Calculates the vertical inflation (expansion) of the background rectangle.
 *
 * Inflation allows the background color to extend beyond the logical bounds of the text box
 * without affecting layout positioning.
 *
 * @param data - The text renderer data.
 * @returns The scaled vertical inflation in pixels.
 */
export declare function getScaledBackgroundInflationY(data: TextRendererData): number;
/**
 * Calculates the horizontal inflation (expansion) of the background rectangle.
 *
 * @param data - The text renderer data.
 * @returns The scaled horizontal inflation in pixels.
 */
export declare function getScaledBackgroundInflationX(data: TextRendererData): number;
/**
 * Calculates the scaled padding value used for line spacing.
 *
 * This value determines the gap between multiple lines of text.
 *
 * @param data - The text renderer data.
 * @returns The scaled padding in pixels.
 */
export declare function getScaledPadding(data: TextRendererData): number;
/**
 * Calculates the final font size in pixels to use for rendering.
 *
 * This takes the base font size and multiplies it by the calculated font-aware scale factor.
 *
 * @param data - The text renderer data.
 * @returns The scaled font size, rounded up to the nearest integer.
 */
export declare function getScaledFontSize(data: TextRendererData): number;
/**
 * Retrieves the base font size from the renderer options.
 *
 * If no font size is specified in `data.text.font.size`, it defaults to 30 pixels.
 *
 * @param data - The text renderer data.
 * @returns The base font size in pixels.
 */
export declare function getFontSize(data: TextRendererData): number;
/**
 * Calculates a normalization scale factor.
 *
 * This combines the user-defined `text.box.scale` with an adjustment based on the font size
 * to ensure consistent rendering across different resolutions or zoom levels.
 * It enforces a minimum scale of 0.01 to prevent mathematical errors.
 *
 * @param data - The text renderer data.
 * @returns The effective scale factor.
 */
export declare function getFontAwareScale(data: TextRendererData): number;
/**
 * Detects if the current document is in Right-to-Left (RTL) mode.
 *
 * It checks `window.document.dir` for the value `'rtl'`. This is used to adjust
 * text alignment defaults (e.g., aligning text to the right by default in RTL contexts).
 *
 * @returns `true` if the document direction is RTL, `false` otherwise.
 */
export declare function isRtl(): boolean;
/**
 * Performs sophisticated word wrapping on a string based on a maximum pixel width.
 *
 * This function:
 * 1. Respects existing newlines (`\n`).
 * 2. Measures text using an off-screen canvas.
 * 3. Wraps lines that exceed `lineWrapWidth`.
 * 4. Breaks individual words if they are wider than the wrap width.
 *
 * @param text - The input text string.
 * @param font - The CSS font string used for measurement.
 * @param lineWrapWidth - The maximum width in pixels for a single line.
 * @returns An array of strings, where each element is a single visual line.
 */
export declare function textWrap(text: string, font: string, lineWrapWidth: number | string | undefined): string[];
/**
 * Checks if a CSS color string represents a completely transparent color.
 *
 * It detects:
 * - The keyword `'transparent'`.
 * - `rgba(...)` strings where alpha is 0.
 * - `hsla(...)` strings where alpha is 0.
 *
 * @param color - The CSS color string to test.
 * @returns `true` if the color is fully transparent, `false` if opaque or translucent.
 */
export declare function isFullyTransparent(color: string): boolean;
