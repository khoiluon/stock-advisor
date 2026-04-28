import { ITimeAxisViewRenderer, ITimeAxisView, // Needed for TimeAxisViewRendererOptions type
TimeAxisViewRendererOptions } from '../types';
import { BaseLineTool } from '../model/base-line-tool';
import { IChartApiBase, Coordinate } from 'lightweight-charts';
/**
 * A concrete implementation of a Time Axis View for a specific anchor point of a Line Tool.
 *
 * This class manages the lifecycle of a single label on the X-axis (Time Scale).
 * Unlike standard views, it implements specialized logic to render labels in the "blank space"
 * (future dates) by using logical index interpolation, ensuring tools can be drawn
 * beyond the last existing data bar.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item (e.g., `Time` or `UTCTimestamp`).
 */
export declare class LineToolTimeAxisLabelView<HorzScaleItem> implements ITimeAxisView {
    private readonly _tool;
    private readonly _pointIndex;
    private readonly _chart;
    private readonly _timeScale;
    private readonly _renderer;
    private readonly _rendererData;
    private _invalidated;
    /**
     * Initializes the time axis label view.
     *
     * @param tool - The parent line tool instance.
     * @param pointIndex - The index of the point in the tool's data array that this label represents.
     * @param chart - The chart API instance (used for time scale access and formatting).
     */
    constructor(tool: BaseLineTool<HorzScaleItem>, pointIndex: number, chart: IChartApiBase<HorzScaleItem>);
    /**
     * Marks the view as invalidated.
     *
     * This signals that the internal data (text, coordinate, color) needs to be recalculated
     * before the next render cycle. This is typically called when the tool moves or options change.
     */
    update(): void;
    /**
     * Retrieves the renderer responsible for drawing the label.
     *
     * This method ensures the renderer's data is up-to-date by triggering a recalculation
     * (`_updateImpl`) if the view is invalidated.
     *
     * @returns The {@link ITimeAxisViewRenderer} instance.
     */
    getRenderer(): ITimeAxisViewRenderer;
    /**
     * Retrieves the formatted text content for the label.
     *
     * @returns The formatted date/time string based on the chart's localization settings.
     */
    text(): string;
    /**
     * Retrieves the X-coordinate of the label's center.
     *
     * @returns The screen coordinate in pixels.
     */
    coordinate(): Coordinate;
    /**
     * Retrieves the text color.
     *
     * @returns A CSS color string (usually calculated for high contrast against the background).
     */
    textColor(): string;
    /**
     * Retrieves the background color of the label tag.
     *
     * @returns A CSS color string (derived from the tool's styling options).
     */
    backColor(): string;
    /**
     * Checks if the label should be currently visible.
     *
     * Visibility depends on:
     * 1. The tool's global visibility.
     * 2. The `showTimeAxisLabels` option.
     * 3. The tool's interaction state (selected/hovered) vs. `timeAxisLabelAlwaysVisible`.
     *
     * @returns `true` if the label should be drawn.
     */
    visible(): boolean;
    /**
     * Calculates the required height of the label in the time scale area.
     *
     * This delegates to the renderer's measurement logic to ensure consistency.
     *
     * @param rendererOptions - Current styling options for the time axis.
     * @returns The height in pixels.
     */
    height(rendererOptions: TimeAxisViewRendererOptions): number;
    /**
     * Internal helper to trigger data recalculation only if the view is dirty.
     *
     * @private
     */
    private _updateRendererDataIfNeeded;
    /**
     * The core logic for calculating the label's data.
     *
     * Performs the following critical steps:
     * 1. **Visibility Check:** Determines if the label should be shown based on options and state.
     * 2. **Styling:** Calculates background and high-contrast text colors.
     * 3. **Formatting:** Uses `horzScaleBehavior` to format the timestamp into a string.
     * 4. **Coordinate Calculation (The "Blank Space" Logic):**
     *    Instead of standard `timeToCoordinate` (which fails for future dates), it uses
     *    {@link interpolateLogicalIndexFromTime} to calculate a logical position even
     *    where no data exists, allowing the label to be placed accurately in the empty future space.
     *
     * @private
     */
    private _updateImpl;
}
