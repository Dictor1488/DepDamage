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
        private var _app:FlyingDamageApp;
        private var _tf:TextField;
        private var _bornAt:int;
        private var _baseAlpha:Number;
        private var _mode:String;
        private var _lifeTime:Number;
        private var _rise:Number;

        private var _startX:Number;
        private var _startY:Number;
        private var _wx:Number;
        private var _wy:Number;
        private var _wz:Number;
        private var _vehicleID:int;
        private var _failed:Boolean = false;

        private static const DEFAULT_LIFETIME:Number = 1.6;
        private static const DEFAULT_RISE:Number = 55.0;
        private static const FADE_START:Number = 0.5;

        public static function createScreen(app:FlyingDamageApp, x:Number, y:Number,
                                            damage:int, colorRGB:uint,
                                            fontSize:int, alpha:Number,
                                            rise:Number, life:Number):FloatingNumber
        {
            return new FloatingNumber(app, "screen", x, y, 0, 0, 0, 0, damage,
                                      colorRGB, fontSize, alpha, rise, life);
        }

        public static function createWorld(app:FlyingDamageApp, wx:Number, wy:Number, wz:Number,
                                           fallbackX:Number, fallbackY:Number,
                                           damage:int, colorRGB:uint,
                                           fontSize:int, alpha:Number,
                                           rise:Number, life:Number):FloatingNumber
        {
            return new FloatingNumber(app, "world", fallbackX, fallbackY, wx, wy, wz, 0,
                                      damage, colorRGB, fontSize, alpha, rise, life);
        }

        public static function createVehicle(app:FlyingDamageApp, vehicleID:int,
                                             fallbackX:Number, fallbackY:Number,
                                             damage:int, colorRGB:uint,
                                             fontSize:int, alpha:Number,
                                             riseMeters:Number, life:Number):FloatingNumber
        {
            return new FloatingNumber(app, "vehicle", fallbackX, fallbackY, 0, 0, 0, vehicleID,
                                      damage, colorRGB, fontSize, alpha, riseMeters, life);
        }

        public function FloatingNumber(app:FlyingDamageApp, mode:String,
                                       startX:Number, startY:Number,
                                       wx:Number, wy:Number, wz:Number,
                                       vehicleID:int,
                                       damage:int, colorRGB:uint,
                                       fontSize:int, baseAlpha:Number,
                                       rise:Number, life:Number)
        {
            _app = app;
            _mode = mode;
            _startX = startX;
            _startY = startY;
            _wx = wx;
            _wy = wy;
            _wz = wz;
            _vehicleID = vehicleID;
            _rise = isNaN(rise) ? DEFAULT_RISE : rise;
            _lifeTime = isNaN(life) ? DEFAULT_LIFETIME : life;
            if (_lifeTime <= 0.1) _lifeTime = DEFAULT_LIFETIME;
            if (_rise <= 0.0) _rise = DEFAULT_RISE;

            _bornAt = getTimer();
            _baseAlpha = isNaN(baseAlpha) ? 1.0 : baseAlpha;

            _tf = new TextField();
            _tf.autoSize = TextFieldAutoSize.CENTER;
            _tf.selectable = false;
            _tf.mouseEnabled = false;
            _tf.multiline = false;
            _tf.wordWrap = false;
            _tf.background = false;
            _tf.border = false;
            _tf.type = TextFieldType.DYNAMIC;
            _tf.embedFonts = false;
            _tf.defaultTextFormat = new TextFormat("Arial", fontSize, colorRGB, true);
            _tf.text = String(damage);
            _tf.x = -_tf.textWidth / 2.0 - 4.0;
            _tf.y = -_tf.textHeight / 2.0 - 4.0;
            _tf.filters = [ new GlowFilter(0x000000, 1.0, 4, 4, 4, 2) ];

            addChild(_tf);
            this.alpha = _baseAlpha;
            this.visible = true;

            update();
        }

        public function update():Boolean
        {
            var age:Number = (getTimer() - _bornAt) / 1000.0;
            if (age >= _lifeTime)
                return false;

            var progress:Number = age / _lifeTime;

            if (_mode == "vehicle" && !_failed)
            {
                var vpos:Object = _app.projectVehicle(_vehicleID, _rise * progress);
                if (vpos != null && vpos.ok)
                {
                    this.x = Number(vpos.x);
                    this.y = Number(vpos.y);
                }
                else
                {
                    _failed = true;
                    this.x = _startX;
                    this.y = _startY - DEFAULT_RISE * progress;
                }
            }
            else if (_mode == "world" && !_failed)
            {
                var pos:Object = _app.projectWorld(_wx, _wy + _rise * progress, _wz);
                if (pos != null && pos.ok)
                {
                    this.x = Number(pos.x);
                    this.y = Number(pos.y);
                }
                else
                {
                    _failed = true;
                    this.x = _startX;
                    this.y = _startY - DEFAULT_RISE * progress;
                }
            }
            else
            {
                this.x = _startX;
                this.y = _startY - _rise * progress;
            }

            if (progress < FADE_START)
                this.alpha = _baseAlpha;
            else
                this.alpha = _baseAlpha * (1.0 - (progress - FADE_START) / (1.0 - FADE_START));

            return true;
        }

        public function dispose():void
        {
            _app = null;
            if (_tf != null)
            {
                if (_tf.parent != null)
                    _tf.parent.removeChild(_tf);
                _tf = null;
            }
        }
    }
}