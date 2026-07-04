package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFieldType;
    import flash.filters.GlowFilter;
    import flash.utils.getTimer;

    public class FloatingNumber extends Sprite
    {
        private var _tf:TextField;
        private var _bornAt:int;
        private var _startY:Number;
        private var _baseAlpha:Number;

        private static const LIFETIME:Number = 1.6;
        private static const RISE_PIXELS:Number = 55.0;
        private static const FADE_START:Number = 0.5;

        public function FloatingNumber(damage:int, colorRGB:uint, fontSize:int, baseAlpha:Number)
        {
            _bornAt = getTimer();
            _baseAlpha = baseAlpha;

            _tf = new TextField();
            _tf.autoSize = TextFieldAutoSize.CENTER;
            _tf.selectable = false;
            _tf.mouseEnabled = false;
            _tf.multiline = false;
            _tf.wordWrap = false;
            _tf.background = false;
            _tf.border = false;
            _tf.type = TextFieldType.DYNAMIC;
            // NORMAL antialias works with device fonts; ADVANCED needs embedded.
            _tf.defaultTextFormat = new TextFormat("$TitleFont", fontSize, colorRGB, true);
            _tf.text = String(damage);
            _tf.x = -_tf.textWidth / 2.0;
            _tf.y = -_tf.textHeight / 2.0;
            _tf.filters = [ new GlowFilter(0x000000, 1.0, 3, 3, 3, 2) ];

            addChild(_tf);
            this.alpha = _baseAlpha;
        }

        public function setStart(x:Number, y:Number):void
        {
            _startY = y;
            this.x = x;
            this.y = y;
        }

        public function update():Boolean
        {
            var age:Number = (getTimer() - _bornAt) / 1000.0;
            if (age >= LIFETIME)
                return false;
            var progress:Number = age / LIFETIME;
            this.y = _startY - RISE_PIXELS * progress;
            if (progress < FADE_START)
                this.alpha = _baseAlpha;
            else
                this.alpha = _baseAlpha * (1.0 - (progress - FADE_START) / (1.0 - FADE_START));
            return true;
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
