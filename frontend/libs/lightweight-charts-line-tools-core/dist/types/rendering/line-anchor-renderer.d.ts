import { IChartApiBase, Coordinate } from 'lightweight-charts';
import { HitTestResult, HitTestType } from '../types';
import { Point } from '../utils/geometry';
import { CanvasRenderingTarget2D, IPaneRenderer, PaneCursorType, LineToolHitTestData } from '../types';
/**
 * Extends the base {@link Point} class to include necessary metadata for an interactive anchor handle.
 *
 * This point represents the screen coordinates of a resize/edit handle, along with data
 * about its type, index in the tool's point array, and specific cursor requirements.
 */
export declare class AnchorPoint extends Point {
    data: number;
    square: boolean;
    specificCursor?: PaneCursorType;
    /**
     * Initializes a new Anchor Point.
     *
     * @param x - The X-coordinate in pixels.
     * @param y - The Y-coordinate in pixels.
     * @param data - The index of this point in the parent tool's point array.
     * @param square - If `true`, the anchor is drawn as a square; otherwise, it is a circle.
     * @param specificCursor - An optional, specific cursor to display when hovering over this anchor.
     */
    constructor(x: number, y: number, data: number, square?: boolean, specificCursor?: PaneCursorType);
    /**
     * Creates a deep copy of the anchor point, preserving all metadata.
     * @returns A new {@link AnchorPoint} instance.
     */
    clone(): AnchorPoint;
}
/**
 * The data payload required by the {@link LineAnchorRenderer}.
 *
 * This encapsulates the list of anchor points to draw, their colors, styling properties
 * (radius, stroke), and the current interaction state (selected, hovered, editing) to
 * determine which effects to render.
 */
export interface LineAnchorRendererData {
    points: AnchorPoint[];
    backgroundColors: string[];
    pointsCursorType?: PaneCursorType[];
    editedPointIndex: number | null;
    currentPoint: Point;
    color: string;
    radius: number;
    strokeWidth: number;
    hoveredStrokeWidth: number;
    selected: boolean;
    visible: boolean;
    hitTestType: HitTestType;
    defaultAnchorHoverCursor?: PaneCursorType;
    defaultAnchorDragCursor?: PaneCursorType;
}
/**
 * Renders the interactive anchor points (resize/edit handles) for a line tool.
 *
 * It draws the small square or circle handles that appear when a tool is selected
 * and performs the highly sensitive hit testing required for dragging these handles.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item.
 */
export declare class LineAnchorRenderer<HorzScaleItem> implements IPaneRenderer {
    /**
     * Internal data payload.
     * @internal
     */
    protected _data: LineAnchorRendererData | null;
    private _chart;
    /**
     * Initializes the Anchor Renderer.
     *
     * @param chart - The Lightweight Charts chart API instance (for context/API access).
     * @param data - Optional initial {@link LineAnchorRendererData} to set.
     */
    constructor(chart: IChartApiBase<HorzScaleItem>, data?: LineAnchorRendererData);
    /**
     * Overwrites the entire data payload for the renderer.
     * @param data - The new {@link LineAnchorRendererData}.
     * @returns void
     */
    setData(data: LineAnchorRendererData): void;
    /**
     * Partially updates the current data payload by merging a set of changes.
     * @param data - A partial update object for the {@link LineAnchorRendererData}.
     * @returns void
     */
    updateData(data: Partial<LineAnchorRendererData>): void;
    /**
     * Draws all configured anchor points (circles or squares) onto the chart pane.
     *
     * It uses helper drawing functions (`drawCircleBody`, `drawRectBody`) to render
     * the main handle and applies special effects (shadows/halos) if the anchor is hovered.
     *
     * @param target - The {@link CanvasRenderingTarget2D} provided by Lightweight Charts.
     * @returns void
     */
    draw(target: CanvasRenderingTarget2D): void;
    /**
     * Performs a hit test specifically over the anchor points.
     *
     * This logic uses an augmented radius (`this._data.radius + interactionTolerance.anchor`)
     * to create a larger, forgiving target area for the user to click/drag.
     * It determines the specific anchor index hit and the appropriate cursor type (e.g., 'resize').
     *
     * @param x - The X coordinate for the hit test.
     * @param y - The Y coordinate for the hit test.
     * @returns A {@link HitTestResult} containing the anchor index and cursor, or `null`.
     */
    hitTest(x: Coordinate, y: Coordinate): HitTestResult<LineToolHitTestData> | null;
    /**
     * Internal helper to iterate over a list of points (either circles or squares) and draw their bodies and hover shadows.
     *
     * This abstracts the logic for drawing the shape itself (`drawBody`) and applying the hover effect (`drawShadow`).
     *
     * @param ctx - The CanvasRenderingContext2D.
     * @param points - The array of {@link AnchorPoint}s to draw.
     * @param colors - The array of corresponding background colors.
     * @param drawBody - The callback function to draw the main body of the shape.
     * @param drawShadow - The callback function to draw the hover shadow/halo.
     * @private
     */
    private _drawPoints;
}
