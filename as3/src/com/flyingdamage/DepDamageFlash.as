package com.flyingdamage
{
    import flash.display.Sprite;

    public final class DepDamageFlash extends Sprite
    {
        private static const SWF_HALF_WIDTH:Number = 400;
        private static const SWF_HALF_HEIGHT:Number = 300;

        private var _layer:FloatingDamageLayer;

        public function DepDamageFlash()
        {
            super();
            mouseEnabled = false;
            mouseChildren = false;
            _layer = new FloatingDamageLayer();
            addChild(_layer);
        }

        public function as_showDamage(
            screenWidth:Number,
            screenHeight:Number,
            xPos:Number,
            yPos:Number,
            damage:int,
            attackerID:Number,
            damageType:String,
            damageFlag:int
        ):void
        {
            // GUI.Flash centers an 800x600 movie. Shift the AS3 root so its
            // local coordinates exactly match screen pixels from the top-left.
            this.x = SWF_HALF_WIDTH - (screenWidth / 2.0);
            this.y = SWF_HALF_HEIGHT - (screenHeight / 2.0);

            _layer.showDamage(damage, attackerID, damageType, damageFlag, xPos, yPos);
        }
    }
}
