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

        public function FloatingDamageNumber(text:String, damage:int, colorHex:String, fontSize:int)
        {
            mouseEnabled = false;
            mouseChildren = false;
            _damage = damage;

            var color:uint = uint('0x' + colorHex);
            var size:int = Math.max(14, Math.min(32, fontSize));

            _tf = new TextField();
            _tf.mouseEnabled = false;
            _tf.selectable = false;
            _tf.antiAliasType = AntiAliasType.ADVANCED;
            _tf.width = 220;
            _tf.height = 80;
            _tf.defaultTextFormat = new TextFormat(
                '$FieldFont',
                size,
                color,
                true,
                false,
                false,
                null,
                null,
                'center'
            );

            // Clean readable style: slightly bold text with a soft black shadow.
            _tf.filters = [
                new DropShadowFilter(
                    1,
                    90,
                    0x000000,
                    0.85,
                    3,
                    3,
                    2.2,
                    1,
                    false,
                    false,
                    false
                )
            ];
            _tf.text = text;
            _tf.x = -110;
            _tf.y = -20;
            addChild(_tf);
        }

        public function get damage():int
        {
            return _damage;
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
