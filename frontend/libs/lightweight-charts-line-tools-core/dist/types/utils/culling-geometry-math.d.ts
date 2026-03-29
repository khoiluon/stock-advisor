/**
 * Represents a simple 2D vector or point with X and Y coordinates.
 * Used primarily for internal geometric calculations in the culling engine.
 */
export interface Vec2 {
    x: number;
    y: number;
}
/**
 * Represents the coefficients of a linear equation in the slope-intercept form: `y = ax + b`.
 */
export interface LineEquation {
    /** The slope of the line (m). */
    a: number;
    /** The y-intercept of the line (b). */
    b: number;
}
/**
 * Computes the linear equation passing through two points.
 *
 * Derives the slope (`a`) and y-intercept (`b`) for the line passing through `p1` and `p2`.
 *
 * @param p1 - The first point.
 * @param p2 - The second point.
 * @returns A {@link LineEquation} object containing the slope and intercept, or `null` if the line is vertical (slope is undefined).
 */
export declare function createLineEquation(p1: Vec2, p2: Vec2): LineEquation | null;
