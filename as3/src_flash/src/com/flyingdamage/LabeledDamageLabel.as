package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFieldType;
    import flash.filters.GlowFilter;
    import flash.filters.DropShadowFilter;

    public class LabeledDamageLabel extends Sprite
    {
        public var textField:TextField;
        public var color:uint;
        public var damageType:String;

        public function LabeledDamageLabel(type:String, fontSize:int = 15)
        {
            mouseEnabled = false;
            mouseChildren = false;
            damageType = type;
            color = getTypeColor(type);

            textField = new TextField();
            textField.autoSize = TextFieldAutoSize.CENTER;
            textField.selectable = false;
            textField.mouseEnabled = false;
            textField.multiline = false;
            textField.wordWrap = false;
            textField.background = false;
            textField.border = false;
            textField.type = TextFieldType.DYNAMIC;
            textField.defaultTextFormat = new TextFormat("$TitleFont", fontSize, color, true);
            textField.text = getTypeText(type);
            textField.x = -textField.textWidth / 2.0;
            textField.y = -textField.textHeight / 2.0;
            textField.filters = [
                new GlowFilter(0x000000, 1.0, 3.0, 3.0, 5.0, 2),
                new GlowFilter(0x000000, 0.75, 6.0, 6.0, 2.0, 2),
                new GlowFilter(color, 0.35, 8.0, 8.0, 1.1, 1),
                new DropShadowFilter(1.0, 90, 0x000000, 0.75, 2.0, 2.0, 1.0, 2)
            ];
            addChild(textField);
        }

        public static function getTypeText(type:String):String
        {
            if (type == VehicleMarkerFlags.DAMAGE_BLOCKED) return "BLOCK";
            if (type == VehicleMarkerFlags.DAMAGE_BLOCKED_CRIT) return "CRIT BLOCK";
            if (type == VehicleMarkerFlags.DAMAGE_RICOCHET) return "RICOCHET";
            return "BLOCK";
        }

        public static function getTypeColor(type:String):uint
        {
            if (type == VehicleMarkerFlags.DAMAGE_BLOCKED_CRIT) return 0xFFDC3C;
            if (type == VehicleMarkerFlags.DAMAGE_RICOCHET) return 0xD9D9D9;
            return 0xB0E0FF;
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
    }
}
