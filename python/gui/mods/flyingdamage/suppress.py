# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Suppress standard floating damage by intercepting onVehicleFeedbackReceived on
# ALL vehicle-marker plugin classes (target marker AND the base marker that
# shows allies' damage), dropping the damage-number event only.

import sys
import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_installed = [False]
_logN = [0]

# eventID carrying the floating damage number (12 confirmed on this client).
_DAMAGE_IDS = set([12])

# Any class whose name ends with this and defines/inherits the feedback method.
_CLASS_SUFFIX = 'VehicleMarkerPlugin'
_SKIP = ('flyingdamage',)


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
    patched_classes = set()

    for modName, mod in list(sys.modules.items()):
        if mod is None:
            continue
        low = modName.lower()
        if any(s in low for s in _SKIP):
            continue
        if 'marker' not in low:
            continue
        for attr in dir(mod):
            if not attr.endswith(_CLASS_SUFFIX):
                continue
            cls = getattr(mod, attr, None)
            if not isinstance(cls, type):
                continue
            # Only patch a class that DEFINES the method itself (avoid patching
            # a subclass that just inherits it -> double wrapping).
            if 'onVehicleFeedbackReceived' not in cls.__dict__:
                continue
            key = (cls.__module__, cls.__name__)
            if key in patched_classes:
                continue
            patched_classes.add(key)
            try:
                override(cls, 'onVehicleFeedbackReceived', _feedbackHook)
                hooked += 1
                logger.info('[FlyingDamage] hooked %s (%s)', attr, modName)
            except Exception:
                logger.info('[FlyingDamage] hook fail %s', modName, exc_info=True)

    logger.info('[FlyingDamage] suppression hooks: %d', hooked)
    if hooked == 0:
        # Fallback: import the canonical module and hook the base class directly.
        _fallbackHook()


def _fallbackHook():
    try:
        m = __import__(
            'gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins',
            fromlist=['VehicleMarkerPlugin'])
        cls = getattr(m, 'VehicleMarkerPlugin', None)
        if cls and hasattr(cls, 'onVehicleFeedbackReceived'):
            override(cls, 'onVehicleFeedbackReceived', _feedbackHook)
            logger.info('[FlyingDamage] fallback hooked VehicleMarkerPlugin')
    except Exception:
        logger.info('[FlyingDamage] fallback hook failed', exc_info=True)


def _feedbackHook(base, self, *args, **kwargs):
    eventID = args[0] if len(args) >= 1 else None
    if _logN[0] < 40:
        _logN[0] += 1
        logger.info('[FlyingDamage] FB eventID=%s cls=%s args=%s',
                    repr(eventID), type(self).__name__, repr(args)[:100])
    if g_config.hideStandard and eventID in _DAMAGE_IDS:
        return None
    return base(self, *args, **kwargs)
