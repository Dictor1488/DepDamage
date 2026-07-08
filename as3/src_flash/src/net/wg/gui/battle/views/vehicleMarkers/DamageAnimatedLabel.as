package net.wg.gui.battle.views.vehicleMarkers
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.events.Event;
    import flash.utils.getTimer;

    /**
     * Compact replacement for the original GreenSock timeline:
     * emerge -> rise upward -> fade -> remove from parent.
     */
    public class DamageAnimatedLabel
    {
        private static const EMERGE_DURATION:Number = 0.30;
        private static const RISE_DURATION:Number = 2.00;
        private static const FADE_DURATION:Number = 0.50;
        private static const TOTAL_DURATION:Number = 2.00;

        private var target:DisplayObject;
        private var startY:Number;
        private var endY:Number;
        private var startTime:int;

        public function DamageAnimatedLabel(display:DisplayObject, risePixels:Number = 40)
        {
            target = display;
            if(target == null)
            {
                return;
            }
            startY = target.y;
            endY = startY - risePixels;
            startTime = getTimer();
            target.alpha = 0;
            target.scaleX = target.scaleY = 0.85;
            target.addEventListener(Event.ENTER_FRAME, tick, false, 0, true);
        }

        private function tick(e:Event) : void
        {
            if(target == null)
            {
                return;
            }
            var t:Number = (getTimer() - startTime) / 1000.0;
            var p:Number = Math.max(0, Math.min(1, t / TOTAL_DURATION));
            target.y = startY + (endY - startY) * p;

            if(t < EMERGE_DURATION)
            {
                target.alpha = t / EMERGE_DURATION;
                target.scaleX = target.scaleY = 0.85 + 0.15 * (t / EMERGE_DURATION);
            }
            else if(t > TOTAL_DURATION - FADE_DURATION)
            {
                target.alpha = Math.max(0, (TOTAL_DURATION - t) / FADE_DURATION);
            }
            else
            {
                target.alpha = 1;
                target.scaleX = target.scaleY = 1;
            }

            if(t >= TOTAL_DURATION)
            {
                dispose();
            }
        }

        private function dispose() : void
        {
            if(target == null)
            {
                return;
            }
            target.removeEventListener(Event.ENTER_FRAME, tick);
            var parent:DisplayObjectContainer = target.parent;
            if(parent != null)
            {
                parent.removeChild(target);
            }
            target = null;
        }
    }
}
