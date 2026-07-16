package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.filters.DropShadowFilter;
    import flash.text.AntiAliasType;
    import flash.text.TextField;
    import flash.text.TextFormat;

    public final class FloatingDamageNumber extends Sprite
    {
        private var _tf:TextField;
        private var _damage:int;

        public function FloatingDamageNumber(text:String, damage:int)
        {
            mouseEnabled = false;
            mouseChildren = false;
            _damage = damage;

            _tf = new TextField();
            _tf.mouseEnabled = false;
            _tf.selectable = false;
            _tf.antiAliasType = AntiAliasType.ADVANCED;
            _tf.width = 220;
            _tf.height = 80;
            _tf.defaultTextFormat = new TextFormat(
                '$FieldFont',
                18,
                0xFFFFFF,
                false,
                false,
                false,
                null,
                null,
                'center'
            );

            // Exact values from the supplied ProTanki vehicle-marker config:
            // distance 1, angle 90, black, alpha 1, blur 4, strength 180.
            _tf.filters = [
                new DropShadowFilter(
                    1,
                    90,
                    0x000000,
                    1.0,
                    4,
                    4,
                    180,
                    1,
                    false,
                    false,
                    false
                )
            ];
            _tf.htmlText = text;
            _tf.x = -110;
            _tf.y = -18;
            addChild(_tf);
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

        public function updateScreenPosition(xPos:Number, yPos:Number, alphaValue:Number, isVisible:Boolean):void
        {
            x = xPos;
            y = yPos;
            alpha = alphaValue;
            visible = isVisible;
        }

        public function dispose():void
        {
            if (parent)
                parent.removeChild(this);
        }
    }
}
