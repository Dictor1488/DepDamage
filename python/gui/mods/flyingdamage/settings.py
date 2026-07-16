# -*- coding: utf-8 -*-
"""In-game settings for DepDamage via ModsSettingsAPI."""

import logging

from . import hooks

LOG = logging.getLogger('DepDamage')
MOD_LINKAGE = 'depdamage'

try:
    from gui.modsSettingsApi import g_modsSettingsApi
except ImportError:
    g_modsSettingsApi = None

DEFAULTS = {
    'enabled': True,
    'playerColor': 'FFD54A',
    'allyColor': '5BE36A',
    'enemyColor': 'FF5A5A',
    'allyFireColor': '1F7A35',
    'enemyFireColor': '981F1F',
    'fontSize': 22,
    'animationDuration': 1.45,
    'spawnHeight': 2.5,
}

SETTINGS = dict(DEFAULTS)
_ORIGINAL_SHOW_DAMAGE = None

TEMPLATE = {
    'modDisplayName': 'DepDamage',
    'enabled': True,
    'column1': [
        {
            'type': 'CheckBox',
            'text': 'Увімкнути мод',
            'value': DEFAULTS['enabled'],
            'varName': 'enabled'
        },
        {
            'type': 'ColorChoice',
            'text': 'Колір мого урону',
            'value': DEFAULTS['playerColor'],
            'varName': 'playerColor'
        },
        {
            'type': 'ColorChoice',
            'text': 'Колір урону по союзниках',
            'value': DEFAULTS['allyColor'],
            'varName': 'allyColor'
        },
        {
            'type': 'ColorChoice',
            'text': 'Колір урону по противниках',
            'value': DEFAULTS['enemyColor'],
            'varName': 'enemyColor'
        },
        {
            'type': 'ColorChoice',
            'text': 'Підпал союзників',
            'value': DEFAULTS['allyFireColor'],
            'varName': 'allyFireColor'
        },
        {
            'type': 'ColorChoice',
            'text': 'Підпал противників',
            'value': DEFAULTS['enemyFireColor'],
            'varName': 'enemyFireColor'
        }
    ],
    'column2': [
        {
            'type': 'Slider',
            'text': 'Розмір шрифту',
            'minimum': 14,
            'maximum': 32,
            'snapInterval': 1,
            'value': DEFAULTS['fontSize'],
            'format': '{{value}}',
            'varName': 'fontSize'
        },
        {
            'type': 'Slider',
            'text': 'Тривалість анімації',
            'minimum': 0.6,
            'maximum': 4.0,
            'snapInterval': 0.05,
            'value': DEFAULTS['animationDuration'],
            'format': '{{value}} с',
            'varName': 'animationDuration'
        },
        {
            'type': 'Slider',
            'text': 'Висота появи над танком',
            'minimum': 0.0,
            'maximum': 4.0,
            'snapInterval': 0.05,
            'value': DEFAULTS['spawnHeight'],
            'format': '{{value}}',
            'varName': 'spawnHeight'
        }
    ]
}


def _clean_color(value, fallback):
    value = str(value or fallback).replace('#', '').upper()
    if len(value) != 6:
        return fallback
    try:
        int(value, 16)
    except Exception:
        return fallback
    return value


def _apply():
    hooks._ENABLED = bool(SETTINGS.get('enabled', True))
    hooks._FlashDamageNumber.DURATION = max(
        0.1,
        float(SETTINGS.get('animationDuration', DEFAULTS['animationDuration']))
    )
    hooks._FlashDamageNumber.TICK = 0.016
    hooks.FlashDamageOverlay.SPAWN_HEIGHT = max(
        0.0,
        float(SETTINGS.get('spawnHeight', DEFAULTS['spawnHeight']))
    )


def _as_create_damage(self, numberID, damage, damageFlag):
    if self._isDAAPIInited():
        return self.flashObject.as_createDamage(
            numberID,
            damage,
            damageFlag,
            _clean_color(SETTINGS.get('playerColor'), DEFAULTS['playerColor']),
            _clean_color(SETTINGS.get('allyColor'), DEFAULTS['allyColor']),
            _clean_color(SETTINGS.get('enemyColor'), DEFAULTS['enemyColor']),
            _clean_color(SETTINGS.get('allyFireColor'), DEFAULTS['allyFireColor']),
            _clean_color(SETTINGS.get('enemyFireColor'), DEFAULTS['enemyFireColor']),
            int(SETTINGS.get('fontSize', DEFAULTS['fontSize']))
        )


def _show_damage_with_fire(self, vehicleID, damage, attackerID, damageType, damageFlag):
    normalizedType = str(damageType or '').lower()
    if 'fire' in normalizedType:
        damageFlag = int(damageFlag) + 10
    return _ORIGINAL_SHOW_DAMAGE(
        self,
        vehicleID,
        damage,
        attackerID,
        damageType,
        damageFlag
    )


def _on_changed(linkage, newSettings):
    if linkage != MOD_LINKAGE:
        return
    SETTINGS.update(newSettings or {})
    _apply()
    LOG.info('[DepDamage] settings updated')


def init():
    global SETTINGS, _ORIGINAL_SHOW_DAMAGE

    hooks.DepDamageFlashMeta.as_createDamage = _as_create_damage

    if _ORIGINAL_SHOW_DAMAGE is None:
        _ORIGINAL_SHOW_DAMAGE = hooks.FlashDamageOverlay.showDamage
        hooks.FlashDamageOverlay.showDamage = _show_damage_with_fire

    if g_modsSettingsApi is None:
        _apply()
        LOG.warning('[DepDamage] ModsSettingsAPI not found; using built-in defaults')
        return

    saved = g_modsSettingsApi.getModSettings(MOD_LINKAGE, TEMPLATE)
    if saved:
        SETTINGS.update(saved)
        g_modsSettingsApi.registerCallback(MOD_LINKAGE, _on_changed)
    else:
        created = g_modsSettingsApi.setModTemplate(MOD_LINKAGE, TEMPLATE, _on_changed)
        if created:
            SETTINGS.update(created)

    _apply()
    LOG.info('[DepDamage] in-game settings registered')
