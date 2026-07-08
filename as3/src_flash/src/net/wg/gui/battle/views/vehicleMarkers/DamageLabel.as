package net.wg.gui.battle.views.vehicleMarkers
{
    import flash.display.Sprite;
    import flash.filters.GlowFilter;
    import flash.text.TextField;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFormat;

    /** Compact color-slot source for damage text formats. */
    public class DamageLabel extends Sprite
    {
        public var tfMap:Object = {};

        public function DamageLabel()
        {
            super();
            createSlot("white",  0xFFFFFF);
            createSlot("yellow", 0xFFDC3C);
            createSlot("orange", 0xFF9630);
            createSlot("red",    0xFF4646);
            createSlot("green",  0x78FF78);
            createSlot("gold",   0xFFD24A);
            createSlot("blue",   0x5ADCFF);
            createSlot("purple", 0xC060FF);
        }

        private function createSlot(name:String, color:uint) : void
        {
            var tf:TextField = new TextField();
            tf.mouseEnabled = false;
            tf.selectable = false;
            tf.autoSize = TextFieldAutoSize.LEFT;
            tf.defaultTextFormat = makeFormat(color);
            tf.filters = [new GlowFilter(0x000000, 1, 4, 4, 4, 2)];
            tf.visible = false;
            addChild(tf);
            tfMap[name] = tf;
        }

        private function makeFormat(color:uint) : TextFormat
        {
            var f:TextFormat = new TextFormat();
            f.font = "$FieldFont";
            f.size = 18;
            f.bold = true;
            f.color = color;
            return f;
        }

        public function showTF(name:String) : TextField
        {
            var tf:TextField = tfMap[name] as TextField;
            if(tf == null)
            {
                tf = tfMap["white"] as TextField;
            }
            return tf;
        }
    }
}
