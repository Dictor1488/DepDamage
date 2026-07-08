package net.wg.app.iml.base
{
    import flash.display.Sprite;
    import net.wg.infrastructure.interfaces.IRootAppMainContent;

    /**
     * Minimal compile-time root used by battleVehicleMarkersApp.swf.
     * The original game provides this class in WG shared UI sources.
     */
    public class RootApp extends Sprite
    {
        protected var main:IRootAppMainContent;
        private var _libsList:Vector.<String>;
        private var _registerCallback:String;

        public function RootApp(mainContent:IRootAppMainContent, libsList:Vector.<String>, registerCallback:String)
        {
            super();
            main = mainContent;
            _libsList = libsList;
            _registerCallback = registerCallback;
            if(mainContent is Sprite)
            {
                addChild(Sprite(mainContent));
            }
        }

        protected function onLibsLoadingComplete() : void
        {
        }

        protected function callRegisterCallback() : void
        {
            try
            {
                if(loaderInfo != null && loaderInfo.sharedEvents != null)
                {
                    loaderInfo.sharedEvents.dispatchEvent(new flash.events.Event(_registerCallback));
                }
            }
            catch(e:Error)
            {
            }
        }
    }
}
