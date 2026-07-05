package com.flyingdamage
{
    import flash.display.DisplayObjectContainer;
    import flash.events.Event;
    import net.wg.infrastructure.base.AbstractView;

    /**
     * FlyingDamageView -- injects a fullscreen damage-number layer into the
     * battle scene (working pattern taken from MasteryPanelInjector). Numbers
     * stick to their tank: each frame the label asks Python for the tank's
     * current screen position (by vehicleID) and rises upward from there.
     *
     * The key to actually rendering (vs content=None) is the injector lifecycle:
     * configUI + nextFrameAfterPopulateHandler + bringToFront, and binding to
     * App.instance.stage — NOT a standalone window.
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
            _ensureLayer();
            _configDone = true;
            _replayPending();

            if (App.instance && App.instance.stage)
                App.instance.stage.addEventListener(Event.RESIZE, _onResize);

            log("configUI done");
        }

        override protected function nextFrameAfterPopulateHandler():void
        {
            super.nextFrameAfterPopulateHandler();
            _bringToFront();
        }

        override protected function onDispose():void
        {
            if (App.instance && App.instance.stage)
                App.instance.stage.removeEventListener(Event.RESIZE, _onResize);
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

        private function _ensureLayer():void
        {
            if (_layer == null)
            {
                _layer = new DamageLayer(this);
                addChild(_layer);
            }
        }

        private function _bringToFront():void
        {
            try
            {
                if (parent != null)
                    parent.setChildIndex(this, parent.numChildren - 1);
            }
            catch (e:Error) {}
        }

        private function _onResize(event:Event):void
        {
            // Nothing to lay out; positions are computed per-frame from Python.
        }

        // ── called directly by Python ──────────────────────────────────
        public function as_showDamage(vehicleID:Number, damage:int,
                                      colorRGB:uint, fontSize:int, alpha:Number):void
        {
            if (!_configDone)
            {
                _pending.push([vehicleID, damage, colorRGB, fontSize, alpha]);
                return;
            }
            _ensureLayer();
            log("recv vid=" + vehicleID + " dmg=" + damage);
            if (_layer)
                _layer.showDamage(vehicleID, damage, colorRGB, fontSize, alpha);
        }

        public function as_clear():void
        {
            if (_layer) _layer.clearAll();
        }

        // Called by DamageLayer each frame to get a tank's current screen pos.
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
