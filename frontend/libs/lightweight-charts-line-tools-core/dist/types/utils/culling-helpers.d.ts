import { LineToolPoint } from '../api/public-api';
import { BaseLineTool } from '../model/base-line-tool';
import { ExtendOptions, SinglePointOrientation, LineToolCullingInfo } from '../types';
/**
 * Enum defining the visibility state of a tool relative to the chart's current viewport.
 *
 * These values are used by the rendering engine to determine if a tool should be drawn (`Visible`)
 * or skipped. If skipped, specific off-screen values (`OffScreenTop`, `OffScreenLeft`, etc.)
 * provide hints about *where* the tool is located, which can be used for directional indicators.
 */
export declare enum OffScreenState {
    Visible = "visible",
    OffScreenTop = "top",
    OffScreenBottom = "bottom",
    OffScreenLeft = "left",
    OffScreenRight = "right",
    FullyOffScreen = "fullyOffScreen"
}
/**
 * Represents an Axis-Aligned Bounding Box (AABB) in the chart's logical coordinate space.
 *
 * This structure is used for broad-phase culling tests. Time values are stored as
 * numbers (timestamps) and prices as raw values.
 */
export interface ToolBoundingBox {
    minTime: number;
    maxTime: number;
    minPrice: number;
    maxPrice: number;
}
/**
 * Calculates the Axis-Aligned Bounding Box (AABB) for a set of tool points.
 *
 * This iterates through all provided points to find the min/max timestamp and price.
 * It is used for fast exclusion checks before performing more expensive geometric clipping.
 *
 * @param points - An array of {@link LineToolPoint}s defining the tool.
 * @returns A {@link ToolBoundingBox} representing the extents, or `null` if the array is empty.
 */
export declare function getToolBoundingBox(points: LineToolPoint[]): ToolBoundingBox | null;
/**
 * Calculates the bounding box of the currently visible chart area in logical units (Timestamp/Price).
 *
 * This function handles the complex logic of mapping the viewport's pixel dimensions back to
 * time and price ranges. Crucially, it uses **interpolation** to determine the timestamp values for
 * the left and right edges of the screen, ensuring accurate bounds even when the user scrolls
 * into the "blank" future space where no data bars exist.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item.
 * @param tool - The tool instance (used to access the chart, series, and scale APIs).
 * @returns A {@link ToolBoundingBox} representing the visible area, or `null` if the chart is not ready.
 */
export declare function getViewportBounds<HorzScaleItem>(tool: BaseLineTool<HorzScaleItem>): ToolBoundingBox | null;
/**
 * Internal geometric helper that computes the culling state for two-point tools with potential infinite extensions.
 *
 * This function determines if a line segment (or Ray/Infinite Line defined by `extendOptions`) intersects
 * the visible viewport. It normalizes point order, performs parametric clipping against the viewport bounds,
 * and falls back to a full AABB check if the line misses the viewport entirely to provide a directional hint.
 *
 * @param points - An array of exactly two {@link LineToolPoint}s.
 * @param viewportBounds - The bounding box of the visible chart area.
 * @param extendOptions - Configuration defining if the line extends infinitely to the left or right.
 * @returns The {@link OffScreenState} indicating visibility or direction of the miss.
 */
export declare function getCullingStateWithExtensions(points: LineToolPoint[], viewportBounds: ToolBoundingBox, extendOptions: ExtendOptions): OffScreenState;
/**
 * The primary culling engine entry point. Determines the precise off-screen state of any tool.
 *
 * This function routes logic based on the tool's geometry:
 * 1. **Complex Shapes**: Uses `cullingInfo` to check specific sub-segments (e.g., for Polylines).
 * 2. **Single Points**: Performs point-in-AABB checks or specific horizontal/vertical line logic if extensions are active.
 * 3. **Two-Point Tools**: Uses robust geometric clipping (via {@link getCullingStateWithExtensions}) to handle segments, rays, and infinite lines.
 * 4. **General Fallback**: Uses a standard AABB overlap check for other cases.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item.
 * @param points - The points defining the tool.
 * @param tool - The tool instance.
 * @param extendOptions - Optional configuration for infinite extensions (Left/Right).
 * @param singlePointOrientation - Optional orientation for single-point infinite lines (Horizontal/Vertical).
 * @param cullingInfo - Optional advanced culling rules (e.g., `subSegments` for multi-segment tools).
 * @returns The final {@link OffScreenState} (Visible, or a specific directional miss).
 */
export declare function getToolCullingState<HorzScaleItem>(points: LineToolPoint[], tool: BaseLineTool<HorzScaleItem>, extendOptions?: ExtendOptions, singlePointOrientation?: SinglePointOrientation, cullingInfo?: LineToolCullingInfo): OffScreenState;
