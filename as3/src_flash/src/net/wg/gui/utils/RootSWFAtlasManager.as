package net.wg.gui.utils
{
    import flash.display.Graphics;
    import flash.events.Event;
    import flash.events.EventDispatcher;
    import flash.geom.Rectangle;
    import net.wg.infrastructure.events.AtlasEvent;

    public class RootSWFAtlasManager extends EventDispatcher
    {
        private static var _instance:RootSWFAtlasManager;
        private var _atlasInitialized:Boolean = false;
        private var _dispatchScheduled:Boolean = false;

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
            _atlasInitialized = true;
            if(!_dispatchScheduled)
            {
                _dispatchScheduled = true;
                addEventListener(Event.ENTER_FRAME, dispatchAtlasInitializedOnce, false, 0, true);
            }
        }

        private function dispatchAtlasInitializedOnce(event:Event) : void
        {
            removeEventListener(Event.ENTER_FRAME, dispatchAtlasInitializedOnce);
            _dispatchScheduled = false;
            dispatchEvent(new AtlasEvent(AtlasEvent.ATLAS_INITIALIZED));
        }

        public function dispose() : void
        {
            removeEventListener(Event.ENTER_FRAME, dispatchAtlasInitializedOnce);
            _atlasInitialized = false;
            _dispatchScheduled = false;
        }

        public function drawGraphics(atlasName:String, itemName:String, graphics:Graphics, position:Object) : void
        {
        }

        public function drawWithCenterAlign(atlasName:String, itemName:String, graphics:Graphics, position:Object, centerAlign:Boolean = true, snapToPixels:Boolean = true, extra:Object = null) : void
        {
        }

        public function getAtlasItemBounds(atlasName:String, itemName:String) : Rectangle
        {
            return new Rectangle();
        }

        public function isAtlasInitialized(atlasName:String) : Boolean
        {
            return _atlasInitialized;
        }
    }
}
