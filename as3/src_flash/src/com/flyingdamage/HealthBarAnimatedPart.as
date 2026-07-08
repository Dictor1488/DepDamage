package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.filters.GlowFilter;

    public class HealthBarAnimatedPart extends Sprite
    {
        private var _bar:Sprite;
        private var _shine:Sprite;
        private var _color:uint;
        private var _damage:int;
        private var _hasHp:Boolean;
        private var _hpCur:int;
        private var _hpBefore:int;
        private var _hpMax:int;

        // Same marker geometry as the original HealthBar: 70px bar and splash
        // anchored at the current HP position, then stretched over lost HP delta.
        public static const LIFETIME:Number = 0.65;
        public static const BAR_WIDTH:Number = 70.0;
        public static const BAR_HEIGHT:Number = 4.0;
        public static const DMG_BAR_X:Number = -35.0;
        public static const DMG_BAR_Y:Number = -19.0;

        public function HealthBarAnimatedPart(damage:int, color:uint, hasHp:Boolean = false, hpCur:int = 0, hpBefore:int = 0, hpMax:int = 0)
        {
            _damage = damage;
            _color = normalizeColor(color);
            _hasHp = hasHp;
            _hpCur = hpCur;
            _hpBefore = hpBefore;
            _hpMax = hpMax;

            mouseEnabled = false;
            mouseChildren = false;

            _bar = new Sprite();
            _bar.filters = [new GlowFilter(0x000000, 0.9, 3, 3, 2, 2), new GlowFilter(_color, 0.45, 7, 4, 1.0, 1)];
            addChild(_bar);

            _shine = new Sprite();
            _shine.filters = [new GlowFilter(0xFFFFFF, 0.65, 4, 4, 1.2, 1)];
            addChild(_shine);

            draw(1.0);
        }

        public function update(age:Number):Boolean
        {
            if (age >= LIFETIME)
                return false;
            var p:Number = age / LIFETIME;
            alpha = 1.0 - p;
            draw(1.0 - p * 0.25);
            return true;
        }

        private function draw(scale:Number):void
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
                startX = DMG_BAR_X + curPx;
            }
            else
            {
                w = damageToWidth(_damage) * scale;
                startX = DMG_BAR_X + BAR_WIDTH - w;
            }

            if (w < 3) w = 3;
            if (w > BAR_WIDTH) w = BAR_WIDTH;

            _bar.graphics.clear();
            _bar.graphics.beginFill(_color, 0.75);
            _bar.graphics.drawRect(startX, 0, w, BAR_HEIGHT);
            _bar.graphics.endFill();

            _shine.graphics.clear();
            _shine.graphics.beginFill(0xFFFFFF, 0.60);
            _shine.graphics.drawRect(startX - 1, -1, 2, BAR_HEIGHT + 2);
            _shine.graphics.endFill();
        }

        private function damageToWidth(d:int):Number
        {
            if (d <= 0) return 0;
            if (d >= 750) return BAR_WIDTH;
            return 6.0 + (BAR_WIDTH - 6.0) * (Number(d) / 750.0);
        }

        private function normalizeColor(c:uint):uint
        {
            return VehicleMarkerFlags.getColorRGB(VehicleMarkerFlags.getColorNameFromRGB(c));
        }

        private function clamp01(v:Number):Number
        {
            if (v < 0) return 0;
            if (v > 1) return 1;
            return v;
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
