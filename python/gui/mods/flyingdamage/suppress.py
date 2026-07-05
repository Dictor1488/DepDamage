# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Suppress standard floating damage by intercepting onVehicleFeedbackReceived
# on VehicleMarkerTargetPlugin (this hook fired reliably in earlier logs) and
# dropping the damage-number event, while leaving HP/crits/direction intact.

import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_installed = [False]
_logN = [0]

_PLUGIN_MODULE = 'gui.Scaleform.daapi.view.battle.shared.markers2d.plugins'
_PLUGIN_CLASSES = ['VehicleMarkerTargetPlugin', 'VehicleMarkerPlugin']

# eventID that carries the floating damage number. 12 confirmed in logs.
_DAMAGE_IDS = set([12])


def installSuppression():
    if _installed[0]:
        return
    if not g_config.hideStandard:
        logger.info('[FlyingDamage] suppression disabled')
        return
    _installed[0] = True

    # Refine damage ids from constants if available (keep 12 as confirmed).
    try:
        from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID as F
        for name in ('VEHICLE_DAMAGE_RECEIVED',):
            v = getattr(F, name, None)
            if v is not None:
                _DAMAGE_IDS.add(v)
    except Exception:
        pass
    logger.info('[FlyingDamage] damage ids: %s', list(_DAMAGE_IDS))

    try:
        mod = __import__(_PLUGIN_MODULE, fromlist=_PLUGIN_CLASSES)
    except Exception:
        logger.error('[FlyingDamage] import plugins failed', exc_info=True)
        return

    hooked = 0
    for clsName in _PLUGIN_CLASSES:
        cls = getattr(mod, clsName, None)
        if not isinstance(cls, type):
            continue
        if not hasattr(cls, 'onVehicleFeedbackReceived'):
            continue
        try:
            override(cls, 'onVehicleFeedbackReceived', _feedbackHook)
            hooked += 1
            logger.info('[FlyingDamage] hooked %s.onVehicleFeedbackReceived', clsName)
        except Exception:
            logger.info('[FlyingDamage] hook fail %s', clsName, exc_info=True)

    logger.info('[FlyingDamage] suppression hooks: %d', hooked)


def _feedbackHook(base, self, *args, **kwargs):
    eventID = args[0] if len(args) >= 1 else None
    if _logN[0] < 30:
        _logN[0] += 1
        logger.info('[FlyingDamage] FB eventID=%s args=%s',
                    repr(eventID), repr(args)[:110])
    if g_config.hideStandard and eventID in _DAMAGE_IDS:
        return None
    return base(self, *args, **kwargs)
