package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.filters.DropShadowFilter;
    import flash.filters.GlowFilter;
    import flash.text.AntiAliasType;
    import flash.text.GridFitType;
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
            cacheAsBitmap = true;
            _damage = damage;

            var color:uint = uint('0x' + colorHex);
            var size:int = Math.max(14, Math.min(32, fontSize));

            _tf = new TextField();
            _tf.mouseEnabled = false;
            _tf.selectable = false;
            _tf.antiAliasType = AntiAliasType.ADVANCED;
            _tf.gridFitType = GridFitType.PIXEL;
            _tf.sharpness = 180;
            _tf.thickness = 80;
            _tf.width = 240;
            _tf.height = 90;
            _tf.defaultTextFormat = new TextFormat(
                '$TitleFont',
                size,
                color,
                true,
                false,
                false,
                null,
                null,
                'center'
            );

            // Crisp game-style edge plus a compact soft shadow. This keeps the
            // number readable without the smeared low-resolution appearance.
            _tf.filters = [
                new GlowFilter(
                    0x000000,
                    0.78,
                    2.2,
                    2.2,
                    2.4,
                    1,
                    false,
                    false
                ),
                new DropShadowFilter(
                    1,
                    90,
                    0x000000,
                    0.92,
                    2.5,
                    2.5,
                    2.5,
                    1,
                    false,
                    false,
                    false
                )
            ];
            _tf.text = text;
            _tf.x = -120;
            _tf.y = -Math.round(size * 0.82);
            addChild(_tf);
        }

        public function get damage():int
        {
            return _damage;
        }

        public function updateScreenPosition(xPos:Number, yPos:Number, alphaValue:Number, isVisible:Boolean):void
        {
            x = Math.round(xPos);
            y = Math.round(yPos);
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