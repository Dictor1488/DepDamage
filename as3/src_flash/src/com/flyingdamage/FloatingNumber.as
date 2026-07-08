package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.utils.getTimer;

    public class FloatingNumber extends Sprite
    {
        public var vehicleID:String;

        private var _label:DamageLabel;
        private var _labeled:LabeledDamageLabel;
        private var _critical:CriticalHitLabel;
        private var _anim:DamageAnimatedLabel;
        private var _bornAt:int;
        private var _markerX:Number = 0;
        private var _markerY:Number = 0;
        private var _hasMarker:Boolean = false;
        private var _damageType:String;

        public function FloatingNumber(vehicleID:String, damage:int, colorRGB:uint, fontSize:int, baseAlpha:Number, startX:Number = 0, startY:Number = 0, hasStart:Boolean = false, sourceFlag:uint = 0, damageType:String = "shot")
        {
            this.vehicleID = vehicleID;
            _bornAt = getTimer();
            _markerX = startX;
            _markerY = startY;
            _hasMarker = hasStart;
            _damageType = damageType;

            if (VehicleMarkerFlags.checkLabeledDamages(_damageType))
            {
                _labeled = new LabeledDamageLabel(_damageType, fontSize);
                addChild(_labeled);
                _anim = new DamageAnimatedLabel(this, _labeled.textField, _labeled.color, baseAlpha, 40.0);
            }
            else
            {
                _label = new DamageLabel(damage, fontSize, colorRGB, sourceFlag, damageType);
                addChild(_label);
                _anim = new DamageAnimatedLabel(this, _label.textField, _label.color, baseAlpha, 40.0);

                if (_damageType == VehicleMarkerFlags.DAMAGE_BLOCKED_CRIT)
                    addCriticalLabel("CRIT");
            }

            visible = _hasMarker;
        }

        public function update(pos:Object):Boolean
        {
            var age:Number = (getTimer() - _bornAt) / 1000.0;
            if (_anim == null || !_anim.isAlive(age))
                return false;

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
            updateCriticalLayout();
            _anim.update(age);

            return true;
        }

        private function addCriticalLabel(text:String):void
        {
            _critical = new CriticalHitLabel(text);
            addChild(_critical);
            updateCriticalLayout();
        }

        private function updateCriticalLayout():void
        {
            if (_critical == null || _label == null)
                return;
            _critical.layoutAfterDamageLabel(_label, 8.0);
        }

        public function dispose():void
        {
            _anim = null;
            if (_critical != null)
            {
                if (_critical.parent != null)
                    _critical.parent.removeChild(_critical);
                _critical.dispose();
                _critical = null;
            }
            if (_label != null)
            {
                if (_label.parent != null)
                    _label.parent.removeChild(_label);
                _label.dispose();
                _label = null;
            }
            if (_labeled != null)
            {
                if (_labeled.parent != null)
                    _labeled.parent.removeChild(_labeled);
                _labeled.dispose();
                _labeled = null;
            }
        }
    }
}
