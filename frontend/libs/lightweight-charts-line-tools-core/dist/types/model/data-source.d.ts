import { IDataSource, IPaneView, IPriceAxisView, ITimeAxisView, AutoscaleInfo, FirstValue, IPriceFormatter } from '../types';
import { Logical, IPriceScaleApi } from 'lightweight-charts';
/**
 * An abstract base class that implements the minimal required structure of a Lightweight Charts `IDataSource`.
 *
 * This class provides basic functionality for managing the price scale reference and Z-order (layering)
 * of any primitive. It is intended to be the top layer of inheritance for primitives that render data
 * (e.g., `PriceDataSource` and ultimately `BaseLineTool`).
 *
 * It leaves key rendering and data methods (like `autoscaleInfo` and `paneViews`) as abstract.
 */
export declare abstract class DataSource implements IDataSource {
    /**
     * The API instance for the price scale this data source is currently bound to.
     * This can be the default price scale or a custom one.
     * @protected
     */
    protected _priceScale: IPriceScaleApi | null;
    private _zorder;
    /**
     * Retrieves the current Z-order value, which determines the drawing layer of the tool's primitive.
     * @returns The Z-order index.
     */
    zorder(): number;
    /**
     * Sets the drawing layer of the tool's primitive.
     * @param zorder - The new Z-order index.
     * @returns void
     */
    setZorder(zorder: number): void;
    /**
     * Retrieves the API for the price scale this primitive is attached to.
     * @returns The `IPriceScaleApi` instance, or `null`.
     */
    priceScale(): IPriceScaleApi | null;
    /**
     * Sets the API instance for the price scale.
     * @param priceScale - The `IPriceScaleApi` instance, or `null` to clear.
     * @returns void
     */
    setPriceScale(priceScale: IPriceScaleApi | null): void;
    /**
     * Abstract method to signal that all views associated with this data source should update.
     * Concrete subclasses (like {@link BaseLineTool}) must implement this to trigger view updates.
     * @abstract
     */
    abstract updateAllViews(): void;
    /**
     * Checks if the data source is visible.
     * @returns Always returns `true` by default, but derived classes can override.
     */
    visible(): boolean;
    /**
     * Abstract method to provide autoscale information.
     * @param startTimePoint - The logical index of the start of the visible range.
     * @param endTimePoint - The logical index of the end of the visible range.
     * @returns An {@link AutoscaleInfo} object, or `null`.
     * @abstract
     */
    abstract autoscaleInfo(startTimePoint: Logical, endTimePoint: Logical): AutoscaleInfo | null;
    /**
     * Abstract method to provide all price axis views for rendering labels.
     * @returns A readonly array of {@link IPriceAxisView} components.
     * @abstract
     */
    abstract priceAxisViews(): readonly IPriceAxisView[];
    /**
     * Abstract method to provide all pane views for rendering the main tool body.
     * @returns A readonly array of {@link IPaneView} components.
     * @abstract
     */
    abstract paneViews(): readonly IPaneView[];
    /**
     * Abstract method to provide all time axis views for rendering labels.
     * @returns A readonly array of {@link ITimeAxisView} components.
     * @abstract
     */
    abstract timeAxisViews(): readonly ITimeAxisView[];
    /**
     * Provides an array of views for labels drawn in the pane (not used by default).
     * @returns An empty array.
     */
    labelPaneViews(): readonly IPaneView[];
    /**
     * Provides an array of views for drawing content above the series data (not used by default).
     * @returns An empty array.
     */
    topPaneViews(): readonly IPaneView[];
    /**
     * Abstract method to provide the base value for the data source.
     * @returns The base value (a number).
     * @abstract
     */
    abstract base(): number;
    /**
     * Abstract method to provide the first value of the series.
     * @returns The {@link FirstValue} object, or `null`.
     * @abstract
     */
    abstract firstValue(): FirstValue | null;
    /**
     * Abstract method to provide a price formatter for the data source.
     * @returns The {@link IPriceFormatter}.
     * @abstract
     */
    abstract formatter(): IPriceFormatter;
    /**
     * Abstract method to determine the price line color based on the last bar.
     * @param lastBarColor - The color of the last bar.
     * @returns The price line color string.
     * @abstract
     */
    abstract priceLineColor(lastBarColor: string): string;
    /**
     * Abstract method to provide the chart model reference.
     * @returns The chart model object.
     * @abstract
     */
    abstract model(): any;
}
