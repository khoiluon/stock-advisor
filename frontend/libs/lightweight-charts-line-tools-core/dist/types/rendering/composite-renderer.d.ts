/**
 * CompositeRenderer combines multiple IPaneRenderer instances
 * into a single renderer. It does not draw itself but orchestrates
 * the drawing of its contained renderers.
 */
import { IPaneRenderer, CanvasRenderingTarget2D, LineToolHitTestData, HitTestResult } from '../types';
import { Coordinate } from 'lightweight-charts';
/**
 * A composite renderer that combines multiple {@link IPaneRenderer} instances into a single object.
 *
 * It is responsible for orchestrating the drawing of its contained renderers in sequence
 * and performing hit tests on all of them in reverse order (top-most first) to simulate Z-order.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item.
 */
export declare class CompositeRenderer<HorzScaleItem> implements IPaneRenderer {
    private _renderers;
    /**
     * Appends a renderer to the composite.
     *
     * Renderers are drawn in the order they are appended, from first to last.
     *
     * @param renderer - The {@link IPaneRenderer} to add.
     * @returns void
     */
    append(renderer: IPaneRenderer): void;
    /**
     * Clears all contained renderers from the composite.
     *
     * This is typically used by views when updating, to rebuild the set of renderers
     * needed for the current tool state.
     *
     * @returns void
     */
    clear(): void;
    /**
     * Checks if the composite contains any renderers.
     * @returns `true` if no renderers are present, `false` otherwise.
     */
    isEmpty(): boolean;
    /**
     * Draws all contained renderers in sequence using the provided rendering target.
     *
     * @param target - The {@link CanvasRenderingTarget2D} provided by Lightweight Charts.
     * @returns void
     */
    draw(target: CanvasRenderingTarget2D): void;
    /**
     * Performs a hit test by querying all contained renderers in reverse order (topmost first).
     *
     * This simulates the Z-order stack. If multiple renderers are hit, the result from the
     * one closest to the top of the stack will be returned.
     *
     * @param x - The X coordinate for the hit test.
     * @param y - The Y coordinate for the hit test.
     * @returns The {@link HitTestResult} of the topmost hit renderer, or `null` if nothing is hit.
     */
    hitTest(x: Coordinate, y: Coordinate): HitTestResult<LineToolHitTestData> | null;
}
