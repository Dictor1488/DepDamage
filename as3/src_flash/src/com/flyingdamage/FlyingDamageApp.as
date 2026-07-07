package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.events.Event;

    public class FlyingDamageApp extends Sprite
    {
        public var py_getScreenPos:Function = null;
        public var py_pullDamage:Function = null;
        public var py_log:Function = null;

        private var _layer:DamageLayer = null;
        private var _populates:int = 0;
        private var _loggedFrame:int = 0;

        public function FlyingDamageApp()
        {
            super();
            mouseEnabled = false;
            mouseChildren = false;
            addEventListener(Event.ADDED_TO_STAGE, onAdded);
            addEventListener(Event.ENTER_FRAME, onFrame);
        }

        private function onAdded(e:Event):void
        {
            log("ADDED_TO_STAGE populate-driven-render");
            if (stage != null)
            {
                stage.frameRate = 60;
                stage.addEventListener(Event.ENTER_FRAME, onFrame);
            }
            _ensureLayer();
            pullAndTick();
        }

        private function onFrame(e:Event):void
        {
            if (_loggedFrame < 2)
            {
                _loggedFrame++;
                log("ENTER_FRAME populate-driven-render #" + _loggedFrame);
            }
            pullAndTick();
        }

        public function as_populate():void
        {
            _populates++;
            _ensureLayer();
            log("as_populate TICK BUILD=populate-driven-render count=" + _populates);
            pullAndTick();
        }

        public function as_update():void
        {
            pullAndTick();
        }

        private function pullAndTick():void
        {
            _ensureLayer();
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
                            var hasStart:Boolean = d.hasStart === true;
                            var sx:Number = hasStart ? Number(d.x) : 0;
                            var sy:Number = hasStart ? Number(d.y) : 0;
                            log("recv vid=" + d.vid + " dmg=" + d.dmg + " hasStart=" + hasStart);
                            _layer.showDamage(String(d.vid), int(d.dmg), uint(d.color), int(d.size), Number(d.alpha), sx, sy, hasStart);
                        }
                    }
                }
                catch (err:Error)
                {
                    log("pull error: " + err.message);
                }
            }
            if (_layer != null)
                _layer.tick();
        }

        public function as_dispose():void
        {
            if (stage != null)
                stage.removeEventListener(Event.ENTER_FRAME, onFrame);
            removeEventListener(Event.ENTER_FRAME, onFrame);
            if (_layer != null)
            {
                _layer.clearAll();
                if (_layer.parent != null)
                    _layer.parent.removeChild(_layer);
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
                log("DamageLayer created populate-driven");
            }
        }

        private function log(msg:String):void
        {
            try
            {
                if (py_log != null)
                    py_log("[SWF] " + msg);
            }
            catch (e:Error) {}
        }
    }
}
