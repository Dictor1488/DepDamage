package com.flyingdamage
{
    import flash.events.Event;
    import net.wg.infrastructure.base.AbstractView;

    /**
     * FlyingDamageView -- floating damage numbers that STICK to the tank.
     * The DamageLayer is created lazily on first use so we don't depend on
     * configUI timing. Each frame the label asks Python for the tank's current
     * screen position (by vehicleID) and places itself there + upward-fly.
     */
    public class FlyingDamageView extends AbstractView
    {
        private var _layer:DamageLayer = null;

        public var py_getScreenPos:Function = null;
        public var py_log:Function = null;

        public function FlyingDamageView()
        {
            super();
        }

        private function _ensureLayer():void
        {
            if (_layer == null)
            {
                _layer = new DamageLayer(this);
                addChild(_layer);
                log("layer created");
            }
        }

        override protected function configUI():void
        {
            super.configUI();
            _ensureLayer();
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
            py_getScreenPos = null;
            py_log = null;
            super.onDispose();
        }

        public function as_showDamage(vehicleID:Number, damage:int,
                                      colorRGB:uint, fontSize:int, alpha:Number):void
        {
            _ensureLayer();
            log("recv vid=" + vehicleID + " dmg=" + damage);
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

        private function log(msg:String):void
        {
            try { if (py_log != null) py_log("[SWF] " + msg); }
            catch (e:Error) {}
        }
    }
}
