package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.filters.GlowFilter;
    import flash.utils.getTimer;

    public class HpSplash extends Sprite
    {
        public var vehicleID:String;

        private var _bornAt:int;
        private var _markerX:Number = 0;
        private var _markerY:Number = 0;
        private var _hasMarker:Boolean = false;
        private var _bar:Sprite;
        private var _shine:Sprite;
        private var _color:uint;
        private var _damage:int;
        private var _hasHp:Boolean;
        private var _hpCur:int;
        private var _hpBefore:int;
        private var _hpMax:int;

        private static const LIFETIME:Number = 0.85;
        private static const BAR_WIDTH:Number = 70.0;
        private static const BAR_HEIGHT:Number = 4.0;
        private static const BAR_Y:Number = -19.0;
        private static const BAR_X:Number = -35.0;

        public function HpSplash(vehicleID:String, damage:int, color:uint, startX:Number = 0, startY:Number = 0, hasStart:Boolean = false, hasHp:Boolean = false, hpCur:int = 0, hpBefore:int = 0, hpMax:int = 0)
        {
            this.vehicleID = vehicleID;
            _damage = damage;
            _color = normalizeColor(color);
            _markerX = startX;
            _markerY = startY;
            _hasMarker = hasStart;
            _hasHp = hasHp;
            _hpCur = hpCur;
            _hpBefore = hpBefore;
            _hpMax = hpMax;
            _bornAt = getTimer();

            mouseEnabled = false;
            mouseChildren = false;

            _bar = new Sprite();
            _bar.filters = [ new GlowFilter(0x000000, 0.9, 3, 3, 2, 2), new GlowFilter(_color, 0.55, 8, 5, 1.2, 1) ];
            addChild(_bar);

            _shine = new Sprite();
            _shine.filters = [ new GlowFilter(0xFFFFFF, 0.8, 5, 5, 1.5, 1) ];
            addChild(_shine);

            drawParts(1.0);
            visible = _hasMarker;
        }

        public function update(pos:Object):Boolean
        {
            var age:Number = (getTimer() - _bornAt) / 1000.0;
            if (age >= LIFETIME)
                return false;

            if (pos != null && pos.ok)
            {
                _markerX = Number(pos.x);
                _markerY = Number(pos.y);
                _hasMarker = true;
            }

            if (!_hasMarker)
            {
                visible = false;
                return true;
            }

            visible = true;
            x = _markerX;
            y = _markerY + BAR_Y;

            var p:Number = age / LIFETIME;
            alpha = 1.0 - p;
            drawParts(1.0 - p * 0.35);
            return true;
        }

        private function drawParts(scale:Number):void
        {
            var startX:Number;
            var w:Number;

            if (_hasHp && _hpMax > 0 && _hpBefore >= _hpCur)
            {
                var beforeRatio:Number = clamp01(Number(_hpBefore) / Number(_hpMax));
                var curRatio:Number = clamp01(Number(_hpCur) / Number(_hpMax));
                var beforePx:Number = BAR_WIDTH * beforeRatio;
                var curPx:Number = BAR_WIDTH * curRatio;
                w = (beforePx - curPx) * scale;
                startX = BAR_X + curPx;
            }
            else
            {
                w = damageToWidth(_damage) * scale;
                startX = BAR_X + BAR_WIDTH - w;
            }

            if (w < 3) w = 3;
            if (w > BAR_WIDTH) w = BAR_WIDTH;

            _bar.graphics.clear();
            _bar.graphics.beginFill(_color, 0.85);
            _bar.graphics.drawRect(startX, 0, w, BAR_HEIGHT);
            _bar.graphics.endFill();

            _shine.graphics.clear();
            _shine.graphics.beginFill(0xFFFFFF, 0.75);
            _shine.graphics.drawRect(startX - 1, -1, 2, BAR_HEIGHT + 2);
            _shine.graphics.endFill();
        }

        private function clamp01(v:Number):Number
        {
            if (v < 0) return 0;
            if (v > 1) return 1;
            return v;
        }

        private function damageToWidth(d:int):Number
        {
            if (d <= 0) return 0;
            if (d >= 750) return BAR_WIDTH;
            return 6.0 + (BAR_WIDTH - 6.0) * (Number(d) / 750.0);
        }

        private function normalizeColor(c:uint):uint
        {
            c = c & 0xFFFFFF;
            var r:int = (c >> 16) & 0xFF;
            var g:int = (c >> 8) & 0xFF;
            var b:int = c & 0xFF;
            if (r > 220 && g > 190 && b < 100) return 0xFFDC3C;
            if (r > 200 && g < 130 && b < 130) return 0xFF4C4C;
            if (g > 170 && r < 170) return 0x7CFF4C;
            return 0xFFDC3C;
        }

        public function dispose():void
        {
            if (_bar != null && _bar.parent != null) _bar.parent.removeChild(_bar);
            if (_shine != null && _shine.parent != null) _shine.parent.removeChild(_shine);
            _bar = null;
            _shine = null;
        }
    }
}
