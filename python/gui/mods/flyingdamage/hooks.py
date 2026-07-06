# -*- coding: utf-8 -*-
# hooks.py  --  Python 2.7
# Damage from onHealthChanged (old-new). Trigger showDamageFromShot.
# World->screen via view-projection matrix.
# Accumulates damage per vehicle over a short window so simultaneous shells
# (e.g. double-barrel 400+400) merge into ONE number (800), like XVM.

import logging

import BigWorld
import GUI
import Math

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_ANCHOR_UP = 4.5   # meters above tank origin (above the turret)
_MERGE_WINDOW = 0.09   # seconds; damage within this window merges into one number
_ctrlRef = [None]
_pending = {}          # vehicleID -> accumulated damage
_callbacks = {}        # vehicleID -> pending callback id


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


_lastAttacker = {}   # vehicleID -> attackerID


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

    # attackerID is typically the 3rd int arg. Skip damage dealt by the player.
    if g_config.hideMyDamage and len(ints) >= 3:
        attackerID = ints[2]
        try:
            player = BigWorld.player()
            myID = getattr(player, 'playerVehicleID', None)
            if myID is None:
                myID = getattr(player, 'vehicleID', None)
            if myID is not None and attackerID == myID:
                logger.info('[FlyingDamage] skip my damage dmg=%d (attacker=%d==me)',
                            dmg, attackerID)
                return  # my own damage -> don't show
        except Exception:
            pass

    # Accumulate; schedule a single flush after the merge window.
    _pending[vid] = _pending.get(vid, 0) + dmg
    if vid not in _callbacks:
        _callbacks[vid] = BigWorld.callback(
            _MERGE_WINDOW, lambda: _flush(vid))


_feedPending = {}
_feedCallbacks = {}
_FEED_MERGE = 0.09


def showDamageForVehicle(vid, damage):
    """Called by the suppress hook: accumulate, then project + color + feed SWF."""
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
        if _feedLog[0] < 10:
            _feedLog[0] += 1
            logger.info('[FlyingDamage] feedFlush: ctrl is None (dmg=%d)', damage)
        return
    vehicle = BigWorld.entity(vid)
    if vehicle is None:
        if _feedLog[0] < 10:
            _feedLog[0] += 1
            logger.info('[FlyingDamage] feedFlush: vehicle None vid=%s', vid)
        return
    if not _isVehicleUsable(vehicle):
        if _feedLog[0] < 10:
            _feedLog[0] += 1
            logger.info('[FlyingDamage] feedFlush: vehicle not usable vid=%s', vid)
        return
    isEnemy = _isEnemy(vehicle, vid)
    color = g_config.colorForTeam(isEnemy)
    if _feedLog[0] < 10:
        _feedLog[0] += 1
        logger.info('[FlyingDamage] feedFlush -> showDamage VEHICLE_ANCHORED vid=%s dmg=%d', vid, damage)
    # Pass vehicleID; the SWF pulls the live screen position each frame.
    ctrl.showDamage(vid, damage, color,
                    g_config.fontSize, g_config.opacity / 100.0)


_feedLog = [0]


_projCallLog = [0]


def projectVehicleScreen(vid):
    """Return {'x','y','ok'} screen position for the tank, called each frame."""
    if _projCallLog[0] < 5:
        _projCallLog[0] += 1
        logger.info('[FlyingDamage] py_getScreenPos called vid=%s', vid)
    try:
        vehicle = BigWorld.entity(vid)
        if vehicle is None or not _isVehicleUsable(vehicle):
            return {'x': 0.0, 'y': 0.0, 'ok': False}
        res = _project(vehicle)
        if res is None:
            return {'x': 0.0, 'y': 0.0, 'ok': False}
        sx, sy, visible = res
        if sx is None or sy is None:
            return {'x': 0.0, 'y': 0.0, 'ok': False}
        return {'x': float(sx), 'y': float(sy), 'ok': True}
    except Exception:
        return {'x': 0.0, 'y': 0.0, 'ok': False}


def _flush(vid):
    _callbacks.pop(vid, None)
    damage = _pending.pop(vid, 0)
    if damage <= 0:
        return
    if not g_config.enabled:
        return
    ctrl = _ctrlRef[0]
    if ctrl is None:
        return

    vehicle = BigWorld.entity(vid)
    if vehicle is None:
        return

    # Only show for vehicles that are actually on the scene and alive.
    if not _isVehicleUsable(vehicle):
        return

    res = _project(vehicle)
    if res is None:
        return
    sx, sy, visible = res
    # Show even slightly off-screen hits (clamp), skip only if fully behind camera.
    if sx is None or sy is None:
        return

    isEnemy = _isEnemy(vehicle, vid)
    color = g_config.colorForTeam(isEnemy)

    # Skip if the projected point is far outside the screen (dead/hidden tank).
    try:
        sw, sh = GUI.screenResolution()[:2]
    except Exception:
        sw, sh = 1920, 1080
    if sx < -sw or sx > 2 * sw or sy < -sh or sy > 2 * sh:
        return

    # Always pass vehicleID to the SWF. Older builds sometimes passed screen
    # x/y here, which made the number screen-fixed and not attached to the tank.
    ctrl.showDamage(vid, damage, color,
                    g_config.fontSize, g_config.opacity / 100.0)


def _isVehicleUsable(vehicle):
    """True only if the vehicle is on the scene and alive (avoids stray/hidden)."""
    try:
        if not getattr(vehicle, 'isStarted', False):
            return False
        if hasattr(vehicle, 'isAlive') and not vehicle.isAlive():
            return False
    except Exception:
        return False
    return True


def _isEnemy(vehicle, vid):
    """True if target is on the enemy team, False if ally."""
    try:
        player = BigWorld.player()
        myTeam = getattr(player, 'team', None)
        targetTeam = None
        # Most reliable: vehicle.publicInfo['team'].
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
        return None   # truly behind camera
    cx = v.x / w
    cy = v.y / w
    visible = -1 <= cx <= 1 and -1 <= cy <= 1
    sw, sh = GUI.screenResolution()[:2]
    return ((0.5 + 0.5 * cx) * sw, (0.5 - 0.5 * cy) * sh, visible)
