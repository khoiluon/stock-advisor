/**
 * This file contains a collection of generic and reusable canvas renderers for
 * common geometric shapes and text, which can be composited to build complex line tools.
 * Each renderer is designed to be fully configurable via its setData() method.
 */
import { Coordinate, LineStyle } from 'lightweight-charts';
import { CanvasRenderingTarget2D, IPaneRenderer, LineToolHitTestData, LineOptions, HitTestResult, PaneCursorType, TextRendererData, TextAlignment } from '../types';
import { Point } from '../utils/geometry';
import { AnchorPoint } from './line-anchor-renderer';
/**
 * Data structure required by the {@link SegmentRenderer}.
 *
 * It defines the geometry of a straight line segment, including its two defining points
 * and the complete set of styling options for drawing the line and its end caps.
 */
export interface SegmentRendererData {
    points: [AnchorPoint, AnchorPoint];
    line: LineOptions;
    toolDefaultHoverCursor?: PaneCursorType;
    toolDefaultDragCursor?: PaneCursorType;
}
/**
 * Renders a single straight line segment between two points.
 *
 * This renderer is highly versatile, supporting infinite extensions (Rays, Extended Lines, Horizontal/Vertical Lines),
 * line dashing/styling, and custom end caps (Arrows, Circles). It implements robust hit testing along the line path.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item.
 */
export declare class SegmentRenderer<HorzScaleItem> implements IPaneRenderer {
    private _data;
    private _mediaSize;
    private _hitTest;
    /**
     * Initializes the Segment Renderer.
     *
     * @param hitTest - An optional, pre-configured {@link HitTestResult} template that will be returned on a successful hit.
     */
    constructor(hitTest?: HitTestResult<LineToolHitTestData>);
    /**
     * Sets the data payload required to draw and hit-test the segment.
     *
     * @param data - The {@link SegmentRendererData} containing the points and styling options.
     * @returns void
     */
    setData(data: SegmentRendererData): void;
    /**
     * Draws the line segment onto the chart pane.
     *
     * This method calculates any necessary line extensions or viewport clipping before drawing
     * the final segment, ensuring that the line stays within the visible area.
     *
     * @param target - The {@link CanvasRenderingTarget2D} provided by Lightweight Charts.
     * @returns void
     */
    draw(target: CanvasRenderingTarget2D): void;
    /**
     * Performs a hit test along the entire rendered path of the line segment.
     *
     * This includes any extended or clipped portions of the line, providing a large enough
     * tolerance to make clicking on the line easy.
     *
     * @param x - The X coordinate for the hit test.
     * @param y - The Y coordinate for the hit test.
     * @returns A {@link HitTestResult} if the coordinates are within the line's tolerance, otherwise `null`.
     */
    hitTest(x: Coordinate, y: Coordinate): HitTestResult<LineToolHitTestData> | null;
    /**
     * Helper method to draw the decorative end caps (Arrow, Circle) specified in the `LineOptions`.
     *
     * This is performed before the main line segment to ensure Z-order correctness.
     *
     * @param ctx - The CanvasRenderingContext2D.
     * @param points - The two defining points of the line.
     * @param width - The line width for sizing the end caps.
     * @param style - The line style, passed for correct arrow dashing consistency.
     * @private
     */
    private _drawEnds;
}
/**
 * Data structure required by the {@link PolygonRenderer}.
 *
 * It defines a shape or path consisting of multiple points, including the line style
 * for the perimeter and background options for the fill.
 */
export interface PolygonRendererData {
    points: AnchorPoint[];
    line: LineOptions;
    background?: {
        color: string;
    };
    hitTestBackground?: boolean;
    toolDefaultHoverCursor?: PaneCursorType;
    toolDefaultDragCursor?: PaneCursorType;
    enclosePerimeterWithLine?: boolean;
}
/**
 * Renders an open or closed shape/path defined by an array of points.
 *
 * This is used for complex freehand tools like Brush, Highlighter, and Path/Polyline.
 * It supports drawing the line perimeter, filling the background, and defining line end decorations.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item.
 */
export declare class PolygonRenderer<HorzScaleItem> implements IPaneRenderer {
    protected _data: PolygonRendererData | null;
    protected _hitTest: HitTestResult<LineToolHitTestData>;
    private _mediaSize;
    /**
     * Initializes the Polygon Renderer.
     *
     * @param hitTest - An optional, pre-configured {@link HitTestResult} template that will be returned on a successful hit.
     */
    constructor(hitTest?: HitTestResult<LineToolHitTestData>);
    /**
     * Sets the data payload required to draw and hit-test the polygon.
     *
     * @param data - The {@link PolygonRendererData} containing the points and styling options.
     * @returns void
     */
    setData(data: PolygonRendererData): void;
    /**
     * Draws the polygon path, including drawing the background fill and stroking the line perimeter.
     *
     * This handles both open paths (Polyline, Brush) and closed shapes (if `enclosePerimeterWithLine` is set).
     *
     * @param target - The {@link CanvasRenderingTarget2D} provided by Lightweight Charts.
     * @returns void
     */
    draw(target: CanvasRenderingTarget2D): void;
    /**
     * Performs a hit test on the polygon's line segments and its optional background fill area.
     *
     * For fills, it uses the robust ray casting algorithm (`pointInPolygon`) to check for hits.
     *
     * @param x - The X coordinate for the hit test.
     * @param y - The Y coordinate for the hit test.
     * @returns A {@link HitTestResult} if the polygon is hit, otherwise `null`.
     */
    hitTest(x: Coordinate, y: Coordinate): HitTestResult<LineToolHitTestData> | null;
}
/**
 * Data structure required by the {@link RectangleRenderer}.
 *
 * It defines the axis-aligned rectangle via its two defining diagonal points, styling (border/background),
 * and behavior (horizontal extensions for Fibs or Price Range tools).
 */
export interface RectangleRendererData {
    points: [AnchorPoint, AnchorPoint];
    background?: {
        color: string;
        inflation?: {
            x: number;
            y: number;
        };
    };
    border?: {
        color: string;
        width: number;
        style: LineStyle;
        radius?: number | number[];
        highlight?: boolean;
    };
    extend?: {
        left: boolean;
        right: boolean;
    };
    hitTestBackground?: boolean;
    toolDefaultHoverCursor?: PaneCursorType;
    toolDefaultDragCursor?: PaneCursorType;
}
/**
 * Renders an axis-aligned rectangular shape.
 *
 * This renderer is primarily used for the Rectangle drawing tool, as well as for drawing the
 * background fills of range tools like Fib Retracements and Price Ranges.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item.
 */
export declare class RectangleRenderer<HorzScaleItem> implements IPaneRenderer {
    protected _data: RectangleRendererData | null;
    private _mediaSize;
    private _hitTest;
    /**
     * Initializes the Rectangle Renderer.
     *
     * @param hitTest - An optional, pre-configured {@link HitTestResult} template that will be returned on a successful hit.
     */
    constructor(hitTest?: HitTestResult<LineToolHitTestData>);
    /**
     * Sets the data payload required to draw and hit-test the rectangle.
     *
     * @param data - The {@link RectangleRendererData} containing the points and styling options.
     * @returns void
     */
    setData(data: RectangleRendererData): void;
    /**
     * Draws the rectangle onto the chart pane, handling background fill, borders, and horizontal extensions.
     *
     * This relies on the core `fillRectWithBorder` canvas helper for drawing the shape with proper pixel alignment.
     *
     * @param target - The {@link CanvasRenderingTarget2D} provided by Lightweight Charts.
     * @returns void
     */
    draw(target: CanvasRenderingTarget2D): void;
    /**
     * Performs a hit test on the four border segments and the optional background fill area of the rectangle.
     *
     * It correctly accounts for horizontal extensions when checking the top and bottom borders.
     *
     * @param x - The X coordinate for the hit test.
     * @param y - The Y coordinate for the hit test.
     * @returns A {@link HitTestResult} if the rectangle is hit, otherwise `null`.
     */
    hitTest(x: Coordinate, y: Coordinate): HitTestResult<LineToolHitTestData> | null;
}
/**
 * Internal utility interface to cache calculated information about text lines after word wrapping.
 *
 * @property lines - An array of strings representing the final, wrapped lines of text.
 * @property linesMaxWidth - The pixel width of the longest line of text.
 */
export interface LinesInfo {
    lines: string[];
    linesMaxWidth: number;
}
/**
 * Internal utility interface to cache the computed font metrics.
 *
 * This prevents repeated calculation of the CSS font string and pixel size.
 *
 * @property fontSize - The computed font size in pixels.
 * @property fontStyle - The complete CSS font string (e.g., `'bold 12px sans-serif'`).
 */
export interface FontInfo {
    fontSize: number;
    fontStyle: string;
}
/**
 * Internal utility interface to cache the final pixel dimensions of the text box.
 *
 * This represents the bounding box required to contain the wrapped text content, including
 * padding, inflation, and border width.
 *
 * @property width - The final calculated width of the text box in pixels.
 * @property height - The final calculated height of the text box in pixels.
 */
export interface BoxSize {
    width: number;
    height: number;
}
/**
 * The master internal state cache for the {@link TextRenderer}.
 *
 * Stores all pre-calculated screen coordinates, dimensions, and text alignment values
 * required to draw the text and its box in the correct position relative to the anchor point.
 */
export interface InternalData {
    boxLeft: number;
    boxTop: number;
    boxWidth: number;
    boxHeight: number;
    textStart: number;
    textTop: number;
    textAlign: TextAlignment;
    rotationPivot: Point;
}
/**
 * Renders complex text and its surrounding box.
 *
 * This powerful renderer supports multi-line word wrapping, custom alignment to a parent rectangle,
 * rotation, scaling, borders, background fills, and drop shadows, making it suitable for all text-based tools.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item.
 */
export declare class TextRenderer<HorzScaleItem> implements IPaneRenderer {
    protected _internalData: InternalData | null;
    protected _polygonPoints: Point[] | null;
    protected _linesInfo: LinesInfo | null;
    protected _fontInfo: FontInfo | null;
    protected _boxSize: BoxSize | null;
    protected _data: TextRendererData | null;
    protected _hitTest: HitTestResult<LineToolHitTestData>;
    private _mediaSize;
    /**
     * Initializes the Text Renderer.
     *
     * @param hitTest - An optional, pre-configured {@link HitTestResult} template.
     */
    constructor(hitTest?: HitTestResult<LineToolHitTestData>);
    /**
     * Sets the data payload required to draw and hit-test the text.
     *
     * This method is complex as it includes logic to **invalidate internal caches** (`_linesInfo`, `_boxSize`, etc.)
     * only when the relevant parts of the new data differ from the old data.
     *
     * @param data - The {@link TextRendererData} containing the content and styling.
     * @returns void
     */
    setData(data: TextRendererData): void;
    /**
     * Performs a hit test on the text box area.
     *
     * The logic first checks if the point falls inside the rotated box polygon and then checks proximity
     * to the box's border segments. A border hit suggests moving the parent tool anchor(s), and an
     * internal hit suggests dragging the entire text box (translation).
     *
     * @param x - The X coordinate for the hit test.
     * @param y - The Y coordinate for the hit test.
     * @returns A {@link HitTestResult} if the text box is hit, otherwise `null`.
     */
    hitTest(x: Coordinate, y: Coordinate): HitTestResult<LineToolHitTestData> | null;
    /**
     * Calculates and retrieves the final pixel dimensions of the rendered text box.
     *
     * @returns The {@link BoxSize} (width and height) of the rendered element.
     */
    measure(): BoxSize;
    /**
     * Retrieves the bounding rectangle (x, y, width, height) of the text box in screen coordinates.
     *
     * This uses the cached internal data for position and size.
     *
     * @returns An object containing the top-left coordinate, width, and height of the bounding box.
     */
    rect(): {
        x: number;
        y: number;
        width: number;
        height: number;
    };
    /**
     * Determines if the entire text box is positioned off-screen.
     *
     * This check first uses a simple AABB comparison and then, for more robust culling of rotated boxes,
     * checks if all four corners of the rotated polygon are outside the viewport.
     *
     * @param width - The width of the visible pane area.
     * @param height - The height of the visible pane area.
     * @returns `true` if the text box is entirely off-screen, `false` otherwise.
     */
    isOutOfScreen(width: number, height: number): boolean;
    /**
     * Retrieves the cached CSS font string used for rendering and measurement (e.g., 'bold 12px sans-serif').
     *
     * @returns The computed font style string.
     */
    fontStyle(): string;
    /**
     * Executes the word-wrapping logic for a given string, font, and maximum line width.
     *
     * This is primarily a proxy for the external `textWrap` utility function.
     *
     * @param test - The raw string content to wrap.
     * @param wrapWidth - The maximum pixel width for a single line before wrapping.
     * @param font - Optional font string to use for measurement.
     * @returns An array of strings representing the final, wrapped lines.
     */
    wordWrap(test: string, wrapWidth?: number, font?: string): string[];
    /**
     * Draws the complete text box element onto the chart pane.
     *
     * This method:
     * 1. Saves the canvas context and applies rotation/translation transforms based on the box's configuration.
     * 2. Draws the shadow, background fill, and border.
     * 3. Draws each of the wrapped text lines.
     * 4. Restores the canvas context.
     *
     * @param target - The {@link CanvasRenderingTarget2D} provided by Lightweight Charts.
     * @returns void
     */
    draw(target: CanvasRenderingTarget2D): void;
    /**
     * Calculates and caches the master internal state (`InternalData`) for positioning and drawing.
     *
     * This is a heavy calculation that:
     * 1. Determines the final position (`boxLeft`, `boxTop`) based on the tool's anchor points and text box alignment/offset.
     * 2. Determines the text alignment and start position within the box.
     * 3. Calculates the `rotationPivot`.
     *
     * @returns The cached {@link InternalData} object.
     * @private
     */
    private _getInternalData;
    /**
     * Calculates the maximum pixel width among all wrapped lines of text.
     *
     * If word wrap is configured, this uses the fixed `wordWrapWidth` instead of measuring.
     *
     * @param lines - The array of wrapped text strings.
     * @returns The maximum width in pixels.
     * @private
     */
    private _getLinesMaxWidth;
    /**
     * Calculates and caches the {@link LinesInfo} structure.
     *
     * This performs the word wrapping, checks for max height constraints (truncating lines if necessary),
     * and calculates the max line width.
     *
     * @returns The cached {@link LinesInfo} object.
     * @private
     */
    private _getLinesInfo;
    /**
     * Calculates and caches the {@link FontInfo} structure, including the final CSS font string and pixel size.
     *
     * This is used once to configure the drawing context and repeatedly for text width measurement.
     *
     * @returns The cached {@link FontInfo} object.
     * @private
     */
    private _getFontInfo;
    /**
     * Calculates and caches the total pixel dimensions of the text box.
     *
     * This uses the results of `_getLinesInfo` and the configured padding/inflation options.
     *
     * @returns The cached {@link BoxSize} object.
     * @private
     */
    private _getBoxSize;
    /**
     * Calculates and caches the four corner points of the rotated text box bounding polygon in screen coordinates.
     *
     * This polygon is the basis for accurate hit testing on the rotated element.
     *
     * @returns An array of four {@link Point} objects defining the rotated bounding box.
     * @private
     */
    private _getPolygonPoints;
    /**
     * Retrieves the pivot point in screen coordinates around which the text box is rotated.
     *
     * This point is calculated and stored in the internal data cache by `_getInternalData`.
     *
     * @returns A {@link Point} object representing the rotation pivot.
     * @private
     */
    private _getRotationPoint;
}
/**
 * Data structure required by the {@link CircleRenderer}.
 *
 * It defines the circle's geometry via two points (Center Point and a point on the Circumference),
 * and includes styling for the background fill and border stroke.
 */
export interface CircleRendererData {
    points: [AnchorPoint, AnchorPoint];
    background?: {
        color: string;
    };
    border?: {
        color: string;
        width: number;
        style: LineStyle;
    };
    hitTestBackground?: boolean;
    toolDefaultHoverCursor?: PaneCursorType;
    toolDefaultDragCursor?: PaneCursorType;
}
/**
 * Renders an arbitrary circle defined by two points.
 *
 * This supports hit testing on both the circle's perimeter (border) and its interior (background fill).
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item.
 */
export declare class CircleRenderer<HorzScaleItem> implements IPaneRenderer {
    protected _data: CircleRendererData | null;
    private _mediaSize;
    protected _hitTest: HitTestResult<LineToolHitTestData>;
    /**
     * Initializes the Circle Renderer.
     *
     * @param hitTest - An optional, pre-configured {@link HitTestResult} template.
     */
    constructor(hitTest?: HitTestResult<LineToolHitTestData>);
    /**
     * Sets the data payload required to draw and hit-test the circle.
     *
     * @param data - The {@link CircleRendererData} containing the points and styling options.
     * @returns void
     */
    setData(data: CircleRendererData): void;
    /**
     * Draws the circle onto the chart pane, handling both the background fill and the border stroke.
     *
     * The radius is dynamically calculated as the distance between the two input points.
     *
     * @param target - The {@link CanvasRenderingTarget2D} provided by Lightweight Charts.
     * @returns void
     */
    draw(target: CanvasRenderingTarget2D): void;
    /**
     * Performs a hit test on the circle's perimeter and its optional background fill area.
     *
     * Perimeter hit testing uses a tolerance around the calculated radius.
     *
     * @param x - The X coordinate for the hit test.
     * @param y - The Y coordinate for the hit test.
     * @returns A {@link HitTestResult} if the circle is hit, otherwise `null`.
     */
    hitTest(x: Coordinate, y: Coordinate): HitTestResult<LineToolHitTestData> | null;
}
