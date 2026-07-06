package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.events.Event;

    /**
     * FlyingDamageApp -- Sprite overlay loaded via ExternalFlashComponent,
     * mirroring DistanceMarker EXACTLY: the game calls as_populate() via DAAPI,
     * which attaches ENTER_FRAME. Each frame we pull new damage from Python and
     * update the floating numbers (stick to tank + fly upward).
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
            // Attach ENTER_FRAME as early as possible, and re-attach when added
            // to stage. The visibility test proved the SWF renders; if the
            // render loop runs, ENTER_FRAME should fire once we're on stage.
            this.addEventListener(Event.ADDED_TO_STAGE, onAddedToStage);
            this.addEventListener(Event.ENTER_FRAME, onEnterFrame);
        }

        private var _efLogged:int = 0;

        private function onAddedToStage(e:Event):void
        {
            log("ADDED_TO_STAGE fired");
            if (this.stage != null)
            {
                this.stage.addEventListener(Event.ENTER_FRAME, onEnterFrame);
                this.stage.frameRate = 60;
            }
        }

        private function onEnterFrame(e:Event):void
        {
            if (_efLogged < 2)
            {
                _efLogged++;
                log("ENTER_FRAME FIRED #" + _efLogged);
            }
            as_update();
        }

        // Called by the GAME via DAAPI when the SWF is ready.
        public function as_populate():void
        {
            _ensureLayer();
            log("as_populate BUILD=old-visible-render+vehicle-anchor-fix");
        }

        private var _updLogged:Boolean = false;

        public function as_update():void
        {
            if (!_updLogged)
            {
                _updLogged = true;
                log("as_update REACHED SWF");
            }
            if (_layer == null)
                return;
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
            _layer.tick();
        }

        public function as_dispose():void
        {
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

        public function debugLog(msg:String):void
        {
            log(msg);
        }

        private function log(msg:String):void
        {
            try { if (py_log != null) py_log("[SWF] " + msg); }
            catch (e:Error) {}
        }
    }
}
