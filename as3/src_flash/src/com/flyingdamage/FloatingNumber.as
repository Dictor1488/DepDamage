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
     * One damage number.
     *
     * Screen mode is the safe/default mode: fixed start screen x/y, then rise.
     * World mode is experimental. If world projection fails, the number falls
     * back to the captured screen point instead of being deleted immediately.
     */
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
        private var _worldFailed:Boolean = false;

        private static const DEFAULT_LIFETIME:Number = 1.6;
        private static const DEFAULT_RISE:Number = 55.0;
        private static const FADE_START:Number = 0.5;

        public function FloatingNumber(app:FlyingDamageApp, data:Object)
        {
            _app = app;
            _mode = data.mode == null ? "screen" : String(data.mode);
            _startX = Number(data.x);
            _startY = Number(data.y);
            _wx = Number(data.wx);
            _wy = Number(data.wy);
            _wz = Number(data.wz);
            _rise = data.rise == null ? DEFAULT_RISE : Number(data.rise);
            _lifeTime = data.life == null ? DEFAULT_LIFETIME : Number(data.life);
            if (_lifeTime <= 0.1) _lifeTime = DEFAULT_LIFETIME;

            _bornAt = getTimer();
            _baseAlpha = Number(data.alpha);
            if (isNaN(_baseAlpha)) _baseAlpha = 1.0;

            _tf = new TextField();
            _tf.autoSize = TextFieldAutoSize.CENTER;
            _tf.selectable = false;
            _tf.mouseEnabled = false;
            _tf.multiline = false;
            _tf.wordWrap = false;
            _tf.background = false;
            _tf.border = false;
            _tf.type = TextFieldType.DYNAMIC;
            _tf.defaultTextFormat = new TextFormat("Arial", int(data.size), uint(data.color), true);
            _tf.text = String(int(data.dmg));
            _tf.x = -_tf.textWidth / 2.0;
            _tf.y = -_tf.textHeight / 2.0;
            _tf.filters = [ new GlowFilter(0x000000, 1.0, 3, 3, 3, 2) ];

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

            if (_mode == "world" && !_worldFailed)
            {
                var pos:Object = _app.projectWorld(_wx, _wy + _rise * progress, _wz);
                if (pos != null && pos.ok)
                {
                    this.x = Number(pos.x);
                    this.y = Number(pos.y);
                }
                else
                {
                    // Do NOT delete the number. Fall back to the hit-time screen
                    // point so the player still sees damage.
                    _worldFailed = true;
                    this.x = _startX;
                    this.y = _startY - DEFAULT_RISE * progress;
                }
            }
            else
            {
                this.x = _startX;
                this.y = _startY - DEFAULT_RISE * progress;
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
