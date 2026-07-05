# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Standard floating damage is emitted by VehicleMarkerPlugin when it receives a
# damage feedback event. We intercept onVehicleFeedbackReceived on that plugin
# and drop ONLY the damage event (eventID that carries the damage number),
# leaving HP bar, crits, direction, etc. intact.

import sys
import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_installed = [False]
_logN = [0]

# The vehicle-marker plugin class that draws the standard damage number.
_TARGET_CLASS_SUFFIX = 'VehicleMarkerPlugin'
_SKIP_MODULE_FRAGMENTS = ('flyingdamage',)

# Feedback event ID that carries floating damage. Loaded at runtime.
_DAMAGE_IDS = [set()]


def _loadDamageIds():
    ids = set()
    try:
        from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID as F
        for name in ('VEHICLE_DAMAGE_RECEIVED', 'VEHICLE_HIT'):
            v = getattr(F, name, None)
            if v is not None:
                ids.add(v)
    except Exception:
        pass
    # eventID=12 confirmed in logs as the damage-number feedback on this client.
    ids.add(12)
    return ids


def installSuppression():
    if _installed[0]:
        return
    if not g_config.hideStandard:
        logger.info('[FlyingDamage] suppression disabled')
        return
    _installed[0] = True

    _DAMAGE_IDS[0] = _loadDamageIds()
    logger.info('[FlyingDamage] damage feedback ids: %s', list(_DAMAGE_IDS[0]))

    hooked = 0
    for modName, mod in list(sys.modules.items()):
        if mod is None:
            continue
        low = modName.lower()
        if any(f in low for f in _SKIP_MODULE_FRAGMENTS):
            continue
        if 'marker' not in low:
            continue
        for attr in dir(mod):
            if not attr.endswith(_TARGET_CLASS_SUFFIX):
                continue
            cls = getattr(mod, attr, None)
            if not isinstance(cls, type):
                continue
            if 'onVehicleFeedbackReceived' not in cls.__dict__:
                continue
            try:
                override(cls, 'onVehicleFeedbackReceived', _feedbackHook)
                hooked += 1
                logger.info('[FlyingDamage] hooked %s.onVehicleFeedbackReceived (%s)',
                            attr, modName)
            except Exception:
                logger.info('[FlyingDamage] hook fail %s', modName, exc_info=True)

    logger.info('[FlyingDamage] suppression hooks: %d', hooked)


def _feedbackHook(base, self, *args, **kwargs):
    eventID = args[0] if len(args) >= 1 else None
    if _logN[0] < 30:
        _logN[0] += 1
        logger.info('[FlyingDamage] FB eventID=%s args=%s', repr(eventID), repr(args)[:110])
    if g_config.hideStandard and eventID in _DAMAGE_IDS[0]:
        return None   # drop standard damage number
    return base(self, *args, **kwargs)
