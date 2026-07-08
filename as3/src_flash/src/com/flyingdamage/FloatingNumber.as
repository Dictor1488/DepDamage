package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFieldType;
    import flash.filters.GlowFilter;
    import flash.filters.DropShadowFilter;
    import flash.utils.getTimer;

    public class FloatingNumber extends Sprite
    {
        public var vehicleID:String;

        private var _tf:TextField;
        private var _bornAt:int;
        private var _baseAlpha:Number;
        private var _markerX:Number = 0;
        private var _markerY:Number = 0;
        private var _hasMarker:Boolean = false;
        private var _targetColor:uint;
        private var _damage:int;
        private var _fontSize:int;

        private static const LIFETIME:Number = 2.0;
        private static const RISE_PIXELS:Number = 40.0;
        private static const FADE_START:Number = 0.75;
        private static const EMERGE_TIME:Number = 0.30;
        private static const WHITE_TINT_TIME:Number = 0.40;
        private static const DAMAGE_X_OFFSET:Number = -15.0;
        private static const DAMAGE_Y_OFFSET:Number = -96.0;

        public function FloatingNumber(vehicleID:String, damage:int, colorRGB:uint, fontSize:int, baseAlpha:Number, startX:Number = 0, startY:Number = 0, hasStart:Boolean = false)
        {
            this.vehicleID = vehicleID;
            _bornAt = getTimer();
            _baseAlpha = baseAlpha;
            _markerX = startX;
            _markerY = startY;
            _hasMarker = hasStart;
            _targetColor = normalizeDamageColor(colorRGB);
            _damage = damage;
            _fontSize = fontSize;

            _tf = new TextField();
            _tf.autoSize = TextFieldAutoSize.CENTER;
            _tf.selectable = false;
            _tf.mouseEnabled = false;
            _tf.multiline = false;
            _tf.wordWrap = false;
            _tf.background = false;
            _tf.border = false;
            _tf.type = TextFieldType.DYNAMIC;
            _tf.defaultTextFormat = new TextFormat("$TitleFont", _fontSize, 0xFFFFFF, true);
            _tf.text = String(_damage);
            _tf.x = -_tf.textWidth / 2.0;
            _tf.y = -_tf.textHeight / 2.0;
            _tf.filters = buildFilters(_targetColor);
            addChild(_tf);

            alpha = _baseAlpha;
            scaleX = scaleY = 0.82;
            visible = _hasMarker;
        }

        public function update(pos:Object):Boolean
        {
            var age:Number = (getTimer() - _bornAt) / 1000.0;
            if (age >= LIFETIME)
                return false;

            var progress:Number = age / LIFETIME;

            // Hit-time snapshot mode: take marker position only once, then do not
            // follow camera/marker anymore. This prevents the number from flying
            // across the screen when the camera moves after the hit.
            if (!_hasMarker && pos != null && pos.ok)
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
            x = _markerX + DAMAGE_X_OFFSET;
            y = _markerY + DAMAGE_Y_OFFSET - RISE_PIXELS * progress;

            applyEmerge(age);
            applyTint(age);
            applyFade(progress);

            return true;
        }

        private function applyEmerge(age:Number):void
        {
            if (age < EMERGE_TIME)
            {
                var p:Number = age / EMERGE_TIME;
                scaleX = scaleY = 0.82 + 0.18 * easeOut(p);
            }
            else
            {
                scaleX = scaleY = 1.0;
            }
        }

        private function applyTint(age:Number):void
        {
            var c:uint;
            if (age < WHITE_TINT_TIME)
            {
                c = mixColor(0xFFFFFF, _targetColor, age / WHITE_TINT_TIME);
            }
            else
            {
                c = _targetColor;
            }
            _tf.textColor = c;
        }

        private function applyFade(progress:Number):void
        {
            if (progress < FADE_START)
                alpha = _baseAlpha;
            else
                alpha = _baseAlpha * (1.0 - (progress - FADE_START) / (1.0 - FADE_START));
        }

        private function easeOut(p:Number):Number
        {
            if (p < 0) p = 0;
            if (p > 1) p = 1;
            return 1.0 - (1.0 - p) * (1.0 - p);
        }

        private function normalizeDamageColor(c:uint):uint
        {
            c = c & 0xFFFFFF;
            var r:int = (c >> 16) & 0xFF;
            var g:int = (c >> 8) & 0xFF;
            var b:int = c & 0xFF;

            if (r > 220 && g > 190 && b < 100) return 0xFFDC3C;
            if (r > 200 && g < 120 && b < 120) return 0xFF4C4C;
            if (g > 170 && r < 160) return 0x7CFF4C;
            if (b > 160 && r < 160) return 0x4CC8FF;
            if (r > 210 && g > 100 && g < 190 && b < 90) return 0xFF9A2E;
            if (r > 170 && b > 150) return 0xD979FF;
            return c;
        }

        private function buildFilters(c:uint):Array
        {
            return [
                new GlowFilter(0x000000, 1.0, 3.0, 3.0, 5.0, 2),
                new GlowFilter(0x000000, 0.75, 6.0, 6.0, 2.0, 2),
                new GlowFilter(c, 0.35, 8.0, 8.0, 1.1, 1),
                new DropShadowFilter(1.0, 90, 0x000000, 0.75, 2.0, 2.0, 1.0, 2)
            ];
        }

        private function mixColor(a:uint, b:uint, t:Number):uint
        {
            if (t < 0) t = 0;
            if (t > 1) t = 1;
            var ar:int = (a >> 16) & 0xFF;
            var ag:int = (a >> 8) & 0xFF;
            var ab:int = a & 0xFF;
            var br:int = (b >> 16) & 0xFF;
            var bg:int = (b >> 8) & 0xFF;
            var bb:int = b & 0xFF;
            var rr:int = ar + int((br - ar) * t);
            var rg:int = ag + int((bg - ag) * t);
            var rb:int = ab + int((bb - ab) * t);
            return (rr << 16) | (rg << 8) | rb;
        }

        public function dispose():void
        {
            if (_tf != null)
            {
                if (_tf.parent != null)
                    _tf.parent.removeChild(_tf);
                _tf = null;
            }
        }
    }
}
