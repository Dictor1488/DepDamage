# -*- coding: utf-8 -*-
# flyingdamage/__init__.py  --  Python 2.7
# Loads FlyingDamageApp.swf as an ExternalFlashComponent over the battle scene.
# Damage is pushed into AS3 using primitive arguments; Python dict/Object passing
# is deliberately avoided because it was not reliable on the current client.

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
_LINKAGE = 'FlyingDamageApp'
_pushLog = [0]
_testLog = [False]


class _FlyingDamageMeta(BaseDAAPIModule):

    def py_log(self, msg):
        logger.info('[FlyingDamage] %s', msg)

    def py_getScreenPos(self, vehicleID):
        try:
            from .hooks import projectVehicleScreen
            return projectVehicleScreen(int(vehicleID))
        except Exception:
            return None

    def py_projectWorld(self, x, y, z):
        try:
            from .hooks import projectWorldPoint
            return projectWorldPoint(float(x), float(y), float(z))
        except Exception:
            return {'x': 0.0, 'y': 0.0, 'ok': False}

    def as_populate(self):
        if self._isDAAPIInited():
            self.flashObject.as_populate()

    def as_clear(self):
        if self._isDAAPIInited():
            self.flashObject.as_clear()

    def as_showDamageScreen(self, x, y, damage, colorRGB, fontSize, alpha, rise, life):
        if self._isDAAPIInited():
            self.flashObject.as_showDamageScreen(x, y, damage, colorRGB, fontSize, alpha, rise, life)

    def as_showDamageWorld(self, wx, wy, wz, fallbackX, fallbackY,
                           damage, colorRGB, fontSize, alpha, rise, life):
        if self._isDAAPIInited():
            self.flashObject.as_showDamageWorld(wx, wy, wz, fallbackX, fallbackY,
                                                damage, colorRGB, fontSize, alpha, rise, life)


class FlyingDamageFlash(ExternalFlashComponent, _FlyingDamageMeta):

    def __init__(self):
        super(FlyingDamageFlash, self).__init__(
            ExternalFlashSettings(_LINKAGE, _SWF_NAME, 'root', None))
        self.createExternalComponent()
        self._configureApp()
        try:
            self.flashObject.py_log = self.py_log
            self.flashObject.py_getScreenPos = self.py_getScreenPos
            self.flashObject.py_projectWorld = self.py_projectWorld
        except Exception:
            logger.error('[FlyingDamage] wiring callbacks failed', exc_info=True)
        self.as_populate()
        logger.info('[FlyingDamage] flash component created')

    def _configureApp(self):
        try:
            self.movie.backgroundAlpha = 0.0
            self.movie.scaleMode = SCALEFORM.eMovieScaleMode.NO_SCALE
            if InputKeyMode is not None:
                self.component.wg_inputKeyMode = InputKeyMode.NO_HANDLE
            self.component.position.z = _DEPTH + 1.0
            self.component.focus = False
            self.component.moveFocus = False
            logger.info('[FlyingDamage] flash depth set to %.3f', self.component.position.z)
        except Exception:
            logger.error('[FlyingDamage] configureApp partial', exc_info=True)

    def close(self):
        try:
            self.as_dispose()
        except Exception:
            pass
        try:
            super(FlyingDamageFlash, self).close()
        except Exception:
            logger.info('[FlyingDamage] flash close (non-fatal)')

    def as_dispose(self):
        if self._isDAAPIInited():
            self.flashObject.as_dispose()


class Controller(object):

    def __init__(self):
        self._enabled = True
        self._battleMode = False
        self._flash = None

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
        logger.info('[FlyingDamage] avatar ready -> creating flash')
        self._createFlash()
        BigWorld.callback(1.0, self._debugTestDamage)
        BigWorld.callback(3.0, self._installSuppressionSafe)

    def _debugTestDamage(self):
        # Temporary diagnostic marker. If this 9999 is visible in battle, SWF
        # rendering works and only damage-event positioning needs tuning.
        if self._flash is None or _testLog[0]:
            return
        try:
            sw, sh = GUI.screenResolution()[:2]
        except Exception:
            sw, sh = 1920, 1080
        _testLog[0] = True
        logger.info('[FlyingDamage] debug test damage at center %.1f %.1f', sw / 2.0, sh / 2.0)
        self.showDamageAt(sw / 2.0, sh / 2.0, 9999, 0x00FFFF, 36, 1.0, 80.0, 2.5)

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

    def showDamageAt(self, x, y, damage, colorRGB, fontSize, alpha, risePixels=55.0, lifeTime=1.6):
        if self._flash is None:
            return
        try:
            self._flash.as_showDamageScreen(float(x), float(y), int(damage), int(colorRGB),
                                            int(fontSize), float(alpha), float(risePixels), float(lifeTime))
            if _pushLog[0] < 12:
                _pushLog[0] += 1
                logger.info('[FlyingDamage] pushed primitive screen d=%s x=%.1f y=%.1f',
                            int(damage), float(x), float(y))
        except Exception:
            logger.error('[FlyingDamage] primitive screen push failed', exc_info=True)

    def showDamageWorld(self, wx, wy, wz, fallbackX, fallbackY, damage, colorRGB,
                        fontSize, alpha, riseMeters=1.35, lifeTime=1.6):
        if self._flash is None:
            return
        try:
            self._flash.as_showDamageWorld(float(wx), float(wy), float(wz),
                                           float(fallbackX), float(fallbackY),
                                           int(damage), int(colorRGB), int(fontSize),
                                           float(alpha), float(riseMeters), float(lifeTime))
            if _pushLog[0] < 12:
                _pushLog[0] += 1
                logger.info('[FlyingDamage] pushed primitive world d=%s x=%.1f y=%.1f',
                            int(damage), float(fallbackX), float(fallbackY))
        except Exception:
            logger.error('[FlyingDamage] primitive world push failed', exc_info=True)

    def showDamage(self, x, y, damage, colorRGB, fontSize, alpha):
        self.showDamageAt(x, y, damage, colorRGB, fontSize, alpha)


g_controller = Controller()
