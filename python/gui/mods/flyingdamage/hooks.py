# -*- coding: utf-8 -*-
# hooks.py  --  Python 2.7
# Damage from health marker hook. Feed Gameface renderer with vehicle id;
# controller projects vehicle to screen pixels and pushes DOM damage numbers.

import logging

import BigWorld
import GUI
import Math

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_ANCHOR_UP = 4.5
_MERGE_WINDOW = 0.09
_ctrlRef = [None]
_pending = {}
_callbacks = {}


def setView(controller):
    _ctrlRef[0] = controller


def resetState():
    _pending.clear()
    for cbid in list(_callbacks.values()):
        try:
            BigWorld.cancelCallback(cbid)
        except Exception:
            pass
    _callbacks.clear()
    for cbid in list(_feedCallbacks.values()):
        try:
            BigWorld.cancelCallback(cbid)
        except Exception:
            pass
    _feedCallbacks.clear()
    _feedPending.clear()
    _lastAttacker.clear()


def installHooks():
    try:
        from Vehicle import Vehicle
    except Exception:
        logger.error('[FlyingDamageGF] cannot import Vehicle', exc_info=True)
        return

    @override(Vehicle, 'onHealthChanged')
    def _onHealthChanged(base, self, *args, **kwargs):
        result = base(self, *args, **kwargs)
        try:
            _recordAttacker(self, args)
        except Exception:
            pass
        return result

    logger.info('[FlyingDamageGF] hooks installed attacker tracking')


_lastAttacker = {}


def _recordAttacker(vehicle, args):
    vid = getattr(vehicle, 'id', None)
    if vid is None:
        return
    ints = []
    for a in args:
        try:
            ints.append(int(a))
        except (TypeError, ValueError):
            pass
    if len(ints) >= 3:
        _lastAttacker[vid] = ints[2]


def isMyDamage(vid):
    try:
        player = BigWorld.player()
        myID = getattr(player, 'playerVehicleID', None)
        if myID is None:
            myID = getattr(player, 'vehicleID', None)
        return myID is not None and _lastAttacker.get(vid) == myID
    except Exception:
        return False


_feedPending = {}
_feedCallbacks = {}
_FEED_MERGE = 0.09
_feedLog = [0]
_projCallLog = [0]


def showDamageForVehicle(vid, damage):
    if not g_config.enabled or damage <= 0:
        return
    if g_config.hideMyDamage and isMyDamage(vid):
        return
    _feedPending[vid] = _feedPending.get(vid, 0) + damage
    if vid not in _feedCallbacks:
        _feedCallbacks[vid] = BigWorld.callback(_FEED_MERGE, lambda: _feedFlush(vid))


def _feedFlush(vid):
    _feedCallbacks.pop(vid, None)
    damage = _feedPending.pop(vid, 0)
    if damage <= 0:
        return
    ctrl = _ctrlRef[0]
    if ctrl is None:
        if _feedLog[0] < 20:
            _feedLog[0] += 1
            logger.info('[FlyingDamageGF] feedFlush: ctrl is None dmg=%d', damage)
        return
    vehicle = BigWorld.entity(vid)
    if vehicle is None:
        if _feedLog[0] < 20:
            _feedLog[0] += 1
            logger.info('[FlyingDamageGF] feedFlush: vehicle None vid=%s', vid)
        return
    if not _isVehicleUsable(vehicle):
        if _feedLog[0] < 20:
            _feedLog[0] += 1
            logger.info('[FlyingDamageGF] feedFlush: vehicle not usable vid=%s', vid)
        return
    isEnemy = _isEnemy(vehicle, vid)
    color = g_config.colorForTeam(isEnemy)
    if _feedLog[0] < 80:
        _feedLog[0] += 1
        logger.info('[FlyingDamageGF] feedFlush -> Gameface showDamage vid=%s dmg=%d', vid, damage)
    ctrl.showDamage(vid, damage, color, g_config.fontSize, g_config.opacity / 100.0)


def projectVehicleScreen(vid):
    try:
        vehicle = BigWorld.entity(vid)
        if vehicle is None or not _isVehicleUsable(vehicle):
            if _projCallLog[0] < 30:
                _projCallLog[0] += 1
                logger.info('[FlyingDamageGF] project vid=%s failed vehicle usable=%s', vid, vehicle is not None)
            return {'x': 0.0, 'y': 0.0, 'ok': False}
        res = _project(vehicle)
        if res is None:
            if _projCallLog[0] < 30:
                _projCallLog[0] += 1
                logger.info('[FlyingDamageGF] project vid=%s failed res=None', vid)
            return {'x': 0.0, 'y': 0.0, 'ok': False}
        sx, sy, visible = res
        if sx is None or sy is None:
            return {'x': 0.0, 'y': 0.0, 'ok': False}
        if _projCallLog[0] < 80:
            _projCallLog[0] += 1
            logger.info('[FlyingDamageGF] project vid=%s xy=(%.1f,%.1f) visible=%s', vid, float(sx), float(sy), visible)
        return {'x': float(sx), 'y': float(sy), 'ok': True}
    except Exception:
        logger.error('[FlyingDamageGF] projectVehicleScreen failed vid=%s', vid, exc_info=True)
        return {'x': 0.0, 'y': 0.0, 'ok': False}


def _isVehicleUsable(vehicle):
    try:
        if not getattr(vehicle, 'isStarted', False):
            return False
        if hasattr(vehicle, 'isAlive') and not vehicle.isAlive():
            return False
    except Exception:
        return False
    return True


def _isEnemy(vehicle, vid):
    try:
        player = BigWorld.player()
        myTeam = getattr(player, 'team', None)
        targetTeam = None
        info = getattr(vehicle, 'publicInfo', None)
        if info is not None:
            try:
                targetTeam = info['team']
            except Exception:
                targetTeam = None
        if targetTeam is None:
            targetTeam = getattr(vehicle, 'team', None)
        if myTeam is not None and targetTeam is not None:
            return targetTeam != myTeam
    except Exception:
        pass
    return True


def _buildVP():
    try:
        proj = BigWorld.projection()
        aspect = BigWorld.getAspectRatio()
        m = Math.Matrix()
        m.perspectiveProjection(proj.fov, aspect, proj.nearPlane, proj.farPlane)
        cam = BigWorld.camera()
        if cam is None:
            return None
        m.preMultiply(cam.matrix)
        return m
    except Exception:
        return None


def _project(vehicle):
    vp = _buildVP()
    if vp is None:
        return None
    try:
        tmp = Math.Matrix()
        tmp.set(vehicle.matrix)
        pos = tmp.translation
    except Exception:
        pos = getattr(vehicle, 'position', None)
        if pos is None:
            return None
    v = Math.Vector4(pos.x, pos.y + _ANCHOR_UP, pos.z, 1.0)
    v = vp.applyV4Point(v)
    w = v.w
    if w <= 0:
        return None
    cx = v.x / w
    cy = v.y / w
    visible = -1 <= cx <= 1 and -1 <= cy <= 1
    sw, sh = GUI.screenResolution()[:2]
    return ((0.5 + 0.5 * cx) * sw, (0.5 - 0.5 * cy) * sh, visible)
