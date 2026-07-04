package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.events.Event;

    public class DamageLayer extends Sprite
    {
        private var _items:Vector.<FloatingNumber>;
        private var _ticking:Boolean = false;

        public function DamageLayer()
        {
            _items = new Vector.<FloatingNumber>();
            mouseEnabled = false;
            mouseChildren = false;
        }

        public function showDamage(screenX:Number, screenY:Number, damage:int,
                                   colorRGB:uint, fontSize:int, alpha:Number):void
        {
            if (damage <= 0)
                return;
            var fn:FloatingNumber = new FloatingNumber(damage, colorRGB, fontSize, alpha);
            fn.setStart(screenX, screenY);
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
                if (fn.update())
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
