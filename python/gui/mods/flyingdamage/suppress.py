# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Suppress the standard floating damage number over tanks.
# The vehicle-marker plugin receives damage via onVehicleFeedbackReceived and
# forwards it to the marker SWF (which draws the number). We intercept that
# method and drop ONLY the damage-type feedback event, leaving everything else
# (hit direction, crits, etc.) intact.

import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_PLUGIN_MODULE = 'gui.Scaleform.daapi.view.battle.shared.markers2d.plugins'
_PLUGIN_CLASS = 'VehicleMarkerTargetPlugin'

# Feedback event IDs that represent floating damage text over a vehicle.
_DAMAGE_EVENT_IDS = set()
_logFeedback = [0]


def _loadDamageEventIds():
    ids = set()
    try:
        from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID as F
        for name in ('VEHICLE_DAMAGE_RECEIVED', 'VEHICLE_HIT',
                     'VEHICLE_DAMAGE', 'DAMAGE_RECEIVED',
                     'VEHICLE_HEALTH', 'VEHICLE_DEAD'):
            val = getattr(F, name, None)
            if val is not None:
                ids.add(val)
    except Exception:
        logger.info('[FlyingDamage] could not load FEEDBACK_EVENT_ID', exc_info=True)
    return ids


def installSuppression():
    if not g_config.hideStandard:
        logger.info('[FlyingDamage] suppression disabled')
        return

    try:
        mod = __import__(_PLUGIN_MODULE, fromlist=[_PLUGIN_CLASS])
        cls = getattr(mod, _PLUGIN_CLASS, None)
    except Exception:
        logger.error('[FlyingDamage] import plugin failed', exc_info=True)
        return

    if cls is None or not hasattr(cls, 'onVehicleFeedbackReceived'):
        logger.warning('[FlyingDamage] onVehicleFeedbackReceived not found')
        return

    global _DAMAGE_EVENT_IDS
    _DAMAGE_EVENT_IDS = _loadDamageEventIds()
    logger.info('[FlyingDamage] damage feedback ids: %s', list(_DAMAGE_EVENT_IDS))

    @override(cls, 'onVehicleFeedbackReceived')
    def _onFeedback(base, self, *args, **kwargs):
        # Signature varies: (eventID, vehicleID, value) OR (event,). Detect eventID.
        eventID = None
        if len(args) >= 1:
            first = args[0]
            eventID = getattr(first, 'eventType', None)
            if eventID is None:
                eventID = getattr(first, 'eventID', None)
            if eventID is None:
                eventID = first  # assume first positional IS the id
        if _logFeedback[0] < 25:
            _logFeedback[0] += 1
            logger.info('[FlyingDamage] feedback eventID=%s args=%s',
                        repr(eventID), repr(args)[:120])
        if g_config.hideStandard and eventID in _DAMAGE_EVENT_IDS:
            return None
        return base(self, *args, **kwargs)

    logger.info('[FlyingDamage] standard damage suppression installed '
                '(onVehicleFeedbackReceived filter)')
