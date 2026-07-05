package com.under_pressure.mastery
{
    import flash.display.Graphics;
    import flash.display.Shape;
    import flash.display.Sprite;
    import flash.filters.DropShadowFilter;
    import flash.text.TextField;
    import flash.text.TextFieldAutoSize;

    public class MasteryBattleResultBadge extends Sprite
    {
        private var _bg:Shape;
        private var _title:TextField;
        private var _value:TextField;
        private var _shadow:DropShadowFilter;
        private var _titleText:String = "Marks";
        private var _mark:Number = 0.0;
        private var _delta:Number = 0.0;

        public function MasteryBattleResultBadge()
        {
            super();
            mouseEnabled = false;
            mouseChildren = false;
            visible = false;

            _shadow = new DropShadowFilter(1, 45, 0x000000, 0.85, 2, 2, 1.2, 1);
            _bg = new Shape();
            addChild(_bg);
            _title = _makeText(12, 0xB8C4D0);
            addChild(_title);
            _value = _makeText(18, 0xFFFFFF);
            addChild(_value);
            redraw();
        }

        public function setTitle(value:String):void
        {
            _titleText = value || "Marks";
            redraw();
        }

        public function setData(mark:Number, delta:Number):void
        {
            _mark = isNaN(mark) ? 0.0 : mark;
            _delta = isNaN(delta) ? 0.0 : delta;
            visible = true;
            redraw();
        }

        public function redraw():void
        {
            var displayDelta:Number = Math.abs(_delta) < 0.005 ? 0.0 : _delta;
            var deltaColor:uint = 0x8896A2;
            if (displayDelta > 0.005) deltaColor = 0x7CB342;
            else if (displayDelta < -0.005) deltaColor = 0xE24B4A;
            var sign:String = displayDelta > 0.005 ? "+" : "";

            _title.htmlText = _fmt(_titleText, 12, 0xB8C4D0);
            _value.htmlText = _fmt(_fmt2(_mark) + "%  " + sign + _fmt2(displayDelta) + "%", 18, deltaColor);

            var padX:int = 12;
            var padY:int = 6;
            var gap:int = 6;
            _title.x = padX;
            _title.y = padY + 2;
            _value.x = padX;
            _value.y = _title.y + _title.height + gap - 2;

            var w:Number = Math.max(_title.width, _value.width) + padX * 2;
            var h:Number = _value.y + _value.height + padY;
            var g:Graphics = _bg.graphics;
            g.clear();
            g.lineStyle(0.75, 0xC8B97A, 0.42);
            g.beginFill(0x0A0E12, 0.78);
            g.drawRoundRect(0, 0, w, h, 6, 6);
            g.endFill();
            g.lineStyle(NaN);
        }

        private function _makeText(size:int, color:uint):TextField
        {
            var tf:TextField = new TextField();
            tf.selectable = false;
            tf.mouseEnabled = false;
            tf.autoSize = TextFieldAutoSize.LEFT;
            tf.multiline = false;
            tf.filters = [_shadow];
            tf.htmlText = _fmt("", size, color);
            return tf;
        }

        private function _fmt(text:String, size:int, color:uint):String
        {
            var hex:String = color.toString(16);
            while (hex.length < 6) hex = "0" + hex;
            return "<font face='$FieldFont' size='" + size + "' color='#" + hex + "'><b>" + text + "</b></font>";
        }

        private function _fmt2(value:Number):String
        {
            return (isNaN(value) ? 0.0 : value).toFixed(2);
        }
    }
}
