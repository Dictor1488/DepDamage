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

        // Ported from the working DamageAnimatedLabel.as:
        // emerge 0.3s, white tint 0.4s, upward move 2s, fade over last 0.5s.
        public static const LIFETIME:Number = 2.0;
        public static const MOVE_TIME:Number = 2.0;
        public static const EMERGE_TIME:Number = 0.30;
        public static const WHITE_TINT_TIME:Number = 0.40;
        public static const FADE_OUT_TIME:Number = 0.50;

        public function DamageAnimatedLabel(target:DisplayObject, textField:TextField, targetColor:uint, baseAlpha:Number, risePixels:Number = 40.0)
        {
            _target = target;
            _tf = textField;
            _targetColor = targetColor & 0xFFFFFF;
            _baseAlpha = baseAlpha;
            _risePixels = risePixels;

            if (_target != null)
                _target.alpha = 0.0;
            if (_tf != null)
                _tf.textColor = 0xFFFFFF;
        }

        public function isAlive(age:Number):Boolean
        {
            return age < LIFETIME;
        }

        public function getYOffset(age:Number):Number
        {
            return -_risePixels * clamp01(age / MOVE_TIME);
        }

        public function update(age:Number):void
        {
            applyEmergeAndFade(age);
            applyTint(age);
        }

        private function applyEmergeAndFade(age:Number):void
        {
            if (_target == null)
                return;

            var a:Number = _baseAlpha;
            if (age < EMERGE_TIME)
                a = _baseAlpha * clamp01(age / EMERGE_TIME);

            var fadeStart:Number = LIFETIME - FADE_OUT_TIME;
            if (age >= fadeStart)
                a *= 1.0 - clamp01((age - fadeStart) / FADE_OUT_TIME);

            _target.alpha = a;
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
