/**
 * This file contains lower-level canvas drawing utilities adapted from the
 * Lightweight Charts V3.8 build's 'renderers' and 'helpers/canvas-helpers'
 * to be reusable components within our plugin.
 */
import { LineStyle } from 'lightweight-charts';
import { Point, Segment } from './geometry';
/**
 * Clears a specific rectangular area on the canvas and fills it immediately with a solid color.
 *
 * This function uses the `copy` global composite operation to replace existing pixels
 * entirely, which is often more performant or predictable than using `clearRect` followed by `fillRect`
 * in layering scenarios.
 *
 * @param ctx - The canvas rendering context to draw on.
 * @param x - The x-coordinate of the top-left corner of the rectangle.
 * @param y - The y-coordinate of the top-left corner of the rectangle.
 * @param w - The width of the rectangle in pixels.
 * @param h - The height of the rectangle in pixels.
 * @param clearColor - The CSS color string to fill the cleared area with (e.g., '#FFFFFF' or 'rgba(0,0,0,0)').
 */
export declare function clearRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, clearColor: string): void;
/**
 * Clears a specific rectangular area on the canvas and fills it with a vertical linear gradient.
 *
 * Similar to {@link clearRect}, this uses the `copy` composite operation. It creates a gradient
 * spanning from the top (`y`) to the bottom (`y + h`) of the specified area.
 *
 * @param ctx - The canvas rendering context to draw on.
 * @param x - The x-coordinate of the top-left corner of the rectangle.
 * @param y - The y-coordinate of the top-left corner of the rectangle.
 * @param w - The width of the rectangle in pixels.
 * @param h - The height of the rectangle in pixels.
 * @param topColor - The CSS color string for the start (top) of the gradient.
 * @param bottomColor - The CSS color string for the end (bottom) of the gradient.
 */
export declare function clearRectWithGradient(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, topColor: string, bottomColor: string): void;
/**
 * Calculates the specific line dash array pattern for a given `LineStyle`.
 *
 * This helper maps abstract style enums (like `LineStyle.Dashed` or `LineStyle.SparseDotted`)
 * into the concrete numerical arrays required by the HTML5 Canvas API's `setLineDash`.
 * The pattern is scaled relative to the current line width of the context to ensure visual consistency.
 *
 * @param ctx - The canvas rendering context (used to retrieve the current `lineWidth`).
 * @param style - The `LineStyle` enum value to convert.
 * @returns An array of numbers representing the dash pattern (segments and gaps), or an empty array for solid lines.
 */
export declare function computeDashPattern(ctx: CanvasRenderingContext2D, style: LineStyle): number[];
/**
 * Applies a specific dash pattern to the canvas rendering context.
 *
 * This low-level wrapper ensures compatibility across different browser implementations,
 * handling standard `setLineDash` as well as legacy vendor-prefixed properties
 * (`mozDash`, `webkitLineDash`) if necessary.
 *
 * @param ctx - The canvas rendering context to configure.
 * @param dashPattern - The array of numbers representing distances to alternately draw a line and a gap.
 */
export declare function setLineDash(ctx: CanvasRenderingContext2D, dashPattern: number[]): void;
/**
 * Configures the canvas context with the dash pattern corresponding to a specific `LineStyle`.
 *
 * This is a high-level utility that combines {@link computeDashPattern} and {@link setLineDash}.
 * It also resets the `lineDashOffset` to 0 to ensure the pattern starts cleanly at the beginning of the path.
 *
 * @param ctx - The canvas rendering context to configure.
 * @param style - The `LineStyle` enum value to apply.
 */
export declare function setLineStyle(ctx: CanvasRenderingContext2D, style: LineStyle): void;
/**
 * Calculates a scaling multiplier for line decorations (such as arrows or circles) based on the line's width.
 *
 * This utility helps maintain visual balance; as lines get thicker, the decoration size multiplier
 * typically decreases to prevent end caps from becoming disproportionately large.
 *
 * @param lineWidth - The width of the line in pixels.
 * @returns A numeric multiplier to be applied to the base decoration size.
 */
export declare function computeEndLineSize(lineWidth: number): number;
/**
 * Draws a pixel-perfect horizontal line on the canvas.
 *
 * This function applies a 0.5-pixel correction offset if the context's line width is odd (e.g., 1px).
 * This "pixel snapping" ensures the line renders sharply on the pixel grid rather than blurring across two pixel rows.
 *
 * @param ctx - The canvas rendering context.
 * @param y - The y-coordinate for the line position.
 * @param left - The starting x-coordinate.
 * @param right - The ending x-coordinate.
 */
export declare function drawHorizontalLine(ctx: CanvasRenderingContext2D, y: number, left: number, right: number): void;
/**
 * Draws a pixel-perfect vertical line on the canvas.
 *
 * Similar to {@link drawHorizontalLine}, this function applies a 0.5-pixel correction offset
 * if the context's line width is odd, ensuring the line renders sharply on the pixel grid.
 *
 * @param ctx - The canvas rendering context.
 * @param x - The x-coordinate for the line position.
 * @param top - The starting y-coordinate.
 * @param bottom - The ending y-coordinate.
 */
export declare function drawVerticalLine(ctx: CanvasRenderingContext2D, x: number, top: number, bottom: number): void;
/**
 * Draws a line segment between two points using the specified `LineStyle`.
 *
 * This is the primary general-purpose line drawing function. It includes safety checks for finite coordinates
 * and automatically delegates to {@link drawDashedLine} or {@link drawSolidLine} based on the style provided.
 *
 * @param ctx - The canvas rendering context.
 * @param x1 - The x-coordinate of the start point.
 * @param y1 - The y-coordinate of the start point.
 * @param x2 - The x-coordinate of the end point.
 * @param y2 - The y-coordinate of the end point.
 * @param style - The `LineStyle` to apply (Solid, Dashed, Dotted, etc.).
 */
export declare function drawLine(ctx: CanvasRenderingContext2D, x1: number, y1: number, x2: number, y2: number, style: LineStyle): void;
/**
 * Draws a standard solid line path between two points.
 *
 * This is a performance-optimized primitive for drawing lines when the style is known to be `LineStyle.Solid`.
 * It assumes the line style/dash has already been handled or cleared by the caller (see {@link setLineStyle}).
 *
 * @param ctx - The canvas rendering context.
 * @param x1 - The x-coordinate of the start point.
 * @param y1 - The y-coordinate of the start point.
 * @param x2 - The x-coordinate of the end point.
 * @param y2 - The y-coordinate of the end point.
 */
export declare function drawSolidLine(ctx: CanvasRenderingContext2D, x1: number, y1: number, x2: number, y2: number): void;
/**
 * Draws a dashed or dotted line segment between two points.
 *
 * This function handles the context state management required for dashed lines.
 * It saves the context, applies the specific `LineStyle` (dash pattern), draws the path,
 * and then restores the context to prevent the dash pattern from leaking into subsequent operations.
 *
 * @param ctx - The canvas rendering context.
 * @param x1 - The x-coordinate of the start point.
 * @param y1 - The y-coordinate of the start point.
 * @param x2 - The x-coordinate of the end point.
 * @param y2 - The y-coordinate of the end point.
 * @param style - The `LineStyle` defining the dash pattern (e.g., Dashed, Dotted).
 */
export declare function drawDashedLine(ctx: CanvasRenderingContext2D, x1: number, y1: number, x2: number, y2: number, style: LineStyle): void;
/**
 * Draws a solid circular decoration at the end of a line.
 *
 * This is typically used for "dot" line endings. The circle's size is automatically scaled
 * relative to the line width using {@link computeEndLineSize}. The circle is filled with
 * the current stroke color of the context.
 *
 * @param point - The center {@link Point} of the circle.
 * @param ctx - The canvas rendering context.
 * @param width - The width of the line this end decoration is attached to (used for scaling).
 */
export declare function drawCircleEnd(point: Point, ctx: CanvasRenderingContext2D, width: number): void;
/**
 * Calculates the geometric line segments required to draw an arrowhead.
 *
 * This function computes the vector geometry for a standard arrow shape pointing from `point0` to `point1`.
 * It scales the arrow size based on the provided line width and ensures the arrow is not drawn
 * if the line segment is too short to support it.
 *
 * @param point0 - The base (tail) point of the direction vector.
 * @param point1 - The tip (head) point of the arrow.
 * @param width - The width of the line (used for scaling the arrow head).
 * @returns An array of {@link Segment}s that form the arrow shape, or an empty array if the line is too short.
 */
export declare function getArrowPoints(point0: Point, point1: Point, width: number): Segment[];
/**
 * Draws an arrow decoration at the end of a line segment.
 *
 * This function utilizes {@link getArrowPoints} to determine the geometry and then renders
 * the arrow using {@link drawLine}. This ensures that the arrow head itself respects the
 * dash style of the parent line (e.g., a dashed line has a dashed arrow head).
 *
 * @param point0 - The base (tail) point of the direction vector.
 * @param point1 - The tip (head) point where the arrow will be drawn.
 * @param ctx - The canvas rendering context.
 * @param width - The width of the line.
 * @param style - The `LineStyle` to apply to the arrow geometry.
 */
export declare function drawArrowEnd(point0: Point, point1: Point, ctx: CanvasRenderingContext2D, width: number, style: LineStyle): void;
/**
 * Draws the outline (stroke) of a rectangle with rounded corners.
 *
 * This function supports flexible corner radius definitions. You can provide a single number for uniform
 * corners, or an array to specify distinct radii for the top-left, top-right, bottom-right, and bottom-left corners.
 *
 * @param ctx - The canvas rendering context.
 * @param x - The x-coordinate of the top-left corner.
 * @param y - The y-coordinate of the top-left corner.
 * @param width - The width of the rectangle.
 * @param height - The height of the rectangle.
 * @param radius - The border radius. Can be a number (all corners) or an array `[TL, TR, BR, BL]`.
 * @param borderStyle - The `LineStyle` to use for the border stroke.
 */
export declare function drawRoundRect(ctx: CanvasRenderingContext2D, x: number, y: number, width: number, height: number, radius: number | number[], borderStyle: LineStyle): void;
/**
 * A comprehensive utility to draw a filled rectangle with an optional border, rounded corners, and infinite horizontal extensions.
 *
 * This function handles complex geometry, including:
 * - Normalizing coordinate bounds (min/max).
 * - Extending the rectangle to the edges of the container (left/right).
 * - Aligning the border stroke (inner, outer, or center) to ensure crisp pixel rendering.
 * - Filling and stroking with distinct colors and styles.
 *
 * @param ctx - The canvas rendering context.
 * @param point0 - The first defining point of the rectangle (any corner).
 * @param point1 - The second defining point of the rectangle (opposite corner).
 * @param backgroundColor - The fill color (optional).
 * @param borderColor - The stroke color (optional).
 * @param borderWidth - The width of the border stroke.
 * @param borderStyle - The `LineStyle` of the border.
 * @param radius - The corner radius (number or array of 4 numbers).
 * @param borderAlign - The alignment of the border relative to the path: `'inner'`, `'outer'`, or `'center'`.
 * @param extendLeft - If `true`, the rectangle extends infinitely to the left (x=0).
 * @param extendRight - If `true`, the rectangle extends infinitely to the right (x=containerWidth).
 * @param containerWidth - The total width of the drawing area (used for extension).
 */
export declare function fillRectWithBorder(ctx: CanvasRenderingContext2D, point0: Point, point1: Point, backgroundColor: string | undefined, borderColor: string | undefined, borderWidth: number | undefined, borderStyle: LineStyle, radius: number | number[], // NEW PARAMETER
borderAlign: 'outer' | 'center' | 'inner', extendLeft: boolean, extendRight: boolean, containerWidth: number): void;
