package com.flyingdamage
{
    import flash.display.Sprite;

    public class FlyingDamageApp extends Sprite
    {
        public var py_getScreenPos:Function = null;
        public var py_pullDamage:Function = null;
        public var py_log:Function = null;

        private var _layer:DamageLayer = null;
        private var _populateCount:int = 0;
        private var _recvLog:int = 0;

        public function FlyingDamageApp()
        {
            super();
        }

        // In this WoT Scaleform bridge, as_populate is the method that reliably
        // reaches AS3. Python calls it repeatedly; we use it as a render tick.
        public function as_populate():void
        {
            _ensureLayer();
            _populateCount++;
            if (_populateCount <= 5 || _populateCount % 300 == 0)
                log("as_populate TICK BUILD=populate-driven-render count=" + _populateCount);
            _tick();
        }

        private function _tick():void
        {
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
                            if (_recvLog < 80)
                            {
                                _recvLog++;
                                log("recv vid=" + d.vid + " dmg=" + d.dmg);
                            }
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
                log("DamageLayer created populate-driven");
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
