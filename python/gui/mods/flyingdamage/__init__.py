# -*- coding: utf-8 -*-
# flyingdamage/__init__.py  --  Python 2.7
# Loads FlyingDamageApp.swf as an ExternalFlashComponent over the battle scene.
# Damage is queued in Python and pulled by AS3 every tick.
# Coordinates are stored normalized 0..1 so the SWF is resolution-independent.

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
_pullLog = [0]
_testLog = [False]
_damageQueue = []
_MAX_QUEUE = 64


def _fmt_float(v):
    try:
        return ('%.6f' % float(v)).rstrip('0').rstrip('.')
    except Exception:
        return '0'


def _screen_size():
    try:
        sw, sh = GUI.screenResolution()[:2]
        sw = float(sw)
        sh = float(sh)
        if sw <= 0.0 or sh <= 0.0:
            return 1920.0, 1080.0
        return sw, sh
    except Exception:
        return 1920.0, 1080.0


def _norm_xy(x, y):
    sw, sh = _screen_size()
    try:
        nx = float(x) / sw
        ny = float(y) / sh
    except Exception:
        nx, ny = 0.5, 0.5
    # Do not hard clamp to 0..1. Slightly off-screen values may still be useful
    # during edge cases, but keep them sane so broken projections cannot explode.
    nx = max(-0.25, min(1.25, nx))
    ny = max(-0.25, min(1.25, ny))
    return nx, ny, sw, sh


def _queue_record(record):
    try:
        _damageQueue.append(record)
        if len(_damageQueue) > _MAX_QUEUE:
            del _damageQueue[0:len(_damageQueue) - _MAX_QUEUE]
    except Exception:
        logger.error('[FlyingDamage] queue append failed', exc_info=True)


class _FlyingDamageMeta(BaseDAAPIModule):

    def py_log(self, msg):
        logger.info('[FlyingDamage] %s', msg)

    def py_pullDamageText(self):
        try:
            if not _damageQueue:
                return ''
            data = '\n'.join(_damageQueue)
            del _damageQueue[:]
            if _pullLog[0] < 20:
                _pullLog[0] += 1
                logger.info('[FlyingDamage] AS3 pulled damage queue: %s', data)
            return data
        except Exception:
            logger.error('[FlyingDamage] py_pullDamageText failed', exc_info=True)
            return ''

    def py_getScreenPos(self, vehicleID):
        try:
            from .hooks import projectVehicleScreen
            return projectVehicleScreen(int(vehicleID))
        except Exception:
            return None

    def py_projectWorld(self, x, y, z):
        try:
            from .hooks import projectWorldPoint
            pos = projectWorldPoint(float(x), float(y), float(z))
            if pos and pos.get('ok'):
                nx, ny, _sw, _sh = _norm_xy(pos.get('x', 0.0), pos.get('y', 0.0))
                pos['x'] = nx
                pos['y'] = ny
                pos['normalized'] = True
            return pos
        except Exception:
            return {'x': 0.5, 'y': 0.5, 'ok': False, 'normalized': True}

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
            self.flashObject.py_pullDamageText = self.py_pullDamageText
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
        if self._flash is None or _testLog[0]:
            return
        _testLog[0] = True
        logger.info('[FlyingDamage] queue debug test damage at normalized center 0.5 0.5')
        self.showDamageNormalized(0.5, 0.5, 9999, 0x00FFFF, 36, 1.0, 0.075, 4.0)

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
            del _damageQueue[:]
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

    def showDamageNormalized(self, nx, ny, damage, colorRGB, fontSize, alpha,
                             riseNormalized=0.055, lifeTime=1.6):
        try:
            rec = 'N|%s|%s|%d|%d|%d|%s|%s|%s' % (
                _fmt_float(nx), _fmt_float(ny), int(damage), int(colorRGB), int(fontSize),
                _fmt_float(alpha), _fmt_float(riseNormalized), _fmt_float(lifeTime))
            _queue_record(rec)
            if _pushLog[0] < 20:
                _pushLog[0] += 1
                logger.info('[FlyingDamage] queued normalized d=%s nx=%.4f ny=%.4f',
                            int(damage), float(nx), float(ny))
        except Exception:
            logger.error('[FlyingDamage] queue normalized failed', exc_info=True)

    def showDamageAt(self, x, y, damage, colorRGB, fontSize, alpha, risePixels=55.0, lifeTime=1.6):
        try:
            nx, ny, sw, sh = _norm_xy(x, y)
            # Convert vertical rise in pixels to normalized screen height.
            riseNorm = max(0.01, min(0.20, float(risePixels) / sh))
            self.showDamageNormalized(nx, ny, damage, colorRGB, fontSize, alpha, riseNorm, lifeTime)
            logger.info('[FlyingDamage] screen->normalized d=%s screen=(%.1f,%.1f) res=(%.0f,%.0f) norm=(%.4f,%.4f)',
                        int(damage), float(x), float(y), sw, sh, nx, ny)
        except Exception:
            logger.error('[FlyingDamage] queue screen failed', exc_info=True)

    def showDamageWorld(self, wx, wy, wz, fallbackX, fallbackY, damage, colorRGB,
                        fontSize, alpha, riseMeters=1.35, lifeTime=1.6):
        try:
            nx, ny, sw, sh = _norm_xy(fallbackX, fallbackY)
            rec = 'W|%s|%s|%s|%s|%s|%d|%d|%d|%s|%s|%s' % (
                _fmt_float(wx), _fmt_float(wy), _fmt_float(wz),
                _fmt_float(nx), _fmt_float(ny),
                int(damage), int(colorRGB), int(fontSize), _fmt_float(alpha),
                _fmt_float(riseMeters), _fmt_float(lifeTime))
            _queue_record(rec)
            if _pushLog[0] < 20:
                _pushLog[0] += 1
                logger.info('[FlyingDamage] queued world normalized d=%s norm=(%.4f,%.4f) res=(%.0f,%.0f)',
                            int(damage), nx, ny, sw, sh)
        except Exception:
            logger.error('[FlyingDamage] queue world failed', exc_info=True)

    def showDamage(self, x, y, damage, colorRGB, fontSize, alpha):
        self.showDamageAt(x, y, damage, colorRGB, fontSize, alpha)


g_controller = Controller()
