# -*- coding: utf-8 -*-
"""Localized, validated and persistent in-game settings for DepDamage."""

import json
import logging
import os

from . import hooks

LOG = logging.getLogger('DepDamage')
MOD_LINKAGE = 'depdamage'

try:
    from gui.modsSettingsApi import g_modsSettingsApi
except ImportError:
    g_modsSettingsApi = None

try:
    from helpers import getClientLanguage
except ImportError:
    getClientLanguage = None

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
TEMPLATE = None

LANG_ALIASES = {
    'ua': 'uk',
    'uk_ua': 'uk',
    'ru_ru': 'ru',
    'en_gb': 'en',
    'en_us': 'en',
    'de_de': 'de',
    'pl_pl': 'pl',
    'cs_cz': 'cs',
    'fr_fr': 'fr',
}

TEXTS = {
    'en': {
        'enable': 'Enable mod',
        'player': 'My damage color',
        'ally': 'Damage to allies color',
        'enemy': 'Damage to enemies color',
        'allyFire': 'Fire damage to allies',
        'enemyFire': 'Fire damage to enemies',
        'fontSize': 'Font size',
        'duration': 'Animation duration',
        'spawnHeight': 'Spawn height above tank',
        'seconds': '{{value}} s',
    },
    'uk': {
        'enable': 'Увімкнути мод',
        'player': 'Колір мого урону',
        'ally': 'Колір урону по союзниках',
        'enemy': 'Колір урону по противниках',
        'allyFire': 'Підпал союзників',
        'enemyFire': 'Підпал противників',
        'fontSize': 'Розмір шрифту',
        'duration': 'Тривалість анімації',
        'spawnHeight': 'Висота появи над танком',
        'seconds': '{{value}} с',
    },
    'ru': {
        'enable': 'Включить мод',
        'player': 'Цвет моего урона',
        'ally': 'Цвет урона по союзникам',
        'enemy': 'Цвет урона по противникам',
        'allyFire': 'Поджог союзников',
        'enemyFire': 'Поджог противников',
        'fontSize': 'Размер шрифта',
        'duration': 'Длительность анимации',
        'spawnHeight': 'Высота появления над танком',
        'seconds': '{{value}} с',
    },
    'de': {
        'enable': 'Mod aktivieren',
        'player': 'Farbe meines Schadens',
        'ally': 'Farbe des Schadens an Verbündeten',
        'enemy': 'Farbe des Schadens an Gegnern',
        'allyFire': 'Brandschaden an Verbündeten',
        'enemyFire': 'Brandschaden an Gegnern',
        'fontSize': 'Schriftgröße',
        'duration': 'Animationsdauer',
        'spawnHeight': 'Erscheinungshöhe über dem Panzer',
        'seconds': '{{value}} s',
    },
    'pl': {
        'enable': 'Włącz mod',
        'player': 'Kolor moich uszkodzeń',
        'ally': 'Kolor uszkodzeń sojuszników',
        'enemy': 'Kolor uszkodzeń przeciwników',
        'allyFire': 'Podpalenie sojuszników',
        'enemyFire': 'Podpalenie przeciwników',
        'fontSize': 'Rozmiar czcionki',
        'duration': 'Czas animacji',
        'spawnHeight': 'Wysokość pojawienia nad czołgiem',
        'seconds': '{{value}} s',
    },
    'cs': {
        'enable': 'Zapnout mod',
        'player': 'Barva mého poškození',
        'ally': 'Barva poškození spojenců',
        'enemy': 'Barva poškození nepřátel',
        'allyFire': 'Požár spojenců',
        'enemyFire': 'Požár nepřátel',
        'fontSize': 'Velikost písma',
        'duration': 'Délka animace',
        'spawnHeight': 'Výška zobrazení nad tankem',
        'seconds': '{{value}} s',
    },
    'fr': {
        'enable': 'Activer le mod',
        'player': 'Couleur de mes dégâts',
        'ally': 'Couleur des dégâts aux alliés',
        'enemy': 'Couleur des dégâts aux ennemis',
        'allyFire': 'Incendie sur les alliés',
        'enemyFire': 'Incendie sur les ennemis',
        'fontSize': 'Taille de police',
        'duration': 'Durée de l’animation',
        'spawnHeight': 'Hauteur d’apparition au-dessus du char',
        'seconds': '{{value}} s',
    },
}


def _settings_path():
    appData = os.environ.get('APPDATA') or os.path.expanduser('~')
    return os.path.join(
        appData,
        'Wargaming.net',
        'WorldOfTanks',
        'mods',
        'DepDamage',
        'settings.json'
    )


def _clean_color(value, fallback):
    try:
        value = str(value or fallback).replace('#', '').upper()
    except Exception:
        return fallback
    if len(value) != 6:
        return fallback
    try:
        int(value, 16)
    except Exception:
        return fallback
    return value


def _safe_bool(value, fallback):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    try:
        normalized = str(value).strip().lower()
    except Exception:
        return fallback
    if normalized in ('true', '1', 'yes', 'on'):
        return True
    if normalized in ('false', '0', 'no', 'off'):
        return False
    return fallback


def _safe_int(value, fallback, minimum, maximum):
    try:
        value = int(round(float(value)))
    except Exception:
        value = fallback
    return max(minimum, min(maximum, value))


def _safe_float(value, fallback, minimum, maximum):
    try:
        value = float(value)
    except Exception:
        value = fallback
    return max(minimum, min(maximum, value))


def _sanitize_settings(values):
    values = values if isinstance(values, dict) else {}
    return {
        'enabled': _safe_bool(values.get('enabled'), DEFAULTS['enabled']),
        'playerColor': _clean_color(values.get('playerColor'), DEFAULTS['playerColor']),
        'allyColor': _clean_color(values.get('allyColor'), DEFAULTS['allyColor']),
        'enemyColor': _clean_color(values.get('enemyColor'), DEFAULTS['enemyColor']),
        'allyFireColor': _clean_color(values.get('allyFireColor'), DEFAULTS['allyFireColor']),
        'enemyFireColor': _clean_color(values.get('enemyFireColor'), DEFAULTS['enemyFireColor']),
        'fontSize': _safe_int(values.get('fontSize'), DEFAULTS['fontSize'], 14, 32),
        'animationDuration': _safe_float(
            values.get('animationDuration'), DEFAULTS['animationDuration'], 0.6, 4.0
        ),
        'spawnHeight': _safe_float(values.get('spawnHeight'), DEFAULTS['spawnHeight'], 0.0, 4.0),
    }


def _load_persistent_settings():
    path = _settings_path()
    try:
        if not os.path.isfile(path):
            return False
        with open(path, 'rb') as stream:
            saved = json.loads(stream.read().decode('utf-8'))
        SETTINGS.update(_sanitize_settings(saved))
        LOG.info('[DepDamage] persistent settings loaded')
        return True
    except Exception:
        LOG.exception('[DepDamage] failed to load persistent settings; defaults will be used')
        SETTINGS.update(DEFAULTS)
        return False


def _save_persistent_settings():
    path = _settings_path()
    try:
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        SETTINGS.update(_sanitize_settings(SETTINGS))
        data = json.dumps(dict(SETTINGS), ensure_ascii=False, indent=2, sort_keys=True)
        if not isinstance(data, bytes):
            data = data.encode('utf-8')
        tempPath = path + '.tmp'
        with open(tempPath, 'wb') as stream:
            stream.write(data)
        if os.path.isfile(path):
            os.remove(path)
        os.rename(tempPath, path)
        LOG.info('[DepDamage] persistent settings saved')
    except Exception:
        LOG.exception('[DepDamage] failed to save persistent settings')


def _client_language():
    language = 'en'
    try:
        if getClientLanguage is not None:
            language = str(getClientLanguage() or 'en').lower().replace('-', '_')
    except Exception:
        LOG.exception('[DepDamage] failed to detect client language')
    language = LANG_ALIASES.get(language, language)
    if language not in TEXTS:
        shortLanguage = language.split('_', 1)[0]
        language = shortLanguage if shortLanguage in TEXTS else 'en'
    return language


def _build_template():
    text = TEXTS[_client_language()]
    return {
        'modDisplayName': 'DepDamage',
        'enabled': True,
        'column1': [
            {'type': 'CheckBox', 'text': text['enable'], 'value': SETTINGS['enabled'], 'varName': 'enabled'},
            {'type': 'ColorChoice', 'text': text['player'], 'value': SETTINGS['playerColor'], 'varName': 'playerColor'},
            {'type': 'ColorChoice', 'text': text['ally'], 'value': SETTINGS['allyColor'], 'varName': 'allyColor'},
            {'type': 'ColorChoice', 'text': text['enemy'], 'value': SETTINGS['enemyColor'], 'varName': 'enemyColor'},
            {'type': 'ColorChoice', 'text': text['allyFire'], 'value': SETTINGS['allyFireColor'], 'varName': 'allyFireColor'},
            {'type': 'ColorChoice', 'text': text['enemyFire'], 'value': SETTINGS['enemyFireColor'], 'varName': 'enemyFireColor'},
        ],
        'column2': [
            {
                'type': 'Slider', 'text': text['fontSize'], 'minimum': 14, 'maximum': 32,
                'snapInterval': 1, 'value': SETTINGS['fontSize'], 'format': '{{value}}', 'varName': 'fontSize'
            },
            {
                'type': 'Slider', 'text': text['duration'], 'minimum': 0.6, 'maximum': 4.0,
                'snapInterval': 0.05, 'value': SETTINGS['animationDuration'],
                'format': text['seconds'], 'varName': 'animationDuration'
            },
            {
                'type': 'Slider', 'text': text['spawnHeight'], 'minimum': 0.0, 'maximum': 4.0,
                'snapInterval': 0.05, 'value': SETTINGS['spawnHeight'], 'format': '{{value}}', 'varName': 'spawnHeight'
            },
        ]
    }


def _apply():
    SETTINGS.update(_sanitize_settings(SETTINGS))
    hooks._FlashDamageNumber.DURATION = SETTINGS['animationDuration']
    hooks._FlashDamageNumber.TICK = 1.0 / 120.0
    hooks.FlashDamageOverlay.MERGE_WINDOW = 0.06
    hooks.FlashDamageOverlay.SPAWN_HEIGHT = SETTINGS['spawnHeight']
    hooks.set_enabled(SETTINGS['enabled'])


def _as_create_damage(self, numberID, damage, damageFlag):
    if self._isDAAPIInited():
        return self.flashObject.as_createDamage(
            numberID,
            damage,
            damageFlag,
            SETTINGS['playerColor'],
            SETTINGS['allyColor'],
            SETTINGS['enemyColor'],
            SETTINGS['allyFireColor'],
            SETTINGS['enemyFireColor'],
            SETTINGS['fontSize']
        )


def _on_changed(linkage, newSettings):
    if linkage != MOD_LINKAGE:
        return
    merged = dict(SETTINGS)
    if isinstance(newSettings, dict):
        merged.update(newSettings)
    SETTINGS.update(_sanitize_settings(merged))
    _apply()
    _save_persistent_settings()
    LOG.info('[DepDamage] settings updated')


def init():
    global TEMPLATE

    hooks.DepDamageFlashMeta.as_createDamage = _as_create_damage

    hasPersistentSettings = _load_persistent_settings()
    TEMPLATE = _build_template()

    if g_modsSettingsApi is not None:
        saved = g_modsSettingsApi.getModSettings(MOD_LINKAGE, TEMPLATE)
        if not hasPersistentSettings and saved:
            SETTINGS.update(_sanitize_settings(saved))
            TEMPLATE = _build_template()
        if saved:
            g_modsSettingsApi.registerCallback(MOD_LINKAGE, _on_changed)
        else:
            created = g_modsSettingsApi.setModTemplate(MOD_LINKAGE, TEMPLATE, _on_changed)
            if not hasPersistentSettings and created:
                SETTINGS.update(_sanitize_settings(created))
    else:
        LOG.warning('[DepDamage] ModsSettingsAPI not found; using persistent built-in settings')

    _apply()
    _save_persistent_settings()
    LOG.info('[DepDamage] localized in-game settings registered')


def fini():
    _save_persistent_settings()
