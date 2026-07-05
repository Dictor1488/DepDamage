package com.under_pressure.mastery
{
    import flash.display.Bitmap;
    import flash.display.DisplayObjectContainer;
    import flash.display.GradientType;
    import flash.display.Graphics;
    import flash.display.Shape;
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.events.KeyboardEvent;
    import flash.events.MouseEvent;
    import flash.filters.DropShadowFilter;
    import flash.filters.GlowFilter;
    import flash.geom.Matrix;
    import flash.geom.Point;
    import flash.text.TextField;
    import flash.text.TextFieldAutoSize;
    import flash.ui.Keyboard;
    import flash.utils.clearTimeout;
    import flash.utils.setTimeout;

    public class MasteryPanelComponent extends Sprite
    {
        [Embed(source="assets/style3_lobby_state_simple_218x77.png")]
        private static const STYLE3_LOBBY_SIMPLE_BG:Class;
        [Embed(source="assets/style3_lobby_state_extra_218x132.png")]
        private static const STYLE3_LOBBY_EXTRA_BG:Class;
        [Embed(source="assets/style3_lobby_marker.png")]
        private static const STYLE3_LOBBY_MARKER:Class;

        public static const MODE_BOTH:int        = 0;
        public static const MODE_MASTERY:int     = 1;
        public static const MODE_MARKS:int       = 2;
        public static const MODE_BOTH_GRAPH:int  = 3;
        public static const MODE_MARKS_GRAPH:int = 4;
        private static const VIEW_MODES:Array = [MODE_BOTH, MODE_MASTERY, MODE_MARKS, MODE_BOTH_GRAPH, MODE_MARKS_GRAPH];

        private static const PAD_H:int        = 10;
        private static const PAD_V:int        = 9;
        private static const ROW_HEIGHT:int   = 23;
        private static const ROW_GAP:int      = 3;
        private static const COL_COUNT:int    = 4;
        private static const COL_GAP:int      = 7;
        private static const ICON_W:int       = 23;
        private static const ICON_H:int       = 21;
        private static const ICON_GAP:int     = 3;
        private static const VALUE_W:int      = 50;
        private static const COL_WIDTH:int    = ICON_W + ICON_GAP + VALUE_W;
        private static const PANEL_MIN_W:int  = PAD_H * 2 + COL_WIDTH * COL_COUNT + COL_GAP * (COL_COUNT - 1);

        private static const GRAPH_TOP_GAP:int = 8;
        private static const GRAPH_LEFT:int    = 38;
        private static const GRAPH_W:int       = PANEL_MIN_W - GRAPH_LEFT - PAD_H;
        private static const GRAPH_H:int       = 88;
        private static const GRAPH_ROWS:int    = 6;
        private static const GRAPH_COLS:int    = 10;

        private static const FONT_FACE:String        = "$FieldFont";
        private static const FONT_SIZE_VALUE:int     = 14;
        private static const FONT_SIZE_PERCENT:int   = 12;
        private static const FONT_SIZE_AXIS:int      = 11;

        private static const BG_COLOR_TOP:uint   = 0x0A0C10;
        private static const BG_COLOR_BOT:uint   = 0x0A0C10;
        private static const BG_ALPHA_TOP:Number  = 0.70;
        private static const BG_ALPHA_BOT:Number  = 0.70;
        private static const FRAME_COLOR:uint     = 0xAEB8C2;
        private static const FRAME_DARK:uint      = 0x141A22;

        private static const COLOR_VALUE:uint   = 0xE8E8E8;
        private static const COLOR_DIM:uint     = 0x667788;
        private static const COLOR_PERCENT:uint = 0xB0BCC8;
        private static const COLOR_GRID:uint    = 0x7A8490;
        private static const COLOR_LINE:uint    = 0xF1F1F1;
        private static const COLOR_AXIS:uint    = 0xA8B2BC;
        private static const COLOR_DOT:uint     = 0xFFFFFF;
        private static const COLOR_LABEL:uint   = 0xFFFFFF;
        private static const COLOR_GOLD:uint    = 0xC8B97A;
        private static const FONT_SIZE_LABEL:int = 11;

        private static const ICON_MASTERY_3RD:String = "img://gui/maps/icons/achievement/48x48/markOfMastery1.png";
        private static const ICON_MASTERY_2ND:String = "img://gui/maps/icons/achievement/48x48/markOfMastery2.png";
        private static const ICON_MASTERY_1ST:String = "img://gui/maps/icons/achievement/48x48/markOfMastery3.png";
        private static const ICON_MASTERY_ACE:String = "img://gui/maps/icons/achievement/48x48/markOfMastery4.png";

        private static const BOUNDARY_GAP:int    = 10;
        private static const DRAG_DELAY:int      = 150;
        private static const DRAG_THRESHOLD:int  = 20;
        private static const CLICK_THRESHOLD:int = 6;

        private static const ICONS:Array          = [ICON_MASTERY_3RD, ICON_MASTERY_2ND, ICON_MASTERY_1ST, ICON_MASTERY_ACE];
        private static const PERCENT_LABELS:Array  = ["65%", "85%", "95%", "100%"];

        private var _background:Shape;
        private var _graphLayer:Shape;
        private var _dragHit:Sprite;
        private var _expandBtn:Sprite;
        private var _markBadgeBtn:Sprite;
        private var _markBadge:Sprite;
        private var _markBadgeBg:Shape;
        private var _markBadgeLine:Shape;
        private var _markBadgeStars:Shape;
        private var _markBadgeValue:TextField;
        private var _markBadgeDelta:TextField;
        private var _markBadgeTotal:TextField;
        private var _markBadgeDetail1:TextField;
        private var _markBadgeDetail2:TextField;
        private var _markBadgeStyle3SimpleBg:Bitmap;
        private var _markBadgeStyle3ExtraBg:Bitmap;
        private var _markBadgeStyle3Marker:Bitmap;

        private var _xpIcon:Array;
        private var _xpValue:Array;
        private var _moePercent:Array;
        private var _moeValue:Array;
        private var _axisLabels:Array;
        private var _markLabel:TextField;

        private var _textShadow:DropShadowFilter;
        private var _matrix:Matrix;

        private var _disposed:Boolean    = false;
        private var _offset:Array        = [100, 100];
        private var _panelWidth:int      = PANEL_MIN_W;
        private var _panelHeight:int     = 0;

        private var _clickPoint:Point;
        private var _clickOffset:Point;
        private var _badgeDragOffset:Point;
        private var _reusablePoint:Point;
        private var _isDragging:Boolean  = false;
        private var _isBadgeDragging:Boolean = false;
        private var _isDragTest:Boolean  = false;
        private var _dragTimeout:uint    = 0;

        private var _xp:Array            = [0, 0, 0, 0];
        private var _moe:Array           = [0, 0, 0, 0];
        private var _battleHistory:Array = [];
        private var _lastDamage:int = 0;
        private var _currentMark:Number  = NaN;
        private var _lastMarkDelta:Number = NaN;
        private var _markStars:int = -1;
        private var _markBadgeOffset:Array = [0, 0];
        private var _markBadgeOffsetSet:Boolean = false;
        private var _hasXp:Boolean       = false;
        private var _hasMoe:Boolean      = false;
        private var _hasGraph:Boolean    = false;
        private var _panelBodyVisible:Boolean = true;
        private var _markBadgeEnabled:Boolean = true;
        private var _markBadgeOpen:Boolean = false;
        private var _markBadgeControlVisible:Boolean = false;
        private var _markBadgeExpanded:Boolean = false;
        private var _markBadgeStyle:int = 0;  // 0=classic, 1=compact, 2=wide HTML-style
        private var _visibleState:Boolean = false;
        private var _isLoading:Boolean   = false;

        private var _strLoading:String   = "...";
        private var _strNoData:String    = "N/A";
        private var _viewMode:int        = MODE_BOTH;

        public function MasteryPanelComponent()
        {
            super();
            mouseEnabled  = false;
            mouseChildren = true;

            _clickPoint    = new Point();
            _clickOffset   = new Point();
            _badgeDragOffset = new Point();
            _reusablePoint = new Point();
            _matrix        = new Matrix();
            _textShadow    = new DropShadowFilter(1, 45, 0x000000, 0.8, 2, 2, 1.2, 1);

            _background = new Shape();
            _background.filters = [];
            addChild(_background);

            _graphLayer = new Shape();
            addChild(_graphLayer);

            _xpIcon     = _createRowFields(COL_COUNT, TextFieldAutoSize.LEFT, FONT_SIZE_VALUE);
            _xpValue    = _createRowFields(COL_COUNT, TextFieldAutoSize.LEFT, FONT_SIZE_VALUE);
            _moePercent = _createRowFields(COL_COUNT, TextFieldAutoSize.LEFT, FONT_SIZE_PERCENT);
            _moeValue   = _createRowFields(COL_COUNT, TextFieldAutoSize.LEFT, FONT_SIZE_VALUE);
            _axisLabels = _createRowFields(4, TextFieldAutoSize.RIGHT, FONT_SIZE_AXIS);

            _markLabel = new TextField();
            _markLabel.selectable  = false;
            _markLabel.mouseEnabled = false;
            _markLabel.autoSize    = TextFieldAutoSize.LEFT;
            _markLabel.multiline   = false;
            _markLabel.filters     = [_textShadow];
            _markLabel.visible     = false;
            addChild(_markLabel);

            _createDragHit();
            _createExpandBtn();
            _createMarkBadge();
            _createMarkBadgeBtn();
            _setupDragListeners();
            addEventListener(Event.ADDED_TO_STAGE, _onAddedToStage);
            _layout();
        }

        public function setMasteryData(third:int, second:int, first:int, ace:int):void
        {
            if (_disposed) return;
            _xp[0] = third; _xp[1] = second; _xp[2] = first; _xp[3] = ace;
            _hasXp = (third > 0 || second > 0 || first > 0 || ace > 0);
            _isLoading = false;
            _layout();
        }

        public function setMoeData(p65:int, p85:int, p95:int, p100:int):void
        {
            if (_disposed) return;
            _moe[0] = p65; _moe[1] = p85; _moe[2] = p95; _moe[3] = p100;
            _hasMoe = (p65 > 0 || p85 > 0 || p95 > 0 || p100 > 0);
            _isLoading = false;
            _layout();
        }

        public function setBattleHistory(values:Array, currentMark:Number):void
        {
            if (_disposed) return;
            _battleHistory = [];
            if (values != null)
            {
                for (var i:int = 0; i < values.length; i++)
                    _battleHistory.push(Number(values[i]));
            }
            _currentMark = currentMark;
            _lastMarkDelta = NaN;
            if (_battleHistory.length >= 2)
                _lastMarkDelta = Number(_battleHistory[_battleHistory.length - 1]) - Number(_battleHistory[_battleHistory.length - 2]);
            _hasGraph = (_battleHistory.length >= 1);
            _layout();
        }

        public function setLastBattleDamage(value:int):void
        {
            if (_disposed) return;
            _lastDamage = Math.max(0, value);
            _layout();
        }

        public function setMarkBadgeOpen(value:Boolean):void
        {
            if (_disposed) return;
            _markBadgeOpen = _markBadgeEnabled && value;
            _layout();
        }

        public function setMarkBadgeEnabled(value:Boolean):void
        {
            if (_disposed) return;
            _markBadgeEnabled = value;
            if (!_markBadgeEnabled)
                _markBadgeOpen = false;
            _layout();
        }

        public function setMarkBadgeControlVisible(value:Boolean):void
        {
            if (_disposed) return;
            if (_markBadgeControlVisible == value) return;
            _markBadgeControlVisible = value;
            _layoutMarkBadge();
        }

        public function setPanelBodyVisible(value:Boolean):void
        {
            if (_disposed) return;
            _panelBodyVisible = value;
            _layout();
        }

        public function setMarkBadgeOffset(offset:Array):void
        {
            if (_disposed) return;
            if (offset && offset.length >= 2)
            {
                var ox:int = int(offset[0]);
                var oy:int = int(offset[1]);
                if (ox >= 0 || oy >= 0)
                {
                    _markBadgeOffset[0] = ox;
                    _markBadgeOffset[1] = oy;
                    _markBadgeOffsetSet = true;
                }
            }
            _layout();
        }

        public function setMarkBadgeStars(value:int):void
        {
            if (_disposed) return;
            _markStars = Math.max(-1, Math.min(3, value));
            _layout();
        }

        public function setMarkBadgeStyle(value:int):void
        {
            if (_disposed) return;
            var v:int = value == 2 ? 2 : (value == 1 ? 1 : 0);
            if (_markBadgeStyle == v) return;
            _markBadgeStyle = v;
            _layout();
        }

        public function setViewMode(mode:int):void
        {
            if (_disposed) return;
            if (VIEW_MODES.indexOf(mode) == -1) mode = MODE_BOTH;
            _viewMode = mode;
            _layout();
        }

        public function setLoading():void
        {
            if (_disposed) return;
            _hasXp = false; _hasMoe = false; _hasGraph = false;
            _isLoading = true;
            _layout();
        }

        public function clearData():void
        {
            if (_disposed) return;
            _hasXp = false; _hasMoe = false; _hasGraph = false;
            _battleHistory = [];
            _currentMark = NaN;
            _isLoading = false;
            _layout();
        }

        public function setVisibleState(value:Boolean):void
        {
            if (_disposed) return;
            _visibleState = value;
            this.visible = value;
            _layoutMarkBadge();
        }

        public function setPositionOffset(offset:Array):void
        {
            if (_disposed) return;
            if (offset && offset.length >= 2)
            {
                _offset[0] = int(offset[0]);
                _offset[1] = int(offset[1]);
            }
            _syncPosition();
        }

        public function setLocalization(data:Object):void
        {
            if (_disposed || !data) return;
            if (data.loading) _strLoading = String(data.loading);
            if (data.noData)  _strNoData  = String(data.noData);
            _layout();
        }

        public function updatePosition():void
        {
            if (_disposed) return;
            _syncPosition();
        }

        public function dispose():void
        {
            if (_disposed) return;
            _disposed = true;
            _teardownDragListeners();
            _clearDragTimeout();
            // Видаляємо badge з parent (Injector) якщо він туди переїхав
            if (_markBadge && _markBadge.parent != null && _markBadge.parent != this)
                _markBadge.parent.removeChild(_markBadge);
            if (_markBadgeBtn && _markBadgeBtn.parent != null && _markBadgeBtn.parent != this)
                _markBadgeBtn.parent.removeChild(_markBadgeBtn);
        }

        private function _layout():void
        {
            if (_disposed) return;
            if (_dragHit) _dragHit.visible = true;

            var showMastery:Boolean = (_viewMode == MODE_BOTH || _viewMode == MODE_MASTERY || _viewMode == MODE_BOTH_GRAPH);
            var showMarks:Boolean   = (_viewMode == MODE_BOTH || _viewMode == MODE_MARKS   || _viewMode == MODE_BOTH_GRAPH || _viewMode == MODE_MARKS_GRAPH);
            var showGraph:Boolean   = (_viewMode == MODE_BOTH_GRAPH || _viewMode == MODE_MARKS_GRAPH);

            _panelWidth = PANEL_MIN_W;
            var y:int = PAD_V;

            if (showMastery)
            {
                _layoutMasteryRow(y);
                y += ROW_HEIGHT + ROW_GAP;
            }
            else
            {
                _hideRow(_xpIcon);
                _hideRow(_xpValue);
            }

            if (showMarks)
            {
                _layoutMarksRow(y);
                y += ROW_HEIGHT + ROW_GAP;
            }
            else
            {
                _hideRow(_moePercent);
                _hideRow(_moeValue);
            }

            if (showGraph)
            {
                _layoutGraph(y + GRAPH_TOP_GAP);
                y += GRAPH_TOP_GAP + GRAPH_H + PAD_V;
            }
            else
            {
                _graphLayer.graphics.clear();
                _hideRow(_axisLabels);
                if (_markLabel) _markLabel.visible = false;
                y += PAD_V;
            }

            _panelHeight = y;
            _drawBackground();
            _redrawDragHit();
            // Expand button only makes sense when the graph is visible —
            // it opens a panel which is fundamentally a bigger version of that
            // graph + per-battle stats. In compact (no-graph) view modes the
            // button would also overlap the data rows, so we hide it there.
            if (_expandBtn != null)
            {
                _expandBtn.visible = showGraph;
                if (showGraph) _redrawExpandBtn(false);
            }
            _applyPanelBodyVisibility();
            // ВАЖЛИВО: спочатку _syncPosition щоб this.x/y були актуальні,
            // потім _layoutMarkBadge який використовує globalToLocal(this)
            _syncPosition();
            _layoutMarkBadge();
        }

        private function _applyPanelBodyVisibility():void
        {
            if (_panelBodyVisible)
            {
                if (_background) _background.visible = true;
                if (_graphLayer) _graphLayer.visible = true;
                if (_dragHit) _dragHit.visible = true;
                return;
            }
            if (_background) _background.visible = false;
            if (_graphLayer) _graphLayer.visible = false;
            if (_dragHit) _dragHit.visible = false;
            if (_expandBtn) _expandBtn.visible = false;
            if (_markLabel) _markLabel.visible = false;
            _hideRow(_xpIcon);
            _hideRow(_xpValue);
            _hideRow(_moePercent);
            _hideRow(_moeValue);
            _hideRow(_axisLabels);
        }

        private function _layoutMasteryRow(rowY:int):void
        {
            for (var i:int = 0; i < COL_COUNT; i++)
            {
                var colX:int   = PAD_H + i * (COL_WIDTH + COL_GAP);
                var valueX:int = colX + ICON_W + ICON_GAP;

                var iconTf:TextField = _xpIcon[i] as TextField;
                iconTf.visible = true;
                iconTf.htmlText = "<img src='" + ICONS[i] + "' width='" + ICON_W + "' height='" + ICON_H + "'/>";
                iconTf.x = colX;
                iconTf.y = rowY - 2;

                var xpTf:TextField = _xpValue[i] as TextField;
                xpTf.visible = true;
                xpTf.htmlText = _fmt(_xpCellText(i), FONT_SIZE_VALUE, _hasXp ? COLOR_VALUE : COLOR_DIM);
                xpTf.x = valueX;
                xpTf.y = rowY + 1;
            }
        }

        private function _layoutMarksRow(rowY:int):void
        {
            for (var i:int = 0; i < COL_COUNT; i++)
            {
                var colX:int   = PAD_H + i * (COL_WIDTH + COL_GAP);
                var valueX:int = colX + ICON_W + ICON_GAP;

                var pctTf:TextField = _moePercent[i] as TextField;
                pctTf.visible = true;
                pctTf.htmlText = _fmt(PERCENT_LABELS[i] as String, FONT_SIZE_PERCENT, COLOR_PERCENT);
                pctTf.x = colX;
                pctTf.y = rowY + 2;

                var moeTf:TextField = _moeValue[i] as TextField;
                moeTf.visible = true;
                moeTf.htmlText = _fmt(_moeCellText(i), FONT_SIZE_VALUE, _hasMoe ? COLOR_VALUE : COLOR_DIM);
                moeTf.x = valueX;
                moeTf.y = rowY + 1;
            }
        }

        private function _layoutGraph(topY:int):void
        {
            var g:Graphics = _graphLayer.graphics;
            g.clear();

            var i:int;
            var left:Number   = PAD_H + GRAPH_LEFT;
            var top:Number    = topY;
            var right:Number  = left + GRAPH_W;
            var bottom:Number = top + GRAPH_H;
            var rowStep:Number = GRAPH_H / GRAPH_ROWS;
            var colStep:Number = GRAPH_W / GRAPH_COLS;

            var values:Array = (_battleHistory && _battleHistory.length > 0) ? _battleHistory.concat() : [];
            if (values.length == 0 && !isNaN(_currentMark))
                values = [_currentMark];

            // Subtle horizontal dashed lines
            for (i = 0; i <= GRAPH_ROWS; i++)
            {
                var gy:Number = top + i * rowStep;
                if (i == GRAPH_ROWS)
                {
                    g.lineStyle(0.5, COLOR_GRID, 0.22);
                    g.moveTo(left, gy);
                    g.lineTo(right, gy);
                }
                else
                {
                    g.lineStyle(0.5, COLOR_GRID, 0.08);
                    var dashX:Number = left;
                    while (dashX + 2 < right)
                    {
                        g.moveTo(dashX, gy);
                        g.lineTo(dashX + 2, gy);
                        dashX += 5;
                    }
                }
            }
            g.lineStyle(NaN);

            if (values.length < 1)
            {
                if (_markLabel) _markLabel.visible = false;
                return;
            }

            var PILL_RESERVE:Number = 38;
            var WINDOW:int = 10;
            var AXIS_STEP:Number = 2.0;
            var AXIS_ROWS:int   = 4; // 4 intervals = 5 labels = 8% total range

            // Current value is the anchor
            var currentVal:Number = !isNaN(_currentMark) ? _currentMark : Number(values[values.length - 1]);

            // Axis: -2% below current (snapped), +6% above = 8% total
            // axisBot = floor(current/2)*2 - 2  →  e.g. 60.9% → 58%
            var axisBot:Number = Math.floor(currentVal / AXIS_STEP) * AXIS_STEP - AXIS_STEP;
            var axisTop:Number = axisBot + AXIS_ROWS * AXIS_STEP;
            // Clamp to valid range
            if (axisBot < 0)  { axisBot = 0;   axisTop = AXIS_ROWS * AXIS_STEP; }
            if (axisTop > 100) { axisTop = 100; axisBot = 100 - AXIS_ROWS * AXIS_STEP; } // 58 + 8 = 66%
            var dynRange:Number = axisTop - axisBot;

            // Collect only points within [axisBot, axisTop] from full history
            // Then take last WINDOW of those
            var inRange:Array = [];
            for (i = 0; i < values.length; i++)
            {
                var val:Number = Number(values[i]);
                if (val >= axisBot && val <= axisTop)
                    inRange.push(val);
            }
            // Always include current value
            if (inRange.length == 0)
                inRange.push(currentVal);

            // Sliding window: keep last WINDOW points
            var winValues:Array = inRange.length > WINDOW
                ? inRange.slice(inRange.length - WINDOW)
                : inRange;

            var winCount:int = winValues.length;
            var LEFT_PAD:Number = 28;
            var filtStep:Number = winCount > 1
                ? (GRAPH_W - PILL_RESERVE - LEFT_PAD) / (winCount - 1)
                : 0;

            var pts:Array = [];
            for (i = 0; i < winCount; i++)
            {
                var fv:Number = Number(winValues[i]);
                var px:Number = winCount > 1
                    ? left + LEFT_PAD + i * filtStep
                    : left + (GRAPH_W - PILL_RESERVE);
                var rawPy:Number = bottom - ((fv - axisBot) / dynRange) * GRAPH_H;
                var py:Number = Math.max(top, Math.min(bottom, rawPy));
                pts.push(new Point(px, py));
            }

            // Axis labels: spread evenly from axisBot to axisTop
            // Show only AXIS_ROWS+1 labels at 2% steps starting from axisBot
            var actualRows:int = int((axisTop - axisBot) / AXIS_STEP);
            // Pick step that gives us ~4-5 visible labels
            var labelStep:int = Math.ceil(actualRows / AXIS_ROWS);
            if (labelStep < 1) labelStep = 1;
            var labelIdx:int = 0;
            for (i = 0; i <= actualRows; i++)
            {
                if (i % labelStep != 0 && i != actualRows) continue;
                if (labelIdx >= _axisLabels.length) break;
                var axisVal:Number = axisBot + i * AXIS_STEP;
                var labelTf2:TextField = _axisLabels[_axisLabels.length - 1 - labelIdx] as TextField;
                if (labelTf2)
                {
                    labelTf2.visible = true;
                    labelTf2.htmlText = _fmt(int(Math.round(axisVal)).toString() + "%", FONT_SIZE_AXIS, COLOR_AXIS);
                    labelTf2.x = PAD_H + GRAPH_LEFT - 4;
                    labelTf2.y = bottom - (i / actualRows) * GRAPH_H - 8;
                }
                labelIdx++;
            }
            // Hide unused labels
            for (i = labelIdx; i < _axisLabels.length; i++)
            {
                var hideTf:TextField = _axisLabels[i] as TextField;
                if (hideTf) hideTf.visible = false;
            }
            if (pts.length >= 2)
            {
                g.endFill();

                // ── Area fill under curve ──
                var areaAlphas:Array  = [0.12, 0.0];
                var areaColors:Array  = [COLOR_LINE, COLOR_LINE];
                var areaRatios:Array  = [0, 255];
                var areaMatrix:Matrix = new Matrix();
                areaMatrix.createGradientBox(GRAPH_W, GRAPH_H, Math.PI / 2, left, top);
                g.beginGradientFill(GradientType.LINEAR, areaColors, areaAlphas, areaRatios, areaMatrix);
                g.moveTo(pts[0].x, pts[0].y);
                var midX:Number = (pts[0].x + pts[1].x) * 0.5;
                var midY:Number = (pts[0].y + pts[1].y) * 0.5;
                g.lineTo(midX, midY);
                for (i = 1; i < pts.length - 1; i++)
                {
                    var nextMidX:Number = (pts[i].x + pts[i+1].x) * 0.5;
                    var nextMidY:Number = (pts[i].y + pts[i+1].y) * 0.5;
                    g.curveTo(pts[i].x, pts[i].y, nextMidX, nextMidY);
                }
                g.lineTo(pts[pts.length - 1].x, pts[pts.length - 1].y);
                g.lineTo(pts[pts.length - 1].x, bottom);
                g.lineTo(pts[0].x, bottom);
                g.endFill();

                // ── Curve line ──
                g.lineStyle(1.5, COLOR_LINE, 0.95);
                g.moveTo(pts[0].x, pts[0].y);
                midX = (pts[0].x + pts[1].x) * 0.5;
                midY = (pts[0].y + pts[1].y) * 0.5;
                g.lineTo(midX, midY);
                for (i = 1; i < pts.length - 1; i++)
                {
                    nextMidX = (pts[i].x + pts[i+1].x) * 0.5;
                    nextMidY = (pts[i].y + pts[i+1].y) * 0.5;
                    g.curveTo(pts[i].x, pts[i].y, nextMidX, nextMidY);
                }
                g.lineTo(pts[pts.length - 1].x, pts[pts.length - 1].y);
                g.endFill();
                g.lineStyle(NaN);
            }

            // Intermediate dots
            for (i = 0; i < pts.length - 1; i++)
            {
                g.lineStyle(NaN);
                g.beginFill(COLOR_DOT, 0.7);
                g.drawCircle(pts[i].x, pts[i].y, 2);
                g.endFill();
            }

            // Last point — double dot (outer ring + inner fill)
            var lastPt:Point = pts[pts.length - 1] as Point;
            g.lineStyle(1, COLOR_DOT, 0.3);
            g.beginFill(0x000000, 0);
            g.drawCircle(lastPt.x, lastPt.y, 5);
            g.endFill();
            g.lineStyle(0);
            g.beginFill(COLOR_DOT, 0.95);
            g.drawCircle(lastPt.x, lastPt.y, 2.5);
            g.endFill();

            // Vertical dashed line from dot to bottom axis
            var dashH:Number = 4;
            var gapH:Number  = 3;
            var dashY:Number = lastPt.y + 4;
            g.lineStyle(0.5, COLOR_DOT, 0.2);
            while (dashY + dashH < bottom)
            {
                g.moveTo(lastPt.x, dashY);
                g.lineTo(lastPt.x, dashY + dashH);
                dashY += dashH + gapH;
            }

            // Prepare label text
            var labelVal:Number = !isNaN(_currentMark) ? _currentMark : Number(values[values.length - 1]);
            var labelStr:String = labelVal.toFixed(2) + "%";
            _markLabel.htmlText = _fmt(labelStr, FONT_SIZE_LABEL, COLOR_LABEL);

            // ── Bubble-style callout: pill sits ABOVE the dot with a small
            // triangle tail pointing down to the dot (lebwa.tv style).
            var pillPadH:Number  = 6;     // horizontal padding inside pill
            var pillPadV:Number  = 1;     // vertical padding inside pill
            var tailH:Number     = 5;     // triangle tail height
            var tailHalfW:Number = 4;     // triangle tail half-width
            var gapAboveDot:Number = 4;   // gap between dot and tail tip

            var pillW:Number = _markLabel.width + pillPadH * 2;
            var pillH:Number = _markLabel.height + pillPadV * 2;
            var pillR:Number = pillH * 0.5;

            // Tail tip points to a spot just above the dot
            var tailTipX:Number = lastPt.x;
            var tailTipY:Number = lastPt.y - gapAboveDot;

            // Pill is centered horizontally on the dot, sitting above the tail
            var pillX:Number = tailTipX - pillW * 0.5;
            var pillY:Number = tailTipY - tailH - pillH;

            // Clamp pill horizontally inside the graph area
            var minPillX:Number = left + 2;
            var maxPillX:Number = right - pillW - 2;
            if (pillX < minPillX) pillX = minPillX;
            if (pillX > maxPillX) pillX = maxPillX;

            // If pill would clip above the graph, push it below the dot instead
            var tailPointsUp:Boolean = false;
            if (pillY < top + 1)
            {
                tailPointsUp = true;
                tailTipY = lastPt.y + gapAboveDot;
                pillY = tailTipY + tailH;
                if (pillY + pillH > bottom - 1) pillY = bottom - 1 - pillH;
            }

            // Tail anchor x — where the triangle base meets the pill.
            // It tracks the dot but is clamped inside the pill body
            // (so the tail never detaches if the pill was pushed sideways).
            var tailAnchorX:Number = tailTipX;
            var tailMinX:Number = pillX + pillR + tailHalfW;
            var tailMaxX:Number = pillX + pillW - pillR - tailHalfW;
            if (tailAnchorX < tailMinX) tailAnchorX = tailMinX;
            if (tailAnchorX > tailMaxX) tailAnchorX = tailMaxX;

            // ── Draw bubble (pill + triangle tail) as one filled shape ──
            var bubbleStrokeColor:uint = 0xC8B97A;
            var bubbleStrokeAlpha:Number = 0.4;
            var bubbleFillColor:uint = 0x0A0E12;
            var bubbleFillAlpha:Number = 0.93;

            g.lineStyle(0.75, bubbleStrokeColor, bubbleStrokeAlpha);
            g.beginFill(bubbleFillColor, bubbleFillAlpha);
            g.drawRoundRect(pillX, pillY, pillW, pillH, pillR * 2, pillR * 2);
            g.endFill();

            // Triangle tail (drawn on top with same fill so the seam blends in)
            g.lineStyle(NaN);
            g.beginFill(bubbleFillColor, bubbleFillAlpha);
            if (tailPointsUp)
            {
                // Tail points up — base sits on TOP edge of pill, tip above
                var baseY1:Number = pillY;
                g.moveTo(tailAnchorX - tailHalfW, baseY1);
                g.lineTo(tailAnchorX + tailHalfW, baseY1);
                g.lineTo(tailTipX,                tailTipY);
                g.lineTo(tailAnchorX - tailHalfW, baseY1);
            }
            else
            {
                // Tail points down — base sits on BOTTOM edge of pill, tip below
                var baseY2:Number = pillY + pillH;
                g.moveTo(tailAnchorX - tailHalfW, baseY2);
                g.lineTo(tailAnchorX + tailHalfW, baseY2);
                g.lineTo(tailTipX,                tailTipY);
                g.lineTo(tailAnchorX - tailHalfW, baseY2);
            }
            g.endFill();

            // Re-stroke the two slanted edges of the tail so the bubble has
            // a consistent outline (we skip the pill-edge segment between them
            // so the seam stays invisible).
            g.lineStyle(0.75, bubbleStrokeColor, bubbleStrokeAlpha);
            if (tailPointsUp)
            {
                g.moveTo(tailAnchorX - tailHalfW, pillY);
                g.lineTo(tailTipX,                tailTipY);
                g.lineTo(tailAnchorX + tailHalfW, pillY);
            }
            else
            {
                g.moveTo(tailAnchorX - tailHalfW, pillY + pillH);
                g.lineTo(tailTipX,                tailTipY);
                g.lineTo(tailAnchorX + tailHalfW, pillY + pillH);
            }
            g.lineStyle(NaN);

            // Position the % text inside the pill
            _markLabel.x = pillX + pillPadH;
            _markLabel.y = pillY + pillPadV;
            _markLabel.visible = true;
        }

        private function _xpCellText(i:int):String
        {
            if (_isLoading) return _strLoading;
            if (!_hasXp)    return _strNoData;
            var v:int = int(_xp[i]);
            if (v <= 0)     return _strNoData;
            return _fmtNum(v);
        }

        private function _moeCellText(i:int):String
        {
            if (_isLoading) return _strLoading;
            if (!_hasMoe)   return _strNoData;
            var v:int = int(_moe[i]);
            if (v <= 0)     return _strNoData;
            return _fmtNum(v);
        }


        private function _drawBackground():void
        {
            var g:Graphics = _background.graphics;
            g.clear();

            // ── рамка в стилі lebwa: дуги по кутах + розрізи (як у мітки) ──
            var w:Number = _panelWidth, h:Number = _panelHeight;
            var inset:Number = 2.5;
            var rad:Number   = 6;
            var a:Number     = 0.55;
            var x0:Number = inset, y0:Number = inset, x1:Number = w - inset, y1:Number = h - inset;

            // заливка строго в межах рамки (щоб чорне не виступало за контур)
            g.beginFill(BG_COLOR_TOP, BG_ALPHA_TOP);
            g.drawRoundRect(x0, y0, x1 - x0, y1 - y0, rad * 2, rad * 2);
            g.endFill();

            g.lineStyle(1.2, FRAME_COLOR, a, true);

            // кутові дуги
            _bgArc(g, x0 + rad, y0 + rad, rad, 180, 270);
            _bgArc(g, x1 - rad, y0 + rad, rad, 270, 360);
            _bgArc(g, x0 + rad, y1 - rad, rad,  90, 180);
            _bgArc(g, x1 - rad, y1 - rad, rad,   0,  90);

            var tl:Number = x0 + rad, tr:Number = x1 - rad;

            // верх: розрив посередині
            var gc0:Number = tl + (tr - tl) * 0.34;
            var gc1:Number = tl + (tr - tl) * 0.66;
            g.moveTo(tl, y0);  g.lineTo(gc0, y0);
            g.moveTo(gc1, y0); g.lineTo(tr, y0);

            // низ: суцільний
            g.moveTo(tl, y1); g.lineTo(tr, y1);

            // боки: короткі розрізи
            var ftop:Number = y0 + rad, fbot:Number = y1 - rad, fh:Number = fbot - ftop;
            var gaps:Array = [0.10, 0.46, 0.66, 0.89];
            var gw:Number  = 0.05;
            _bgSide(g, x0, ftop, fbot, fh, gaps, gw);
            _bgSide(g, x1, ftop, fbot, fh, gaps, gw);

            g.lineStyle(NaN);
        }

        private function _bgArc(g:Graphics, cx:Number, cy:Number, r:Number,
                                startDeg:Number, endDeg:Number):void
        {
            var steps:int = 8;
            var a0:Number = startDeg * Math.PI / 180.0;
            var a1:Number = endDeg   * Math.PI / 180.0;
            g.moveTo(cx + Math.cos(a0) * r, cy + Math.sin(a0) * r);
            for (var i:int = 1; i <= steps; i++)
            {
                var t:Number = a0 + (a1 - a0) * (i / Number(steps));
                g.lineTo(cx + Math.cos(t) * r, cy + Math.sin(t) * r);
            }
        }

        private function _bgSide(g:Graphics, x:Number, ftop:Number, fbot:Number,
                                 fh:Number, gaps:Array, gw:Number):void
        {
            var prev:Number = ftop;
            for (var i:int = 0; i < gaps.length; i++)
            {
                var gy:Number = ftop + fh * Number(gaps[i]);
                g.moveTo(x, prev);  g.lineTo(x, gy - fh * gw / 2);
                prev = gy + fh * gw / 2;
            }
            g.moveTo(x, prev);  g.lineTo(x, fbot);
        }


        private function _createDragHit():void
        {
            _dragHit = new Sprite();
            _dragHit.buttonMode   = true;
            _dragHit.useHandCursor = true;
            addChild(_dragHit);
            _redrawDragHit();
        }

        private function _createExpandBtn():void
        {
            _expandBtn = new Sprite();
            _expandBtn.mouseEnabled  = true;
            _expandBtn.mouseChildren = false;
            _expandBtn.buttonMode    = true;
            _expandBtn.useHandCursor = true;
            _expandBtn.tabEnabled    = false;
            _expandBtn.addEventListener(MouseEvent.CLICK, _onExpandClick);
            _expandBtn.addEventListener(MouseEvent.ROLL_OVER, _onExpandRollOver);
            _expandBtn.addEventListener(MouseEvent.ROLL_OUT,  _onExpandRollOut);
            addChild(_expandBtn);
            _redrawExpandBtn(false);
        }

        private static const EXPAND_BTN_W:int = 16;
        private static const EXPAND_BTN_H:int = 14;
        private static const EXPAND_BTN_PAD:int = 4;
        private static const MARK_BADGE_BTN_W:int = 16;
        private static const MARK_BADGE_BTN_H:int = 28;
        private static const MARK_BADGE_W:int = 198;
        private static const MARK_BADGE_H:int = 86;
        private static const MARK_BADGE_H_EXP:int = 132;
        private static const MARK_BADGE_W_HTML:int = 258;
        private static const MARK_BADGE_H_HTML:int = 110;
        private static const MARK_BADGE_H_HTML_EXP:int = 164;
        private static const MARK_BADGE_PAD:int = 24;
        private static const MARK_BADGE_GAP:int = 8;

        private function _mbW():int { return _markBadgeStyle == 2 ? MARK_BADGE_W_HTML : MARK_BADGE_W; }
        private function _mbH():int { return _markBadgeStyle == 2 ? MARK_BADGE_H_HTML : MARK_BADGE_H; }
        private function _mbHExp():int { return _markBadgeStyle == 2 ? MARK_BADGE_H_HTML_EXP : MARK_BADGE_H_EXP; }
        private function _mbCurH():int { return _markBadgeExpanded ? _mbHExp() : _mbH(); }

        private function _redrawExpandBtn(hover:Boolean):void
        {
            if (!_expandBtn) return;
            var g:Graphics = _expandBtn.graphics;
            g.clear();

            // ── Position: bottom-right corner of the panel ──
            var btnX:int = _panelWidth  - EXPAND_BTN_W - EXPAND_BTN_PAD;
            var btnY:int = _panelHeight - EXPAND_BTN_H - EXPAND_BTN_PAD;
            _expandBtn.x = btnX;
            _expandBtn.y = btnY;

            // ── Hit area: full button rect (transparent) ──
            g.beginFill(0x000000, 0.001);
            g.drawRect(0, 0, EXPAND_BTN_W, EXPAND_BTN_H);
            g.endFill();

            // ── Subtle background pill (only on hover) ──
            if (hover)
            {
                g.lineStyle(0.5, 0xC8B97A, 0.4);
                g.beginFill(0x1A1F26, 0.85);
                g.drawRoundRect(0, 0, EXPAND_BTN_W, EXPAND_BTN_H, 4, 4);
                g.endFill();
                g.lineStyle(NaN);
            }

            // ── Down-pointing chevron ── (▼ style, two-line)
            var cx:Number = EXPAND_BTN_W * 0.5;
            var cy:Number = EXPAND_BTN_H * 0.5;
            var armW:Number = 4;       // half-width of chevron
            var armH:Number = 2.5;     // half-height of chevron
            var alpha:Number = hover ? 1.0 : 0.7;

            g.lineStyle(1.5, 0xFFFFFF, alpha, true);
            g.moveTo(cx - armW, cy - armH);
            g.lineTo(cx,        cy + armH);
            g.lineTo(cx + armW, cy - armH);
            g.lineStyle(NaN);
        }

        private function _onExpandClick(e:MouseEvent):void
        {
            if (_disposed) return;
            e.stopImmediatePropagation();
            dispatchEvent(new MasteryPanelEvent(MasteryPanelEvent.EXPAND_TOGGLE, null));
        }

        private function _onExpandRollOver(e:MouseEvent):void
        {
            _redrawExpandBtn(true);
        }

        private function _onExpandRollOut(e:MouseEvent):void
        {
            _redrawExpandBtn(false);
        }

        private function _createMarkBadgeBtn():void
        {
            _markBadgeBtn = new Sprite();
            _markBadgeBtn.mouseEnabled = true;
            _markBadgeBtn.mouseChildren = false;
            _markBadgeBtn.buttonMode = true;
            _markBadgeBtn.useHandCursor = true;
            _markBadgeBtn.tabEnabled = false;
            _markBadgeBtn.addEventListener(MouseEvent.CLICK, _onMarkBadgeClick);
            _markBadgeBtn.addEventListener(MouseEvent.ROLL_OVER, _onMarkBadgeRollOver);
            _markBadgeBtn.addEventListener(MouseEvent.ROLL_OUT, _onMarkBadgeRollOut);
            addChild(_markBadgeBtn);
            _redrawMarkBadgeBtn(false);
        }

        private function _createMarkBadge():void
        {
            _markBadge = new Sprite();
            _markBadge.mouseEnabled = true;
            _markBadge.mouseChildren = false;
            _markBadge.visible = false;
            _markBadgeBg = new Shape();
            _markBadge.addChild(_markBadgeBg);
            _markBadgeStyle3SimpleBg = _makeBitmap(STYLE3_LOBBY_SIMPLE_BG);
            _markBadge.addChild(_markBadgeStyle3SimpleBg);
            _markBadgeStyle3ExtraBg = _makeBitmap(STYLE3_LOBBY_EXTRA_BG);
            _markBadge.addChild(_markBadgeStyle3ExtraBg);
            _markBadgeLine = new Shape();
            _markBadge.addChild(_markBadgeLine);
            _markBadgeStars = new Shape();
            _markBadge.addChild(_markBadgeStars);
            _markBadgeStyle3Marker = _makeBitmap(STYLE3_LOBBY_MARKER);
            _markBadge.addChild(_markBadgeStyle3Marker);
            _markBadgeValue = _createBadgeText(24, COLOR_LABEL, TextFieldAutoSize.LEFT);
            _markBadgeDelta = _createBadgeText(13, COLOR_DIM, TextFieldAutoSize.LEFT);
            _markBadgeTotal = _createBadgeText(12, COLOR_DIM, TextFieldAutoSize.LEFT);
            _markBadgeDetail1 = _createBadgeText(12, COLOR_DIM, TextFieldAutoSize.LEFT);
            _markBadgeDetail2 = _createBadgeText(12, COLOR_DIM, TextFieldAutoSize.LEFT);
            _markBadge.addChild(_markBadgeValue);
            _markBadge.addChild(_markBadgeDelta);
            _markBadge.addChild(_markBadgeTotal);
            _markBadge.addChild(_markBadgeDetail1);
            _markBadge.addChild(_markBadgeDetail2);
            _markBadge.addEventListener(MouseEvent.MOUSE_DOWN, _onMarkBadgeMouseDown);
            addChild(_markBadge);
        }

        private function _createBadgeText(size:int, color:uint, autoSize:String):TextField
        {
            var tf:TextField = new TextField();
            tf.selectable = false;
            tf.mouseEnabled = false;
            tf.autoSize = autoSize;
            tf.multiline = false;
            tf.filters = [new GlowFilter(0x000000, 1.0, 4, 4, 4, 1), new DropShadowFilter(1.2, 45, 0x000000, 0.95, 3, 3, 1.6, 1)];
            tf.htmlText = _fmt("", size, color);
            return tf;
        }

        private function _layoutMarkBadge():void
        {
            if (!_markBadge) return;
            if (!_markBadgeEnabled)
            {
                _markBadge.visible = false;
                if (_markBadgeBtn) _markBadgeBtn.visible = false;
                return;
            }
            _markBadge.visible = _visibleState && _markBadgeOpen;
            if (!_markBadgeOffsetSet)
            {
                // За замовчуванням: праворуч від панелі (в глобальних координатах)
                var defaultLocalX:Number = _panelWidth + MARK_BADGE_GAP + MARK_BADGE_BTN_W;
                var defaultLocalY:Number = 0;
                var globalDefault:Point = this.localToGlobal(new Point(defaultLocalX, defaultLocalY));
                _markBadgeOffset[0] = int(globalDefault.x);
                _markBadgeOffset[1] = int(globalDefault.y);
                _markBadgeOffsetSet = true;
            }
            _clampMarkBadgeOffset();
            // Badge позиціонується у координатній системі БАТЬКА (Injector),
            // не this — тому використовуємо parent.globalToLocal.
            // Це означає що переміщення this не впливає на badge.x/y
            var targetContainer:DisplayObjectContainer = (_markBadge.parent != null) ? _markBadge.parent : this;
            var localBadge:Point = targetContainer.globalToLocal(new Point(_markBadgeOffset[0], _markBadgeOffset[1]));
            _markBadge.x = int(localBadge.x);
            _markBadge.y = int(localBadge.y);
            if (_markBadgeBtn)
            {
                _updateMarkBadgeBtnPosition();
                _redrawMarkBadgeBtn(false);
            }
            _redrawMarkBadge();
        }

        private function _updateMarkBadgeBtnPosition():void
        {
            if (!_markBadgeBtn) return;
            _markBadgeBtn.visible = _visibleState && _markBadgeEnabled && _markBadgeControlVisible;
            var btnGlobal:Point;
            if (_markBadgeOpen)
            {
                btnGlobal = new Point(
                    _markBadgeOffset[0] - MARK_BADGE_BTN_W - 3,
                    _markBadgeOffset[1] + int((_mbCurH() - MARK_BADGE_BTN_H) * 0.5)
                );
            }
            else
            {
                btnGlobal = this.localToGlobal(new Point(_panelWidth + 2, int((_panelHeight - MARK_BADGE_BTN_H) * 0.5)));
            }
            var btnContainer:DisplayObjectContainer = (_markBadgeBtn.parent != null) ? _markBadgeBtn.parent : this;
            var btnLocal:Point = btnContainer.globalToLocal(btnGlobal);
            _markBadgeBtn.x = int(btnLocal.x);
            _markBadgeBtn.y = int(btnLocal.y);
        }

        private function _redrawMarkBadgeBtn(hover:Boolean):void
        {
            if (!_markBadgeBtn) return;
            var g:Graphics = _markBadgeBtn.graphics;
            g.clear();
            g.beginFill(0x000000, 0.001);
            g.drawRect(0, 0, MARK_BADGE_BTN_W, MARK_BADGE_BTN_H);
            g.endFill();
            if (hover || _markBadgeOpen)
            {
                g.lineStyle(0.5, 0xC8B97A, 0.45);
                g.beginFill(0x1A1F26, 0.85);
                g.drawRoundRect(0, 0, MARK_BADGE_BTN_W, MARK_BADGE_BTN_H, 4, 4);
                g.endFill();
            }
            var cx:Number = MARK_BADGE_BTN_W * 0.5;
            var cy:Number = MARK_BADGE_BTN_H * 0.5;
            g.lineStyle(1.8, 0xFFFFFF, hover || _markBadgeOpen ? 1.0 : 0.72, true);
            g.moveTo(cx - 4, cy);
            g.lineTo(cx + 4, cy);
            if (!_markBadgeOpen)
            {
                g.moveTo(cx, cy - 4);
                g.lineTo(cx, cy + 4);
            }
            g.lineStyle(NaN);
        }

        private function _redrawMarkBadge():void
        {
            if (!_markBadge || !_markBadgeBg) return;
            _setMarkBadgeStyle3AssetsVisible(_markBadgeStyle == 2);
            if (_markBadgeStyle == 1)
            {
                _redrawMarkBadgeCompact();
                return;
            }
            if (_markBadgeStyle == 2)
            {
                _redrawMarkBadgeHtmlStyle();
                return;
            }
            var badgeH:int = _markBadgeExpanded ? MARK_BADGE_H_EXP : MARK_BADGE_H;
            var g:Graphics = _markBadgeBg.graphics;
            g.clear();

            g.lineStyle(0, 0x000000, 0.0);
            g.beginFill(0x05080C, 0.16);
            g.drawRoundRect(0, 0, MARK_BADGE_W, badgeH, 4, 4);
            g.endFill();
            _drawMarkBadgeFrame(g, MARK_BADGE_W, badgeH, 58);

            var mark:Number = isNaN(_currentMark) ? 0.0 : _currentMark;

            _drawBadgeStars();
            // Garage mark badge shows only current progression. No + / - delta in hangar.
            _markBadgeValue.htmlText = _fmt(_fmt2(mark) + "%", 25, COLOR_LABEL);
            _markBadgeValue.x = int(MARK_BADGE_W / 2 - _markBadgeValue.width / 2);
            _markBadgeValue.y = 22;

            _markBadgeDelta.visible = false;

            var currentDamage:int = _estimateCurrentDamage(mark);
            var targetDamage:int = _nextMoeTarget(mark);
            if (targetDamage <= 0) targetDamage = int(_moe[2] > 0 ? _moe[2] : (_moe[3] > 0 ? _moe[3] : 0));

            _drawBadgeProgress(currentDamage, targetDamage);

            _markBadgeTotal.htmlText =
                _fmt(currentDamage > 0 ? _fmtNum(currentDamage) : _strNoData, 14, COLOR_LABEL) +
                _fmt(" / " + (targetDamage > 0 ? _fmtNum(targetDamage) : _strNoData), 14, COLOR_DIM);
            // Сумарний прогрес під планкою — по центру, як в бою.
            _markBadgeTotal.x = int(MARK_BADGE_W / 2 - _markBadgeTotal.width / 2);
            _markBadgeTotal.y = 64;

            _markBadgeDetail1.htmlText = _fmt("65%", 15, COLOR_DIM) + " " +
                _fmt(_moe[0] > 0 ? _fmtNum(int(_moe[0])) : _strNoData, 15, COLOR_LABEL) +
                _fmt("   85%", 15, COLOR_DIM) + " " +
                _fmt(_moe[1] > 0 ? _fmtNum(int(_moe[1])) : _strNoData, 15, COLOR_LABEL);
            _markBadgeDetail1.x = int(MARK_BADGE_W / 2 - _markBadgeDetail1.width / 2);
            _markBadgeDetail1.y = 88;
            _markBadgeDetail1.visible = _markBadgeExpanded;

            _markBadgeDetail2.htmlText = _fmt("95%", 15, COLOR_DIM) + " " +
                _fmt(_moe[2] > 0 ? _fmtNum(int(_moe[2])) : _strNoData, 15, COLOR_LABEL) +
                _fmt("   100%", 15, COLOR_DIM) + " " +
                _fmt(_moe[3] > 0 ? _fmtNum(int(_moe[3])) : _strNoData, 15, COLOR_LABEL);
            _markBadgeDetail2.x = int(MARK_BADGE_W / 2 - _markBadgeDetail2.width / 2);
            _markBadgeDetail2.y = 108;
            _markBadgeDetail2.visible = _markBadgeExpanded;
        }

        private function _redrawMarkBadgeCompact():void
        {
            var badgeW:int = MARK_BADGE_W;
            var badgeH:int = _markBadgeExpanded ? MARK_BADGE_H_EXP : MARK_BADGE_H;
            var g:Graphics = _markBadgeBg.graphics;
            g.clear();
            g.lineStyle(0, 0x000000, 0.0);
            g.beginFill(0x05080C, 0.16);
            g.drawRoundRect(0, 0, badgeW, badgeH, 4, 4);
            g.endFill();
            _drawMarkBadgeFrameCompact(g, badgeW, badgeH, 56);

            var mark:Number = isNaN(_currentMark) ? 0.0 : _currentMark;
            var filled:int = _markStars >= 0 ? _markStars :
                (mark >= 95 ? 3 : (mark >= 85 ? 2 : (mark >= 65 ? 1 : 0)));

            // ── зірки + смужки зліва ──
            var sg:Graphics = _markBadgeStars.graphics;
            sg.clear();
            var starX:int = 14;
            var starYs:Array = [68, 46, 24];
            var i:int;
            for (i = 0; i < 3; i++)
            {
                sg.lineStyle(NaN);
                sg.beginFill(i < filled ? 0xFFFFFF : 0x27313C, 1.0);
                _starPath(sg, starX, Number(starYs[i]), 7, 3);
                sg.endFill();
            }
            var barXcol:Number = 30;
            var slots:Array = [[58, 72], [36, 50], [14, 28]];
            for (i = 0; i < 3; i++)
            {
                var on:Boolean = i < filled;
                sg.lineStyle(3, 0xFFFFFF, on ? 0.95 : 0.22);
                sg.moveTo(barXcol, Number(slots[i][1]));
                sg.lineTo(barXcol, Number(slots[i][0]));
            }
            sg.lineStyle(NaN);

            var contentX:int = 44;
            var contentR:int = badgeW - 12;
            var barMidX:Number = (contentX + contentR) * 0.5;
            var dimWhite:uint = 0xCED6DE;

            var currentDamage:int = _estimateCurrentDamage(mark);
            var targetDamage:int = _nextMoeTarget(mark);
            if (targetDamage <= 0) targetDamage = int(_moe[2] > 0 ? _moe[2] : (_moe[3] > 0 ? _moe[3] : 0));

            // ── число % ПО ЦЕНТРУ (над баром) ──
            _markBadgeValue.htmlText = _fmt(_fmt2(mark) + "%", 21, COLOR_LABEL);
            _markBadgeValue.x = int(barMidX - _markBadgeValue.width / 2);
            _markBadgeValue.y = 18;

            // квадратний бар
            _drawBadgeProgressSquare(currentDamage, targetDamage, contentX, contentR - contentX, 56);

            // підпис "Сум. урон" зліва (reuse delta field)
            _markBadgeDelta.htmlText = _fmt(_strSumLabel(), 12, dimWhite);
            _markBadgeDelta.x = contentX;
            _markBadgeDelta.y = 66;
            _markBadgeDelta.visible = true;

            // ── цифри урону справа (щоб не налазили на підпис) ──
            _markBadgeTotal.htmlText = _fmt(
                (currentDamage > 0 ? _fmtNum(currentDamage) : _strNoData) + " / " +
                (targetDamage > 0 ? _fmtNum(targetDamage) : _strNoData), 12, dimWhite);
            _markBadgeTotal.x = int(contentR - _markBadgeTotal.width);
            _markBadgeTotal.y = 66;

            // ── expanded (Alt): пороги MoE ──
            _markBadgeDetail1.htmlText = _fmt("65%", 15, COLOR_DIM) + " " +
                _fmt(_moe[0] > 0 ? _fmtNum(int(_moe[0])) : _strNoData, 15, COLOR_LABEL) +
                _fmt("   85%", 15, COLOR_DIM) + " " +
                _fmt(_moe[1] > 0 ? _fmtNum(int(_moe[1])) : _strNoData, 15, COLOR_LABEL);
            _markBadgeDetail1.x = int(badgeW / 2 - _markBadgeDetail1.width / 2);
            _markBadgeDetail1.y = 84;
            _markBadgeDetail1.visible = _markBadgeExpanded;

            _markBadgeDetail2.htmlText = _fmt("95%", 15, COLOR_DIM) + " " +
                _fmt(_moe[2] > 0 ? _fmtNum(int(_moe[2])) : _strNoData, 15, COLOR_LABEL) +
                _fmt("   100%", 15, COLOR_DIM) + " " +
                _fmt(_moe[3] > 0 ? _fmtNum(int(_moe[3])) : _strNoData, 15, COLOR_LABEL);
            _markBadgeDetail2.x = int(badgeW / 2 - _markBadgeDetail2.width / 2);
            _markBadgeDetail2.y = 106;
            _markBadgeDetail2.visible = _markBadgeExpanded;
        }

        private function _redrawMarkBadgeHtmlStyle():void
        {
            var badgeW:int = MARK_BADGE_W_HTML;
            var badgeH:int = _markBadgeExpanded ? MARK_BADGE_H_HTML_EXP : MARK_BADGE_H_HTML;
            var g:Graphics = _markBadgeBg.graphics;
            g.clear();
            _markBadgeStyle3SimpleBg.x = 20;
            _markBadgeStyle3SimpleBg.y = 32;
            _markBadgeStyle3ExtraBg.x = 20;
            _markBadgeStyle3ExtraBg.y = 32;
            _markBadgeStyle3SimpleBg.visible = !_markBadgeExpanded;
            _markBadgeStyle3ExtraBg.visible = _markBadgeExpanded;
            _markBadgeStyle3Marker.x = 161.15;
            _markBadgeStyle3Marker.y = 62;

            var mark:Number = isNaN(_currentMark) ? 0.0 : _currentMark;
            var filled:int = _markStars >= 0 ? _markStars :
                (mark >= 95 ? 3 : (mark >= 85 ? 2 : (mark >= 65 ? 1 : 0)));

            var sg:Graphics = _markBadgeStars.graphics;
            sg.clear();
            for (var i:int = 0; i < 3; i++)
            {
                sg.lineStyle(NaN);
                sg.beginFill(i < filled ? 0xFFFFFF : 0x303946, 1.0);
                _starPath(sg, 177 + i * 17, 51, 7, 3);
                sg.endFill();
            }

            _markBadgeDelta.htmlText = _fmt("\u041e\u0422\u041b\u0418\u0427\u0418\u0422\u0415\u041b\u042c\u041d\u042b\u0415 \u041e\u0422\u041c\u0415\u0422\u041a\u0418", 12, 0xFFEEC9);
            _markBadgeDelta.x = 48;
            _markBadgeDelta.y = 20;
            _markBadgeDelta.visible = true;

            _markBadgeValue.htmlText = _fmt(_fmt2(mark) + "%", 20, COLOR_LABEL);
            _markBadgeValue.x = 65;
            _markBadgeValue.y = 37;


            var currentDamage:int = _estimateCurrentDamage(mark);
            var targetDamage:int = _nextMoeTarget(mark);
            if (targetDamage <= 0) targetDamage = int(_moe[2] > 0 ? _moe[2] : (_moe[3] > 0 ? _moe[3] : 0));
            _drawBadgeProgressSquare(currentDamage, targetDamage, 68, 150, 72, 3.0);

            _markBadgeTotal.htmlText = _fmt(_strSumLabel() + "    " + (currentDamage > 0 ? _fmtNum(currentDamage) : _strNoData), 14, 0xFFEEC9);
            _markBadgeTotal.x = 65;
            _markBadgeTotal.y = 81;

            _markBadgeDetail1.htmlText =
                _fmt("65%  ", 13, COLOR_LABEL) + _fmt(_moe[0] > 0 ? _fmtNum(int(_moe[0])) : _strNoData, 13, COLOR_DIM) +
                _fmt("     85%  ", 13, COLOR_LABEL) + _fmt(_moe[1] > 0 ? _fmtNum(int(_moe[1])) : _strNoData, 13, COLOR_DIM);
            _markBadgeDetail1.x = 65;
            _markBadgeDetail1.y = 116;
            _markBadgeDetail1.visible = _markBadgeExpanded;

            _markBadgeDetail2.htmlText =
                _fmt("95%  ", 13, COLOR_LABEL) + _fmt(_moe[2] > 0 ? _fmtNum(int(_moe[2])) : _strNoData, 13, COLOR_DIM) +
                _fmt("   100%  ", 13, COLOR_LABEL) + _fmt(_moe[3] > 0 ? _fmtNum(int(_moe[3])) : _strNoData, 13, COLOR_DIM);
            _markBadgeDetail2.x = 65;
            _markBadgeDetail2.y = 136;
            _markBadgeDetail2.visible = _markBadgeExpanded;

            if (_markBadgeExpanded)
            {
                _markBadgeDetail2.htmlText = _markBadgeDetail2.htmlText +
                    _fmt("   next " + _nextMoePct(mark) + "% " + (targetDamage > 0 ? _fmtNum(targetDamage) : _strNoData), 13, COLOR_GOLD);
            }
        }

        private function _makeBitmap(asset:Class):Bitmap
        {
            var bmp:Bitmap = new asset() as Bitmap;
            bmp.smoothing = false;
            bmp.visible = false;
            return bmp;
        }

        private function _setMarkBadgeStyle3AssetsVisible(value:Boolean):void
        {
            if (_markBadgeStyle3SimpleBg) _markBadgeStyle3SimpleBg.visible = value && !_markBadgeExpanded;
            if (_markBadgeStyle3ExtraBg) _markBadgeStyle3ExtraBg.visible = value && _markBadgeExpanded;
            if (_markBadgeStyle3Marker) _markBadgeStyle3Marker.visible = value;
        }

        private function _drawMarkBadgeFrameCompact(g:Graphics, w:Number, h:Number, barY:Number):void
        {
            var inset:Number   = 3.0;
            var rad:Number     = 6;
            var lineColor:uint = 0xC9D2DC;
            var a:Number       = 0.46;
            var x0:Number = inset, y0:Number = inset, x1:Number = w - inset, y1:Number = h - inset;
            g.lineStyle(0.9, lineColor, a, true);
            _bgArc(g, x0 + rad, y0 + rad, rad, 180, 270);
            _bgArc(g, x1 - rad, y0 + rad, rad, 270, 360);
            _bgArc(g, x0 + rad, y1 - rad, rad,  90, 180);
            _bgArc(g, x1 - rad, y1 - rad, rad,   0,  90);
            var tl:Number = x0 + rad, tr:Number = x1 - rad;
            g.moveTo(tl, y0); g.lineTo(tr, y0);
            g.moveTo(tl, y1); g.lineTo(tr, y1);
            var ftop:Number = y0 + rad, fbot:Number = y1 - rad, fh:Number = fbot - ftop;
            var gaps:Array = [0.10, 0.46, 0.66, 0.89];
            var gw:Number  = 0.05;
            _bgSide(g, x0, ftop, fbot, fh, gaps, gw);
            _bgSide(g, x1, ftop, fbot, fh, gaps, gw);
            g.lineStyle(NaN);
        }

        private function _strSumLabel():String
        {
            return "\u0421\u0443\u043c. \u0443\u0440\u043e\u043d"; // "Сум. урон"
        }

        private function _drawBadgeProgressSquare(currentDamage:int, targetDamage:int,
                                                  x0:Number, w:Number, yPos:Number,
                                                  barH:Number = 6.0):void
        {
            var g:Graphics = _markBadgeLine.graphics;
            g.clear();
            var pct:Number = targetDamage > 0
                ? Math.max(0.0, Math.min(1.0, Number(currentDamage) / Number(targetDamage)))
                : 0.0;
            var top:Number  = yPos - barH / 2;

            g.lineStyle(1.4, 0x0A0E14, 1.0);
            g.beginFill(0x16202A, 1.0);
            g.drawRect(x0, top, w, barH);
            g.endFill();
            g.lineStyle(NaN);

            if (pct > 0)
            {
                g.beginFill(0xFFFFFF, 0.88);
                g.drawRect(x0, top, w * pct, barH);
                g.endFill();
            }
        }

        private function _nextMoeTarget(mark:Number):int
        {
            if (mark < 65.0) return int(_moe[0]);
            if (mark < 85.0) return int(_moe[1]);
            if (mark < 95.0) return int(_moe[2]);
            return int(_moe[3]);
        }

        private function _nextMoePct(mark:Number):int
        {
            if (mark < 65.0) return 65;
            if (mark < 85.0) return 85;
            if (mark < 95.0) return 95;
            return 100;
        }

        private function _estimateCurrentDamage(mark:Number):int
        {
            if (!_hasMoe || isNaN(mark)) return 0;
            var points:Array = [
                { pct: 65.0, value: Number(_moe[0]) },
                { pct: 85.0, value: Number(_moe[1]) },
                { pct: 95.0, value: Number(_moe[2]) },
                { pct: 100.0, value: Number(_moe[3]) }
            ];
            var i:int;
            var prevPct:Number = 0.0;
            var prevValue:Number = 0.0;
            for (i = 0; i < points.length; i++)
            {
                var nextPct:Number = Number(points[i].pct);
                var nextValue:Number = Number(points[i].value);
                if (nextValue <= 0) continue;
                if (mark <= nextPct)
                {
                    var span:Number = nextPct - prevPct;
                    if (span <= 0.0) return int(Math.round(nextValue));
                    var t:Number = Math.max(0.0, Math.min(1.0, (mark - prevPct) / span));
                    return int(Math.round(prevValue + (nextValue - prevValue) * t));
                }
                prevPct = nextPct;
                prevValue = nextValue;
            }
            return int(Math.round(prevValue));
        }

        private function _clampMarkBadgeOffset():void
        {
            if (!stage) return;
            // Не клампаємо якщо stage ще не готовий
            if (stage.stageWidth <= 0 || stage.stageHeight <= 0) return;
            var badgeH:int = _mbCurH();
            // Координати offset глобальні — клампаємо відносно stage
            var minX:Number = BOUNDARY_GAP;
            var minY:Number = BOUNDARY_GAP;
            var maxX:Number = stage.stageWidth  - BOUNDARY_GAP - _mbW();
            var maxY:Number = stage.stageHeight - BOUNDARY_GAP - badgeH;
            if (maxX < minX) maxX = minX;
            if (maxY < minY) maxY = minY;
            if (_markBadgeOffset[0] < minX) _markBadgeOffset[0] = minX;
            if (_markBadgeOffset[0] > maxX) _markBadgeOffset[0] = maxX;
            if (_markBadgeOffset[1] < minY) _markBadgeOffset[1] = minY;
            if (_markBadgeOffset[1] > maxY) _markBadgeOffset[1] = maxY;
        }

        private function _drawBadgeStars():void
        {
            var g:Graphics = _markBadgeStars.graphics;
            g.clear();
            var filled:int = _markStars >= 0 ? _markStars :
                (_currentMark >= 95 ? 3 : (_currentMark >= 85 ? 2 : (_currentMark >= 65 ? 1 : 0)));
            var starSpacing:int = 22;
            var starTotalW:int = 3 * starSpacing;
            var starStartX:int = int(MARK_BADGE_W / 2 - starTotalW / 2 + starSpacing / 2);
            for (var i:int = 0; i < 3; i++)
            {
                g.lineStyle(NaN);
                g.beginFill(i < filled ? 0xFFFFFF : 0x27313C, 1.0);
                _starPath(g, starStartX + i * starSpacing, 13, 8, 3.4);
                g.endFill();
            }
        }

        private function _drawBadgeProgress(currentDamage:int, targetDamage:int):void
        {
            var g:Graphics = _markBadgeLine.graphics;
            g.clear();
            var x:Number = MARK_BADGE_PAD;
            var y:Number = 58;
            var w:Number = MARK_BADGE_W - MARK_BADGE_PAD * 2;
            var pct:Number = targetDamage > 0
                ? Math.max(0.0, Math.min(1.0, Number(currentDamage) / Number(targetDamage)))
                : 0.0;

            // Capsule with fixed dark outline + rounded ends
            var barH:Number = 6.0;
            var top:Number  = y - barH / 2;

            g.lineStyle(1.4, 0x0A0E14, 1.0);
            g.beginFill(0x16202A, 1.0);
            g.drawRoundRect(x, top, w, barH, barH, barH);
            g.endFill();
            g.lineStyle(NaN);

            // Fill — біла (ангар нейтральний, без виграш/програш)
            if (pct > 0)
            {
                g.beginFill(0xFFFFFF, 0.88);
                g.drawRoundRect(x, top, Math.max(barH, w * pct), barH, barH, barH);
                g.endFill();
            }

            // Knob — білий кружок з темною обводкою
            g.lineStyle(1.4, 0x000000, 0.60);
            g.beginFill(0xFFFFFF, 0.95);
            g.drawCircle(x + w * pct, y, 4.5);
            g.endFill();
            g.lineStyle(NaN);
        }

        private function _drawMarkBadgeFrame(g:Graphics, w:Number, h:Number, barY:Number):void
        {
            var inset:Number   = 3.0;
            var rad:Number     = 6;
            var pad:Number     = MARK_BADGE_PAD;
            var lineColor:uint = 0xC9D2DC;
            var a:Number       = 0.46;
            var x0:Number = inset, y0:Number = inset, x1:Number = w - inset, y1:Number = h - inset;

            g.lineStyle(0.9, lineColor, a, true);

            // ── кутові дуги ──
            _arcSeg(g, x0 + rad, y0 + rad, rad, 180, 270);
            _arcSeg(g, x1 - rad, y0 + rad, rad, 270, 360);
            _arcSeg(g, x0 + rad, y1 - rad, rad,  90, 180);
            _arcSeg(g, x1 - rad, y1 - rad, rad,   0,  90);

            var tl:Number = x0 + rad, tr:Number = x1 - rad;

            // ── верх: розрив посередині ──
            var gc0:Number = tl + (tr - tl) * 0.34;
            var gc1:Number = tl + (tr - tl) * 0.66;
            g.moveTo(tl, y0);  g.lineTo(gc0, y0);
            g.moveTo(gc1, y0); g.lineTo(tr, y0);

            // ── низ: суцільний ──
            g.moveTo(tl, y1); g.lineTo(tr, y1);

            // ── боки: короткі розрізи ──
            var ftop:Number = y0 + rad, fbot:Number = y1 - rad, fh:Number = fbot - ftop;
            var gaps:Array = [0.10, 0.46, 0.66, 0.89];
            var gw:Number  = 0.05;
            _sideEdge(g, x0, ftop, fbot, fh, gaps, gw);
            _sideEdge(g, x1, ftop, fbot, fh, gaps, gw);

            // ── бічні конектори: від краю до бара (короткі) ──
            g.moveTo(x0, barY);                      g.lineTo((x0 + pad - 3) / 2, barY);
            g.moveTo((x1 + w - pad + 3) / 2, barY);  g.lineTo(x1, barY);

            g.lineStyle(NaN);
        }

        private function _arcSeg(g:Graphics, cx:Number, cy:Number, r:Number,
                                 startDeg:Number, endDeg:Number):void
        {
            var steps:int = 8;
            var a0:Number = startDeg * Math.PI / 180.0;
            var a1:Number = endDeg   * Math.PI / 180.0;
            g.moveTo(cx + Math.cos(a0) * r, cy + Math.sin(a0) * r);
            for (var i:int = 1; i <= steps; i++)
            {
                var t:Number = a0 + (a1 - a0) * (i / Number(steps));
                g.lineTo(cx + Math.cos(t) * r, cy + Math.sin(t) * r);
            }
        }

        private function _sideEdge(g:Graphics, x:Number, ftop:Number, fbot:Number,
                                   fh:Number, gaps:Array, gw:Number):void
        {
            var prev:Number = ftop;
            for (var i:int = 0; i < gaps.length; i++)
            {
                var gy:Number = ftop + fh * Number(gaps[i]);
                g.moveTo(x, prev);  g.lineTo(x, gy - fh * gw / 2);
                prev = gy + fh * gw / 2;
            }
            g.moveTo(x, prev);  g.lineTo(x, fbot);
        }

        private function _onMarkBadgeClick(e:MouseEvent):void
        {
            if (_disposed || !_markBadgeEnabled) return;
            e.stopImmediatePropagation();
            _markBadgeOpen = !_markBadgeOpen;
            _layout();
            dispatchEvent(new MasteryPanelEvent(MasteryPanelEvent.MARK_BADGE_TOGGLE, _markBadgeOpen));
        }

        private function _onMarkBadgeRollOver(e:MouseEvent):void { _redrawMarkBadgeBtn(true); }
        private function _onMarkBadgeRollOut(e:MouseEvent):void  { _redrawMarkBadgeBtn(false); }

        private function _onAddedToStage(e:Event):void
        {
            removeEventListener(Event.ADDED_TO_STAGE, _onAddedToStage);
            if (stage)
            {
                stage.addEventListener(KeyboardEvent.KEY_DOWN, _onKeyDown);
                stage.addEventListener(KeyboardEvent.KEY_UP, _onKeyUp);
            }
            // Badge lives in the injector layer so it can be dragged freely.
            // Кнопку теж переносимо в injector-шар, щоб при відкритій мітці
            // вона жила разом з міткою, а не рухалась з панеллю Masters.
            if (parent != null)
            {
                if (_markBadge && _markBadge.parent == this)
                {
                    removeChild(_markBadge);
                    parent.addChild(_markBadge);
                }
                if (_markBadgeBtn && _markBadgeBtn.parent == this)
                {
                    removeChild(_markBadgeBtn);
                    parent.addChild(_markBadgeBtn);
                }
            }
        }

        private function _onKeyDown(e:KeyboardEvent):void
        {
            if (e.keyCode == Keyboard.ALTERNATE && !_markBadgeExpanded)
            {
                _markBadgeExpanded = true;
                _redrawMarkBadge(); // тільки перемальовуємо, не чіпаємо position
            }
        }

        private function _onKeyUp(e:KeyboardEvent):void
        {
            if (e.keyCode == Keyboard.ALTERNATE && _markBadgeExpanded)
            {
                _markBadgeExpanded = false;
                _redrawMarkBadge(); // тільки перемальовуємо
            }
        }

        private function _onMarkBadgeMouseDown(e:MouseEvent):void
        {
            if (_disposed || !_markBadgeEnabled || !_markBadgeOpen || !stage) return;
            e.stopImmediatePropagation();
            _isBadgeDragging = true;
            // offset зберігається в глобальних координатах
            _badgeDragOffset.x = _markBadgeOffset[0] - stage.mouseX;
            _badgeDragOffset.y = _markBadgeOffset[1] - stage.mouseY;
            stage.addEventListener(MouseEvent.MOUSE_MOVE, _onMarkBadgeMouseMove);
            stage.addEventListener(MouseEvent.MOUSE_UP, _onMarkBadgeMouseUp);
        }

        private function _onMarkBadgeMouseMove(e:MouseEvent):void
        {
            if (!_isBadgeDragging || !stage) return;
            // Зберігаємо глобальні координати
            _markBadgeOffset[0] = int(stage.mouseX + _badgeDragOffset.x);
            _markBadgeOffset[1] = int(stage.mouseY + _badgeDragOffset.y);
            _clampMarkBadgeOffset();
            _markBadgeOffsetSet = true;
            // Тільки перелейаут бейджа+кнопки (не всієї панелі) —
            // інакше кнопка "<" стрибає й відстає під час перетягування.
            _layoutMarkBadge();
        }

        private function _onMarkBadgeMouseUp(e:MouseEvent):void
        {
            _isBadgeDragging = false;
            if (stage)
            {
                stage.removeEventListener(MouseEvent.MOUSE_MOVE, _onMarkBadgeMouseMove);
                stage.removeEventListener(MouseEvent.MOUSE_UP, _onMarkBadgeMouseUp);
            }
            dispatchEvent(new MasteryPanelEvent(MasteryPanelEvent.MARK_BADGE_OFFSET_CHANGED, _markBadgeOffset));
        }

        private function _redrawDragHit():void
        {
            if (!_dragHit) return;
            _dragHit.graphics.clear();
            _dragHit.graphics.beginFill(0x000000, 0.0);
            _dragHit.graphics.drawRect(0, 0, _panelWidth, _panelHeight);
            _dragHit.graphics.endFill();
        }

        private function _setupDragListeners():void
        {
            if (!_dragHit) return;
            _dragHit.addEventListener(MouseEvent.MOUSE_DOWN, _onDragMouseDown);
        }

        private function _teardownDragListeners():void
        {
            if (_dragHit) _dragHit.removeEventListener(MouseEvent.MOUSE_DOWN, _onDragMouseDown);
            if (_expandBtn)
            {
                _expandBtn.removeEventListener(MouseEvent.CLICK,     _onExpandClick);
                _expandBtn.removeEventListener(MouseEvent.ROLL_OVER, _onExpandRollOver);
                _expandBtn.removeEventListener(MouseEvent.ROLL_OUT,  _onExpandRollOut);
            }
            if (_markBadgeBtn)
            {
                _markBadgeBtn.removeEventListener(MouseEvent.CLICK,     _onMarkBadgeClick);
                _markBadgeBtn.removeEventListener(MouseEvent.ROLL_OVER, _onMarkBadgeRollOver);
                _markBadgeBtn.removeEventListener(MouseEvent.ROLL_OUT,  _onMarkBadgeRollOut);
            }
            if (_markBadge)
                _markBadge.removeEventListener(MouseEvent.MOUSE_DOWN, _onMarkBadgeMouseDown);
            if (stage)
            {
                stage.removeEventListener(MouseEvent.MOUSE_MOVE, _onMarkBadgeMouseMove);
                stage.removeEventListener(MouseEvent.MOUSE_UP, _onMarkBadgeMouseUp);
                stage.removeEventListener(KeyboardEvent.KEY_DOWN, _onKeyDown);
                stage.removeEventListener(KeyboardEvent.KEY_UP, _onKeyUp);
            }
            removeEventListener(Event.ADDED_TO_STAGE, _onAddedToStage);
            _removeStageListeners();
        }

        private function _addStageListeners():void
        {
            if (stage)
            {
                stage.addEventListener(MouseEvent.MOUSE_UP,   _onDragMouseUp);
                stage.addEventListener(MouseEvent.MOUSE_MOVE, _onDragMouseMove);
            }
        }

        private function _removeStageListeners():void
        {
            if (stage)
            {
                stage.removeEventListener(MouseEvent.MOUSE_UP,   _onDragMouseUp);
                stage.removeEventListener(MouseEvent.MOUSE_MOVE, _onDragMouseMove);
            }
        }

        private function _clearDragTimeout():void
        {
            if (_dragTimeout != 0) { clearTimeout(_dragTimeout); _dragTimeout = 0; }
        }

        private function _onDragMouseDown(e:MouseEvent):void
        {
            if (_disposed || !stage) return;
            // Ignore mouseDown that originated inside the expand button —
            // it has its own click handler which opens the detail panel.
            if (_expandBtn != null && _expandBtn.visible)
            {
                var localX:Number = e.stageX - this.x;
                var localY:Number = e.stageY - this.y;
                if (localX >= _expandBtn.x && localX <= _expandBtn.x + EXPAND_BTN_W
                 && localY >= _expandBtn.y && localY <= _expandBtn.y + EXPAND_BTN_H)
                {
                    return;
                }
            }
            if (_markBadgeBtn != null)
            {
                var btnLocalX:Number = e.stageX - this.x;
                var btnLocalY:Number = e.stageY - this.y;
                if (btnLocalX >= _markBadgeBtn.x && btnLocalX <= _markBadgeBtn.x + MARK_BADGE_BTN_W
                 && btnLocalY >= _markBadgeBtn.y && btnLocalY <= _markBadgeBtn.y + MARK_BADGE_BTN_H)
                {
                    return;
                }
            }
            _clickPoint.x  = stage.mouseX;
            _clickPoint.y  = stage.mouseY;
            _clickOffset.x = this.x - _clickPoint.x;
            _clickOffset.y = this.y - _clickPoint.y;
            _isDragTest = true;
            _clearDragTimeout();
            _dragTimeout = setTimeout(_beginDrag, DRAG_DELAY);
            _addStageListeners();
        }

        private function _beginDrag():void
        {
            _isDragTest  = false;
            _isDragging  = true;
            _dragTimeout = 0;
        }

        private function _onDragMouseMove(e:MouseEvent):void
        {
            if (_disposed || !stage) return;
            if (!_isDragging && _isDragTest)
            {
                var dx:Number = stage.mouseX - _clickPoint.x;
                var dy:Number = stage.mouseY - _clickPoint.y;
                if (dx * dx + dy * dy > DRAG_THRESHOLD * DRAG_THRESHOLD)
                {
                    _clearDragTimeout();
                    _beginDrag();
                    return;
                }
            }
            if (_isDragging)
            {
                _clampToScreen(_clickOffset.x + stage.mouseX, _clickOffset.y + stage.mouseY);
                this.x = _reusablePoint.x;
                this.y = _reusablePoint.y;
                // Кнопка "<"/">" живе в injector-шарі. У згорнутому стані вона
                // має триматись біля панелі (яку тягнемо), тож перераховуємо її
                // позицію на кожному кроці драгу. У відкритому стані вона
                // прив'язана до офсету мітки й лишається на місці.
                _updateMarkBadgeBtnPosition();
            }
        }

        private function _onDragMouseUp(e:MouseEvent):void
        {
            var distSq:Number = (stage.mouseX - _clickPoint.x) * (stage.mouseX - _clickPoint.x)
                              + (stage.mouseY - _clickPoint.y) * (stage.mouseY - _clickPoint.y);
            _clearDragTimeout();
            if (_isDragging)
            {
                _offset[0] = int(this.x);
                _offset[1] = int(this.y);
                dispatchEvent(new MasteryPanelEvent(MasteryPanelEvent.OFFSET_CHANGED, _offset));
            }
            else if (_isDragTest && distSq <= CLICK_THRESHOLD * CLICK_THRESHOLD)
            {
                _cycleViewMode();
            }
            _isDragTest = false;
            _isDragging = false;
            _removeStageListeners();
        }

        private function _cycleViewMode():void
        {
            var idx:int = VIEW_MODES.indexOf(_viewMode);
            if (idx < 0) idx = 0;
            idx = (idx + 1) % VIEW_MODES.length;
            _viewMode = int(VIEW_MODES[idx]);
            _layout();
            dispatchEvent(new MasteryPanelEvent(MasteryPanelEvent.VIEW_MODE_CHANGED, _viewMode));
        }

        private function _clampToScreen(px:Number, py:Number):void
        {
            var sw:int = (stage != null && stage.stageWidth  > 0) ? stage.stageWidth  : 1920;
            var sh:int = (stage != null && stage.stageHeight > 0) ? stage.stageHeight : 1080;
            var totalW:int = _panelWidth + (_markBadgeOpen ? (MARK_BADGE_BTN_W + MARK_BADGE_GAP + _mbW()) : MARK_BADGE_BTN_W);
            _reusablePoint.x = int(Math.max(BOUNDARY_GAP, Math.min(sw - totalW - BOUNDARY_GAP, px)));
            _reusablePoint.y = int(Math.max(BOUNDARY_GAP, Math.min(sh - _panelHeight - BOUNDARY_GAP, py)));
        }

        private function _syncPosition():void
        {
            if (_isDragging || _disposed) return;
            _clampToScreen(_offset[0], _offset[1]);
            this.x = _reusablePoint.x;
            this.y = _reusablePoint.y;
        }

        private function _createRowFields(count:int, autoSize:String, fontSize:int):Array
        {
            var arr:Array = [];
            for (var i:int = 0; i < count; i++)
            {
                var tf:TextField = new TextField();
                tf.selectable   = false;
                tf.mouseEnabled  = false;
                tf.autoSize      = autoSize;
                tf.multiline     = false;
                tf.filters       = [_textShadow];
                addChild(tf);
                arr.push(tf);
            }
            return arr;
        }

        private function _hideRow(arr:Array):void
        {
            for (var i:int = 0; i < arr.length; i++)
                TextField(arr[i]).visible = false;
        }

        private function _fmt(text:String, size:int, color:uint):String
        {
            return '<font face="' + FONT_FACE + '" size="' + size + '" color="' + _hex(color) + '"><b>' + text + '</b></font>';
        }

        private static function _hex(color:uint):String
        {
            var h:String = color.toString(16).toUpperCase();
            while (h.length < 6) h = "0" + h;
            return "#" + h;
        }

        private static function _fmt2(value:Number):String
        {
            if (isNaN(value)) return "0.00";
            var sign:String = "";
            var v:Number = value;
            if (v < 0) { sign = "-"; v = -v; }
            var rounded:Number = Math.round(v * 100) / 100;
            var intPart:int = int(rounded);
            var frac:int = int(Math.round((rounded - intPart) * 100));
            var fracStr:String = String(frac);
            if (fracStr.length < 2) fracStr = "0" + fracStr;
            return sign + intPart.toString() + "." + fracStr;
        }

        private static function _starPath(g:Graphics, cx:Number, cy:Number,
                                          rOuter:Number, rInner:Number):void
        {
            var pts:int = 5;
            var startA:Number = -Math.PI * 0.5;
            var step:Number = Math.PI / pts;
            for (var i:int = 0; i < pts * 2; i++)
            {
                var r:Number = (i % 2 == 0) ? rOuter : rInner;
                var a:Number = startA + i * step;
                var px:Number = cx + Math.cos(a) * r;
                var py:Number = cy + Math.sin(a) * r;
                if (i == 0) g.moveTo(px, py);
                else g.lineTo(px, py);
            }
            g.lineTo(cx + Math.cos(startA) * rOuter, cy + Math.sin(startA) * rOuter);
        }

        private function _fmtNum(value:int):String
        {
            var neg:Boolean = value < 0;
            var abs:int     = neg ? -value : value;
            var s:String    = String(abs);
            var result:String = "";
            var count:int   = 0;
            for (var i:int = s.length - 1; i >= 0; i--)
            {
                if (count > 0 && count % 3 == 0) result = " " + result;
                result = s.charAt(i) + result;
                count++;
            }
            return neg ? ("-" + result) : result;
        }
    }
}
