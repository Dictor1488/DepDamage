package com.flyingdamage
{
    import flash.events.Event;
    import net.wg.infrastructure.base.AbstractView;

    /**
     * FlyingDamageView -- Scaleform battle view (AbstractView) that renders
     * floating damage numbers. Python calls as_showDamage(...) directly.
     *
     * Being an AbstractView from base_app.swc makes it Scaleform-compatible,
     * unlike a plain Sprite SWF (which Scaleform won't instantiate).
     */
    public class FlyingDamageView extends AbstractView
    {
        private var _layer:DamageLayer = null;
        private var _configDone:Boolean = false;
        private var _pending:Array = [];

        public var py_log:Function = null;

        public function FlyingDamageView()
        {
            super();
        }

        override protected function configUI():void
        {
            super.configUI();
            _layer = new DamageLayer();
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
            py_log = null;
            _configDone = false;
            super.onDispose();
        }

        // ── called directly by Python ──────────────────────────────────
        public function as_showDamage(screenX:Number, screenY:Number, damage:int,
                                      colorRGB:uint, fontSize:int, alpha:Number):void
        {
            if (!_configDone)
            {
                _pending.push({fn: this.as_showDamage,
                    args: [screenX, screenY, damage, colorRGB, fontSize, alpha]});
                return;
            }
            log("recv d=" + damage + " x=" + int(screenX) + " y=" + int(screenY));
            if (_layer)
                _layer.showDamage(screenX, screenY, damage, colorRGB, fontSize, alpha);
        }

        public function as_clear():void
        {
            if (_layer) _layer.clearAll();
        }

        private function _replayPending():void
        {
            if (_pending.length == 0) return;
            var calls:Array = _pending;
            _pending = [];
            for (var i:int = 0; i < calls.length; i++)
            {
                var c:Object = calls[i];
                var fn:Function = c.fn as Function;
                if (fn != null) fn.apply(null, c.args);
            }
        }

        private function log(msg:String):void
        {
            try { if (py_log != null) py_log("[SWF] " + msg); }
            catch (e:Error) {}
        }
    }
}
