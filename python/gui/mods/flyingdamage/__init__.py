# -*- coding: utf-8 -*-
import logging

import BigWorld
import GUI
import SCALEFORM
from PlayerEvents import g_playerEvents
from gui.Scaleform.daapi.view.external_components import ExternalFlashComponent, ExternalFlashSettings
from gui.Scaleform.framework.entities.BaseDAAPIModule import BaseDAAPIModule

try:
    from gui.Scaleform.flash_wrapper import InputKeyMode
except Exception:
    InputKeyMode = None

logger = logging.getLogger(__name__)

_SWF_NAME = 'FlyingDamageApp.swf'
_LINKAGE = 'FlyingDamageApp'
_HIGH_DEPTH = 9999.0
_MAX_QUEUE = 128
_PULL_BATCH = 24
_damageQueue = []
_nextQueueID = [1]
_pushLog = [0]
_pullLog = [0]
_ackLog = [0]


def _fmt_float(v):
    try:
        return ('%.6f' % float(v)).rstrip('0').rstrip('.')
    except Exception:
        return '0'


def _screen_size():
    try:
        sw, sh = GUI.screenResolution()[:2]
        sw, sh = float(sw), float(sh)
        if sw > 0.0 and sh > 0.0:
            return sw, sh
    except Exception:
        pass
    return 1920.0, 1080.0


def _norm_xy(x, y):
    sw, sh = _screen_size()
    try:
        nx = float(x) / sw
        ny = float(y) / sh
    except Exception:
        nx, ny = 0.5, 0.5
    return max(-0.5, min(1.5, nx)), max(-0.5, min(1.5, ny)), sw, sh


def _queue_record(record):
    try:
        qid = _nextQueueID[0]
        _nextQueueID[0] += 1
        full = '%d|%s' % (qid, record)
        _damageQueue.append(full)
        if len(_damageQueue) > _MAX_QUEUE:
            del _damageQueue[0:len(_damageQueue) - _MAX_QUEUE]
        return qid
    except Exception:
        logger.error('[FlyingDamage] queue append failed', exc_info=True)
        return 0


def _ack_record(qid):
    try:
        qid = str(int(qid))
    except Exception:
        return False
    removed = 0
    try:
        for i in xrange(len(_damageQueue) - 1, -1, -1):
            if _damageQueue[i].split('|', 1)[0] == qid:
                del _damageQueue[i]
                removed += 1
        if _ackLog[0] < 80:
            _ackLog[0] += 1
            logger.info('[FlyingDamage] ACK queue id=%s removed=%s left=%s', qid, removed, len(_damageQueue))
        return removed > 0
    except Exception:
        logger.error('[FlyingDamage] ack failed id=%s', qid, exc_info=True)
        return False


class _FlyingDamageMeta(BaseDAAPIModule):

    def py_log(self, msg):
        logger.info('[FlyingDamage] %s', msg)

    def py_ackDamage(self, qid):
        return _ack_record(qid)

    def py_pullDamageText(self):
        try:
            if not _damageQueue:
                return ''
            data = '\n'.join(_damageQueue[:_PULL_BATCH])
            if _pullLog[0] < 60:
                _pullLog[0] += 1
                logger.info('[FlyingDamage] AS3 pulled damage queue keep=%s batch=%s data=%s', len(_damageQueue), min(len(_damageQueue), _PULL_BATCH), data)
            return data
        except Exception:
            logger.error('[FlyingDamage] py_pullDamageText failed', exc_info=True)
            return ''

    def py_getScreenPos(self, vehicleID, riseMeters=0.0):
        try:
            from .hooks import projectVehicleScreen
            pos = projectVehicleScreen(int(vehicleID), float(riseMeters))
            if pos and pos.get('ok'):
                nx, ny, _sw, _sh = _norm_xy(pos.get('x', 0.0), pos.get('y', 0.0))
                pos['x'] = nx
                pos['y'] = ny
                pos['normalized'] = True
            return pos
        except Exception:
            return {'x': 0.5, 'y': 0.5, 'ok': False, 'normalized': True}

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


class FlyingDamageFlash(ExternalFlashComponent, _FlyingDamageMeta):

    def __init__(self):
        super(FlyingDamageFlash, self).__init__(ExternalFlashSettings(_LINKAGE, _SWF_NAME, 'root', None))
        self.createExternalComponent()
        self._configureApp()
        try:
            self.flashObject.py_log = self.py_log
            self.flashObject.py_pullDamageText = self.py_pullDamageText
            self.flashObject.py_ackDamage = self.py_ackDamage
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
            self.forceTopDepth()
        except Exception:
            logger.error('[FlyingDamage] configureApp partial', exc_info=True)

    def forceTopDepth(self):
        try:
            self.component.position.z = _HIGH_DEPTH
            self.component.focus = False
            self.component.moveFocus = False
            logger.info('[FlyingDamage] flash depth forced to %.1f', self.component.position.z)
        except Exception:
            logger.error('[FlyingDamage] force depth failed', exc_info=True)

    def close(self):
        try:
            if self._isDAAPIInited():
                self.flashObject.as_dispose()
        except Exception:
            pass
        try:
            super(FlyingDamageFlash, self).close()
        except Exception:
            logger.info('[FlyingDamage] flash close non-fatal')


class Controller(object):

    def __init__(self):
        self._battleMode = False
        self._flash = None
        self._depthTicks = 0

    def init(self):
        logger.info('[FlyingDamage] controller.init begin ACK polling custom SWF vehicle anchor')
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
        self._onBattleLeave()
        try:
            from .utils import restore_overrides
            restore_overrides()
        except Exception:
            pass

    def _onAvatarReady(self, *a, **kw):
        self._battleMode = True
        self._depthTicks = 0
        logger.info('[FlyingDamage] avatar ready -> delayed ACK polling custom SWF create')
        BigWorld.callback(2.0, self._createFlashDelayed)
        BigWorld.callback(3.5, self._installSuppressionSafe)

    def _createFlashDelayed(self):
        if not self._battleMode:
            return
        logger.info('[FlyingDamage] delayed create ACK polling custom SWF now')
        self._createFlash()
        self._keepDepthOnTop()

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

    def _keepDepthOnTop(self):
        if not self._battleMode or self._flash is None:
            return
        self._depthTicks += 1
        try:
            self._flash.forceTopDepth()
        except Exception:
            pass
        if self._depthTicks < 12:
            BigWorld.callback(1.0, self._keepDepthOnTop)

    def _installSuppressionSafe(self):
        try:
            from .suppress import installSuppression, setFeed
            from .hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FlyingDamage] installSuppression failed', exc_info=True)

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

    def showDamageAt(self, x, y, damage, colorRGB, fontSize, alpha, risePixels=55.0, lifeTime=1.6):
        try:
            nx, ny, sw, sh = _norm_xy(x, y)
            riseNorm = max(0.01, min(0.20, float(risePixels) / sh))
            qid = _queue_record('N|%s|%s|%d|%d|%d|%s|%s|%s' % (_fmt_float(nx), _fmt_float(ny), int(damage), int(colorRGB), int(fontSize), _fmt_float(alpha), _fmt_float(riseNorm), _fmt_float(lifeTime)))
            logger.info('[FlyingDamage] queued screen ACK id=%s d=%s norm=(%.4f,%.4f)', qid, int(damage), nx, ny)
        except Exception:
            logger.error('[FlyingDamage] queue screen failed', exc_info=True)

    def showDamageWorld(self, wx, wy, wz, fallbackX, fallbackY, damage, colorRGB, fontSize, alpha, riseMeters=1.35, lifeTime=1.6, vehicleID=None):
        try:
            nx, ny, sw, sh = _norm_xy(fallbackX, fallbackY)
            if vehicleID is not None:
                qid = _queue_record('V|%d|%s|%s|%d|%d|%d|%s|%s|%s' % (int(vehicleID), _fmt_float(nx), _fmt_float(ny), int(damage), int(colorRGB), int(fontSize), _fmt_float(alpha), _fmt_float(riseMeters), _fmt_float(lifeTime)))
                if _pushLog[0] < 120:
                    _pushLog[0] += 1
                    logger.info('[FlyingDamage] queued vehicle ACK id=%s d=%s vid=%s norm=(%.4f,%.4f) queue=%s', qid, int(damage), int(vehicleID), nx, ny, len(_damageQueue))
            else:
                qid = _queue_record('W|%s|%s|%s|%s|%s|%d|%d|%d|%s|%s|%s' % (_fmt_float(wx), _fmt_float(wy), _fmt_float(wz), _fmt_float(nx), _fmt_float(ny), int(damage), int(colorRGB), int(fontSize), _fmt_float(alpha), _fmt_float(riseMeters), _fmt_float(lifeTime)))
                logger.info('[FlyingDamage] queued world ACK id=%s d=%s norm=(%.4f,%.4f)', qid, int(damage), nx, ny)
        except Exception:
            logger.error('[FlyingDamage] queue vehicle failed', exc_info=True)

    def showDamage(self, x, y, damage, colorRGB, fontSize, alpha):
        self.showDamageAt(x, y, damage, colorRGB, fontSize, alpha)


g_controller = Controller()
