package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.filters.GlowFilter;
    import flash.text.AntiAliasType;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.utils.getTimer;

    public final class FloatingDamageNumber extends Sprite
    {
        private var _tf:TextField;
        private var _startTime:int;
        private var _duration:Number;
        private var _startY:Number;
        private var _endY:Number;
        private var _damage:int;

        public function FloatingDamageNumber(text:String, damage:int, xPos:Number, yPos:Number, speed:Number, maxRange:Number)
        {
            mouseEnabled = false;
            mouseChildren = false;
            x = xPos;
            y = yPos;
            alpha = 0;
            _damage = damage;
            _duration = Math.max(0.1, speed) * 1000;
            _startY = yPos;
            _endY = yPos - maxRange;

            _tf = new TextField();
            _tf.mouseEnabled = false;
            _tf.selectable = false;
            _tf.antiAliasType = AntiAliasType.ADVANCED;
            _tf.width = 220;
            _tf.height = 80;
            _tf.defaultTextFormat = new TextFormat('$FieldFont', 18, 0xFFFFFF, false, false, false, null, null, 'center');
            _tf.filters = [new GlowFilter(0x000000, 1, 3, 3, 2, 1)];
            _tf.htmlText = text;
            _tf.x = -110;
            _tf.y = 0;
            addChild(_tf);

            _startTime = getTimer();
            addEventListener(Event.ENTER_FRAME, onFrame, false, 0, true);
        }

        public function get damage():int
        {
            return _damage;
        }

        public function setDamage(value:int, text:String):void
        {
            _damage = value;
            _tf.htmlText = text;
        }

        private function onFrame(e:Event):void
        {
            var t:Number = (getTimer() - _startTime) / _duration;
            if (t >= 1)
            {
                dispose();
                return;
            }

            // The parent movie now lives in the fixed battle HUD plane, so only
            // local Y is animated. No marker, vehicle or camera coordinates are
            // consulted after spawn.
            y = _startY + (_endY - _startY) * t;

            if (t < 0.15)
                alpha = t / 0.15;
            else if (t > 0.75)
                alpha = 1 - ((t - 0.75) / 0.25);
            else
                alpha = 1;
        }

        public function dispose():void
        {
            removeEventListener(Event.ENTER_FRAME, onFrame);
            if (parent)
                parent.removeChild(this);
        }
    }
}
