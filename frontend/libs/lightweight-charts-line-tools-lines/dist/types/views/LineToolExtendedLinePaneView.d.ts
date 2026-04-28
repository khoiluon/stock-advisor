import { IChartApiBase, ISeriesApi, SeriesType } from 'lightweight-charts';
import { LineToolTrendLinePaneView } from './LineToolTrendLinePaneView';
import { LineToolTrendLine } from '../model/LineToolTrendLine';
/**
 * Pane View for the Extended Line tool.
 *
 * **Inheritance Note:**
 * This class inherits directly from {@link LineToolTrendLinePaneView}.
 *
 * **Why no rendering logic?**
 * An Extended Line is geometrically identical to a Trend Line (defined by 2 points).
 * The visual difference (infinite extension in both directions) is controlled entirely
 * by the tool's options (`extend: { left: true, right: true }`).
 *
 * The parent view's `_updateImpl` method passes these options to the `SegmentRenderer`,
 * which contains the mathematical logic to clip infinite lines to the viewport.
 * Therefore, this view requires no custom drawing code.
 */
export declare class LineToolExtendedLinePaneView<HorzScaleItem> extends LineToolTrendLinePaneView<HorzScaleItem> {
    /**
     * Initializes the Extended Line View.
     *
     * @param source - The specific Extended Line model instance.
     * @param chart - The Chart API.
     * @param series - The Series API.
     */
    constructor(source: LineToolTrendLine<HorzScaleItem>, chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>);
}
