package net.wg.infrastructure.events
{
    import flash.events.Event;

    public class AtlasEvent extends Event
    {
        public static const ATLAS_INITIALIZED:String = "atlasInitialized";

        public function AtlasEvent(type:String, bubbles:Boolean = false, cancelable:Boolean = false)
        {
            super(type, bubbles, cancelable);
        }

        override public function clone() : Event
        {
            return new AtlasEvent(type, bubbles, cancelable);
        }
    }
}
