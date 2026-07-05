package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.events.Event;

    /**
     * FlyingDamageApp -- Sprite overlay (ExternalFlashComponent, DistanceMarker
     * pattern). Data flows via PULL: each frame the SWF calls py_pullDamage()
     * to fetch newly-dealt damage, and py_getScreenPos(vid) to position numbers.
     * Push-with-params (as_showDamage) does not work across the Scaleform bridge,
     * so everything is pulled instead.
     */
    public class FlyingDamageApp extends Sprite
    {
        public var py_getScreenPos:Function = null;
        public var py_pullDamage:Function = null;
        public var py_log:Function = null;

        private var _layer:DamageLayer = null;

        public function FlyingDamageApp()
        {
            super();
        }

        public function as_populate():void
        {
            _ensureLayer();
            this.addEventListener(Event.ENTER_FRAME, onEnterFrame);
            log("as_populate");
        }

        public function as_dispose():void
        {
            this.removeEventListener(Event.ENTER_FRAME, onEnterFrame);
            if (_layer)
            {
                _layer.clearAll();
                if (_layer.parent) _layer.parent.removeChild(_layer);
                _layer = null;
            }
            py_getScreenPos = null;
            py_pullDamage = null;
            py_log = null;
        }

        public function getScreenPos(vehicleID:String):Object
        {
            if (py_getScreenPos == null)
                return null;
            try { return py_getScreenPos(vehicleID); }
            catch (e:Error) {}
            return null;
        }

        private function _ensureLayer():void
        {
            if (_layer == null)
            {
                _layer = new DamageLayer(this);
                addChild(_layer);
            }
        }

        private function onEnterFrame(e:Event):void
        {
            if (_layer == null)
                return;

            // Pull any newly-dealt damage from Python.
            if (py_pullDamage != null)
            {
                try
                {
                    var list:Object = py_pullDamage();
                    if (list != null && list.length > 0)
                    {
                        for (var i:int = 0; i < list.length; i++)
                        {
                            var d:Object = list[i];
                            log("recv vid=" + d.vid + " dmg=" + d.dmg);
                            _layer.showDamage(String(d.vid), int(d.dmg),
                                uint(d.color), int(d.size), Number(d.alpha));
                        }
                    }
                }
                catch (err:Error)
                {
                    log("pull error: " + err.message);
                }
            }

            // Update existing numbers (stick to tanks + fly up).
            _layer.tick();
        }

        private function log(msg:String):void
        {
            try { if (py_log != null) py_log("[SWF] " + msg); }
            catch (e:Error) {}
        }
    }
}
