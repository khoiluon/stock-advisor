import { PriceAxisViewRendererCommonData, PriceAxisViewRendererData, IPriceAxisViewRenderer, IPriceAxisView, // Our internal interface that extends ISeriesPrimitiveAxisView
PriceAxisViewRendererOptions } from '../types';
import { Coordinate } from 'lightweight-charts';
/**
 * Interface defining the constructor signature for a Price Axis View Renderer.
 *
 * This allows the `PriceAxisView` to be instantiated with a custom renderer implementation,
 * facilitating testing or specialized rendering logic.
 */
interface PriceAxisViewRendererConstructor {
    new (data: PriceAxisViewRendererData, commonData: PriceAxisViewRendererCommonData): IPriceAxisViewRenderer;
}
/**
 * Abstract base class for Price Axis Views.
 *
 * This class implements the `ISeriesPrimitiveAxisView` interface and manages the data state
 * for two distinct renderers: one for the axis label itself and one for potential pane-side labels.
 * It handles caching, dirty state (`invalidated`), and integration with the stacking manager via `fixedCoordinate`.
 */
export declare abstract class PriceAxisView implements IPriceAxisView {
    private readonly _commonRendererData;
    private readonly _axisRendererData;
    private readonly _paneRendererData;
    private readonly _axisRenderer;
    private readonly _paneRenderer;
    private _invalidated;
    /**
     * Initializes the Price Axis View.
     *
     * @param ctor - Optional constructor for the renderer. Defaults to `PriceAxisViewRenderer`.
     */
    constructor(ctor?: PriceAxisViewRendererConstructor);
    /**
     * Retrieves the text to be displayed on the axis label.
     *
     * @returns The formatted price string.
     */
    text(): string;
    /**
     * Retrieves the Y-coordinate for the label.
     *
     * **Stacking Logic:** This method checks if a `fixedCoordinate` has been set by the
     * `PriceAxisLabelStackingManager`. If so, it returns that shifted coordinate to prevent
     * overlap. Otherwise, it returns the natural price-to-coordinate value.
     *
     * @returns The Y-coordinate in pixels.
     */
    coordinate(): Coordinate;
    /**
     * Marks the view as invalid, forcing a data recalculation on the next access.
     */
    update(): void;
    /**
     * Measures the height required by the label.
     *
     * It queries both the axis renderer and the pane renderer and returns the maximum height
     * to ensure sufficient space is reserved.
     *
     * @param rendererOptions - Current styling options from the chart.
     * @param useSecondLine - Whether to account for a second line of text (default `false`).
     * @returns The height in pixels.
     */
    height(rendererOptions: PriceAxisViewRendererOptions, useSecondLine?: boolean): number;
    /**
     * Retrieves the manually fixed Y-coordinate set by the Stacking Manager.
     *
     * @returns The fixed coordinate, or `0` if unset (nominal type cast).
     */
    getFixedCoordinate(): Coordinate;
    /**
     * Sets a manual Y-coordinate for this view.
     *
     * This is called by the `PriceAxisLabelStackingManager` when it detects a collision
     * with another label.
     *
     * @param value - The new Y-coordinate in pixels.
     */
    setFixedCoordinate(value: Coordinate): void;
    /**
     * Retrieves the text color for the label.
     *
     * @returns A CSS color string.
     */
    textColor(): string;
    /**
     * Retrieves the background color for the label.
     *
     * @returns A CSS color string.
     */
    backColor(): string;
    /**
     * Checks if the view is currently visible.
     *
     * Returns `true` if either the main axis label or the pane-side label is set to visible.
     *
     * @returns `true` if visible, `false` otherwise.
     */
    visible(): boolean;
    /**
     * Retrieves the renderer for the main axis label.
     *
     * This method triggers a data update if the view is invalidated, applies the latest
     * data to the renderer instance, and returns it for drawing by the chart engine.
     *
     * @returns The {@link IPriceAxisViewRenderer} for the axis.
     */
    getRenderer(): IPriceAxisViewRenderer;
    /**
     * Retrieves the renderer for the pane-side label (e.g., text drawn inside the chart area near the axis).
     *
     * @returns The {@link IPriceAxisViewRenderer} for the pane.
     */
    getPaneRenderer(): IPriceAxisViewRenderer;
    /**
     * Abstract method to update the internal data structures based on the tool's current state.
     *
     * Concrete implementations must override this to populate `axisRendererData`, `paneRendererData`,
     * and `commonData` with the correct text, colors, and coordinates derived from the specific tool model.
     *
     * @param axisRendererData - Data object for the axis label.
     * @param paneRendererData - Data object for the pane label.
     * @param commonData - Shared data (coordinates, colors).
     * @protected
     */
    protected abstract _updateRendererData(axisRendererData: PriceAxisViewRendererData, paneRendererData: PriceAxisViewRendererData, commonData: PriceAxisViewRendererCommonData): void;
    /**
     * Internal helper to trigger data recalculation if the view is dirty.
     *
     * It resets default visibility flags and colors before calling the abstract `_updateRendererData`.
     *
     * **Note on Stacking:** This method intentionally does *not* reset `fixedCoordinate`.
     * The fixed coordinate is managed exclusively by the concrete view's interaction with the
     * `PriceAxisLabelStackingManager`, ensuring that stacking shifts persist across standard update cycles.
     *
     * @private
     */
    private _updateRendererDataIfNeeded;
}
export {};
