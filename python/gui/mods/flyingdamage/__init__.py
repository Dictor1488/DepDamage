# -*- coding: utf-8 -*-
# flyingdamage/__init__.py  --  Python 2.7
# One-shot visible renderer: in this WoT build only the first framework-driven
# as_populate reliably reaches AS3. Therefore the SWF is created when damage is
# already queued, so that first as_populate immediately pulls and draws it.

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
_flashSeq = [0]


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
            logger.error('[FlyingDamage] py_pullDamage failed', exc_info=True)
            return []

    def as_populate(self):
        if self._isDAAPIInited():
            self.flashObject.as_populate()


class FlyingDamageFlash(ExternalFlashComponent, _FlyingDamageMeta):

    def __init__(self, seq):
        self._seq = seq
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
        try:
            self.active(True)
            logger.info('[FlyingDamage] oneShot flash #%s active(True) queue=%d', self._seq, len(_damageQueue[0]))
        except Exception:
            logger.error('[FlyingDamage] active failed', exc_info=True)
        logger.info('[FlyingDamage] oneShot flash #%s created', self._seq)

    def _configureApp(self):
        try:
            self.movie.backgroundAlpha = 0.0
            self.movie.scaleMode = SCALEFORM.eMovieScaleMode.NO_SCALE
            if InputKeyMode is not None:
                self.component.wg_inputKeyMode = InputKeyMode.NO_HANDLE
            self.component.position.z = 9999.0
            self.component.focus = False
            self.component.moveFocus = False
        except Exception:
            logger.error('[FlyingDamage] configureApp partial', exc_info=True)

    def close(self):
        try:
            if self._isDAAPIInited():
                self.flashObject.as_dispose()
        except Exception:
            pass
        try:
            super(FlyingDamageFlash, self).close()
        except Exception:
            logger.info('[FlyingDamage] oneShot flash close non-fatal')


class Controller(object):

    def __init__(self):
        self._enabled = True
        self._battleMode = False
        self._flashes = []
        self._pushLog = 0

    def init(self):
        logger.info('[FlyingDamage] controller.init begin one-shot SWF renderer')
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
        self._destroyAllFlashes()
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
        # Do not create SWF here. Creating it before damage means the only
        # reliable AS3 entry (first as_populate) is wasted with an empty queue.
        logger.info('[FlyingDamage] marker plugin start -> waiting for damage')
        try:
            from .hooks import setView
            setView(self)
        except Exception:
            pass

    def _installSuppressionSafe(self):
        try:
            from .suppress import installSuppression, setFeed
            from .hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FlyingDamage] installSuppression failed', exc_info=True)

    def _makeFlashForQueuedDamage(self):
        _flashSeq[0] += 1
        seq = _flashSeq[0]
        try:
            flash = FlyingDamageFlash(seq)
            self._flashes.append(flash)
            BigWorld.callback(2.0, lambda: self._closeFlash(flash, seq))
        except Exception:
            logger.error('[FlyingDamage] oneShot flash create failed', exc_info=True)

    def _closeFlash(self, flash, seq):
        try:
            if flash in self._flashes:
                self._flashes.remove(flash)
            flash.close()
            logger.info('[FlyingDamage] oneShot flash #%s closed', seq)
        except Exception:
            pass

    def _onBattleLeave(self, *a, **kw):
        logger.info('[FlyingDamage] battle leave')
        self._battleMode = False
        self._destroyAllFlashes()
        try:
            del _damageQueue[0][:]
        except Exception:
            pass
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

    def _destroyAllFlashes(self):
        for flash in list(self._flashes):
            try:
                flash.close()
            except Exception:
                pass
        self._flashes = []
        try:
            from .hooks import setView
            setView(None)
        except Exception:
            pass

    def showDamage(self, vehicleID, damage, colorRGB, fontSize, alpha):
        _damageQueue[0].append({
            'vid': str(int(vehicleID)),
            'dmg': int(damage),
            'color': int(colorRGB),
            'size': int(fontSize),
            'alpha': float(alpha),
        })
        if self._pushLog < 120:
            self._pushLog += 1
            logger.info('[FlyingDamage] queued oneShot damage vid=%s dmg=%s queue=%d -> create SWF',
                        int(vehicleID), int(damage), len(_damageQueue[0]))
        self._makeFlashForQueuedDamage()


g_controller = Controller()
