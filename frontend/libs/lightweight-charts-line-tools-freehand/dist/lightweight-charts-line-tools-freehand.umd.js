(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports, require('lightweight-charts'), require('lightweight-charts-line-tools-core')) :
    typeof define === 'function' && define.amd ? define(['exports', 'lightweight-charts', 'lightweight-charts-line-tools-core'], factory) :
    (global = typeof globalThis !== 'undefined' ? globalThis : global || self, factory(global.LightweightChartsLineToolsFreehand = {}, global.LightweightCharts, global.LightweightChartsLineToolsCore));
})(this, (function (exports, lightweightCharts, lightweightChartsLineToolsCore) { 'use strict';

    // lightweight-charts-line-tools-freehand/src/views/LineToolBrushPaneView.ts
    /**
     * Pane View for the Brush tool.
     *
     * **Tutorial Note on View Logic:**
     * The Brush View is responsible for two critical transformations:
     * 1. **Data Conversion:** Converting the unbounded stream of logical points into screen coordinates.
     * 2. **Path Smoothing:** Applying a post-processing algorithm (`_smoothArray`) to the raw screen points
     *    to create a fluid, natural-looking curve instead of a jagged polyline.
     * 3. **Rendering:** Using the `PolygonRenderer` to draw the final smoothed path.
     */
    class LineToolBrushPaneView extends lightweightChartsLineToolsCore.LineToolPaneView {
        /**
         * Initializes the Brush View.
         *
         * @param source - The specific Brush model instance.
         * @param chart - The Chart API.
         * @param series - The Series API.
         */
        constructor(source, chart, series) {
            super(source, chart, series);
            /**
             * Internal renderer responsible for drawing the continuous freehand line.
             * @protected
             */
            this._polygonRenderer = new lightweightChartsLineToolsCore.PolygonRenderer();
        }
        /**
         * Smooths the raw path points using an iterative moving average algorithm.
         *
         * **Algorithm Details:**
         * It uses a simple box blur kernel (window size 3: [prev, current, next]).
         * The smoothing is applied iteratively (default 2 passes) to progressively reduce high-frequency
         * jitter from the mouse input without significantly distorting the original shape.
         *
         * @param points - The raw screen points captured from mouse movements.
         * @param iterations - The number of smoothing passes to apply (default: 2).
         * @returns A new array of smoothed {@link AnchorPoint}s.
         * @protected
         */
        _smoothArray(points, iterations = 2) {
            if (points.length <= 2 || iterations === 0) {
                return points;
            }
            // Use a simple, iterative moving average (box blur kernel)
            let smoothedPoints = points.map(p => p.clone());
            const windowSize = 3; // Window of [previous, current, next]
            for (let i = 0; i < iterations; i++) {
                const currentIterationPoints = smoothedPoints.map(p => p.clone());
                for (let j = 1; j < smoothedPoints.length - 1; j++) {
                    const prev = smoothedPoints[j - 1];
                    const current = smoothedPoints[j];
                    const next = smoothedPoints[j + 1];
                    // Calculate new position as the average of the window
                    const avgX = (prev.x + current.x + next.x) / windowSize;
                    const avgY = (prev.y + current.y + next.y) / windowSize;
                    currentIterationPoints[j].x = avgX;
                    currentIterationPoints[j].y = avgY;
                }
                smoothedPoints = currentIterationPoints;
            }
            return smoothedPoints;
        }
        /**
         * The core update logic.
         *
         * It orchestrates the pipeline: Culling -> Coordinate Conversion -> Smoothing -> Rendering.
         *
         * @param height - The height of the pane.
         * @param width - The width of the pane.
         * @protected
         * @override
         */
        _updateImpl(height, width) {
            this._invalidated = false;
            this._renderer.clear();
            const options = this._tool.options();
            const permanentPoints = this._tool.getPermanentPointsForTranslation();
            // 1. Convert logical points to raw screen coordinates
            const hasScreenPoints = this._updatePoints(); // Populates this._points (raw screen points)
            if (!options.visible || !hasScreenPoints || this._points.length === 0) {
                return;
            }
            // --- CULLING IMPLEMENTATION START (For Unbounded Brush Tool) ---
            // We only cull the final, completed tool. We must show the tool during creation/editing.
            if (!this._tool.isCreating() && !this._tool.isEditing() && permanentPoints.length > 1) {
                // Get the AABB (Axis-Aligned Bounding Box) of ALL points in Logical Space
                const toolAABB = lightweightChartsLineToolsCore.getToolBoundingBox(permanentPoints);
                if (toolAABB) {
                    // Synthesize the two AABB corners in Logical Space
                    const boundingPointsLogical = [
                        // Point 1: Top-Left Corner (Min Time, Max Price)
                        { timestamp: toolAABB.minTime, price: toolAABB.maxPrice },
                        // Point 2: Bottom-Right Corner (Max Time, Min Price)
                        { timestamp: toolAABB.maxTime, price: toolAABB.minPrice }
                    ];
                    // Culling Check: Get culling state and skip rendering if not visible
                    /**
                     * CULLING & VISIBILITY CHECK
                     *
                     * For an unbounded tool like the Brush, we cannot check a simple fixed box.
                     * 1. We calculate the AABB (Axis-Aligned Bounding Box) of *all* points in logical space.
                     * 2. We synthesize a logical box from these min/max values.
                     * 3. We check if this box intersects the viewport.
                     *
                     * Note: We only cull when the tool is *finished*. During creation/editing, we always render
                     * to ensure immediate feedback to the user.
                     */
                    const cullingState = lightweightChartsLineToolsCore.getToolCullingState(boundingPointsLogical, this._tool);
                    if (cullingState !== lightweightChartsLineToolsCore.OffScreenState.Visible) {
                        // Clear the renderer and exit the update function
                        //console.log('brush culled')
                        this._renderer.clear();
                        return;
                    }
                }
            }
            // --- CULLING IMPLEMENTATION END ---
            // 2. Apply Smoothing (The V3.8 Step 2)
            /**
             * PATH SMOOTHING
             *
             * We apply the smoothing algorithm to the raw screen points.
             * This transforms the jagged raw input into the fluid stroke characteristic of a brush.
             */
            const smoothedPoints = this._smoothArray(this._points, 2);
            // 3. Configure Renderers (The V3.8 Step 3)
            // --- CRITICAL FIX: Ensure all required properties are non-optional (string/number) before passing to setData ---
            // The options object is already complete and type-safe thanks to the Model's constructor merge.
            const finalLineOptions = options.line;
            // The background property of PolygonRendererData is an object { color: string } | undefined.
            // We can safely create this object only if options.background exists and has a color.
            let finalBackgroundData = undefined;
            if (options.background && options.background.color) {
                finalBackgroundData = { color: options.background.color };
            }
            /**
             * POLYGON RENDERER DATA SETUP
             *
             * We configure the `PolygonRenderer` with the **smoothed** points.
             * - `line`: The visual styling (color, width, caps).
             * - `hitTestBackground`: Set to `false` because we only want to hit-test the stroke itself,
             *   not the area "inside" the open path.
             */
            const polygonRendererData = {
                points: smoothedPoints,
                line: finalLineOptions, // Guaranteed to be a complete LineOptions object
                background: finalBackgroundData, // Properly handled as optional
                hitTestBackground: false, // Allow dragging the stroke for movement
                toolDefaultHoverCursor: options.defaultHoverCursor,
                toolDefaultDragCursor: options.defaultDragCursor,
            };
            this._polygonRenderer.setData(polygonRendererData);
            this._renderer.append(this._polygonRenderer);
            // 4. Add Anchors
            //if (this.areAnchorsVisible()) {
            this._addAnchors(this._renderer);
            //}
        }
        /**
         * Adds the interactive anchor point.
         *
         * **Tutorial Note on Anchors:**
         * A freehand drawing has hundreds of points. Showing handles for all of them would be unusable.
         * Instead, we calculate the **geometric center** of the drawing and place a single
         * "Move Handle" there. This allows the user to grab and translate the entire drawing easily.
         *
         * @param renderer - The composite renderer to append anchors to.
         * @protected
         * @override
         */
        _addAnchors(renderer) {
            if (this._points.length === 0)
                return;
            // Find the center of the bounding box of the drawn points
            const avgX = this._points.reduce((sum, p) => sum + p.x, 0) / this._points.length;
            const avgY = this._points.reduce((sum, p) => sum + p.y, 0) / this._points.length;
            // Create a single anchor point at the center (arbitrarily assign pointIndex 0)
            const centerAnchor = new lightweightChartsLineToolsCore.AnchorPoint(avgX, avgY, 0, true);
            const anchorData = {
                points: [centerAnchor],
                pointsCursorType: [lightweightChartsLineToolsCore.PaneCursorType.Grabbing],
            };
            // Add the anchor renderer. It only uses the logic from the base LineToolPaneView's createLineAnchor
            renderer.append(this.createLineAnchor(anchorData, 0));
        }
    }

    // lightweight-charts-line-tools-freehand/src/model/LineToolBrush.ts
    /**
     * Defines the default configuration options for the Brush (Freehand) tool.
     *
     * **Key Defaults:**
     * - **Points:** `pointsCount: -1` indicates an unbounded tool (variable number of points).
     * - **Interaction:** `MouseUp` finalization for continuous drawing.
     * - **Line Style:** `Round` line caps and joins for a smooth, natural brush stroke.
     * - **Color:** Default cyan line, transparent background.
     * - **Labels:** Axis labels are hidden by default as this is an annotation tool.
     * - **Anchors:** Only the center anchor is active for dragging the whole tool.
     */
    const BrushOptionDefaults = {
        visible: true,
        editable: true,
        defaultHoverCursor: lightweightChartsLineToolsCore.PaneCursorType.Pointer,
        defaultDragCursor: lightweightChartsLineToolsCore.PaneCursorType.Grabbing,
        defaultAnchorHoverCursor: lightweightChartsLineToolsCore.PaneCursorType.DiagonalNwSeResize,
        defaultAnchorDragCursor: lightweightChartsLineToolsCore.PaneCursorType.Grabbing,
        notEditableCursor: lightweightChartsLineToolsCore.PaneCursorType.NotAllowed,
        showPriceAxisLabels: false,
        showTimeAxisLabels: false,
        priceAxisLabelAlwaysVisible: false,
        timeAxisLabelAlwaysVisible: false,
        // Specific Options for BrushToolOptions
        line: {
            width: 2,
            color: 'rgba(0, 188, 212, 1)', // Cyan
            style: lightweightCharts.LineStyle.Solid,
            join: lightweightChartsLineToolsCore.LineJoin.Round,
            cap: lightweightChartsLineToolsCore.LineCap.Round,
        },
        background: {
            color: 'rgba(0, 0, 0, 0)', // Transparent by default
        },
    };
    /**
     * Defines the minimum pixel distance a new mouse point must move from the last recorded point
     * before it is added to the Brush's internal data array.
     *
     * **Why is this needed?**
     * Freehand tools generate a high volume of mouse events. This threshold acts as a filter
     * to smooth out the input, preventing an excessive number of redundant points and
     * creating a cleaner, less "jittery" line. This value is based on the V3.8 implementation.
     */
    const DISTANCE_THRESHOLD_PX$1 = 2;
    /**
     * Concrete implementation of the Brush (Freehand) drawing tool.
     *
     * **What is a Brush Tool?**
     * A Brush tool allows the user to draw continuous, freehand lines by clicking and dragging
     * the mouse. It captures a stream of points as the mouse moves.
     *
     * **Key Characteristics:**
     * - **Unbounded Points:** `pointsCount: -1` (it can have any number of points).
     * - **MouseUp Finalization:** Drawing ends when the mouse button is released.
     * - **Point Filtering:** Implements `addPoint` override to filter out redundant points
     *   (i.e., points too close to the last one).
     */
    class LineToolBrush extends lightweightChartsLineToolsCore.BaseLineTool {
        // Max interactive anchor index should be 0, as we only allow moving the tool as a whole
        /**
         * Explicitly defines the highest valid index for an interactive anchor point.
         *
         * For a Brush tool, typically only one virtual "center" anchor is used to drag
         * the entire shape. Therefore, the maximum index is **0**.
         *
         * @override
         * @returns `0`
         */
        maxAnchorIndex() {
            return 0; // Only the center anchor is typically used for whole-tool drag
        }
        /**
         * Indicates if the tool supports "Click-Click" creation.
         *
         * **Tutorial Note:**
         * Freehand tools (`Brush`, `Highlighter`) are designed for continuous drawing via drag.
         * "Click-Click" is not a natural interaction for them.
         *
         * @override
         * @returns `false`
         */
        supportsClickClickCreation() {
            return false; // Brush does NOT support click-click
        }
        /**
         * Confirms that this tool can be created via the "Click-Drag" method.
         *
         * **Interaction Flow:** Press Down -> Draw Continuously -> Release.
         * This is the primary and only way to draw with the Brush tool.
         *
         * @override
         * @returns `true`
         */
        supportsClickDragCreation() {
            return true; // Brush supports click-drag
        }
        /**
         * Indicates if holding Shift should apply geometric constraints during creation/editing.
         *
         * **Tutorial Note:**
         * For freehand drawing, applying constraints would hinder the natural flow.
         * Therefore, this is disabled.
         *
         * @override
         * @returns `false`
         */
        supportsShiftClickDragConstraint() {
            return false; // Brush does not constrain movement
        }
        /**
         * Initializes the Brush tool.
         *
         * **Tutorial Note on Construction:**
         * 1. **Base Defaults:** Uses `BrushOptionDefaults` (cyan line, transparent background).
         * 2. **User Options:** Merges user provided settings.
         * 3. **Points Count:** Explicitly sets `pointsCount` to `-1` for unbounded drawing.
         * 4. **View:** Assigns `LineToolBrushPaneView`, which handles smoothing the raw mouse input
         *    and rendering the continuous path.
         *
         * @param coreApi - The Core Plugin API.
         * @param chart - The Lightweight Charts Chart API.
         * @param series - The Series API this tool is attached to.
         * @param horzScaleBehavior - The horizontal scale behavior.
         * @param options - Configuration overrides.
         * @param points - Initial points.
         * @param priceAxisLabelStackingManager - The manager for label collision.
         */
        constructor(coreApi, chart, series, horzScaleBehavior, options = {}, points = [], priceAxisLabelStackingManager) {
            const finalOptions = lightweightChartsLineToolsCore.deepCopy(BrushOptionDefaults);
            lightweightChartsLineToolsCore.merge(finalOptions, options);
            super(coreApi, chart, series, horzScaleBehavior, finalOptions, points, 'Brush', -1, // Unbounded
            priceAxisLabelStackingManager);
            /**
             * The unique identifier for this tool type ('Brush').
             *
             * @override
             */
            this.toolType = 'Brush';
            /**
             * Defines the number of anchor points required to draw this tool.
             *
             * A Brush tool is **unbounded** and can have any number of points, so `pointsCount` is `-1`.
             *
             * @override
             */
            this.pointsCount = -1; // Unbounded points
            // A PaneView is responsible for rendering the tool on the chart.
            this._setPaneViews([new LineToolBrushPaneView(this, this._chart, this._series)]);
        }
        /**
         * Overrides the base `addPoint` method to implement **distance-based point filtering**.
         *
         * **Tutorial Note on Smoothing Input:**
         * Freehand drawing captures many points. To prevent jagged lines and reduce data load,
         * this method checks the pixel distance between the new point and the last permanent point.
         * - If the distance is below `DISTANCE_THRESHOLD_PX`, the new point is discarded.
         * - Only significant movements are added, creating a smoother visual path.
         *
         * @param newLogicalPoint - The new point suggested by the `InteractionManager`.
         * @override
         */
        addPoint(newLogicalPoint) {
            const permanentPointsCount = this.getPermanentPointsCount();
            if (permanentPointsCount > 0) {
                const lastLogicalPoint = lightweightChartsLineToolsCore.ensureNotNull(this.getPoint(permanentPointsCount - 1));
                // 1. Convert the new point and the last permanent point to screen coordinates
                const lastScreenPoint = this.pointToScreenPoint(lastLogicalPoint);
                const newScreenPoint = this.pointToScreenPoint(newLogicalPoint);
                if (lastScreenPoint && newScreenPoint) {
                    // 2. Check the screen distance (in pixels)
                    const distance = newScreenPoint.subtract(lastScreenPoint).length();
                    // 3. Filter the point: Only add if the movement is significant
                    if (distance < DISTANCE_THRESHOLD_PX$1) {
                        return; // Point is too close to the last one, filter it out
                    }
                }
            }
            // If it's the first point, or the distance is sufficient, add the point
            super.addPoint(newLogicalPoint);
        }
        /**
         * Specifies how the tool creation should end.
         *
         * For a freehand tool like Brush, drawing continues as long as the mouse button is down.
         * Therefore, creation is finalized on `MouseUp`.
         *
         * @override
         * @returns `FinalizationMethod.MouseUp`
         */
        getFinalizationMethod() {
            return lightweightChartsLineToolsCore.FinalizationMethod.MouseUp;
        }
        /**
         * Explicitly enables full tool translation when dragging the first anchor (index 0).
         *
         * **Tutorial Note:**
         * For unbounded tools like Brush, there isn't really a "point 0" in the traditional sense
         * that you'd resize from. The single anchor that appears for a Brush is intended to
         * let the user **drag the entire shape** around the chart. This override enables that behavior.
         *
         * @override
         * @returns `true`
         */
        anchor0TriggersTranslation() {
            // Override to explicitly enable the translation behavior for Anchor 0,
            // as this tool is designed to move as a whole via its single anchor.
            return true;
        }
        /**
         * Performs the hit test for the Brush tool by delegating to its associated Pane View.
         *
         * **Architecture Note:**
         * The `LineToolBrushPaneView` uses a `PolygonRenderer` to draw the smoothed, filled path.
         * The `PolygonRenderer` is responsible for the complex `pointInPolygon` hit-testing.
         * This method simply acts as the bridge to that logic.
         *
         * @param x - X coordinate in pixels.
         * @param y - Y coordinate in pixels.
         * @returns A hit result if the mouse is over the brush stroke or its bounding box.
         * @override
         */
        _internalHitTest(x, y) {
            // This guards against hitTest being called after the tool has been destroyed and _paneViews cleared.
            if (!this._paneViews || this._paneViews.length === 0 || !this._paneViews[0]) {
                return null;
            }
            // The Brush tool only has one view, which is the BrushPaneView.
            const paneView = this._paneViews[0];
            // Get the composite renderer from the view
            const compositeRenderer = paneView.renderer();
            if (!compositeRenderer || !compositeRenderer.hitTest) {
                return null;
            }
            // Delegate the hit-test to the CompositeRenderer, which will check the PolygonRenderer
            const hitResult = compositeRenderer.hitTest(x, y);
            return hitResult;
        }
    }

    // lightweight-charts-line-tools-freehand/src/views/LineToolHighlighterPaneView.ts
    /**
     * Pane View for the Highlighter tool.
     *
     * **Tutorial Note on Logic:**
     * This view is structurally very similar to the {@link LineToolBrushPaneView}.
     * It converts the stream of logical points into screen coordinates, applies a smoothing
     * algorithm to create fluid strokes, and renders the result using a `PolygonRenderer`.
     *
     * The primary difference lies in the configuration passed from the Model (thicker, translucent lines).
     */
    class LineToolHighlighterPaneView extends lightweightChartsLineToolsCore.LineToolPaneView {
        /**
         * Initializes the Highlighter View.
         *
         * @param source - The specific Highlighter model instance.
         * @param chart - The Chart API.
         * @param series - The Series API.
         */
        constructor(source, // Accepts the specific Highlighter Model type
        chart, series) {
            super(source, chart, series);
            /**
             * Internal renderer responsible for drawing the thick, freehand highlighter stroke.
             * @protected
             */
            this._polygonRenderer = new lightweightChartsLineToolsCore.PolygonRenderer();
        }
        /**
         * Smooths the raw path points using an iterative moving average algorithm.
         *
         * This algorithm reduces the "jitter" from raw mouse input, resulting in a cleaner
         * looking highlight stroke. It uses the same logic as the Brush tool to ensure consistent feel.
         *
         * @param points - The raw screen points.
         * @param iterations - Number of smoothing passes (default 2).
         * @returns The smoothed array of points.
         * @protected
         */
        _smoothArray(points, iterations = 2) {
            if (points.length <= 2 || iterations === 0) {
                return points;
            }
            // Use a simple, iterative moving average (box blur kernel)
            let smoothedPoints = points.map(p => p.clone());
            const windowSize = 3; // Window of [previous, current, next]
            for (let i = 0; i < iterations; i++) {
                const currentIterationPoints = smoothedPoints.map(p => p.clone());
                for (let j = 1; j < smoothedPoints.length - 1; j++) {
                    const prev = smoothedPoints[j - 1];
                    const current = smoothedPoints[j];
                    const next = smoothedPoints[j + 1];
                    // Calculate new position as the average of the window
                    const avgX = (prev.x + current.x + next.x) / windowSize;
                    const avgY = (prev.y + current.y + next.y) / windowSize;
                    currentIterationPoints[j].x = avgX;
                    currentIterationPoints[j].y = avgY;
                }
                smoothedPoints = currentIterationPoints;
            }
            return smoothedPoints;
        }
        /**
         * The core update logic.
         *
         * It manages visibility (culling), coordinate conversion, path smoothing, and finally
         * configuring the renderer with the specific visual options (color, width, opacity).
         *
         * @param height - The height of the pane.
         * @param width - The width of the pane.
         * @protected
         * @override
         */
        _updateImpl(height, width) {
            this._invalidated = false;
            this._renderer.clear();
            // Trust that the model's options are correct (Highlighter options)
            const options = this._tool.options();
            const permanentPoints = this._tool.getPermanentPointsForTranslation();
            // 1. Convert logical points to raw screen coordinates
            const hasScreenPoints = this._updatePoints(); // Populates this._points (raw screen points)
            if (!options.visible || !hasScreenPoints || this._points.length === 0) {
                return;
            }
            // --- CULLING IMPLEMENTATION START (For Unbounded Brush Tool) ---
            // We only cull the final, completed tool. We must show the tool during creation/editing.
            if (!this._tool.isCreating() && !this._tool.isEditing() && permanentPoints.length > 1) {
                // Get the AABB (Axis-Aligned Bounding Box) of ALL points in Logical Space
                const toolAABB = lightweightChartsLineToolsCore.getToolBoundingBox(permanentPoints);
                if (toolAABB) {
                    // Synthesize the two AABB corners in Logical Space
                    const boundingPointsLogical = [
                        // Point 1: Top-Left Corner (Min Time, Max Price)
                        { timestamp: toolAABB.minTime, price: toolAABB.maxPrice },
                        // Point 2: Bottom-Right Corner (Max Time, Min Price)
                        { timestamp: toolAABB.maxTime, price: toolAABB.minPrice }
                    ];
                    // Culling Check: Get culling state and skip rendering if not visible
                    /**
                     * CULLING & VISIBILITY CHECK
                     *
                     * Highlighters are unbounded shapes.
                     * 1. We calculate the AABB (Axis-Aligned Bounding Box) of all points in the path.
                     * 2. We convert this box to logical space.
                     * 3. We check if this logical box intersects the current viewport.
                     *
                     * This ensures that complex, large highlights don't disappear just because the "center" is off-screen.
                     */
                    const cullingState = lightweightChartsLineToolsCore.getToolCullingState(boundingPointsLogical, this._tool);
                    if (cullingState !== lightweightChartsLineToolsCore.OffScreenState.Visible) {
                        // Clear the renderer and exit the update function
                        //console.log('highlighter culled')
                        this._renderer.clear();
                        return;
                    }
                }
            }
            // --- CULLING IMPLEMENTATION END ---		
            // 2. Apply Smoothing (The V3.8 Step 2)
            /**
             * PATH SMOOTHING
             *
             * We apply the smoothing algorithm to the raw screen points.
             * This is crucial for Highlighters, as the thick line width makes jittery input
             * visually obvious and unappealing.
             */
            const smoothedPoints = this._smoothArray(this._points, 2);
            // 3. Configure Renderers (The V3.8 Step 3)
            const finalLineOptions = options.line;
            // Determine final background data for the renderer
            let finalBackgroundData = undefined;
            if (options.background && options.background.color) {
                finalBackgroundData = { color: options.background.color };
            }
            /**
             * POLYGON RENDERER DATA SETUP
             *
             * We configure the `PolygonRenderer` with the **smoothed** points.
             * - `line`: Contains the specific highlighter styling (e.g., width: 20px, opacity: 0.4).
             * - `background`: Handles optional fill if configured (though highlighters are usually just thick strokes).
             */
            const polygonRendererData = {
                points: smoothedPoints,
                line: finalLineOptions,
                background: finalBackgroundData,
                hitTestBackground: false,
                toolDefaultHoverCursor: options.defaultHoverCursor,
                toolDefaultDragCursor: options.defaultDragCursor,
            };
            this._polygonRenderer.setData(polygonRendererData);
            this._renderer.append(this._polygonRenderer);
            // 4. Add Anchors
            //if (this.areAnchorsVisible()) {
            this._addAnchors(this._renderer);
            //}
        }
        /**
         * Adds the interactive anchor point.
         *
         * **Tutorial Note:**
         * Like the Brush, we calculate the geometric center of the highlight path and place a
         * single "Move Handle" there. This allows the user to reposition the specific highlight
         * annotation without needing to interact with every single point in the path.
         *
         * @param renderer - The composite renderer to append anchors to.
         * @protected
         * @override
         */
        _addAnchors(renderer) {
            if (this._points.length === 0)
                return;
            // Find the center of the bounding box of the drawn points
            const avgX = this._points.reduce((sum, p) => sum + p.x, 0) / this._points.length;
            const avgY = this._points.reduce((sum, p) => sum + p.y, 0) / this._points.length;
            // Create a single anchor point at the center (arbitrarily assign pointIndex 0)
            const centerAnchor = new lightweightChartsLineToolsCore.AnchorPoint(avgX, avgY, 0, true);
            const anchorData = {
                points: [centerAnchor],
                pointsCursorType: [lightweightChartsLineToolsCore.PaneCursorType.Grabbing],
            };
            // Add the anchor renderer.
            renderer.append(this.createLineAnchor(anchorData, 0));
        }
    }

    // lightweight-charts-line-tools-freehand/src/model/LineToolHighlighter.ts
    /**
     * Defines the default configuration options for the Highlighter tool.
     *
     * **Tutorial Note:**
     * The Highlighter is functionally identical to the Brush but differs in its visual defaults:
     * - **Width:** Much thicker (20px) to cover text or bars.
     * - **Color:** Translucent yellow (`rgba(255, 255, 0, 0.4)`) to simulate a real highlighter marker.
     * - **End Caps:** Round caps for smooth strokes.
     */
    const HighlighterOptionDefaults = {
        visible: true,
        editable: true,
        defaultHoverCursor: lightweightChartsLineToolsCore.PaneCursorType.Pointer,
        defaultDragCursor: lightweightChartsLineToolsCore.PaneCursorType.Grabbing,
        defaultAnchorHoverCursor: lightweightChartsLineToolsCore.PaneCursorType.DiagonalNwSeResize,
        defaultAnchorDragCursor: lightweightChartsLineToolsCore.PaneCursorType.Grabbing,
        notEditableCursor: lightweightChartsLineToolsCore.PaneCursorType.NotAllowed,
        showPriceAxisLabels: false,
        showTimeAxisLabels: false,
        priceAxisLabelAlwaysVisible: false,
        timeAxisLabelAlwaysVisible: false,
        // Specific Options for HighlighterToolOptions
        line: {
            width: 20,
            color: 'rgba(255, 255, 0, 0.4)',
            style: lightweightCharts.LineStyle.Solid,
            join: lightweightChartsLineToolsCore.LineJoin.Round,
            cap: lightweightChartsLineToolsCore.LineCap.Round,
        },
        background: {
            color: 'rgba(0, 0, 0, 0)',
        },
    };
    // Threshold for point filtering in screen space (pixels) - Must be the same as Brush
    const DISTANCE_THRESHOLD_PX = 2;
    /**
     * Concrete implementation of the Highlighter drawing tool.
     *
     * **What is a Highlighter?**
     * It is a freehand drawing tool designed to overlay chart data with a thick, translucent stroke.
     *
     * **Inheritance:**
     * It extends {@link BaseLineTool} directly. While it shares almost all logic with {@link LineToolBrush}
     * (unbounded points, mouse-up finalization, point filtering), it is implemented as a separate class
     * to allow for distinct type identification (`toolType: 'Highlighter'`) and specific default styling.
     */
    class LineToolHighlighter extends lightweightChartsLineToolsCore.BaseLineTool {
        /**
         * Explicitly defines the highest valid index for an interactive anchor point.
         *
         * We only use a single center anchor (index 0) to allow dragging the entire highlight shape.
         *
         * @override
         * @returns `0`
         */
        maxAnchorIndex() {
            return 0; // Only the center anchor is typically used for whole-tool drag
        }
        /**
         * Indicates if the tool supports "Click-Click" creation.
         *
         * **Tutorial Note:**
         * Highlighter drawing is a continuous drag operation. Discrete clicks are not supported.
         *
         * @override
         * @returns `false`
         */
        supportsClickClickCreation() {
            return false; // Does NOT support click-click
        }
        /**
         * Confirms that this tool is created via the "Click-Drag" method.
         *
         * **Interaction Flow:** Press Down -> Highlight Area -> Release.
         *
         * @override
         * @returns `true`
         */
        supportsClickDragCreation() {
            return true; // Supports click-drag
        }
        /**
         * Indicates if holding Shift should apply geometric constraints.
         *
         * Disabled (`false`) for freehand tools to allow natural movement.
         *
         * @override
         * @returns `false`
         */
        supportsShiftClickDragConstraint() {
            return false; // Does not constrain movement
        }
        /**
         * Initializes the Highlighter tool.
         *
         * **Tutorial Note on Construction:**
         * 1. **Base Defaults:** Uses `HighlighterOptionDefaults` (thick yellow line).
         * 2. **User Options:** Merges user settings.
         * 3. **Points Count:** Sets `-1` for unbounded drawing.
         * 4. **View:** Assigns `LineToolHighlighterPaneView`, which handles the rendering of the thick, smoothed path.
         *
         * @param coreApi - The Core Plugin API.
         * @param chart - The Lightweight Charts Chart API.
         * @param series - The Series API this tool is attached to.
         * @param horzScaleBehavior - The horizontal scale behavior.
         * @param options - Configuration overrides.
         * @param points - Initial points.
         * @param priceAxisLabelStackingManager - The manager for label collision.
         */
        constructor(coreApi, chart, series, horzScaleBehavior, options = {}, points = [], priceAxisLabelStackingManager) {
            const finalOptions = lightweightChartsLineToolsCore.deepCopy(HighlighterOptionDefaults);
            lightweightChartsLineToolsCore.merge(finalOptions, options);
            super(coreApi, chart, series, horzScaleBehavior, finalOptions, points, 'Highlighter', // Unique tool type identifier
            -1, // Unbounded
            priceAxisLabelStackingManager);
            /**
             * The unique identifier for this tool type ('Highlighter').
             *
             * @override
             */
            this.toolType = 'Highlighter';
            /**
             * Defines the number of anchor points required to draw this tool.
             *
             * Like the Brush, the Highlighter is **unbounded** (`-1`), allowing an unlimited number of points
             * to define the freehand path.
             *
             * @override
             */
            this.pointsCount = -1; // Unbounded points
            // A PaneView is responsible for rendering the tool on the chart.
            this._setPaneViews([new LineToolHighlighterPaneView(this, this._chart, this._series)]);
        }
        /**
         * Overrides the base `addPoint` method to implement **distance-based point filtering**.
         *
         * **Tutorial Note on Optimization:**
         * Just like the Brush tool, the Highlighter filters out points that are too close (within `DISTANCE_THRESHOLD_PX`)
         * to the previous point. This keeps the data array smaller and the rendering performance higher
         * without sacrificing visual quality.
         *
         * @param newLogicalPoint - The new point suggested by the `InteractionManager`.
         * @override
         */
        addPoint(newLogicalPoint) {
            const permanentPointsCount = this.getPermanentPointsCount();
            if (permanentPointsCount > 0) {
                const lastLogicalPoint = lightweightChartsLineToolsCore.ensureNotNull(this.getPoint(permanentPointsCount - 1));
                // 1. Convert the new point and the last permanent point to screen coordinates
                const lastScreenPoint = this.pointToScreenPoint(lastLogicalPoint);
                const newScreenPoint = this.pointToScreenPoint(newLogicalPoint);
                if (lastScreenPoint && newScreenPoint) {
                    // 2. Check the screen distance (in pixels)
                    const distance = newScreenPoint.subtract(lastScreenPoint).length();
                    // 3. Filter the point: Only add if the movement is significant
                    if (distance < DISTANCE_THRESHOLD_PX) {
                        return; // Point is too close to the last one, filter it out
                    }
                }
            }
            // If it's the first point, or the distance is sufficient, add the point
            super.addPoint(newLogicalPoint);
        }
        /**
         * Specifies how the tool creation should end.
         *
         * Highlighting ends immediately when the user releases the mouse button.
         *
         * @override
         * @returns `FinalizationMethod.MouseUp`
         */
        getFinalizationMethod() {
            return lightweightChartsLineToolsCore.FinalizationMethod.MouseUp;
        }
        /**
         * Explicitly enables full tool translation when dragging the first anchor (index 0).
         *
         * This allows the user to reposition the entire highlight mark by dragging its single handle.
         *
         * @override
         * @returns `true`
         */
        anchor0TriggersTranslation() {
            // Override to explicitly enable the translation behavior for Anchor 0,
            // as this tool is designed to move as a whole via its single anchor.
            return true;
        }
        /**
         * Performs the hit test for the Highlighter tool.
         *
         * **Architecture Note:**
         * Delegates to the `LineToolHighlighterPaneView`. The view's `PolygonRenderer` handles the complex
         * geometry check to see if the mouse is hovering over the thick stroke of the highlighter.
         *
         * @param x - X coordinate in pixels.
         * @param y - Y coordinate in pixels.
         * @returns A hit result if the mouse is over the highlight.
         * @override
         */
        _internalHitTest(x, y) {
            // This guards against hitTest being called after the tool has been destroyed and _paneViews cleared.
            if (!this._paneViews || this._paneViews.length === 0 || !this._paneViews[0]) {
                return null;
            }
            // The Highlighter tool only has one view, which is the HighlighterPaneView.
            const paneView = this._paneViews[0];
            // Get the composite renderer from the view
            const compositeRenderer = paneView.renderer();
            if (!compositeRenderer || !compositeRenderer.hitTest) {
                return null;
            }
            // Delegate the hit-test to the CompositeRenderer, which will check the PolygonRenderer
            const hitResult = compositeRenderer.hitTest(x, y);
            return hitResult;
        }
    }

    // /src/index.ts
    // Define the name under which this specific tool will be registered
    const BRUSH_NAME = 'Brush';
    const HIGHLIGHTER_NAME = 'Highlighter';
    /**
     * Registers the Freehand tools (Brush and Highlighter) with the provided Core Plugin instance.
     *
     * @param corePlugin - The instance of the Core Line Tools Plugin.
     * @returns void
     *
     * @example
     * ```ts
     * registerFreehandPlugin(corePlugin);
     * ```
     */
    function registerFreehandPlugin(corePlugin) {
        // 1. Register the Brush Tool
        corePlugin.registerLineTool(BRUSH_NAME, LineToolBrush);
        console.log(`Registered Line Tool: ${BRUSH_NAME}`);
        corePlugin.registerLineTool(HIGHLIGHTER_NAME, LineToolHighlighter);
        console.log(`Registered Line Tool: ${HIGHLIGHTER_NAME}`);
    }

    exports.LineToolBrush = LineToolBrush;
    exports.LineToolHighlighter = LineToolHighlighter;
    exports.default = registerFreehandPlugin;
    exports.registerFreehandPlugin = registerFreehandPlugin;

    Object.defineProperty(exports, '__esModule', { value: true });

}));
//# sourceMappingURL=lightweight-charts-line-tools-freehand.umd.js.map
