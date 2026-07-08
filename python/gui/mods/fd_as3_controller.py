# -*- coding: utf-8 -*-
import logging

import BigWorld
from PlayerEvents import g_playerEvents

from gui.mods import fd_as3_state as state
from gui.mods.fd_as3_flash import FlyingDamageFlash

logger = logging.getLogger(__name__)
_LABELED_TYPES = ('blocked', 'blocked_crit', 'ricochet')
_CLOSE_DELAY = 2.35
_MAX_FLASHES = 16


class Controller(object):

    def __init__(self):
        self._battleMode = False
        self._flashes = []
        self._closeCbs = []
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
        self._destroyAllFlash(True)
        try:
            from flyingdamage.utils import restore_overrides
            restore_overrides()
        except Exception:
            pass
        state.controller[0] = None

    def _onAvatarReady(self, *a, **kw):
        self._battleMode = True
        self._logN = 0
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
        try:
            from flyingdamage.hooks import setView
            setView(self)
        except Exception:
            pass

    def _destroyAllFlash(self, clearQueue=False):
        if clearQueue:
            del state.queue[:]
        for cb in list(self._closeCbs):
            try:
                BigWorld.cancelCallback(cb)
            except Exception:
                pass
        self._closeCbs = []
        for flash in list(self._flashes):
            self._closeFlash(flash)
        self._flashes = []

    def _closeFlash(self, flash):
        try:
            if flash in self._flashes:
                self._flashes.remove(flash)
        except Exception:
            pass
        try:
            flash.close()
        except Exception:
            pass

    def _closeLater(self, flash):
        try:
            self._closeFlash(flash)
        except Exception:
            pass

    def _createFlashForQueue(self):
        if not self._battleMode or not state.queue:
            return
        try:
            while len(self._flashes) >= _MAX_FLASHES:
                old = self._flashes.pop(0)
                self._closeFlash(old)
            flash = FlyingDamageFlash()
            self._flashes.append(flash)
            flash.activate()
            cb = BigWorld.callback(_CLOSE_DELAY, lambda f=flash: self._closeLater(f))
            self._closeCbs.append(cb)
            logger.info('[FD_AS3] flash spawned q=%s active=%s', len(state.queue), len(self._flashes))
        except Exception:
            logger.error('[FD_AS3] spawn flash failed', exc_info=True)

    def _onBattleLeave(self, *a, **kw):
        logger.info('[FD_AS3] battle leave')
        self._battleMode = False
        self._destroyAllFlash(True)
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

    def _getStartPoint(self, vehicleID):
        try:
            from flyingdamage.hooks import projectVehicleScreen
            pos = projectVehicleScreen(int(vehicleID), quiet=True)
            if pos and pos.get('ok'):
                return True, float(pos.get('x', 0.0)), float(pos.get('y', 0.0))
        except Exception:
            pass
        return False, 0.0, 0.0

    def _getHpData(self, vehicleID, damage):
        try:
            vehicle = BigWorld.entity(int(vehicleID))
            if vehicle is None:
                return False, 0, 0, 0
            cur = int(getattr(vehicle, 'health', 0) or 0)
            desc = getattr(vehicle, 'typeDescriptor', None)
            maxHp = int(getattr(desc, 'maxHealth', 0) or 0) if desc is not None else 0
            if maxHp <= 0:
                maxHp = int(getattr(vehicle, 'maxHealth', 0) or 0)
            if maxHp <= 0:
                return False, 0, 0, 0
            if cur < 0:
                cur = 0
            if cur > maxHp:
                cur = maxHp
            before = cur + int(max(0, damage))
            if before > maxHp:
                before = maxHp
            if before < cur:
                before = cur
            return True, cur, before, maxHp
        except Exception:
            return False, 0, 0, 0

    def showDamage(self, vehicleID, damage, colorRGB, fontSize, alpha, damageType='shot'):
        damageType = damageType or 'shot'
        if not self._battleMode:
            return
        if damage <= 0 and damageType not in _LABELED_TYPES:
            return
        hasStart, sx, sy = self._getStartPoint(vehicleID)
        hasHp, hpCur, hpBefore, hpMax = self._getHpData(vehicleID, damage)
        sourceFlag = 2 if (int(colorRGB) & 0xFFFFFF) == 0xFFDC3C else 0
        item = {
            'vid': str(int(vehicleID)),
            'dmg': int(max(0, damage)),
            'color': int(colorRGB) & 0xFFFFFF,
            'size': int(fontSize),
            'alpha': float(alpha),
            'hasStart': bool(hasStart),
            'x': float(sx),
            'y': float(sy),
            'hasHp': bool(hasHp),
            'hpCur': int(hpCur),
            'hpBefore': int(hpBefore),
            'hpMax': int(hpMax),
            'sourceFlag': int(sourceFlag),
            'damageType': str(damageType),
        }
        state.queue.append(item)
        if self._logN < 120:
            self._logN += 1
            logger.info('[FD_AS3] queued marker vid=%s dmg=%s hasStart=%s hp=%s %s/%s->%s source=%s type=%s color=0x%06X q=%s', int(vehicleID), int(damage), bool(hasStart), bool(hasHp), hpBefore, hpMax, hpCur, sourceFlag, damageType, int(colorRGB) & 0xFFFFFF, len(state.queue))
        self._createFlashForQueue()


g_controller = Controller()
