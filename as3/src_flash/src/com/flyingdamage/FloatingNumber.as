package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFieldType;
    import flash.filters.GlowFilter;
    import flash.filters.DropShadowFilter;
    import flash.utils.getTimer;

    public class FloatingNumber extends Sprite
    {
        public var vehicleID:String;

        private var _tf:TextField;
        private var _anim:DamageAnimatedLabel;
        private var _bornAt:int;
        private var _markerX:Number = 0;
        private var _markerY:Number = 0;
        private var _hasMarker:Boolean = false;
        private var _targetColor:uint;
        private var _damage:int;
        private var _fontSize:int;

        public function FloatingNumber(vehicleID:String, damage:int, colorRGB:uint, fontSize:int, baseAlpha:Number, startX:Number = 0, startY:Number = 0, hasStart:Boolean = false)
        {
            this.vehicleID = vehicleID;
            _bornAt = getTimer();
            _markerX = startX;
            _markerY = startY;
            _hasMarker = hasStart;
            _targetColor = normalizeDamageColor(colorRGB);
            _damage = damage;
            _fontSize = fontSize;

            _tf = new TextField();
            _tf.autoSize = TextFieldAutoSize.CENTER;
            _tf.selectable = false;
            _tf.mouseEnabled = false;
            _tf.multiline = false;
            _tf.wordWrap = false;
            _tf.background = false;
            _tf.border = false;
            _tf.type = TextFieldType.DYNAMIC;
            _tf.defaultTextFormat = new TextFormat("$TitleFont", _fontSize, 0xFFFFFF, true);
            _tf.text = String(_damage);
            _tf.x = -_tf.textWidth / 2.0;
            _tf.y = -_tf.textHeight / 2.0;
            _tf.filters = buildFilters(_targetColor);
            addChild(_tf);

            _anim = new DamageAnimatedLabel(this, _tf, _targetColor, baseAlpha, 40.0);
            visible = _hasMarker;
        }

        public function update(pos:Object):Boolean
        {
            var age:Number = (getTimer() - _bornAt) / 1000.0;
            if (_anim == null || !_anim.isAlive(age))
                return false;

            // Same visual behavior as copied VehicleMarker logic, but in our AS3 layer:
            // lock to the hit-time marker snapshot and animate locally from that point.
            if (!_hasMarker && pos != null && pos.ok)
            {
                _markerX = Number(pos.x);
                _markerY = Number(pos.y);
                _hasMarker = true;
            }

            if (!_hasMarker)
            {
                visible = false;
                return true;
            }

            visible = true;
            x = _markerX + VehicleMarkerDamageLayout.DAMAGE_X;
            y = _markerY + VehicleMarkerDamageLayout.getDamageLabelOffset(true, true, true, true) + _anim.getYOffset(age);
            _anim.update(age);

            return true;
        }

        private function normalizeDamageColor(c:uint):uint
        {
            c = c & 0xFFFFFF;
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

        private function buildFilters(c:uint):Array
        {
            return [
                new GlowFilter(0x000000, 1.0, 3.0, 3.0, 5.0, 2),
                new GlowFilter(0x000000, 0.75, 6.0, 6.0, 2.0, 2),
                new GlowFilter(c, 0.35, 8.0, 8.0, 1.1, 1),
                new DropShadowFilter(1.0, 90, 0x000000, 0.75, 2.0, 2.0, 1.0, 2)
            ];
        }

        public function dispose():void
        {
            _anim = null;
            if (_tf != null)
            {
                if (_tf.parent != null)
                    _tf.parent.removeChild(_tf);
                _tf = null;
            }
        }
    }
}
