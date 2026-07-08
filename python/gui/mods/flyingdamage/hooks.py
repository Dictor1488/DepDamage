# -*- coding: utf-8 -*-
# hooks.py  --  Python 2.7
# Damage from health marker hook. Feed AS3 renderer with vehicle id.

import logging

import BigWorld
import GUI
import Math

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_ANCHOR_UP = 4.5
_MARKER_Y_OFFSET = 0.0
_PLAYER_DAMAGE_COLOR = 0xFFDC3C
_ctrlRef = [None]
_pending = {}
_callbacks = {}
_vehicleMarkerClass = [None]


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
    _lastAttacker.clear()
    _feedLog[0] = 0


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

    try:
        from gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins import VehicleMarkerPlugin

        @override(VehicleMarkerPlugin, 'start')
        def _markerStart(base, self):
            result = base(self)
            try:
                _vehicleMarkerClass[0] = getattr(self, '_clazz', None)
                logger.info('[FlyingDamageGF] VehicleMarkerPlugin.start captured clazz=%s', _vehicleMarkerClass[0] is not None)
            except Exception:
                logger.error('[FlyingDamageGF] capture marker clazz failed', exc_info=True)
            return result

        @override(VehicleMarkerPlugin, 'stop')
        def _markerStop(base, self):
            result = base(self)
            try:
                _vehicleMarkerClass[0] = None
            except Exception:
                pass
            return result
    except Exception:
        logger.error('[FlyingDamageGF] VehicleMarkerPlugin hook failed', exc_info=True)

    logger.info('[FlyingDamageGF] hooks installed attacker tracking + marker provider')


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
        if _feedLog[0] < 300:
            logger.info('[FD_DEBUG_ATTACKER] vid=%s attacker=%s ints=%s rawArgs=%s', vid, ints[2], ints, _compactArgs(args, 10, 160))


def isMyDamage(vid):
    try:
        player = BigWorld.player()
        myID = getattr(player, 'playerVehicleID', None)
        if myID is None:
            myID = getattr(player, 'vehicleID', None)
        return myID is not None and _lastAttacker.get(vid) == myID
    except Exception:
        return False


_feedLog = [0]
_projCallLog = [0]
_LABELED_TYPES = ('blocked', 'blocked_crit', 'ricochet')


def showDamageForVehicle(vid, damage, damageType='shot'):
    # Original VehicleMarker.addDamageLabel is event-based: every incoming marker
    # damage event creates its own animated label. Do not merge events by vehicle;
    # merging hides fast multi-hit damage and makes debugging offsets misleading.
    if not g_config.enabled:
        return
    damageType = damageType or 'shot'
    if damage <= 0 and damageType not in _LABELED_TYPES:
        return

    ctrl = _ctrlRef[0]
    if ctrl is None:
        if _feedLog[0] < 300:
            _feedLog[0] += 1
            logger.info('[FD_DEBUG_FEED_OUT] ctrl=None vid=%s dmg=%s type=%s', vid, damage, damageType)
        return

    vehicle = BigWorld.entity(vid)
    if vehicle is None:
        if _feedLog[0] < 300:
            _feedLog[0] += 1
            logger.info('[FD_DEBUG_FEED_OUT] vehicle=None vid=%s dmg=%s type=%s', vid, damage, damageType)
        return
    if not _isVehicleUsable(vehicle):
        if _feedLog[0] < 300:
            _feedLog[0] += 1
            logger.info('[FD_DEBUG_FEED_OUT] vehicleNotUsable vid=%s dmg=%s type=%s', vid, damage, damageType)
        return

    myDamage = isMyDamage(vid)
    isEnemy = _isEnemy(vehicle, vid)
    color = _PLAYER_DAMAGE_COLOR if myDamage else g_config.colorForTeam(isEnemy)
    if _feedLog[0] < 300:
        _feedLog[0] += 1
        logger.info('[FD_DEBUG_FEED_OUT] immediate vid=%s dmg=%s type=%s mine=%s enemy=%s attacker=%s color=0x%06X', vid, damage, damageType, myDamage, isEnemy, _lastAttacker.get(vid), color)
    try:
        ctrl.showDamage(vid, damage, color, g_config.fontSize, g_config.opacity / 100.0, damageType)
    except TypeError:
        ctrl.showDamage(vid, damage, color, g_config.fontSize, g_config.opacity / 100.0)


def _compactArgs(args, maxCount=8, limit=120):
    try:
        out = []
        for i, a in enumerate(args[:maxCount]):
            s = repr(a)
            if len(s) > limit:
                s = s[:limit - 3] + '...'
            out.append('%d:%s:%s' % (i, type(a).__name__, s))
        if len(args) > maxCount:
            out.append('... total=%d' % len(args))
        return '(' + ', '.join(out) + ')'
    except Exception:
        return '<args>'


def projectVehicleScreen(vid, quiet=False):
    try:
        vehicle = BigWorld.entity(vid)
        if vehicle is None or not _isVehicleUsable(vehicle):
            if not quiet and _projCallLog[0] < 30:
                _projCallLog[0] += 1
                logger.info('[FlyingDamageGF] project vid=%s failed vehicle usable=%s', vid, vehicle is not None)
            return {'x': 0.0, 'y': 0.0, 'ok': False}
        res = _project(vehicle)
        if res is None:
            if not quiet and _projCallLog[0] < 30:
                _projCallLog[0] += 1
                logger.info('[FlyingDamageGF] project vid=%s failed res=None', vid)
            return {'x': 0.0, 'y': 0.0, 'ok': False}
        sx, sy, visible, source = res
        if sx is None or sy is None:
            return {'x': 0.0, 'y': 0.0, 'ok': False}
        if not quiet and _projCallLog[0] < 100:
            _projCallLog[0] += 1
            logger.info('[FlyingDamageGF] project vid=%s xy=(%.1f,%.1f) visible=%s source=%s markerYOffset=%.1f', vid, float(sx), float(sy), visible, source, _MARKER_Y_OFFSET)
        if not visible:
            return {'x': float(sx), 'y': float(sy), 'ok': False}
        return {'x': float(sx), 'y': float(sy), 'ok': True}
    except Exception:
        if not quiet:
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


def _markerWorldPos(vehicle):
    clazz = _vehicleMarkerClass[0]
    if clazz is None:
        return None
    try:
        provider = clazz.fetchMatrixProvider(vehicle)
        if provider is None:
            return None
        tmp = Math.Matrix()
        tmp.set(provider)
        return tmp.translation
    except Exception:
        return None


def _fallbackWorldPos(vehicle):
    try:
        tmp = Math.Matrix()
        tmp.set(vehicle.matrix)
        pos = tmp.translation
        return Math.Vector3(pos.x, pos.y + _ANCHOR_UP, pos.z)
    except Exception:
        pos = getattr(vehicle, 'position', None)
        if pos is None:
            return None
        return Math.Vector3(pos.x, pos.y + _ANCHOR_UP, pos.z)


def _project(vehicle):
    vp = _buildVP()
    if vp is None:
        return None

    source = 'marker'
    pos = _markerWorldPos(vehicle)
    if pos is None:
        source = 'fallback'
        pos = _fallbackWorldPos(vehicle)
        if pos is None:
            return None

    v = Math.Vector4(pos.x, pos.y, pos.z, 1.0)
    v = vp.applyV4Point(v)
    w = v.w
    if w <= 0:
        return None
    cx = v.x / w
    cy = v.y / w
    visible = -1 <= cx <= 1 and -1 <= cy <= 1
    sw, sh = GUI.screenResolution()[:2]
    x = (0.5 + 0.5 * cx) * sw
    y = (0.5 - 0.5 * cy) * sh
    if source == 'marker':
        y += _MARKER_Y_OFFSET
    return (x, y, visible, source)
