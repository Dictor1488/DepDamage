package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.filters.DropShadowFilter;
    import flash.filters.GlowFilter;
    import flash.text.TextField;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFieldType;
    import flash.text.TextFormat;

    public class DamageLabel extends Sprite
    {
        public var orange:TextField = null;
        public var green:TextField = null;
        public var red:TextField = null;
        public var gold:TextField = null;
        public var blue:TextField = null;
        public var yellow:TextField = null;
        public var purple:TextField = null;
        public var white:TextField = null;

        public var textField:TextField = null;
        public var color:uint;
        public var colorName:String = "red";
        public var damageType:String;
        public var sourceFlag:uint;

        protected var tfMap:Object = {};
        private var _currentTF:TextField = null;
        private var _fontSize:int = 15;
        private var _disposed:Boolean = false;

        public function DamageLabel(value:int = 0, fontSize:int = 15, colorRGB:uint = 0xFFFFFF, source:uint = 0, type:String = "shot")
        {
            super();
            mouseEnabled = false;
            mouseChildren = false;

            _fontSize = fontSize;
            sourceFlag = source;
            damageType = type;

            green = createField("green", VehicleMarkerFlags.getColorRGB("green"));
            red = createField("red", VehicleMarkerFlags.getColorRGB("red"));
            gold = createField("gold", VehicleMarkerFlags.getColorRGB("gold"));
            blue = createField("blue", VehicleMarkerFlags.getColorRGB("blue"));
            orange = createField("orange", VehicleMarkerFlags.getColorRGB("orange"));
            yellow = createField("yellow", VehicleMarkerFlags.getColorRGB("yellow"));
            purple = createField("purple", VehicleMarkerFlags.getColorRGB("purple"));
            white = createField("white", VehicleMarkerFlags.getColorRGB("white"));

            tfMap["green"] = green;
            tfMap["red"] = red;
            tfMap["gold"] = gold;
            tfMap["blue"] = blue;
            tfMap["orange"] = orange;
            tfMap["yellow"] = yellow;
            tfMap["purple"] = purple;
            tfMap["white"] = white;

            _currentTF = green;
            textField = _currentTF;
            hideAll();

            autoSize = TextFieldAutoSize.CENTER;
            setSourceColor(colorRGB, sourceFlag);
            text = VehicleMarkerFlags.formatDamageValue(value);
        }

        private function createField(name:String, rgb:uint):TextField
        {
            var tf:TextField = new TextField();
            tf.name = name;
            tf.autoSize = TextFieldAutoSize.CENTER;
            tf.selectable = false;
            tf.mouseEnabled = false;
            tf.multiline = false;
            tf.wordWrap = false;
            tf.background = false;
            tf.border = false;
            tf.type = TextFieldType.DYNAMIC;
            tf.width = 54;
            tf.height = 28;
            tf.defaultTextFormat = new TextFormat("$TitleFont", _fontSize, rgb, true);
            tf.filters = getMarkerStyleFilters(rgb);
            tf.visible = false;
            addChild(tf);
            return tf;
        }

        private function hideAll():void
        {
            for each (var tf:TextField in tfMap)
            {
                if (tf != null)
                    tf.visible = false;
            }
        }

        private function showTF(name:String):void
        {
            if (tfMap == null || !tfMap.hasOwnProperty(name) || tfMap[name] == null)
                name = "white";
            if (_currentTF != null)
                _currentTF.visible = false;
            _currentTF = tfMap[name] as TextField;
            textField = _currentTF;
            _currentTF.visible = true;
            colorName = name;
            color = VehicleMarkerFlags.getColorRGB(name);
            centerCurrent();
        }

        public function setSourceColor(colorRGB:uint, source:uint):void
        {
            var markerColor:String = VehicleMarkerFlags.getColorNameFromRGB(colorRGB);
            this.color = VehicleMarkerFlags.getColorRGB(VehicleMarkerFlags.getDamageColorName(source, markerColor));
            this.colorName = VehicleMarkerFlags.getDamageColorName(source, markerColor);
            showTF(this.colorName);
        }

        public function set colorLabel(name:String):void
        {
            showTF(name);
        }

        public function set text(value:String):void
        {
            for each (var tf:TextField in tfMap)
            {
                if (tf != null)
                    tf.text = value;
            }
            centerCurrent();
        }

        public function get textWidth():Number
        {
            return _currentTF ? Number(_currentTF.textWidth) : Number(0);
        }

        public function getCurrentTextFormat():TextFormat
        {
            return _currentTF ? _currentTF.getTextFormat() : new TextFormat("$TitleFont", _fontSize, color, true);
        }

        public function getCurrentFilters():Array
        {
            return _currentTF ? _currentTF.filters : getMarkerStyleFilters(color);
        }

        public function set autoSize(value:String):void
        {
            for each (var tf:TextField in tfMap)
            {
                if (tf != null)
                    tf.autoSize = value;
            }
            centerCurrent();
        }

        private function centerCurrent():void
        {
            if (_currentTF == null)
                return;
            _currentTF.x = -_currentTF.textWidth * 0.5;
            _currentTF.y = -_currentTF.textHeight * 0.5;
        }

        public function dispose():void
        {
            _disposed = true;
            for each (var tf:TextField in tfMap)
            {
                if (tf != null && tf.parent != null)
                    tf.parent.removeChild(tf);
            }
            green = null;
            red = null;
            gold = null;
            blue = null;
            orange = null;
            yellow = null;
            purple = null;
            white = null;
            textField = null;
            _currentTF = null;
            tfMap = null;
        }

        public function isDisposed():Boolean
        {
            return _disposed;
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
