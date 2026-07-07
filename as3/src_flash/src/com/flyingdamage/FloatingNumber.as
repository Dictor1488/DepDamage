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
        public var vehicleID:String;

        private var _tf:TextField;
        private var _bornAt:int;
        private var _baseAlpha:Number;
        private var _markerX:Number = 0;
        private var _markerY:Number = 0;
        private var _hasMarker:Boolean = false;

        private static const LIFETIME:Number = 2.0;
        private static const RISE_PIXELS:Number = 40.0;
        private static const FADE_START:Number = 0.75;
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

            alpha = _baseAlpha;
            visible = _hasMarker;
        }

        public function update(pos:Object):Boolean
        {
            var age:Number = (getTimer() - _bornAt) / 1000.0;
            if (age >= LIFETIME)
                return false;

            var progress:Number = age / LIFETIME;

            // VehicleMarker-style anchoring: marker position may move every frame,
            // damage label keeps local x/y offsets inside that moving marker.
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
            x = _markerX + DAMAGE_X_OFFSET;
            y = _markerY + DAMAGE_Y_OFFSET - RISE_PIXELS * progress;

            if (progress < FADE_START)
                alpha = _baseAlpha;
            else
                alpha = _baseAlpha * (1.0 - (progress - FADE_START) / (1.0 - FADE_START));

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
