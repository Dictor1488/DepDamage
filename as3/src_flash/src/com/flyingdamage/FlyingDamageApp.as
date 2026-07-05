package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.events.Event;

    /**
     * FlyingDamageApp -- Sprite-based overlay loaded via ExternalFlashComponent
     * (same mechanism as DistanceMarker, which is proven to actually load and
     * run over the battle scene). Python calls as_populate() to start the frame
     * loop; each frame we ask Python for tank screen positions and place the
     * floating damage numbers there (they stick to the tank + fly upward).
     */
    public class FlyingDamageApp extends Sprite
    {
        // Python-assigned callbacks
        public var py_getScreenPos:Function = null;
        public var py_log:Function = null;

        private var _layer:DamageLayer = null;
        private var _ticking:Boolean = false;

        public function FlyingDamageApp()
        {
            super();
        }

        // ── called by Python (ExternalFlashComponent lifecycle) ──────────
        public function as_populate():void
        {
            _ensureLayer();
            log("as_populate");
        }

        public function as_dispose():void
        {
            _stopTicking();
            if (_layer)
            {
                _layer.clearAll();
                if (_layer.parent) _layer.parent.removeChild(_layer);
                _layer = null;
            }
            py_getScreenPos = null;
            py_log = null;
        }

        public function as_showDamage(vehicleID:String, damage:int,
                                      colorRGB:uint, fontSize:int, alpha:Number):void
        {
            _ensureLayer();
            log("recv vid=" + vehicleID + " dmg=" + damage);
            if (_layer)
            {
                _layer.showDamage(vehicleID, damage, colorRGB, fontSize, alpha);
                _ensureTicking();
            }
        }

        public function as_clear():void
        {
            if (_layer) _layer.clearAll();
        }

        // Called by DamageLayer each frame to get a tank's current screen pos.
        public function getScreenPos(vehicleID:String):Object
        {
            if (py_getScreenPos == null)
                return null;
            try
            {
                return py_getScreenPos(vehicleID);
            }
            catch (e:Error)
            {
            }
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

        private function _ensureTicking():void
        {
            if (!_ticking)
            {
                _ticking = true;
                this.addEventListener(Event.ENTER_FRAME, onEnterFrame);
            }
        }

        private function _stopTicking():void
        {
            if (_ticking)
            {
                _ticking = false;
                this.removeEventListener(Event.ENTER_FRAME, onEnterFrame);
            }
        }

        private function onEnterFrame(e:Event):void
        {
            if (_layer == null)
            {
                _stopTicking();
                return;
            }
            var alive:int = _layer.tick();
            if (alive == 0)
                _stopTicking();
        }

        private function log(msg:String):void
        {
            try { if (py_log != null) py_log("[SWF] " + msg); }
            catch (e:Error) {}
        }
    }
}
