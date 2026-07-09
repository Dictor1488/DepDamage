package net.wg.gui.utils
{
    import flash.display.Graphics;
    import flash.events.EventDispatcher;
    import flash.geom.Rectangle;
    import net.wg.infrastructure.events.AtlasEvent;

    public class RootSWFAtlasManager extends EventDispatcher
    {
        private static var _instance:RootSWFAtlasManager;

        public function RootSWFAtlasManager()
        {
            super();
        }

        public static function get instance() : RootSWFAtlasManager
        {
            if(_instance == null)
            {
                _instance = new RootSWFAtlasManager();
            }
            return _instance;
        }

        public function initAtlas(atlasName:String) : void
        {
            dispatchEvent(new AtlasEvent(AtlasEvent.ATLAS_INITIALIZED));
        }

        public function dispose() : void
        {
        }

        public function drawGraphics(atlasName:String, itemName:String, position:Object, graphics:Graphics) : void
        {
        }

        public function drawWithCenterAlign(atlasName:String, itemName:String, position:Object, graphics:Graphics, centerAlign:Boolean = true, snapToPixels:Boolean = true) : void
        {
        }

        public function getAtlasItemBounds(atlasName:String, itemName:String) : Rectangle
        {
            return new Rectangle();
        }

        public function isAtlasInitialized(atlasName:String) : Boolean
        {
            return true;
        }
    }
}
