package net.wg.gui.battle.views.vehicleMarkers
{
   import com.greensock.TimelineLite;
   import com.greensock.TweenLite;
   import com.greensock.easing.Linear;
   import com.greensock.plugins.TintPlugin;
   import com.greensock.plugins.TweenPlugin;
   import flash.display.MovieClip;
   
   internal class DamageAnimatedLabel
   {
      
      private static var EMERGE_DURATION:Number = 0.3;
      
      private static var TINT_DURATION:Number = 0.4;
      
      private static var FADEOUT_DURATION:Number = 0.5;
      
      private static var FADEOUT_TIME_OFFSET:Number = -FADEOUT_DURATION;
      
      TweenPlugin.activate([TintPlugin]);
      
      private var mc:MovieClip;
      
      private var timeline:TimelineLite;
      
      public function DamageAnimatedLabel(param1:MovieClip, param2:Number)
      {
         super();
         this.mc = param1;
         var _loc4_:Number = param1.y - param2;
         this.timeline = new TimelineLite({"onComplete":this.removeMovieClip});
         this.timeline.insert(this.emerge(),0);
         this.timeline.insert(this.tint(),0);
         this.timeline.insert(this.moveUpward(2,_loc4_),0);
         this.timeline.append(this.fadeOut(),FADEOUT_TIME_OFFSET);
      }
      
      private function emerge() : TweenLite
      {
         return TweenLite.from(this.mc,EMERGE_DURATION,{
            "alpha":0,
            "ease":Linear.easeNone,
            "cacheAsBitmap":true
         });
      }
      
      private function tint() : TweenLite
      {
         return TweenLite.from(this.mc,TINT_DURATION,{
            "tint":"0xFFFFFF",
            "ease":Linear.easeNone,
            "cacheAsBitmap":true
         });
      }
      
      private function moveUpward(param1:Number, param2:Number) : TweenLite
      {
         return TweenLite.to(this.mc,param1,{
            "y":param2,
            "ease":Linear.easeNone,
            "cacheAsBitmap":true
         });
      }
      
      private function fadeOut() : TweenLite
      {
         return TweenLite.to(this.mc,FADEOUT_DURATION,{
            "alpha":0,
            "ease":Linear.easeNone,
            "cacheAsBitmap":true
         });
      }
      
      private function removeMovieClip() : void
      {
         this.mc.removeChildren();
         this.mc.parent.removeChild(this.mc);
         this.mc = null;
      }
   }
}

