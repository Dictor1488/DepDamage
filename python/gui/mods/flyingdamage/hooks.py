# -*- coding: utf-8 -*-
# hooks.py  --  Python 2.7
# Damage source + projection helpers for FlyingDamage.
#
# Two display modes are supported:
#   1) screen_fixed: capture screen x/y once at hit time.
#   2) world_anchor: capture the tank/world point once at hit time and let the
#      SWF re-project that fixed world point every frame while it rises. This is
#      the closest standalone behaviour to XVM-style marker damage without
#      depending on XVM internals: the number belongs to a world point over the
#      target, not to a free overlay or to the moving vehicle object.

import logging

import BigWorld
import GUI
import Math

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_ANCHOR_UP = 4.5        # meters above tank origin, near turret/marker height
_MERGE_WINDOW = 0.09    # seconds; merge near-simultaneous damage into one value
_ctrlRef = [None]
_pending = {}           # vehicleID -> accumulated damage from onHealthChanged
_callbacks = {}         # vehicleID -> pending callback id

_feedPending = {}       # vehicleID -> accumulated damage from marker hook
_feedCallbacks = {}
_FEED_MERGE = 0.09
_feedLog = [0]
_projCallLog = [0]
_lastAttacker = {}      # vehicleID -> attackerID


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
        logger.error('[FlyingDamage] cannot import Vehicle', exc_info=True)
        return

    @override(Vehicle, 'onHealthChanged')
    def _onHealthChanged(base, self, *args, **kwargs):
        result = base(self, *args, **kwargs)
        try:
            _recordAttacker(self, args)
        except Exception:
            pass
        return result

    logger.info('[FlyingDamage] hooks installed (attacker tracking)')


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
    # args: (newHealth, oldHealth, attackerID, ...)
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


def _capture(vehicle, args):
    """Legacy onHealthChanged capture path. Suppression hook is usually used."""
    vid = getattr(vehicle, 'id', None)
    if vid is None:
        return
    ints = []
    for a in args:
        try:
            ints.append(int(a))
        except (TypeError, ValueError):
            pass
    if len(ints) < 2:
        return
    newH, oldH = ints[0], ints[1]
    if newH < 0:
        newH = 0
    dmg = oldH - newH
    if dmg <= 0:
        return

    if g_config.hideMyDamage and len(ints) >= 3:
        attackerID = ints[2]
        try:
            player = BigWorld.player()
            myID = getattr(player, 'playerVehicleID', None)
            if myID is None:
                myID = getattr(player, 'vehicleID', None)
            if myID is not None and attackerID == myID:
                return
        except Exception:
            pass

    _pending[vid] = _pending.get(vid, 0) + dmg
    if vid not in _callbacks:
        _callbacks[vid] = BigWorld.callback(_MERGE_WINDOW, lambda: _flush(vid))


def showDamageForVehicle(vid, damage):
    """Called by suppress.py: accumulate, then resolve relation + anchor + feed SWF."""
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
    _showResolvedDamage(vid, damage, 'feedFlush')


def _flush(vid):
    _callbacks.pop(vid, None)
    damage = _pending.pop(vid, 0)
    if damage <= 0 or not g_config.enabled:
        return
    _showResolvedDamage(vid, damage, 'healthFlush')


def _showResolvedDamage(vid, damage, source):
    ctrl = _ctrlRef[0]
    if ctrl is None:
        _limitedLog('[FlyingDamage] %s: ctrl is None (dmg=%d)', source, damage)
        return

    vehicle = BigWorld.entity(vid)
    if vehicle is None:
        _limitedLog('[FlyingDamage] %s: vehicle None vid=%s', source, vid)
        return
    if not _isVehicleUsable(vehicle):
        _limitedLog('[FlyingDamage] %s: vehicle not usable vid=%s', source, vid)
        return

    anchor = _vehicleAnchor(vehicle)
    if anchor is None:
        _limitedLog('[FlyingDamage] %s: anchor failed vid=%s', source, vid)
        return

    sx, sy, visible = _projectPoint(anchor.x, anchor.y, anchor.z)
    if sx is None or sy is None:
        return
    if _isFarOutside(sx, sy):
        return

    isEnemy = _isEnemy(vehicle, vid)
    color = g_config.colorForTeam(isEnemy)

    if _feedLog[0] < 10:
        _feedLog[0] += 1
        logger.info('[FlyingDamage] %s -> showDamage vid=%s dmg=%d mode=%s screen=(%.1f,%.1f) world=(%.2f,%.2f,%.2f)',
                    source, vid, damage, g_config.anchorMode, sx, sy,
                    anchor.x, anchor.y, anchor.z)

    if g_config.anchorMode == 'world_anchor':
        ctrl.showDamageWorld(anchor.x, anchor.y, anchor.z, sx, sy, damage, color,
                             g_config.fontSize, g_config.opacity / 100.0,
                             g_config.riseMeters, g_config.lifeTime)
    else:
        ctrl.showDamageAt(sx, sy, damage, color,
                          g_config.fontSize, g_config.opacity / 100.0,
                          g_config.risePixels, g_config.lifeTime)


def _limitedLog(fmt, *args):
    if _feedLog[0] < 10:
        _feedLog[0] += 1
        logger.info(fmt, *args)


def _isFarOutside(sx, sy):
    try:
        sw, sh = GUI.screenResolution()[:2]
    except Exception:
        sw, sh = 1920, 1080
    return sx < -sw or sx > 2 * sw or sy < -sh or sy > 2 * sh


def _isVehicleUsable(vehicle):
    """True only if the vehicle is on the scene and alive enough for a marker."""
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


def _vehicleAnchor(vehicle):
    """Capture a fixed world point above the vehicle at damage time."""
    try:
        tmp = Math.Matrix()
        tmp.set(vehicle.matrix)
        pos = tmp.translation
    except Exception:
        pos = getattr(vehicle, 'position', None)
        if pos is None:
            return None
    return Math.Vector3(pos.x, pos.y + _ANCHOR_UP, pos.z)


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


def _projectPoint(x, y, z):
    vp = _buildVP()
    if vp is None:
        return (None, None, False)
    try:
        v = Math.Vector4(float(x), float(y), float(z), 1.0)
        v = vp.applyV4Point(v)
        w = v.w
        if w <= 0:
            return (None, None, False)  # behind camera
        cx = v.x / w
        cy = v.y / w
        visible = -1 <= cx <= 1 and -1 <= cy <= 1
        sw, sh = GUI.screenResolution()[:2]
        return ((0.5 + 0.5 * cx) * sw, (0.5 - 0.5 * cy) * sh, visible)
    except Exception:
        return (None, None, False)


def _project(vehicle):
    anchor = _vehicleAnchor(vehicle)
    if anchor is None:
        return None
    sx, sy, visible = _projectPoint(anchor.x, anchor.y, anchor.z)
    if sx is None or sy is None:
        return None
    return (sx, sy, visible)


def projectVehicleScreen(vid):
    """Legacy callback kept for compatibility."""
    if _projCallLog[0] < 5:
        _projCallLog[0] += 1
        logger.info('[FlyingDamage] py_getScreenPos called vid=%s', vid)
    try:
        vehicle = BigWorld.entity(int(vid))
        if vehicle is None or not _isVehicleUsable(vehicle):
            return {'x': 0.0, 'y': 0.0, 'ok': False}
        res = _project(vehicle)
        if res is None:
            return {'x': 0.0, 'y': 0.0, 'ok': False}
        sx, sy, visible = res
        return {'x': float(sx), 'y': float(sy), 'ok': sx is not None and sy is not None}
    except Exception:
        return {'x': 0.0, 'y': 0.0, 'ok': False}


def projectWorldPoint(x, y, z):
    """SWF callback: project a fixed world point to current screen coordinates."""
    try:
        sx, sy, visible = _projectPoint(float(x), float(y), float(z))
        if sx is None or sy is None or _isFarOutside(sx, sy):
            return {'x': 0.0, 'y': 0.0, 'ok': False}
        return {'x': float(sx), 'y': float(sy), 'ok': True, 'visible': bool(visible)}
    except Exception:
        return {'x': 0.0, 'y': 0.0, 'ok': False}
