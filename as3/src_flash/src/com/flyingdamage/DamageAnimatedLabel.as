package com.flyingdamage
{
    import flash.display.DisplayObject;
    import flash.text.TextField;

    public class DamageAnimatedLabel
    {
        private var _target:DisplayObject;
        private var _tf:TextField;
        private var _targetColor:uint;
        private var _baseAlpha:Number;
        private var _risePixels:Number;

        public static const LIFETIME:Number = 2.0;
        public static const MOVE_TIME:Number = 2.0;
        public static const FADE_OUT_TIME:Number = 0.5;
        public static const EMERGE_TIME:Number = 0.30;
        public static const WHITE_TINT_TIME:Number = 0.40;
        public static const START_SCALE:Number = 0.82;
        public static const END_SCALE:Number = 1.0;

        public function DamageAnimatedLabel(target:DisplayObject, textField:TextField, targetColor:uint, baseAlpha:Number, risePixels:Number = 40.0)
        {
            _target = target;
            _tf = textField;
            _targetColor = targetColor & 0xFFFFFF;
            _baseAlpha = baseAlpha;
            _risePixels = risePixels;
            if (_target != null)
            {
                _target.alpha = _baseAlpha;
                _target.scaleX = START_SCALE;
                _target.scaleY = START_SCALE;
            }
            if (_tf != null)
                _tf.textColor = 0xFFFFFF;
        }

        public function isAlive(age:Number):Boolean
        {
            return age < LIFETIME;
        }

        public function getYOffset(age:Number):Number
        {
            var moveProgress:Number = clamp01(age / MOVE_TIME);
            return -_risePixels * moveProgress;
        }

        public function update(age:Number):void
        {
            applyEmerge(age);
            applyTint(age);
            applyFade(age);
        }

        private function applyEmerge(age:Number):void
        {
            if (_target == null)
                return;
            if (age < EMERGE_TIME)
            {
                var p:Number = easeOut(age / EMERGE_TIME);
                var s:Number = START_SCALE + (END_SCALE - START_SCALE) * p;
                _target.scaleX = s;
                _target.scaleY = s;
            }
            else
            {
                _target.scaleX = END_SCALE;
                _target.scaleY = END_SCALE;
            }
        }

        private function applyTint(age:Number):void
        {
            if (_tf == null)
                return;
            if (age < WHITE_TINT_TIME)
                _tf.textColor = mixColor(0xFFFFFF, _targetColor, age / WHITE_TINT_TIME);
            else
                _tf.textColor = _targetColor;
        }

        private function applyFade(age:Number):void
        {
            if (_target == null)
                return;
            var fadeStart:Number = LIFETIME - FADE_OUT_TIME;
            if (age < fadeStart)
                _target.alpha = _baseAlpha;
            else
                _target.alpha = _baseAlpha * (1.0 - clamp01((age - fadeStart) / FADE_OUT_TIME));
        }

        private function easeOut(p:Number):Number
        {
            p = clamp01(p);
            return 1.0 - (1.0 - p) * (1.0 - p);
        }

        private function clamp01(v:Number):Number
        {
            if (v < 0) return 0;
            if (v > 1) return 1;
            return v;
        }

        private function mixColor(a:uint, b:uint, t:Number):uint
        {
            t = clamp01(t);
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
    }
}
