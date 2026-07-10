package net.wg.app.impl
{
    import flash.display.DisplayObject;
    import flash.display.Loader;
    import flash.display.LoaderInfo;
    import flash.events.Event;
    import flash.events.IOErrorEvent;
    import flash.net.URLRequest;
    import flash.system.ApplicationDomain;
    import flash.system.LoaderContext;
    import net.wg.app.iml.base.RootApp;
    import net.wg.data.constants.generated.ROOT_SWF_CONSTANTS;
    import net.wg.gui.battle.views.vehicleMarkers.VehicleMarkersManager;
    import net.wg.infrastructure.base.meta.impl.ClassManagerBattleMarkersMeta;
    import net.wg.infrastructure.interfaces.IRootAppMainContent;

    public class BattleVehicleMarkersApp extends RootApp
    {
        public static const CLASS_MANAGER_META:Class = ClassManagerBattleMarkersMeta;

        private static const LIBS_LIST:Vector.<String> = new <String>[
            'epicSharedAssets.swf',
            'battleStaticMarkers.swf',
            'battleVehicleMarkers.swf'
        ];

        private static const DEPDAMAGE_UI_SWF:String = 'depdamage_vehiclemarkers_ui.swf';

        private var _depDamageLoader:Loader;
        private var _depDamageSwf:DisplayObject;

        public function BattleVehicleMarkersApp()
        {
            super(new VehicleMarkersManager(), LIBS_LIST, ROOT_SWF_CONSTANTS.BATTLE_VEHICLE_MARKERS_REGISTER_CALLBACK);
        }

        override protected function onLibsLoadingComplete():void
        {
            super.onLibsLoadingComplete();
            loadDepDamage(DEPDAMAGE_UI_SWF);
        }

        private function loadDepDamage(swfPath:String):void
        {
            _depDamageLoader = new Loader();
            addChild(_depDamageLoader);
            _depDamageLoader.contentLoaderInfo.addEventListener(Event.COMPLETE, onDepDamageLoadedComplete, false, 0, true);
            _depDamageLoader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR, onDepDamageLoadedError, false, 0, true);
            _depDamageLoader.load(
                new URLRequest(swfPath),
                new LoaderContext(false, ApplicationDomain.currentDomain)
            );
        }

        private function onDepDamageLoadedComplete(e:Event):void
        {
            var loaderInfo:LoaderInfo = e.currentTarget as LoaderInfo;
            if (loaderInfo != null)
            {
                _depDamageSwf = loaderInfo.content;
                finishDepDamageLoading(loaderInfo);
            }
            else
            {
                callRegisterCallback();
            }
        }

        private function onDepDamageLoadedError(e:IOErrorEvent):void
        {
            var loaderInfo:LoaderInfo = e.currentTarget as LoaderInfo;
            finishDepDamageLoading(loaderInfo);
        }

        private function finishDepDamageLoading(loaderInfo:LoaderInfo):void
        {
            if (loaderInfo != null)
            {
                loaderInfo.removeEventListener(Event.COMPLETE, onDepDamageLoadedComplete);
                loaderInfo.removeEventListener(IOErrorEvent.IO_ERROR, onDepDamageLoadedError);
            }
            callRegisterCallback();
        }

        public function get vehicleMarkersCanvas():IRootAppMainContent
        {
            return main;
        }
    }
}
