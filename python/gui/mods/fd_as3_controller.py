# -*- coding: utf-8 -*-
import logging

import BigWorld
from PlayerEvents import g_playerEvents

import fd_as3_state as state
from fd_as3_flash import FlyingDamageFlash

logger = logging.getLogger(__name__)


class Controller(object):

    def __init__(self):
        self._battleMode = False
        self._flash = None
        self._logN = 0

    def init(self):
        logger.info('[FD_AS3] controller init')
        state.controller[0] = self
        try:
            from flyingdamage.settings.config import g_config
            g_config.registerSettings()
        except Exception:
            logger.error('[FD_AS3] settings failed', exc_info=True)
        try:
            from flyingdamage.hooks import installHooks
            installHooks()
        except Exception:
            logger.error('[FD_AS3] hooks failed', exc_info=True)
        try:
            from flyingdamage.suppress import installSuppression, setFeed
            from flyingdamage.hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FD_AS3] suppression failed', exc_info=True)
        g_playerEvents.onAvatarReady += self._onAvatarReady
        g_playerEvents.onAvatarBecomeNonPlayer += self._onBattleLeave

    def fini(self):
        logger.info('[FD_AS3] controller fini')
        try:
            g_playerEvents.onAvatarReady -= self._onAvatarReady
            g_playerEvents.onAvatarBecomeNonPlayer -= self._onBattleLeave
        except Exception:
            pass
        self._battleMode = False
        self._destroyFlash()
        try:
            from flyingdamage.utils import restore_overrides
            restore_overrides()
        except Exception:
            pass
        state.controller[0] = None

    def _onAvatarReady(self, *a, **kw):
        self._battleMode = True
        del state.queue[:]
        logger.info('[FD_AS3] avatar ready')
        BigWorld.callback(3.0, self._installSuppressionSafe)

    def _installSuppressionSafe(self):
        if not self._battleMode:
            return
        try:
            from flyingdamage.suppress import installSuppression, setFeed
            from flyingdamage.hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FD_AS3] suppression late failed', exc_info=True)

    def onMarkerPluginStart(self):
        if not self._battleMode:
            return
        logger.info('[FD_AS3] marker plugin start')
        self._createFlash()

    def _createFlash(self):
        if self._flash is not None:
            return
        try:
            self._flash = FlyingDamageFlash()
            self._flash.activate()
            from flyingdamage.hooks import setView
            setView(self)
        except Exception:
            logger.error('[FD_AS3] create failed', exc_info=True)
            self._flash = None

    def _onBattleLeave(self, *a, **kw):
        logger.info('[FD_AS3] battle leave')
        self._battleMode = False
        self._destroyFlash()
        try:
            from flyingdamage.hooks import resetState
            resetState()
        except Exception:
            pass
        try:
            from flyingdamage.suppress import resetState as suppressReset
            suppressReset()
        except Exception:
            pass

    def _destroyFlash(self):
        del state.queue[:]
        if self._flash is not None:
            try:
                self._flash.close()
            except Exception:
                pass
            self._flash = None
        try:
            from flyingdamage.hooks import setView
            setView(None)
        except Exception:
            pass

    def showDamage(self, vehicleID, damage, colorRGB, fontSize, alpha):
        if not self._battleMode or self._flash is None or damage <= 0:
            return
        state.queue.append({
            'vid': str(int(vehicleID)),
            'dmg': int(damage),
            'color': int(colorRGB) & 0xFFFFFF,
            'size': int(fontSize),
            'alpha': float(alpha),
        })
        if self._logN < 80:
            self._logN += 1
            logger.info('[FD_AS3] queued vid=%s dmg=%s color=0x%06X q=%s', int(vehicleID), int(damage), int(colorRGB) & 0xFFFFFF, len(state.queue))


g_controller = Controller()
