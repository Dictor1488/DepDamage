# -*- coding: utf-8 -*-
import logging

import SCALEFORM

logger = logging.getLogger(__name__)

try:
    from gui import DEPTH_OF_VehicleMarker as _DEPTH
except Exception:
    try:
        from gui import DEPTH_OF_Battle as _DEPTH
    except Exception:
        _DEPTH = 0.0

from gui.Scaleform.daapi.view.external_components import ExternalFlashComponent, ExternalFlashSettings
from gui.Scaleform.framework.entities.BaseDAAPIModule import BaseDAAPIModule

try:
    from gui.Scaleform.flash_wrapper import InputKeyMode
except Exception:
    InputKeyMode = None

import fd_as3_state as state

_SWF_NAME = 'FlyingDamageApp.swf'
_LINKAGE = 'com.flyingdamage.FlyingDamageApp'


class FlyingDamageMeta(BaseDAAPIModule):

    def py_log(self, msg):
        logger.info('[FD_AS3] %s', msg)

    def py_getScreenPos(self, vehicleID):
        try:
            from flyingdamage.hooks import projectVehicleScreen
            return projectVehicleScreen(int(vehicleID), quiet=True)
        except Exception:
            return {'x': 0.0, 'y': 0.0, 'ok': False}

    def py_pullDamage(self):
        try:
            if not state.queue:
                return []
            q = list(state.queue)
            del state.queue[:]
            return q
        except Exception:
            return []

    def as_populate(self):
        try:
            if self._isDAAPIInited():
                self.flashObject.as_populate()
        except Exception:
            logger.error('[FD_AS3] as_populate failed', exc_info=True)

    def as_dispose(self):
        try:
            if self._isDAAPIInited():
                self.flashObject.as_dispose()
        except Exception:
            pass


class FlyingDamageFlash(ExternalFlashComponent, FlyingDamageMeta):

    def __init__(self):
        super(FlyingDamageFlash, self).__init__(ExternalFlashSettings(_LINKAGE, _SWF_NAME, 'root', None))
        self.createExternalComponent()
        self._configureApp()
        try:
            self.flashObject.py_log = self.py_log
            self.flashObject.py_getScreenPos = self.py_getScreenPos
            self.flashObject.py_pullDamage = self.py_pullDamage
        except Exception:
            logger.error('[FD_AS3] callback wiring failed', exc_info=True)
        logger.info('[FD_AS3] component created')

    def _configureApp(self):
        try:
            self.movie.backgroundAlpha = 0.0
            self.movie.scaleMode = SCALEFORM.eMovieScaleMode.NO_SCALE
            if InputKeyMode is not None:
                self.component.wg_inputKeyMode = InputKeyMode.NO_HANDLE
            self.component.position.z = _DEPTH - 0.02
            self.component.focus = False
            self.component.moveFocus = False
        except Exception:
            logger.error('[FD_AS3] configure partial', exc_info=True)

    def activate(self):
        try:
            self.active(True)
            logger.info('[FD_AS3] active true')
        except Exception:
            logger.error('[FD_AS3] active failed', exc_info=True)
        self.as_populate()

    def close(self):
        try:
            self.as_dispose()
        except Exception:
            pass
        try:
            super(FlyingDamageFlash, self).close()
        except Exception:
            logger.info('[FD_AS3] close non fatal')
