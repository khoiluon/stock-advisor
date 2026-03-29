import { IChartApiBase, ISeriesApi, SeriesType } from 'lightweight-charts';
import { LineToolTrendLinePaneView } from './LineToolTrendLinePaneView';
import { LineToolArrow } from '../model/LineToolArrow';
/**
 * Pane View for the Arrow tool.
 *
 * **Inheritance Note:**
 * This class extends {@link LineToolTrendLinePaneView} directly.
 *
 * **Why no rendering logic?**
 * The Arrow tool is geometrically identical to a Trend Line (2 points). The distinction
 * (the arrow head) is defined purely in the Model's options (`line.end.right`).
 * The parent view's `_updateImpl` reads these options and passes them to the
 * `SegmentRenderer`, which handles drawing the arrow cap automatically. Therefore,
 * this class requires no custom drawing code.
 */
export declare class LineToolArrowPaneView<HorzScaleItem> extends LineToolTrendLinePaneView<HorzScaleItem> {
    /**
     * Initializes the Arrow Pane View.
     *
     * @param source - The specific Arrow model instance.
     * @param chart - The Chart API.
     * @param series - The Series API.
     */
    constructor(source: LineToolArrow<HorzScaleItem>, // Use the specific model class for strong typing
    chart: IChartApiBase<HorzScaleItem>, series: ISeriesApi<SeriesType, HorzScaleItem>);
}
