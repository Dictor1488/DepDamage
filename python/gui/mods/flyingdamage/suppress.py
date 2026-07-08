# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Hook _updateHealthMarker only for debug/tracking. Damage rendering is left to
# the native VehicleMarker implementation, so original addDamageLabel() runs.

import sys
import logging

import BigWorld

from .utils import override

logger = logging.getLogger(__name__)

_installed = [False]
_logN = [0]
_DEBUG_LOG_LIMIT = 500
_SKIP = ('flyingdamage',)
_TARGET = '_updateHealthMarker'

_lastHealth = {}          # vehicleID -> last known health
_feedCallback = [None]    # kept for compatibility; native path does not use it


def setFeed(fn):
    # Native VehicleMarker path: do not feed damage into FlyingDamageApp overlay.
    _feedCallback[0] = None


def resetState():
    _lastHealth.clear()
    _logN[0] = 0


def installSuppression():
    if _installed[0]:
        return
    for modName in (
        'gui.Scaleform.daapi.view.battle.shared.markers2d.plugins',
        'gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins',
    ):
        try:
            __import__(modName)
        except Exception:
            pass

    hooked = 0
    done = set()
    for modName, mod in list(sys.modules.items()):
        if mod is None:
            continue
        low = modName.lower()
        if any(s in low for s in _SKIP) or 'marker' not in low:
            continue
        for attr in dir(mod):
            cls = getattr(mod, attr, None)
            if not isinstance(cls, type):
                continue
            if 'VehicleMarkerPlugin' not in [c.__name__ for c in cls.__mro__]:
                continue
            if _TARGET not in cls.__dict__:
                continue
            key = (cls.__module__, cls.__name__)
            if key in done:
                continue
            done.add(key)
            try:
                override(cls, _TARGET, _updateHealthMarkerHook)
                hooked += 1
                logger.info('[FlyingDamage] hooked %s.%s native VehicleMarker path (%s)', attr, _TARGET, modName)
            except Exception:
                logger.info('[FlyingDamage] hook fail %s', attr, exc_info=True)
            if 'start' in cls.__dict__:
                try:
                    override(cls, 'start', _pluginStartHook)
                    logger.info('[FlyingDamage] hooked %s.start', attr)
                except Exception:
                    pass

    logger.info('[FlyingDamage] _updateHealthMarker hooks: %d debugLimit=%d nativeAddDamageLabel=True', hooked, _DEBUG_LOG_LIMIT)
    if hooked > 0:
        _installed[0] = True


def _pluginStartHook(base, self, *args, **kwargs):
    result = base(self, *args, **kwargs)
    try:
        from . import g_controller
        g_controller.onMarkerPluginStart()
    except Exception:
        logger.error('[FlyingDamage] onMarkerPluginStart failed', exc_info=True)
    return result


def _updateHealthMarkerHook(base, self, *args, **kwargs):
    # Observed signature: (vehicleID, index, newHealth, aInfo, attackReason, extId)
    # Important: always return base(...). That keeps WG's original
    # VehicleMarker._updateHealthMarker/addDamageLabel logic alive and bound to
    # the real tank marker. We only log/debug here.
    try:
        if len(args) >= 3:
            vehID = args[0]
            index = args[1]
            newHealth = args[2]
            aInfo = args[3] if len(args) >= 4 else None
            reason = args[4] if len(args) >= 5 else None
            extId = args[5] if len(args) >= 6 else None
            damageType = _reasonToDamageType(reason, args, kwargs)

            if vehID in _lastHealth:
                prev = _lastHealth[vehID]
            else:
                prev = _maxHealth(vehID, newHealth)

            damage = prev - newHealth if isinstance(newHealth, int) else 0
            if damage < 0:
                damage = 0
            _lastHealth[vehID] = newHealth

            if _logN[0] < _DEBUG_LOG_LIMIT:
                _logN[0] += 1
                logger.info('[FD_DEBUG_HM_NATIVE] n=%d veh=%s index=%s prev=%s new=%s dmg=%s dtype=%s',
                            _logN[0], vehID, index, prev, newHealth, damage, damageType)
                logger.info('[FD_DEBUG_HM_NATIVE] reason type=%s repr=%s int=%s text=%s',
                            _safeType(reason), _safeRepr(reason, 240), _safeInt(reason), _safeText(reason, 240))
                logger.info('[FD_DEBUG_HM_NATIVE] aInfo type=%s repr=%s attrs=%s',
                            _safeType(aInfo), _safeRepr(aInfo, 320), _dumpInterestingAttrs(aInfo))
                logger.info('[FD_DEBUG_HM_NATIVE] extId type=%s repr=%s int=%s text=%s',
                            _safeType(extId), _safeRepr(extId, 240), _safeInt(extId), _safeText(extId, 240))
                logger.info('[FD_DEBUG_HM_NATIVE] argsFull=%s kwargs=%s',
                            _compactArgs(args, 12, 220), _compactKwargs(kwargs))
    except Exception:
        logger.error('[FlyingDamage] HM native hook debug error', exc_info=True)

    return base(self, *args, **kwargs)


def _reasonToDamageType(reason, args=None, kwargs=None):
    try:
        text = ''
        if reason is not None:
            text = str(reason).lower()
        if 'ricochet' in text:
            return 'ricochet'
        if 'block' in text and 'crit' in text:
            return 'blocked_crit'
        if 'block' in text or 'armor' in text or 'absorbed' in text:
            return 'blocked'
        if 'fire' in text or 'burn' in text:
            return 'fire'
        if 'ram' in text:
            return 'ramming'
        if 'collision' in text:
            return 'world_collision'
        if 'death_zone' in text or 'deathzone' in text:
            return 'death_zone'
        if 'drown' in text or 'water' in text:
            return 'drowning'
        if 'explosion' in text or 'ammo' in text or 'blow' in text:
            return 'explosion'

        rid = _safeInt(reason)
        if rid is not None:
            if rid in (2, 16):
                return 'fire'
            if rid in (3, 17):
                return 'ramming'
            if rid in (4, 18):
                return 'world_collision'
            if rid in (5, 19):
                return 'death_zone'
            if rid in (6, 20):
                return 'drowning'
            if rid in (7, 21):
                return 'explosion'
    except Exception:
        pass
    return 'shot'


def _safeType(v):
    try:
        return type(v).__name__
    except Exception:
        return '<type>'


def _safeInt(v):
    try:
        return int(v)
    except Exception:
        return None


def _safeText(v, limit=200):
    try:
        s = str(v)
    except Exception:
        return '<str-error>'
    if len(s) > limit:
        s = s[:limit - 3] + '...'
    return s


def _safeRepr(v, limit=200):
    try:
        s = repr(v)
    except Exception:
        return '<repr-error>'
    if len(s) > limit:
        s = s[:limit - 3] + '...'
    return s


def _compactArgs(args, maxCount=8, limit=120):
    try:
        out = []
        for i, a in enumerate(args[:maxCount]):
            out.append('%d:%s:%s' % (i, _safeType(a), _safeRepr(a, limit)))
        if len(args) > maxCount:
            out.append('... total=%d' % len(args))
        return '(' + ', '.join(out) + ')'
    except Exception:
        return '<args>'


def _compactKwargs(kwargs):
    try:
        if not kwargs:
            return '{}'
        out = []
        for k, v in kwargs.items():
            out.append('%s:%s:%s' % (k, _safeType(v), _safeRepr(v, 180)))
        return '{' + ', '.join(out) + '}'
    except Exception:
        return '<kwargs>'


def _dumpInterestingAttrs(obj):
    if obj is None:
        return '{}'
    names = ('attackerID', 'attackerId', 'attacker', 'attackReason', 'reason', 'damageType', 'attackReasonID', 'hitFlags', 'flags', 'isCritical', 'isBlocked', 'isRicochet', 'isFire', 'isExplosion')
    out = []
    for name in names:
        try:
            if hasattr(obj, name):
                out.append('%s=%s' % (name, _safeRepr(getattr(obj, name), 120)))
        except Exception:
            pass
    try:
        if isinstance(obj, dict):
            for k in obj.keys():
                if len(out) >= 20:
                    break
                out.append('%s=%s' % (_safeRepr(k, 60), _safeRepr(obj.get(k), 120)))
    except Exception:
        pass
    return '{' + ', '.join(out) + '}'


def _maxHealth(vehID, fallback):
    try:
        vehicle = BigWorld.entity(vehID)
        if vehicle is not None:
            desc = getattr(vehicle, 'typeDescriptor', None)
            if desc is not None:
                maxH = getattr(desc, 'maxHealth', None)
                if maxH:
                    return int(maxH)
    except Exception:
        pass
    return int(fallback)
