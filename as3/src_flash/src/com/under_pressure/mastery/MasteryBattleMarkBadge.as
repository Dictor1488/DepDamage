package com.under_pressure.mastery
{
    import flash.display.Bitmap;
    import flash.display.Graphics;
    import flash.display.Shape;
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.events.KeyboardEvent;
    import flash.events.MouseEvent;
    import flash.filters.DropShadowFilter;
    import flash.filters.GlowFilter;
    import flash.geom.Rectangle;
    import flash.text.TextField;
    import flash.text.TextFieldAutoSize;
    import flash.ui.Keyboard;

    public class MasteryBattleMarkBadge extends Sprite
    {
        [Embed(source="assets/style3_battle_bg.png")]
        private static const STYLE3_BATTLE_BG:Class;
        [Embed(source="assets/style3_battle_state_up_299x214.png")]
        private static const STYLE3_BATTLE_STATE_UP:Class;
        [Embed(source="assets/style3_battle_state_down_299x214.png")]
        private static const STYLE3_BATTLE_STATE_DOWN:Class;
        [Embed(source="assets/style3_battle_state_down_blind_299x214.png")]
        private static const STYLE3_BATTLE_STATE_DOWN_BLIND:Class;
        [Embed(source="assets/style3_battle_state_same_299x214.png")]
        private static const STYLE3_BATTLE_STATE_SAME:Class;
        [Embed(source="assets/style3_battle_state_up_alt_299x284.png")]
        private static const STYLE3_BATTLE_STATE_UP_ALT:Class;
        [Embed(source="assets/style3_battle_state_down_alt_299x284.png")]
        private static const STYLE3_BATTLE_STATE_DOWN_ALT:Class;
        [Embed(source="assets/style3_battle_state_down_blind_alt_299x284.png")]
        private static const STYLE3_BATTLE_STATE_DOWN_BLIND_ALT:Class;
        [Embed(source="assets/style3_battle_state_same_alt_299x284.png")]
        private static const STYLE3_BATTLE_STATE_SAME_ALT:Class;
        [Embed(source="assets/style3_battle_state_unavailable_299x214.png")]
        private static const STYLE3_BATTLE_STATE_UNAVAILABLE:Class;
        [Embed(source="assets/style3_battle_state_marks_0_up_299x214.png")]
        private static const STYLE3_BATTLE_STATE_MARKS0:Class;
        [Embed(source="assets/style3_battle_state_marks_1_up_299x214.png")]
        private static const STYLE3_BATTLE_STATE_MARKS1:Class;
        [Embed(source="assets/style3_battle_state_marks_2_up_299x214.png")]
        private static const STYLE3_BATTLE_STATE_MARKS2:Class;
        [Embed(source="assets/style3_battle_state_marks_3_up_299x214.png")]
        private static const STYLE3_BATTLE_STATE_MARKS3:Class;
        [Embed(source="assets/style3_battle_marker.png")]
        private static const STYLE3_BATTLE_MARKER:Class;

        private static const W:int      = 198;
        private static const H:int      = 86;
        private static const H_EXP:int  = 112;
        private static const W_HTML:int     = 339;
        private static const H_HTML:int     = 254;
        private static const H_HTML_EXP:int = 254;
        private static const PAD:int    = 24;

        private function _curW():int { return _style == 2 ? W_HTML : W; }
        private function _curH():int { return _style == 2 ? (_expanded ? H_HTML_EXP : H_HTML) : (_expanded ? H_EXP : H); }
        private static const FONT_FACE:String  = "$FieldFont";
        private static const COLOR_LABEL:uint  = 0xFFFFFF;
        private static const COLOR_DIM:uint    = 0x98A6B3;
        private static const COLOR_GREEN:uint  = 0xB6E86A;
        private static const COLOR_RED:uint    = 0xD64A4A;
        private static const COLOR_GOLD:uint   = 0xC8B97A;
        private static const FRAME_COLOR:uint  = 0xAEB8C2;
        private static const FRAME_DARK:uint   = 0x141A22;
        // delta arrow colours: up / down / zero
        private static const ARROW_UP:uint     = 0x82B15C;
        private static const ARROW_DOWN:uint   = 0xBE5151;
        private static const ARROW_ZERO:uint   = 0xE6E6E6;

        // milestone colours: 1 star 65%, 2 stars 85%, 3 stars 95%
        private static const MILESTONE_PCTS:Array  = [65.0, 85.0, 95.0];
        private static const MILESTONE_LABELS:Array = ["1\u2605  65%", "2\u2605  85%", "3\u2605  95%"];
        private static const MILESTONE_COLORS:Array = [0x78909C, 0xC0C0C0, 0xC8B97A];

        private var _bg:Shape;
        private var _line:Shape;        // main progress bar
        private var _targetLine:Shape;  // milestone progress bar (expanded)
        private var _stars:Shape;
        private var _arrow:Shape;       // delta direction arrow (up/down/zero)
        private var _value:TextField;
        private var _total:TextField;
        private var _targetLabel:TextField;
        private var _targetDmg:TextField;
        private var _delta:TextField;   // delta % shown next to value
        private var _shadow:DropShadowFilter;
        private var _style3Bg:Bitmap;
        private var _style3Bgs:Array;
        private var _style3Marker:Bitmap;

        private var _mark:Number       = 0.0;
        private var _p65:int           = 0;
        private var _p85:int           = 0;
        private var _p95:int           = 0;
        private var _p100:int          = 0;
        private var _currentDamage:int = -1;
        private var _baseDamage:int    = 0;
        private var _projectedMark:Number = -1.0;
        private var _projectedAvg:int  = 0;
        private var _starsCount:int    = -1;
        private var _expanded:Boolean  = false;
        private var _disposed:Boolean  = false;
        private var _offset:Array      = [-1, -1];
        private var _dragging:Boolean  = false;
        // 0 = classic (зірки/число по центру), 1 = compact (зірки+смужки зліва)
        private var _style:int         = 0;

        public function MasteryBattleMarkBadge()
        {
            super();
            mouseEnabled  = true;
            mouseChildren = false;
            visible       = false;
            _shadow = new DropShadowFilter(1.2, 45, 0x000000, 0.95, 3, 3, 1.6, 1);

            _bg          = new Shape();  addChild(_bg);
            _style3Bg     = _makeBitmap(STYLE3_BATTLE_BG);      addChild(_style3Bg);
            _style3Bgs = [
                _addStyle3Bg(STYLE3_BATTLE_STATE_UP),
                _addStyle3Bg(STYLE3_BATTLE_STATE_DOWN),
                _addStyle3Bg(STYLE3_BATTLE_STATE_DOWN_BLIND),
                _addStyle3Bg(STYLE3_BATTLE_STATE_SAME),
                _addStyle3Bg(STYLE3_BATTLE_STATE_UP_ALT),
                _addStyle3Bg(STYLE3_BATTLE_STATE_DOWN_ALT),
                _addStyle3Bg(STYLE3_BATTLE_STATE_DOWN_BLIND_ALT),
                _addStyle3Bg(STYLE3_BATTLE_STATE_SAME_ALT),
                _addStyle3Bg(STYLE3_BATTLE_STATE_UNAVAILABLE),
                _addStyle3Bg(STYLE3_BATTLE_STATE_MARKS0),
                _addStyle3Bg(STYLE3_BATTLE_STATE_MARKS1),
                _addStyle3Bg(STYLE3_BATTLE_STATE_MARKS2),
                _addStyle3Bg(STYLE3_BATTLE_STATE_MARKS3)
            ];
            _line        = new Shape();  addChild(_line);
            _targetLine  = new Shape();  addChild(_targetLine);
            _stars       = new Shape();  addChild(_stars);
            _style3Marker = _makeBitmap(STYLE3_BATTLE_MARKER);  addChild(_style3Marker);
            _arrow       = new Shape();  addChild(_arrow);
            _value       = _makeText(24, COLOR_LABEL);
            _total       = _makeText(12, COLOR_DIM);
            _targetLabel = _makeText(12, COLOR_DIM);
            _targetDmg   = _makeText(12, COLOR_DIM);
            _delta       = _makeText(14, COLOR_GREEN);
            addChild(_value);
            addChild(_total);
            addChild(_targetLabel);
            addChild(_targetDmg);
            addChild(_delta);

            addEventListener(Event.ADDED_TO_STAGE, _onAddedToStage);
            addEventListener(MouseEvent.MOUSE_DOWN, _onMouseDown);
            _draw();
        }

        // ── public API ───────────────────────────────────────────────────────

        public function setExpanded(value:Boolean):void
        {
            if (_disposed) return;
            if (_expanded == value) return;
            _expanded = value;
            _draw();
            updatePosition();
        }

        public function setStyle(value:int):void
        {
            if (_disposed) return;
            var v:int = value == 2 ? 2 : (value == 1 ? 1 : 0);
            if (_style == v) return;
            _style = v;
            _draw();
            updatePosition();
        }

        public function setData(mark:Number, p65:int, p85:int, p95:int, p100:int,
                                currentDamage:int, baseDamage:int, stars:int,
                                projectedMark:Number = -1.0, projectedAvg:int = 0):void
        {
            _mark          = isNaN(mark)          ? 0.0  : mark;
            _p65           = int(Math.max(0, p65));
            _p85           = int(Math.max(0, p85));
            _p95           = int(Math.max(0, p95));
            _p100          = int(Math.max(0, p100));
            _currentDamage = int(Math.max(-1, currentDamage));
            _baseDamage    = int(Math.max(0,  baseDamage));
            _projectedMark = isNaN(projectedMark) ? -1.0 : projectedMark;
            _projectedAvg  = int(Math.max(0, projectedAvg));
            _starsCount    = int(Math.max(-1, Math.min(3, stars)));
            _draw();
            updatePosition();
        }

        public function setCurrentDamage(value:int):void
        {
            _currentDamage = int(Math.max(0, value));
            _projectedMark = -1.0;
            _projectedAvg  = 0;
            _draw();
        }

        public function setPositionOffset(offset:Array):void
        {
            if (offset && offset.length >= 2)
                _offset = [int(offset[0]), int(offset[1])];
            updatePosition();
        }

        public function updatePosition():void
        {
            if (!stage || _dragging) return;
            var sw:int = stage.stageWidth  > 0 ? stage.stageWidth  : 1280;
            var sh:int = stage.stageHeight > 0 ? stage.stageHeight : 720;
            var h:int  = _curH();
            var ww:int = _curW();
            if (_offset[0] < 0 && _offset[1] < 0)
            {
                x = int(sw * 0.5 - ww * 0.5);
                y = int(sh - h - 118);
            }
            else
            {
                x = Math.max(0, Math.min(sw - ww,  int(_offset[0])));
                y = Math.max(0, Math.min(sh - h,  int(_offset[1])));
            }
        }

        public function dispose():void
        {
            if (_disposed) return;
            _disposed = true;
            removeEventListener(Event.ADDED_TO_STAGE, _onAddedToStage);
            removeEventListener(MouseEvent.MOUSE_DOWN, _onMouseDown);
            if (stage)
            {
                stage.removeEventListener(KeyboardEvent.KEY_DOWN, _onKeyDown);
                stage.removeEventListener(KeyboardEvent.KEY_UP,   _onKeyUp);
                stage.removeEventListener(MouseEvent.MOUSE_UP,    _onMouseUp);
            }
        }

        // ── keyboard / mouse ─────────────────────────────────────────────────

        private function _onAddedToStage(e:Event):void
        {
            removeEventListener(Event.ADDED_TO_STAGE, _onAddedToStage);
            stage.addEventListener(KeyboardEvent.KEY_DOWN, _onKeyDown);
            stage.addEventListener(KeyboardEvent.KEY_UP,   _onKeyUp);
        }

        private function _onKeyDown(e:KeyboardEvent):void
        {
            if (e.keyCode == Keyboard.ALTERNATE && !_expanded)
            {
                _expanded = true;
                _draw();
                updatePosition();
            }
        }

        private function _onKeyUp(e:KeyboardEvent):void
        {
            if (e.keyCode == Keyboard.ALTERNATE && _expanded)
            {
                _expanded = false;
                _draw();
                updatePosition();
            }
        }

        private function _onMouseDown(e:MouseEvent):void
        {
            if (!stage) return;
            _dragging = true;
            var bounds:Rectangle = new Rectangle(
                0, 0,
                Math.max(0, stage.stageWidth  - width),
                Math.max(0, stage.stageHeight - height)
            );
            startDrag(false, bounds);
            stage.addEventListener(MouseEvent.MOUSE_UP, _onMouseUp);
            e.stopPropagation();
        }

        private function _onMouseUp(e:MouseEvent):void
        {
            stopDrag();
            if (stage) stage.removeEventListener(MouseEvent.MOUSE_UP, _onMouseUp);
            _dragging = false;
            _offset = [int(x), int(y)];
            dispatchEvent(new MasteryPanelEvent(MasteryPanelEvent.BATTLE_BADGE_OFFSET_CHANGED, _offset));
        }

        // ── draw ─────────────────────────────────────────────────────────────

        private function _draw():void
        {
            _setStyle3AssetsVisible(_style == 2);
            if (_style == 1)
            {
                _drawCompact();
                return;
            }
            if (_style == 2)
            {
                _drawHtmlStyle();
                return;
            }

            var h:int = _expanded ? H_EXP : H;

            var g:Graphics = _bg.graphics;
            g.clear();
            g.lineStyle(0, 0x000000, 0.0);
            g.beginFill(0x05080C, 0.001);
            g.drawRoundRect(0, 0, W, h, 4, 4);
            g.endFill();
            _drawFrameSegments(g, W, h, 58);

            // computed values
            var current:int       = _currentDamage >= 0 ? _currentDamage : 0;
            var projAvg:int       = _projectedAvg > 0 ? _projectedAvg : _projectedAverage(current);
            var projMark:Number   = _projectedMark >= 0.0 ? _projectedMark :
                                    (projAvg > 0 ? _estimateMarkFromDamage(projAvg) : _mark);
            var delta:Number      = projMark - _mark;
            var deltaColor:uint   = Math.abs(delta) < 0.005 ? COLOR_DIM : (delta > 0 ? COLOR_GREEN : COLOR_RED);

            // stars + main value + delta arrow
            _drawStars(projMark);

            var kind:int = Math.abs(delta) < 0.005 ? 0 : (delta > 0 ? 1 : -1); // 0=zero 1=up -1=down
            var valStr:String   = _fmt2(projMark) + "%";
            var deltaStr:String = (kind == 0) ? "" : ((delta > 0 ? "+" : "") + _fmt2(delta) + "%");

            _value.htmlText = _fmtBold(valStr, 25, COLOR_LABEL);
            var valW:Number   = _value.width;

            var deltaW:Number = 0;
            if (deltaStr.length > 0)
            {
                _delta.htmlText = _fmtBold(deltaStr, 14, deltaColor);
                deltaW = _delta.width;
                _delta.visible = true;
            }
            else
            {
                _delta.visible = false;
            }

            var arrowGap:Number = (kind == 0 ? 16 : 22);
            var blockW:Number   = valW + arrowGap + deltaW;
            var blockX:Number   = int(W / 2 - blockW / 2);
            _value.x = blockX;
            _value.y = 22;

            // arrow placed with clear margin from both value and delta
            _drawArrow(blockX + valW + 8, 35, kind);

            // delta text after the arrow (extra margin so they never touch)
            if (deltaStr.length > 0)
            {
                _delta.x = int(blockX + valW + arrowGap);
                _delta.y = 30;
            }

            // main progress bar: 0 → baseDamage (скільки треба щоб не впасти)
            var nearestIdx:int    = _nearestMilestone(projMark);
            var nearestDmg:int    = _milestoneRequiredDamage(nearestIdx);
            _drawProgressBar(_line, current, _baseDamage > 0 ? _baseDamage : nearestDmg, delta, 58);

            // "Current / target" line (без підпису)
            var baseTarget:int = _baseDamage > 0 ? _baseDamage : (nearestDmg > 0 ? nearestDmg : (_p85 > 0 ? _p85 : 0));
            _total.htmlText = _fmtBold(_fmtNum(current), 14, COLOR_LABEL) +
                              _fmt(" / " + (baseTarget > 0 ? _fmtNum(baseTarget) : "N/A"), 14, COLOR_DIM);
            // Сумарний прогрес під планкою — по центру.
            _total.x = int(W / 2 - _total.width / 2);
            _total.y = 64;

            // ── expanded: nearest milestone ──────────────────────────────────
            _targetLine.visible  = _expanded;
            _targetLabel.visible = _expanded;
            _targetDmg.visible   = _expanded;

            if (_expanded)
            {
                var milestoneIdx:int      = _nearestMilestone(projMark);
                var milestonePct:Number   = Number(MILESTONE_PCTS[milestoneIdx]);
                var milestoneColor:uint   = uint(MILESTONE_COLORS[milestoneIdx]);
                var milestoneDmg:int      = _milestoneRequiredDamage(milestoneIdx);

                // Просто текст: "85%  3 761" без полосок
                var pctStr:String = milestonePct.toFixed(0) + "%";
                var dmgStr:String = _fmtNum(milestoneDmg);
                _targetLabel.htmlText = _fmt(pctStr + "  " + dmgStr, 15, milestoneColor);
                _targetLabel.x = int(W / 2 - _targetLabel.width / 2);
                _targetLabel.y = 88;

                _targetDmg.htmlText = "";
                _targetLine.graphics.clear();
            }
        }

        // ── compact style (зірки+смужки зліва, як на макеті) ─────────────────
        private static const COMPACT_DIM_WHITE:uint = 0xCED6DE;

        private function _drawHtmlStyle():void
        {
            var g:Graphics = _bg.graphics;
            g.clear();
            _style3Marker.x = 179;
            _style3Marker.y = 100;

            var current:int     = _currentDamage >= 0 ? _currentDamage : 0;
            var projAvg:int     = _projectedAvg > 0 ? _projectedAvg : _projectedAverage(current);
            var projMark:Number = _projectedMark >= 0.0 ? _projectedMark :
                                  (projAvg > 0 ? _estimateMarkFromDamage(projAvg) : _mark);
            var delta:Number    = projMark - _mark;
            var kind:int        = Math.abs(delta) < 0.005 ? 0 : (delta > 0 ? 1 : -1);
            var filled:int      = _starsCount >= 0 ? _starsCount :
                                  (projMark >= 95 ? 3 : (projMark >= 85 ? 2 : (projMark >= 65 ? 1 : 0)));
            var noData:Boolean  = (_p65 <= 0 && _p85 <= 0 && _p95 <= 0 && _p100 <= 0);
            _selectStyle3BattleBg(kind, filled, noData);

            var sg:Graphics = _stars.graphics;
            sg.clear();
            var i:int;
            for (i = 0; i < 3; i++)
            {
                sg.lineStyle(NaN);
                sg.beginFill(i < filled ? 0xFFFFFF : 0x303946, 1.0);
                _starPath(sg, 152 + i * 17, 76, 7, 3);
                sg.endFill();
            }

            _value.htmlText = _fmtBold(_fmt2(projMark) + "%", 25, COLOR_LABEL);
            _value.x = 118;
            _value.y = 88;

            var deltaStr:String = (kind == 0) ? "" :
                ((delta > 0 ? "+" : "-") + _fmt2(Math.abs(delta)) + "%");
            if (deltaStr.length > 0)
            {
                _delta.htmlText = _fmt(deltaStr, 13, kind > 0 ? COLOR_GREEN : COLOR_RED);
                _delta.x = 193;
                _delta.y = 94;
                _delta.visible = true;
            }
            else
            {
                _delta.visible = false;
            }
            _drawTrendArrow(184, 101, kind);

            var nearestIdx:int = _nearestMilestone(projMark);
            var nearestDmg:int = _milestoneRequiredDamage(nearestIdx);
            var target:int     = _baseDamage > 0 ? _baseDamage : nearestDmg;
            _drawProgressBarSquare(_line, current, target, delta, 94, 150, 123, 3.0);

            _total.htmlText = _fmt(_strSumLabel(), 13, 0xFFEEC9);
            _total.x = 96;
            _total.y = 132;

            var d65:String  = _p65  > 0 ? _fmtNum(_p65)  : "N/A";
            var d85:String  = _p85  > 0 ? _fmtNum(_p85)  : "N/A";
            var d95:String  = _p95  > 0 ? _fmtNum(_p95)  : "N/A";
            var d100:String = _p100 > 0 ? _fmtNum(_p100) : "N/A";

            _targetLabel.htmlText =
                _fmt("65%  ", 13, COLOR_LABEL) + _fmt(d65, 13, COLOR_DIM) +
                _fmt("     85%  ", 13, COLOR_LABEL) + _fmt(d85, 13, COLOR_DIM);
            _targetLabel.x = 96;
            _targetLabel.y = 154;
            _targetLabel.visible = true;

            _targetDmg.htmlText =
                _fmt("95%  ", 13, COLOR_LABEL) + _fmt(d95, 13, COLOR_DIM) +
                _fmt("   100%  ", 13, COLOR_LABEL) + _fmt(d100, 13, COLOR_DIM);
            _targetDmg.x = 96;
            _targetDmg.y = 174;
            _targetDmg.visible = true;

            _targetLine.visible = false;
            if (_expanded)
            {
                var milestonePct:Number = Number(MILESTONE_PCTS[nearestIdx]);
                var milestoneDmg:int = _milestoneRequiredDamage(nearestIdx);
                _targetDmg.htmlText = _targetDmg.htmlText + _fmt("   next " + milestonePct.toFixed(0) + "% " + _fmtNum(milestoneDmg), 13, COLOR_GOLD);
            }
        }

        private function _makeBitmap(asset:Class):Bitmap
        {
            var bmp:Bitmap = new asset() as Bitmap;
            bmp.smoothing = false;
            bmp.visible = false;
            return bmp;
        }

        private function _addStyle3Bg(asset:Class):Bitmap
        {
            var bmp:Bitmap = _makeBitmap(asset);
            bmp.x = 20;
            bmp.y = 20;
            addChild(bmp);
            return bmp;
        }

        private function _selectStyle3BattleBg(kind:int, filled:int, noData:Boolean):void
        {
            var idx:int = 0;
            if (noData)
                idx = 8;
            else if (_expanded)
                idx = kind > 0 ? 4 : (kind < 0 ? (_currentDamage < 0 ? 6 : 5) : 7);
            else if (_starsCount >= 0)
                idx = 9 + Math.max(0, Math.min(3, filled));
            else
                idx = kind > 0 ? 0 : (kind < 0 ? (_currentDamage < 0 ? 2 : 1) : 3);

            for (var i:int = 0; i < _style3Bgs.length; i++)
                Bitmap(_style3Bgs[i]).visible = (i == idx);
            if (_style3Bg) _style3Bg.visible = false;
        }

        private function _setStyle3AssetsVisible(value:Boolean):void
        {
            if (_style3Bg) _style3Bg.visible = value;
            if (_style3Bgs)
            {
                for (var i:int = 0; i < _style3Bgs.length; i++)
                    Bitmap(_style3Bgs[i]).visible = false;
            }
            if (_style3Marker) _style3Marker.visible = value;
        }

        private function _drawCompact():void
        {
            var h:int = _expanded ? H_EXP : H;
            var g:Graphics = _bg.graphics;
            g.clear();
            g.lineStyle(0, 0x000000, 0.0);
            g.beginFill(0x05080C, 0.001);
            g.drawRoundRect(0, 0, W, h, 4, 4);
            g.endFill();
            _drawFrameSegmentsCompact(g, W, h, 56);

            // обчислення (ті самі, що в classic)
            var current:int     = _currentDamage >= 0 ? _currentDamage : 0;
            var projAvg:int     = _projectedAvg > 0 ? _projectedAvg : _projectedAverage(current);
            var projMark:Number = _projectedMark >= 0.0 ? _projectedMark :
                                  (projAvg > 0 ? _estimateMarkFromDamage(projAvg) : _mark);
            var delta:Number    = projMark - _mark;
            var kind:int        = Math.abs(delta) < 0.005 ? 0 : (delta > 0 ? 1 : -1);

            var filled:int = _starsCount >= 0 ? _starsCount :
                             (projMark >= 95 ? 3 : (projMark >= 85 ? 2 : (projMark >= 65 ? 1 : 0)));

            // ── колонка 1: зірки (3 слоти, знизу вгору) ──
            var sg:Graphics = _stars.graphics;
            sg.clear();
            var starX:int = 14;
            var starYs:Array = [68, 46, 24];
            for (var i:int = 0; i < 3; i++)
            {
                sg.beginFill(i < filled ? 0xFFFFFF : 0x27313C, 1.0);
                _starPath(sg, starX, Number(starYs[i]), 7, 3);
                sg.endFill();
            }

            // ── колонка 2: вертикальні смужки = к-сть міток ──
            var barX:Number = 30;
            var slots:Array = [[58, 72], [36, 50], [14, 28]];
            for (i = 0; i < 3; i++)
            {
                var on:Boolean = i < filled;
                sg.lineStyle(3, 0xFFFFFF, on ? 0.95 : 0.22);
                sg.moveTo(barX, Number(slots[i][1]));
                sg.lineTo(barX, Number(slots[i][0]));
            }
            sg.lineStyle(NaN);

            var contentX:int = 44;
            var contentR:int = W - 12;

            // ── діагональна стрілка тренду ──
            _drawTrendArrow(contentX + 3, 28, kind);

            // ── дельта (13px, читабельна) ──
            var deltaStr:String = (kind == 0) ? "" :
                ((delta > 0 ? "+" : "-") + _fmt2(Math.abs(delta)) + "%");
            if (deltaStr.length > 0)
            {
                _delta.htmlText = _fmt(deltaStr, 13, kind > 0 ? COLOR_GREEN : COLOR_RED);
                _delta.x = contentX + 14;
                _delta.y = 20;
                _delta.visible = true;
            }
            else
            {
                _delta.visible = false;
            }

            // ── велике число справа (26px, з захистом від накладання на дельту) ──
            var valStr:String = _fmt2(projMark) + "%";
            var deltaRight:Number = _delta.visible ? (_delta.x + _delta.width) : (contentX + 10);
            var vSize:int = 26;
            _value.htmlText = _fmtBold(valStr, vSize, COLOR_LABEL);
            while (vSize > 22 && (contentR - _value.width) < (deltaRight + 6))
            {
                vSize--;
                _value.htmlText = _fmtBold(valStr, vSize, COLOR_LABEL);
            }
            _value.x = int(contentR - _value.width);
            _value.y = int(14 + (26 - vSize) * 0.5);

            // ── квадратний прогрес-бар ──
            var nearestIdx:int = _nearestMilestone(projMark);
            var nearestDmg:int = _milestoneRequiredDamage(nearestIdx);
            var target:int     = _baseDamage > 0 ? _baseDamage : nearestDmg;
            _drawProgressBarSquare(_line, current, target, delta, contentX, contentR - contentX, 56);

            // ── "Сум. урон" + "cur / req" (обидва приглушено-білі) ──
            _total.htmlText = _fmt(_fmtNum(current) + " / " +
                              (target > 0 ? _fmtNum(target) : "N/A"), 12, COMPACT_DIM_WHITE);
            _total.x = int(contentR - _total.width);
            _total.y = 66;

            _targetLabel.htmlText = _fmt(_strSumLabel(), 12, COMPACT_DIM_WHITE);
            _targetLabel.x = contentX;
            _targetLabel.y = 66;
            _targetLabel.visible = true;

            // ── expanded (Alt): найближча планка ──
            _targetLine.visible = false;
            if (_expanded)
            {
                var milestoneIdx:int    = _nearestMilestone(projMark);
                var milestonePct:Number = Number(MILESTONE_PCTS[milestoneIdx]);
                var milestoneColor:uint = uint(MILESTONE_COLORS[milestoneIdx]);
                var milestoneDmg:int    = _milestoneRequiredDamage(milestoneIdx);
                var pctStr:String = milestonePct.toFixed(0) + "%";
                var dmgStr:String = _fmtNum(milestoneDmg);
                _targetDmg.htmlText = _fmt(pctStr + "  " + dmgStr, 15, milestoneColor);
                _targetDmg.x = int(W / 2 - _targetDmg.width / 2);
                _targetDmg.y = 88;
                _targetDmg.visible = true;
            }
            else
            {
                _targetDmg.visible = false;
            }
        }

        private function _strSumLabel():String
        {
            return "\u0421\u0443\u043c. \u0443\u0440\u043e\u043d"; // "Сум. урон"
        }

        /** Тонка діагональна стрілка тренду: kind 1=↗ up(green) -1=↘ down(red) 0=dash */
        private function _drawTrendArrow(cx:Number, cy:Number, kind:int):void
        {
            var g:Graphics = _arrow.graphics;
            g.clear();
            if (kind == 0)
            {
                g.lineStyle(1.4, ARROW_ZERO, 1.0);
                g.moveTo(cx - 4, cy);  g.lineTo(cx + 4, cy);
                g.lineStyle(NaN);
                return;
            }
            var col:uint = kind > 0 ? ARROW_UP : ARROW_DOWN;
            var len:Number = 9;
            g.lineStyle(1.6, col, 1.0);
            if (kind < 0)
            {
                var x0:Number = cx - len / 2, y0:Number = cy - len / 2;
                var x1:Number = cx + len / 2, y1:Number = cy + len / 2;
                g.moveTo(x0, y0);  g.lineTo(x1, y1);
                g.moveTo(x1, y1);  g.lineTo(x1 - 5, y1);
                g.moveTo(x1, y1);  g.lineTo(x1, y1 - 5);
            }
            else
            {
                x0 = cx - len / 2; y0 = cy + len / 2;
                x1 = cx + len / 2; y1 = cy - len / 2;
                g.moveTo(x0, y0);  g.lineTo(x1, y1);
                g.moveTo(x1, y1);  g.lineTo(x1 - 5, y1);
                g.moveTo(x1, y1);  g.lineTo(x1, y1 + 5);
            }
            g.lineStyle(NaN);
        }

        /** Квадратний прогрес-бар (без заокруглень). */
        private function _drawProgressBarSquare(shape:Shape, currentDamage:int,
                                                targetDamage:int, delta:Number,
                                                x0:Number, w:Number, yPos:Number,
                                                barH:Number = 6.0):void
        {
            var g:Graphics = shape.graphics;
            g.clear();
            var pct:Number = targetDamage > 0
                ? Math.max(0.0, Math.min(1.0, Number(currentDamage) / Number(targetDamage)))
                : 0.0;
            var color:uint = delta >= 0 ? COLOR_GREEN : COLOR_RED;
            var top:Number  = yPos - barH / 2;

            // track
            g.lineStyle(1.4, 0x0A0E14, 1.0);
            g.beginFill(0x16202A, 1.0);
            g.drawRect(x0, top, w, barH);
            g.endFill();
            g.lineStyle(NaN);

            // fill
            if (pct > 0)
            {
                g.beginFill(color, 1.0);
                g.drawRect(x0, top, w * pct, barH);
                g.endFill();
            }
        }

        // ── progress bars ────────────────────────────────────────────────────

        /** Bar filling from 0 to targetDamage, showing currentDamage progress.
            Capsule with fixed dark outline + rounded ends + knob. */
        private function _drawProgressBar(shape:Shape, currentDamage:int,
                                          targetDamage:int, delta:Number, yPos:Number):void
        {
            var g:Graphics  = shape.graphics;
            g.clear();
            var w:Number    = W - PAD * 2;
            var pct:Number  = targetDamage > 0
                ? Math.max(0.0, Math.min(1.0, Number(currentDamage) / Number(targetDamage)))
                : 0.0;
            var color:uint  = delta >= 0 ? COLOR_GREEN : COLOR_RED;

            var barH:Number = 6.0;
            var x0:Number   = PAD;
            var x1:Number   = PAD + w;
            var top:Number  = yPos - barH / 2;

            // fixed dark outline capsule
            g.lineStyle(1.4, 0x0A0E14, 1.0);
            g.beginFill(0x16202A, 1.0);
            g.drawRoundRect(x0, top, w, barH, barH, barH);
            g.endFill();
            g.lineStyle(NaN);

            // fill
            if (pct > 0)
            {
                g.beginFill(color, 1.0);
                g.drawRoundRect(x0, top, Math.max(barH, w * pct), barH, barH, barH);
                g.endFill();
            }

            // knob
            g.lineStyle(1.4, 0xFFFFFF, 0.92);
            g.beginFill(color, 1.0);
            g.drawCircle(x0 + w * pct, yPos, 4.5);
            g.endFill();
            g.lineStyle(NaN);
        }

        /** Delta direction arrow: kind 1=up(green) -1=down(red) 0=zero(white dash) */
        private function _drawArrow(cx:Number, cy:Number, kind:int):void
        {
            var g:Graphics = _arrow.graphics;
            g.clear();
            if (kind == 1)
            {
                g.lineStyle(1.4, ARROW_UP, 1.0);
                g.moveTo(cx, cy + 6);  g.lineTo(cx, cy - 3);
                g.lineStyle(NaN);
                g.beginFill(ARROW_UP, 1.0);
                g.moveTo(cx, cy - 7);  g.lineTo(cx - 4, cy - 2);  g.lineTo(cx + 4, cy - 2);
                g.lineTo(cx, cy - 7);
                g.endFill();
            }
            else if (kind == -1)
            {
                g.lineStyle(1.4, ARROW_DOWN, 1.0);
                g.moveTo(cx, cy - 6);  g.lineTo(cx, cy + 3);
                g.lineStyle(NaN);
                g.beginFill(ARROW_DOWN, 1.0);
                g.moveTo(cx, cy + 7);  g.lineTo(cx - 4, cy + 2);  g.lineTo(cx + 4, cy + 2);
                g.lineTo(cx, cy + 7);
                g.endFill();
            }
            else
            {
                g.lineStyle(1.6, ARROW_ZERO, 1.0);
                g.moveTo(cx - 4, cy);  g.lineTo(cx + 4, cy);
                g.lineStyle(NaN);
            }
        }

        private function _drawFrameSegments(g:Graphics, w:Number, h:Number, barY:Number):void
        {
            var inset:Number   = 3.0;
            var rad:Number     = 6;
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

            // ── верх: розрив посередині (де зірки/число) ──
            var gc0:Number = tl + (tr - tl) * 0.34;
            var gc1:Number = tl + (tr - tl) * 0.66;
            g.moveTo(tl, y0);  g.lineTo(gc0, y0);
            g.moveTo(gc1, y0); g.lineTo(tr, y0);

            // ── низ: суцільний ──
            g.moveTo(tl, y1); g.lineTo(tr, y1);

            // ── боки: короткі розрізи (4 на кожен) ──
            var ftop:Number = y0 + rad, fbot:Number = y1 - rad, fh:Number = fbot - ftop;
            var gaps:Array = [0.10, 0.46, 0.66, 0.89];
            var gw:Number  = 0.05;
            _sideEdge(g, x0, ftop, fbot, fh, gaps, gw);
            _sideEdge(g, x1, ftop, fbot, fh, gaps, gw);

            // ── бічні конектори: від краю рамки до бара (короткі, половина) ──
            g.moveTo(x0, barY);                  g.lineTo((x0 + PAD - 3) / 2, barY);
            g.moveTo((x1 + w - PAD + 3) / 2, barY); g.lineTo(x1, barY);

            g.lineStyle(NaN);
        }

        /** Рамка для compact-стилю: верх суцільний (контент не по центру),
            конектори до бару відрізають ліву зону зірок/смужок. */
        private function _drawFrameSegmentsCompact(g:Graphics, w:Number, h:Number, barY:Number):void
        {
            var inset:Number   = 3.0;
            var rad:Number     = 6;
            var lineColor:uint = 0xC9D2DC;
            var a:Number       = 0.46;
            var x0:Number = inset, y0:Number = inset, x1:Number = w - inset, y1:Number = h - inset;

            g.lineStyle(0.9, lineColor, a, true);

            // кутові дуги
            _arcSeg(g, x0 + rad, y0 + rad, rad, 180, 270);
            _arcSeg(g, x1 - rad, y0 + rad, rad, 270, 360);
            _arcSeg(g, x0 + rad, y1 - rad, rad,  90, 180);
            _arcSeg(g, x1 - rad, y1 - rad, rad,   0,  90);

            var tl:Number = x0 + rad, tr:Number = x1 - rad;

            // верх: суцільний (без центрального розриву)
            g.moveTo(tl, y0); g.lineTo(tr, y0);
            // низ: суцільний
            g.moveTo(tl, y1); g.lineTo(tr, y1);

            // боки: короткі розрізи
            var ftop:Number = y0 + rad, fbot:Number = y1 - rad, fh:Number = fbot - ftop;
            var gaps:Array = [0.10, 0.46, 0.66, 0.89];
            var gw:Number  = 0.05;
            _sideEdge(g, x0, ftop, fbot, fh, gaps, gw);
            _sideEdge(g, x1, ftop, fbot, fh, gaps, gw);

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

        /** Milestone bar: shows progress from 0 to milestonePct */
        private function _drawMilestoneBar(shape:Shape, projMark:Number,
                                           milestonePct:Number, milestoneColor:uint, yPos:Number):void
        {
            var g:Graphics = shape.graphics;
            g.clear();
            var w:Number   = W - PAD * 2;

            // track
            g.lineStyle(5, 0x2A2F35, 1.0);
            g.moveTo(PAD, yPos);  g.lineTo(PAD + w, yPos);

            // fill up to current projected mark (capped at milestone)
            var fillPct:Number = Math.max(0.0, Math.min(milestonePct, projMark)) / milestonePct;
            var fillColor:uint = projMark >= milestonePct ? 0x8ED05A : milestoneColor;
            g.lineStyle(5, fillColor, 1.0);
            g.moveTo(PAD, yPos);  g.lineTo(PAD + w * fillPct, yPos);

            // milestone end marker (right edge = goal)
            g.lineStyle(2, milestoneColor, 1.0);
            g.moveTo(PAD + w, yPos - 6);
            g.lineTo(PAD + w, yPos + 6);

            // knob at current position
            if (projMark < milestonePct)
            {
                g.lineStyle(1, 0xFFFFFF, 0.85);
                g.beginFill(fillColor, 1.0);
                g.drawCircle(PAD + w * fillPct, yPos, 4.0);
                g.endFill();
            }
            else
            {
                // checkmark circle
                g.lineStyle(1.5, 0x8ED05A, 1.0);
                g.beginFill(0x8ED05A, 0.25);
                g.drawCircle(PAD + w, yPos, 5.0);
                g.endFill();
            }
            g.lineStyle(NaN);
        }

        // ── milestone helpers ─────────────────────────────────────────────────

        /** Returns index 0/1/2 of nearest milestone ≥ projMark (clamps to last) */
        private function _nearestMilestone(projMark:Number):int
        {
            for (var i:int = 0; i < MILESTONE_PCTS.length; i++)
            {
                if (projMark < Number(MILESTONE_PCTS[i]))
                    return i;
            }
            return MILESTONE_PCTS.length - 1; // already at/above 95% → show 95% bar
        }

        /** Required damage for milestone index */
        private function _milestoneRequiredDamage(idx:int):int
        {
            if (idx == 0) return _p65;
            if (idx == 1) return _p85;
            return _p95;
        }

        // ── math helpers ──────────────────────────────────────────────────────

        private static const MOE_CALC_KOEFF:Number = 2.0 / 101.0;

        private function _projectedAverage(currentDamage:int):int
        {
            if (_baseDamage <= 0) return 0;
            return int(Math.round(
                Number(_baseDamage) * (1.0 - MOE_CALC_KOEFF) + Number(currentDamage) * MOE_CALC_KOEFF
            ));
        }

        private function _estimateMarkFromDamage(damage:int):Number
        {
            var points:Array = [
                { pct: 65.0,  val: Number(_p65)  },
                { pct: 85.0,  val: Number(_p85)  },
                { pct: 95.0,  val: Number(_p95)  },
                { pct: 100.0, val: Number(_p100) }
            ];
            var prevPct:Number = 0.0, prevVal:Number = 0.0;
            for (var i:int = 0; i < points.length; i++)
            {
                var np:Number = Number(points[i].pct), nv:Number = Number(points[i].val);
                if (nv <= 0) continue;
                if (damage <= nv)
                {
                    var span:Number = nv - prevVal;
                    if (span <= 0) return np;
                    var t:Number = Math.max(0.0, Math.min(1.0, (Number(damage) - prevVal) / span));
                    return prevPct + (np - prevPct) * t;
                }
                prevPct = np;  prevVal = nv;
            }
            return prevPct;
        }

        // ── stars ─────────────────────────────────────────────────────────────

        private function _drawStars(markValue:Number):void
        {
            var g:Graphics = _stars.graphics;
            g.clear();
            var filled:int = _starsCount >= 0 ? _starsCount :
                             (markValue >= 95 ? 3 : (markValue >= 85 ? 2 : (markValue >= 65 ? 1 : 0)));
            // Зірки по центру, більші
            var starSpacing:int = 22;
            var starTotalW:int  = 3 * starSpacing;
            var starStartX:int  = int(W / 2 - starTotalW / 2 + starSpacing / 2);
            for (var i:int = 0; i < 3; i++)
            {
                g.beginFill(i < filled ? 0xFFFFFF : 0x27313C, 1.0);
                _starPath(g, starStartX + i * starSpacing, 13, 8, 3.4);
                g.endFill();
            }
        }

        // ── text / util ───────────────────────────────────────────────────────

        private function _makeText(size:int, color:uint):TextField
        {
            var tf:TextField = new TextField();
            tf.selectable  = false;
            tf.mouseEnabled = false;
            tf.autoSize    = TextFieldAutoSize.LEFT;
            tf.multiline   = false;
            tf.filters     = [new GlowFilter(0x000000, 1.0, 4, 4, 4, 1), _shadow];
            tf.htmlText    = _fmt("", size, color);
            return tf;
        }

        private function _starPath(g:Graphics, cx:Number, cy:Number, r1:Number, r2:Number):void
        {
            var a:Number    = -Math.PI / 2;
            var step:Number = Math.PI / 5;
            g.moveTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1);
            for (var i:int = 1; i <= 10; i++)
            {
                a += step;
                var r:Number = (i % 2 == 0) ? r1 : r2;
                g.lineTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r);
            }
        }

        private function _fmtBold(text:String, size:int, color:uint):String
        {
            var hex:String = color.toString(16);
            while (hex.length < 6) hex = "0" + hex;
            return "<font face='" + FONT_FACE + "' size='" + size + "' color='#" + hex + "'><b>" + text + "</b></font>";
        }

        private function _fmt(text:String, size:int, color:uint):String
        {
            var hex:String = color.toString(16);
            while (hex.length < 6) hex = "0" + hex;
            return "<font face='" + FONT_FACE + "' size='" + size + "' color='#" + hex + "'>" + text + "</font>";
        }

        private function _fmt2(value:Number):String
        {
            return (isNaN(value) ? 0.0 : value).toFixed(2);
        }

        private function _fmtNum(value:int):String
        {
            var s:String = Math.abs(value).toString();
            var out:String = "";
            while (s.length > 3) { out = " " + s.substr(s.length - 3) + out; s = s.substr(0, s.length - 3); }
            out = s + out;
            return value < 0 ? "-" + out : out;
        }
    }
}
