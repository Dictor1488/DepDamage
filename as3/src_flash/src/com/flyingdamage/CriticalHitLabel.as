package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFieldType;
    import flash.filters.GlowFilter;
    import flash.filters.DropShadowFilter;

    public class CriticalHitLabel extends Sprite
    {
        private var _icon:Sprite;
        private var _tf:TextField;

        public static const ICON_SIZE:Number = 12.0;
        public static const TEXT_OFFSET:Number = 4.0;

        public function CriticalHitLabel(text:String = "CRIT")
        {
            mouseEnabled = false;
            mouseChildren = false;

            _icon = new Sprite();
            _icon.graphics.beginFill(0xFFDC3C, 0.95);
            _icon.graphics.drawCircle(0, 0, ICON_SIZE * 0.5);
            _icon.graphics.endFill();
            _icon.graphics.lineStyle(1, 0x000000, 0.95);
            _icon.graphics.moveTo(-3, -3);
            _icon.graphics.lineTo(3, 3);
            _icon.graphics.moveTo(3, -3);
            _icon.graphics.lineTo(-3, 3);
            _icon.filters = [ new GlowFilter(0x000000, 1.0, 3, 3, 3, 2), new GlowFilter(0xFFDC3C, 0.55, 6, 6, 1.2, 1) ];
            addChild(_icon);

            _tf = new TextField();
            _tf.autoSize = TextFieldAutoSize.LEFT;
            _tf.selectable = false;
            _tf.mouseEnabled = false;
            _tf.type = TextFieldType.DYNAMIC;
            _tf.defaultTextFormat = new TextFormat("$TitleFont", 13, 0xFFDC3C, true);
            _tf.text = text;
            _tf.x = ICON_SIZE * 0.5 + TEXT_OFFSET;
            _tf.y = -_tf.textHeight * 0.5;
            _tf.filters = [ new GlowFilter(0x000000, 1.0, 3, 3, 4, 2), new DropShadowFilter(1, 90, 0x000000, 0.65, 2, 2, 1, 2) ];
            addChild(_tf);
        }

        public function layoutAfterDamageLabel(label:DamageLabel, spacing:Number = 8.0):void
        {
            if (label == null || label.textField == null)
                return;
            x = label.x + label.textField.x + label.textField.textWidth * 0.5 + spacing + ICON_SIZE * 0.5;
            y = label.y;
        }

        public function dispose():void
        {
            if (_icon != null && _icon.parent != null) _icon.parent.removeChild(_icon);
            if (_tf != null && _tf.parent != null) _tf.parent.removeChild(_tf);
            _icon = null;
            _tf = null;
        }
    }
}
