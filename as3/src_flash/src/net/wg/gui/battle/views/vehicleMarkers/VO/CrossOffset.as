package net.wg.gui.battle.views.vehicleMarkers.VO
{
   import flash.utils.Dictionary;
   import net.wg.infrastructure.interfaces.entity.IDisposable;
   
   public class CrossOffset implements IDisposable
   {
      
      private var _offsetByObject:Dictionary;
      
      private var _disposed:Boolean = false;
      
      public function CrossOffset(... rest)
      {
         var _loc2_:int = 0;
         this._offsetByObject = new Dictionary(true);
         super();
         var _loc3_:int = int(rest.length);
         var _loc4_:Object = null;
         var _loc5_:int = 0;
         while(_loc5_ < _loc3_)
         {
            if((_loc5_ & 1) == 0)
            {
               _loc4_ = rest[_loc5_];
            }
            else
            {
               _loc2_ = int(rest[_loc5_]);
               this._offsetByObject[_loc4_] = _loc2_;
            }
            _loc5_++;
         }
      }
      
      final public function dispose() : void
      {
         var _loc1_:* = undefined;
         this._disposed = true;
         for(_loc1_ in this._offsetByObject)
         {
            this._offsetByObject[_loc1_] = null;
            delete this._offsetByObject[_loc1_];
         }
         this._offsetByObject = null;
      }
      
      public function getOffset(param1:Object) : int
      {
         return this._offsetByObject[param1];
      }
      
      public function hasOffset(param1:Object) : Boolean
      {
         return this._offsetByObject[param1] != undefined && this._offsetByObject[param1] != null;
      }
      
      public function isDisposed() : Boolean
      {
         return this._disposed;
      }
      
      public function appendOffset(param1:Object, param2:int) : void
      {
         this._offsetByObject[param1] = param2;
      }
   }
}

