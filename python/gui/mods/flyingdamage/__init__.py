# -*- coding: utf-8 -*-
# flyingdamage/__init__.py  --  Python 2.7
# Loads FlyingDamageApp.swf as an ExternalFlashComponent over the battle scene
# (same mechanism as DistanceMarker, which reliably loads and runs its SWF).
# Feeds floating damage numbers that stick to tanks.

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
_bridgeLog = [False]
_damageQueue = [[]]   # list of {vid, dmg, color, size, alpha} pending for SWF


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
        # Return and clear the queue of newly-dealt damage.
        try:
            q = _damageQueue[0]
            if not q:
                return []
            _damageQueue[0] = []
            return q
        except Exception:
            return []

    def as_populate(self):
        if self._isDAAPIInited():
            self.flashObject.as_populate()

    def as_update(self):
        try:
            fo = self.flashObject
            if fo is not None:
                fo.as_update()
        except Exception:
            logger.error('[FlyingDamage] as_update error', exc_info=True)

    def as_tick(self):
        try:
            if self._isDAAPIInited():
                self.flashObject.as_tick()
        except Exception:
            pass

    def as_clear(self):
        if self._isDAAPIInited():
            self.flashObject.as_clear()


class FlyingDamageFlash(ExternalFlashComponent, _FlyingDamageMeta):

    def __init__(self):
        super(FlyingDamageFlash, self).__init__(
            ExternalFlashSettings(_LINKAGE, _SWF_NAME, 'root', None))
        self.createExternalComponent()
        self._configureApp()
        # Wire callbacks. active(True) is NOT called here — DistanceMarker calls
        # it externally AFTER construction (from the start hook). Activating
        # inside the constructor, before the object is fully wired, breaks the
        # render/tick activation.
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
        # SYNC TEST: call as_update once synchronously here (same context in
        # which DistanceMarker calls as_applyConfig successfully). If this
        # reaches the SWF, push works synchronously and we drive from a sync
        # source; if not, the bridge is fully one-way for us.
        try:
            if self._isDAAPIInited():
                self.flashObject.as_update()
                logger.info('[FlyingDamage] SYNC as_update called in activate')
        except Exception:
            logger.error('[FlyingDamage] sync as_update failed', exc_info=True)
        self._updRunning = True
        self._pumpUpdate()

    def _pumpUpdate(self):
        if not getattr(self, '_updRunning', False):
            return
        self._updCount = getattr(self, '_updCount', 0) + 1
        if self._updCount <= 3 or self._updCount % 300 == 0:
            logger.info('[FlyingDamage] pumpUpdate #%d DAAPIInited=%s flashObj=%s',
                        self._updCount, self._isDAAPIInited(),
                        self.flashObject is not None)
        try:
            self.as_update()
        except Exception:
            pass
        BigWorld.callback(0.016, self._pumpUpdate)

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
        self._tickRunning = False
        self._updRunning = False
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
        logger.info('[FlyingDamage] avatar ready')
        BigWorld.callback(3.0, self._installSuppressionSafe)

    def onMarkerPluginStart(self):
        # Called from VehicleMarkerPlugin.start hook — the correct lifecycle
        # point to create+activate the flash (matches DistanceMarker).
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
            # Activate AFTER construction — exactly as DistanceMarker does:
            #   g_distanceMarkerFlash = DistanceMarkerFlash(...); .active(True)
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
        # Enqueue; the SWF pulls this via py_pullDamage() each frame.
        _damageQueue[0].append({
            'vid': str(int(vehicleID)),
            'dmg': int(damage),
            'color': int(colorRGB),
            'size': int(fontSize),
            'alpha': float(alpha),
        })


g_controller = Controller()
