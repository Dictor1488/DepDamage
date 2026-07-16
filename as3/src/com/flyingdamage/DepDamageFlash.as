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

        public function as_configureScreen(screenWidth:Number, screenHeight:Number):void
        {
            this.x = SWF_HALF_WIDTH - (screenWidth / 2.0);
            this.y = SWF_HALF_HEIGHT - (screenHeight / 2.0);
        }

        public function as_createDamage(id:int, damage:int, damageFlag:int):void
        {
            _layer.createDamage(id, damage, damageFlag);
        }

        public function as_updateDamage(id:int, xPos:Number, yPos:Number, alphaValue:Number, isVisible:Boolean):void
        {
            _layer.updateDamage(id, xPos, yPos, alphaValue, isVisible);
        }

        public function as_removeDamage(id:int):void
        {
            _layer.removeDamage(id);
        }

        public function as_populate():void
        {
        }

        public function as_dispose():void
        {
        }
    }
}
