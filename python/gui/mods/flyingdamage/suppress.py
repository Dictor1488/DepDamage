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
_logInvoke = [0]


def _loadDamageEventIds():
    # Intentionally empty: suppressing by feedback eventID also breaks HP bars.
    # We instead suppress precisely at the marker-invoke level (damage command).
    return set()


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

    # Also intercept the marker invocation that renders the damage text.
    for invName in ('_invokeMarker', 'invokeMarker'):
        if hasattr(cls, invName):
            def _makeInvHook(name):
                def _invHook(base, self, *args, **kwargs):
                    if _logInvoke[0] < 40:
                        _logInvoke[0] += 1
                        logger.info('[FlyingDamage] %s args=%s', name, repr(args)[:160])
                    # Suppress marker calls that show damage text.
                    if g_config.hideStandard and len(args) >= 2:
                        cmd = args[1]
                        if isinstance(cmd, basestring) and 'amage' in cmd:
                            return None
                    return base(self, *args, **kwargs)
                return _invHook
            override(cls, invName, _makeInvHook(invName))
            logger.info('[FlyingDamage] hooked %s for damage-command filter', invName)

    logger.info('[FlyingDamage] standard damage suppression installed '
                '(onVehicleFeedbackReceived filter)')


def dumpDamageControllers():
    """Diagnostic: find controllers that might draw standard floating damage."""
    try:
        import BigWorld
        player = BigWorld.player()
        sp = getattr(player, 'guiSessionProvider', None)
        if sp is None:
            logger.warning('[FlyingDamage] no guiSessionProvider')
            return
        shared = getattr(sp, 'shared', None)
        dynamic = getattr(sp, 'dynamic', None)
        logger.info('[FlyingDamage] shared ctrls: %s',
                    [a for a in dir(shared) if not a.startswith('_')] if shared else None)
        # feedback controller
        fb = getattr(sp, 'feedback', None) or (getattr(shared, 'feedback', None) if shared else None)
        if fb is not None:
            logger.info('[FlyingDamage] feedback ctrl type: %s methods: %s',
                        type(fb).__name__,
                        [m for m in dir(fb) if 'amage' in m.lower() or 'marker' in m.lower()])
    except Exception:
        logger.info('[FlyingDamage] dumpDamageControllers failed', exc_info=True)
