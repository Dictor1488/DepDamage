# -*- coding: utf-8 -*-
# flyingdamage/__init__.py  --  Python 2.7
# Loads FlyingDamageApp.swf as an ExternalFlashComponent over the battle scene.
# In this WoT build only as_populate reliably reaches AS3, so Python drives the
# renderer by repeatedly calling as_populate(); the SWF treats it as a tick.

import logging

import BigWorld
import GUI
import SCALEFORM
from PlayerEvents import g_playerEvents

logger = logging.getLogger(__name__)

try:
    from gui import DEPTH_OF_VehicleMarker as _DEPTH
except Exception:
    try:
        from gui import DEPTH_OF_Battle as _DEPTH
    except Exception:
        _DEPTH = 0.0

from gui.Scaleform.daapi.view.external_components import (
    ExternalFlashComponent, ExternalFlashSettings)
from gui.Scaleform.framework.entities.BaseDAAPIModule import BaseDAAPIModule

try:
    from gui.Scaleform.flash_wrapper import InputKeyMode
except Exception:
    InputKeyMode = None


_SWF_NAME = 'FlyingDamageApp.swf'
_LINKAGE = 'com.flyingdamage.FlyingDamageApp'
_damageQueue = [[]]


class _FlyingDamageMeta(BaseDAAPIModule):

    def py_log(self, msg):
        logger.info('[FlyingDamage] %s', msg)

    def py_getScreenPos(self, vehicleID):
        try:
            from .hooks import projectVehicleScreen
            return projectVehicleScreen(int(vehicleID))
        except Exception:
            return None

    def py_pullDamage(self):
        try:
            q = _damageQueue[0]
            if not q:
                return []
            _damageQueue[0] = []
            logger.info('[FlyingDamage] py_pullDamage returns %d item(s)', len(q))
            return q
        except Exception:
            return []

    def as_populate(self):
        if self._isDAAPIInited():
            self.flashObject.as_populate()

    def as_clear(self):
        if self._isDAAPIInited():
            self.flashObject.as_clear()


class FlyingDamageFlash(ExternalFlashComponent, _FlyingDamageMeta):

    def __init__(self):
        super(FlyingDamageFlash, self).__init__(
            ExternalFlashSettings(_LINKAGE, _SWF_NAME, 'root', None))
        self.createExternalComponent()
        self._configureApp()
        try:
            self.flashObject.py_log = self.py_log
            self.flashObject.py_getScreenPos = self.py_getScreenPos
            self.flashObject.py_pullDamage = self.py_pullDamage
        except Exception:
            logger.error('[FlyingDamage] wiring callbacks failed', exc_info=True)
        logger.info('[FlyingDamage] flash component created')

    def activate(self):
        try:
            self.active(True)
            logger.info('[FlyingDamage] active(True) called')
        except Exception:
            logger.error('[FlyingDamage] active(True) failed', exc_info=True)
        self._popRunning = True
        self._popCount = 0
        self._pumpPopulate()

    def _pumpPopulate(self):
        if not getattr(self, '_popRunning', False):
            return
        self._popCount += 1
        if self._popCount <= 5 or self._popCount % 300 == 0:
            logger.info('[FlyingDamage] pumpPopulate #%d DAAPIInited=%s flashObj=%s queue=%d',
                        self._popCount, self._isDAAPIInited(),
                        self.flashObject is not None, len(_damageQueue[0]))
        try:
            self.as_populate()
        except Exception:
            logger.error('[FlyingDamage] pumpPopulate failed', exc_info=True)
        BigWorld.callback(0.016, self._pumpPopulate)

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
            logger.error('[FlyingDamage] configureApp partial', exc_info=True)

    def close(self):
        self._popRunning = False
        try:
            if self._isDAAPIInited():
                self.flashObject.as_dispose()
        except Exception:
            pass
        try:
            super(FlyingDamageFlash, self).close()
        except Exception:
            logger.info('[FlyingDamage] flash close (non-fatal)')


class Controller(object):

    def __init__(self):
        self._enabled = True
        self._battleMode = False
        self._flash = None
        self._pushLog = 0

    def init(self):
        logger.info('[FlyingDamage] controller.init begin')
        try:
            from .settings.config import g_config
            g_config.registerSettings()
        except Exception:
            logger.error('[FlyingDamage] settings failed', exc_info=True)

        try:
            from .hooks import installHooks
            installHooks()
        except Exception:
            logger.error('[FlyingDamage] installHooks failed', exc_info=True)

        try:
            from .suppress import installSuppression, setFeed
            from .hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FlyingDamage] early suppression failed', exc_info=True)

        g_playerEvents.onAvatarReady += self._onAvatarReady
        g_playerEvents.onAvatarBecomeNonPlayer += self._onBattleLeave
        logger.info('[FlyingDamage] controller.init done')

    def fini(self):
        logger.info('[FlyingDamage] controller.fini')
        try:
            g_playerEvents.onAvatarReady -= self._onAvatarReady
            g_playerEvents.onAvatarBecomeNonPlayer -= self._onBattleLeave
        except Exception:
            pass
        self._destroyFlash()
        try:
            from .utils import restore_overrides
            restore_overrides()
        except Exception:
            pass

    def _onAvatarReady(self, *a, **kw):
        self._battleMode = True
        logger.info('[FlyingDamage] avatar ready')
        BigWorld.callback(3.0, self._installSuppressionSafe)

    def onMarkerPluginStart(self):
        logger.info('[FlyingDamage] marker plugin start -> creating flash')
        self._createFlash()

    def _installSuppressionSafe(self):
        try:
            from .suppress import installSuppression, setFeed
            from .hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FlyingDamage] installSuppression failed', exc_info=True)

    def _createFlash(self):
        if self._flash is not None:
            return
        try:
            self._flash = FlyingDamageFlash()
            self._flash.activate()
            from .hooks import setView
            setView(self)
        except Exception:
            logger.error('[FlyingDamage] createFlash failed', exc_info=True)
            self._flash = None

    def _onBattleLeave(self, *a, **kw):
        logger.info('[FlyingDamage] battle leave')
        self._battleMode = False
        self._destroyFlash()
        try:
            from .hooks import resetState
            resetState()
        except Exception:
            pass
        try:
            from .suppress import resetState as suppressReset
            suppressReset()
        except Exception:
            pass

    def _destroyFlash(self):
        if self._flash is not None:
            try:
                self._flash.close()
            except Exception:
                pass
            self._flash = None
        try:
            from .hooks import setView
            setView(None)
        except Exception:
            pass

    def showDamage(self, vehicleID, damage, colorRGB, fontSize, alpha):
        if self._flash is None:
            return
        _damageQueue[0].append({
            'vid': str(int(vehicleID)),
            'dmg': int(damage),
            'color': int(colorRGB),
            'size': int(fontSize),
            'alpha': float(alpha),
        })
        if self._pushLog < 80:
            self._pushLog += 1
            logger.info('[FlyingDamage] queued visible vehicle damage vid=%s dmg=%s queue=%d',
                        int(vehicleID), int(damage), len(_damageQueue[0]))


g_controller = Controller()
