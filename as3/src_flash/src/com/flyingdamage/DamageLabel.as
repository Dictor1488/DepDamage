package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFieldType;
    import flash.filters.GlowFilter;
    import flash.filters.DropShadowFilter;

    public class DamageLabel extends Sprite
    {
        public var textField:TextField;
        public var color:uint;
        public var damageType:String;
        public var sourceFlag:uint;

        public function DamageLabel(value:int, fontSize:int, colorRGB:uint, source:uint = 0, type:String = "shot")
        {
            mouseEnabled = false;
            mouseChildren = false;

            sourceFlag = source;
            damageType = type;
            color = normalizeDamageColor(colorRGB, sourceFlag);

            textField = new TextField();
            textField.autoSize = TextFieldAutoSize.CENTER;
            textField.selectable = false;
            textField.mouseEnabled = false;
            textField.multiline = false;
            textField.wordWrap = false;
            textField.background = false;
            textField.border = false;
            textField.type = TextFieldType.DYNAMIC;
            textField.defaultTextFormat = new TextFormat("$TitleFont", fontSize, 0xFFFFFF, true);
            textField.text = String(value);
            textField.x = -textField.textWidth / 2.0;
            textField.y = -textField.textHeight / 2.0;
            textField.filters = getMarkerStyleFilters(color);
            addChild(textField);
        }

        public function dispose():void
        {
            if (textField != null)
            {
                if (textField.parent != null)
                    textField.parent.removeChild(textField);
                textField = null;
            }
        }

        private function normalizeDamageColor(c:uint, source:uint):uint
        {
            c = c & 0xFFFFFF;
            if (c != 0)
            {
                var r:int = (c >> 16) & 0xFF;
                var g:int = (c >> 8) & 0xFF;
                var b:int = c & 0xFF;
                if (r > 220 && g > 190 && b < 100) return 0xFFDC3C;
                if (r > 200 && g < 120 && b < 120) return 0xFF4C4C;
                if (g > 170 && r < 160) return 0x7CFF4C;
                if (b > 160 && r < 160) return 0x4CC8FF;
                if (r > 210 && g > 100 && g < 190 && b < 90) return 0xFF9A2E;
                if (r > 170 && b > 150) return 0xD979FF;
                return c;
            }
            return VehicleMarkerFlags.getColorRGB(VehicleMarkerFlags.getDamageColorName(source, "red"));
        }

        public static function getMarkerStyleFilters(c:uint):Array
        {
            return [
                new GlowFilter(0x000000, 1.0, 3.0, 3.0, 5.0, 2),
                new GlowFilter(0x000000, 0.75, 6.0, 6.0, 2.0, 2),
                new GlowFilter(c, 0.35, 8.0, 8.0, 1.1, 1),
                new DropShadowFilter(1.0, 90, 0x000000, 0.75, 2.0, 2.0, 1.0, 2)
            ];
        }
    }
}
