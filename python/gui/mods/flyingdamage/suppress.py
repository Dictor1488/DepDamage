# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Suppress standard floating damage. Directly import the marker-plugin module
# and hook onVehicleFeedbackReceived on BOTH the base plugin (allies' damage)
# and the target plugin (my damage). Drop only the damage-number event.

import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_installed = [False]
_logN = [0]
_DAMAGE_IDS = set([12])

# Modules that define the vehicle marker plugins (import directly; scanning
# sys.modules at init is unreliable because they may not be loaded yet).
_MODULES = [
    'gui.Scaleform.daapi.view.battle.shared.markers2d.plugins',
    'gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins',
]
_CLASSES = ['VehicleMarkerPlugin', 'VehicleMarkerTargetPlugin']


def installSuppression():
    if _installed[0]:
        return
    if not g_config.hideStandard:
        return
    _installed[0] = True

    try:
        from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID as F
        v = getattr(F, 'VEHICLE_DAMAGE_RECEIVED', None)
        if v is not None:
            _DAMAGE_IDS.add(v)
    except Exception:
        pass
    logger.info('[FlyingDamage] damage ids: %s', list(_DAMAGE_IDS))

    hooked = 0
    done = set()
    for modName in _MODULES:
        try:
            mod = __import__(modName, fromlist=_CLASSES)
        except Exception:
            logger.info('[FlyingDamage] import %s failed', modName)
            continue
        for clsName in _CLASSES:
            cls = getattr(mod, clsName, None)
            if not isinstance(cls, type):
                continue
            # Hook only if this class DEFINES the method (not inherited).
            if 'onVehicleFeedbackReceived' not in cls.__dict__:
                continue
            key = (cls.__module__, cls.__name__)
            if key in done:
                continue
            done.add(key)
            try:
                override(cls, 'onVehicleFeedbackReceived', _feedbackHook)
                hooked += 1
                logger.info('[FlyingDamage] hooked %s.%s', modName, clsName)
            except Exception:
                logger.info('[FlyingDamage] hook fail %s.%s', modName, clsName,
                            exc_info=True)

    logger.info('[FlyingDamage] suppression hooks: %d', hooked)
    if hooked == 0:
        # Nothing hooked yet (modules not loaded at init) -> allow a later retry.
        _installed[0] = False


def _feedbackHook(base, self, *args, **kwargs):
    eventID = args[0] if len(args) >= 1 else None
    if _logN[0] < 40:
        _logN[0] += 1
        logger.info('[FlyingDamage] FB eventID=%s cls=%s args=%s',
                    repr(eventID), type(self).__name__, repr(args)[:100])
    if g_config.hideStandard and eventID in _DAMAGE_IDS:
        return None
    return base(self, *args, **kwargs)
