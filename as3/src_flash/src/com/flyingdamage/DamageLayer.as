package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.events.Event;

    public class DamageLayer extends Sprite
    {
        private var _view:FlyingDamageView;
        private var _items:Vector.<FloatingNumber>;
        private var _ticking:Boolean = false;

        public function DamageLayer(view:FlyingDamageView)
        {
            _view = view;
            _items = new Vector.<FloatingNumber>();
            mouseEnabled = false;
            mouseChildren = false;
        }

        public function showDamage(vehicleID:Number, damage:int,
                                   colorRGB:uint, fontSize:int, alpha:Number):void
        {
            if (damage <= 0)
                return;
            var fn:FloatingNumber = new FloatingNumber(vehicleID, damage, colorRGB, fontSize, alpha);
            addChild(fn);
            _items.push(fn);
            ensureTicking();
        }

        public function clearAll():void
        {
            for each (var fn:FloatingNumber in _items)
            {
                if (fn.parent != null)
                    fn.parent.removeChild(fn);
                fn.dispose();
            }
            _items = new Vector.<FloatingNumber>();
            stopTicking();
        }

        private function ensureTicking():void
        {
            if (!_ticking)
            {
                _ticking = true;
                addEventListener(Event.ENTER_FRAME, onEnterFrame);
            }
        }

        private function stopTicking():void
        {
            if (_ticking)
            {
                _ticking = false;
                removeEventListener(Event.ENTER_FRAME, onEnterFrame);
            }
        }

        private function onEnterFrame(e:Event):void
        {
            var survivors:Vector.<FloatingNumber> = new Vector.<FloatingNumber>();
            for each (var fn:FloatingNumber in _items)
            {
                // Ask Python for this tank's current screen position.
                var pos:Object = _view.getScreenPos(fn.vehicleID);
                if (fn.update(pos))
                    survivors.push(fn);
                else
                {
                    if (fn.parent != null)
                        fn.parent.removeChild(fn);
                    fn.dispose();
                }
            }
            _items = survivors;
            if (_items.length == 0)
                stopTicking();
        }
    }
}
