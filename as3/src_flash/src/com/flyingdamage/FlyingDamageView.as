package com.flyingdamage
{
    import flash.events.Event;
    import net.wg.infrastructure.base.AbstractView;

    /**
     * FlyingDamageView -- floating damage numbers that STICK to the tank.
     * Each frame the label asks Python for the tank's current screen position
     * (by vehicleID) and places itself there, plus the upward-fly animation.
     */
    public class FlyingDamageView extends AbstractView
    {
        private var _layer:DamageLayer = null;
        private var _configDone:Boolean = false;
        private var _pending:Array = [];

        public var py_getScreenPos:Function = null;
        public var py_log:Function = null;

        public function FlyingDamageView()
        {
            super();
        }

        override protected function configUI():void
        {
            super.configUI();
            _layer = new DamageLayer(this);
            addChild(_layer);
            _configDone = true;
            _replayPending();
            log("configUI done");
        }

        override protected function onDispose():void
        {
            if (_layer)
            {
                _layer.clearAll();
                if (_layer.parent) _layer.parent.removeChild(_layer);
                _layer = null;
            }
            _pending = [];
            py_getScreenPos = null;
            py_log = null;
            _configDone = false;
            super.onDispose();
        }

        public function as_showDamage(vehicleID:Number, damage:int,
                                      colorRGB:uint, fontSize:int, alpha:Number):void
        {
            if (!_configDone)
            {
                _pending.push([vehicleID, damage, colorRGB, fontSize, alpha]);
                return;
            }
            if (_layer)
                _layer.showDamage(vehicleID, damage, colorRGB, fontSize, alpha);
        }

        public function as_clear():void
        {
            if (_layer) _layer.clearAll();
        }

        public function getScreenPos(vehicleID:Number):Object
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

        private function _replayPending():void
        {
            if (_pending.length == 0) return;
            var calls:Array = _pending;
            _pending = [];
            for (var i:int = 0; i < calls.length; i++)
            {
                var a:Array = calls[i];
                _layer.showDamage(a[0], a[1], a[2], a[3], a[4]);
            }
        }

        private function log(msg:String):void
        {
            try { if (py_log != null) py_log("[SWF] " + msg); }
            catch (e:Error) {}
        }
    }
}
