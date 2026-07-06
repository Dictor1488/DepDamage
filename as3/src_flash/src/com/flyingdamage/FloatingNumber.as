package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFieldType;
    import flash.filters.GlowFilter;
    import flash.utils.getTimer;

    /**
     * One damage number that STICKS to a tank (by vehicleID) and flies upward.
     * Every frame it is positioned at the tank's current screen pos + a rising,
     * fading animation offset. Smooth upward motion is preserved.
     */
    public class FloatingNumber extends Sprite
    {
        public var vehicleID:String;

        private var _tf:TextField;
        private var _bornAt:int;
        private var _baseAlpha:Number;
        private var _lastX:Number = 0;
        private var _lastY:Number = 0;
        private var _hasPos:Boolean = false;

        private static const LIFETIME:Number = 1.6;
        private static const RISE_PIXELS:Number = 55.0;
        private static const FADE_START:Number = 0.5;
        // vertical offset above the tank origin (screen pixels)
        private static const ANCHOR_OFFSET_Y:Number = 0.0;

        public function FloatingNumber(vehicleID:String, damage:int,
                                       colorRGB:uint, fontSize:int, baseAlpha:Number)
        {
            this.vehicleID = vehicleID;
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
            _tf.defaultTextFormat = new TextFormat("$TitleFont", fontSize, colorRGB, true);
            _tf.text = String(damage);
            _tf.x = -_tf.textWidth / 2.0;
            _tf.y = -_tf.textHeight / 2.0;
            _tf.filters = [ new GlowFilter(0x000000, 1.0, 3, 3, 3, 2) ];

            addChild(_tf);
            this.alpha = _baseAlpha;
            this.visible = false; // shown once we have a valid position
        }

        /**
         * pos: {x, y, ok} from Python, or null if unavailable this frame.
         * Returns false when the animation is finished.
         */
        public function update(pos:Object):Boolean
        {
            var age:Number = (getTimer() - _bornAt) / 1000.0;
            if (age >= LIFETIME)
                return false;

            var progress:Number = age / LIFETIME;

            // Base position = tank's current screen position (sticks to tank).
            if (pos != null && pos.ok)
            {
                _lastX = pos.x;
                _lastY = pos.y;
                _hasPos = true;
            }

            if (!_hasPos)
            {
                // No position yet: stay hidden but keep the clock running.
                this.visible = false;
                return true;
            }

            this.visible = true;

            // Rise upward over the animation (screen y decreases upward).
            this.x = _lastX;
            this.y = _lastY + ANCHOR_OFFSET_Y - RISE_PIXELS * progress;

            // Fade out over the last part of the life.
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
