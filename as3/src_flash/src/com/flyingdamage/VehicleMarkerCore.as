package com.flyingdamage
{
    import flash.display.Sprite;

    public class VehicleMarkerCore extends Sprite
    {
        public var id:String;
        public var vehicleID:String;

        private var _markerX:Number = 0;
        private var _markerY:Number = 0;
        private var _hasMarker:Boolean = false;
        private var _damageContainer:Sprite;
        private var _hpContainer:Sprite;
        private var _items:Vector.<FloatingNumber>;
        private var _splashes:Vector.<HpSplash>;

        public function VehicleMarkerCore(id:String, vehicleID:String = null)
        {
            this.id = id;
            this.vehicleID = vehicleID != null ? vehicleID : id;
            mouseEnabled = false;
            mouseChildren = false;

            _hpContainer = new Sprite();
            _hpContainer.mouseEnabled = false;
            _hpContainer.mouseChildren = false;
            addChild(_hpContainer);

            _damageContainer = new Sprite();
            _damageContainer.mouseEnabled = false;
            _damageContainer.mouseChildren = false;
            addChild(_damageContainer);

            _items = new Vector.<FloatingNumber>();
            _splashes = new Vector.<HpSplash>();
            visible = false;
        }

        public function setMarkerSnapshot(xPos:Number, yPos:Number, ok:Boolean):void
        {
            if (!ok)
                return;
            if (!_hasMarker)
            {
                _markerX = xPos;
                _markerY = yPos;
                _hasMarker = true;
                x = _markerX;
                y = _markerY;
                visible = true;
            }
        }

        public function addDamageLabel(damage:int, colorRGB:uint, fontSize:int, alpha:Number, sourceFlag:uint, damageType:String):void
        {
            if (damage <= 0 && !VehicleMarkerFlags.checkLabeledDamages(damageType))
                return;

            // Normal shot damage must be allowed here. VehicleMarkerFlags.checkAllowedDamages()
            // is the original hit-effect filter and only includes fire/explosion, so using it
            // here hides regular damage numbers. Use the label-specific filter instead.
            if (!VehicleMarkerFlags.checkAllowedDamageLabel(damageType))
                return;

            var fn:FloatingNumber = new FloatingNumber(vehicleID, damage, colorRGB, fontSize, alpha, sourceFlag, damageType);
            _damageContainer.addChild(fn);
            _items.push(fn);
        }

        public function updateHealth(damage:int, colorRGB:uint, hasHp:Boolean, hpCur:int, hpBefore:int, hpMax:int):void
        {
            // Temporarily disabled: without the real WoT HealthBar MovieClip anchor the
            // splash is drawn relative to our marker root and can fly to the side.
            // Damage numbers remain active; HP splash can be re-enabled after exact
            // health-bar anchoring is ported.
            return;
        }

        public function tick(pos:Object):Boolean
        {
            if (!_hasMarker && pos != null && pos.ok)
                setMarkerSnapshot(Number(pos.x), Number(pos.y), true);

            if (!_hasMarker)
            {
                visible = false;
                return true;
            }

            visible = true;
            x = _markerX;
            y = _markerY;

            var itemSurvivors:Vector.<FloatingNumber> = new Vector.<FloatingNumber>();
            for each (var fn:FloatingNumber in _items)
            {
                if (fn.update())
                    itemSurvivors.push(fn);
                else
                {
                    if (fn.parent != null)
                        fn.parent.removeChild(fn);
                    fn.dispose();
                }
            }
            _items = itemSurvivors;

            var splashSurvivors:Vector.<HpSplash> = new Vector.<HpSplash>();
            for each (var sp:HpSplash in _splashes)
            {
                if (sp.update())
                    splashSurvivors.push(sp);
                else
                {
                    if (sp.parent != null)
                        sp.parent.removeChild(sp);
                    sp.dispose();
                }
            }
            _splashes = splashSurvivors;

            return _items.length > 0 || _splashes.length > 0;
        }

        public function dispose():void
        {
            for each (var fn:FloatingNumber in _items)
            {
                if (fn.parent != null)
                    fn.parent.removeChild(fn);
                fn.dispose();
            }
            _items = new Vector.<FloatingNumber>();

            for each (var sp:HpSplash in _splashes)
            {
                if (sp.parent != null)
                    sp.parent.removeChild(sp);
                sp.dispose();
            }
            _splashes = new Vector.<HpSplash>();

            if (_damageContainer != null && _damageContainer.parent != null)
                _damageContainer.parent.removeChild(_damageContainer);
            if (_hpContainer != null && _hpContainer.parent != null)
                _hpContainer.parent.removeChild(_hpContainer);
            _damageContainer = null;
            _hpContainer = null;
        }
    }
}
