# Flying Damage — WoT mod (SWF battle view)

Відлітаючий урон над танками, намальований Flash-в'юхою (SWF) як повноцінний
Scaleform-view — тому AS3-код реально виконується в грі (на відміну від простого
Sprite-SWF, який Scaleform не запускає).

## Структура (як у шаблоні Masters-Marks)
```
as3/
  libs/            — WoT SWC-бібліотеки + playerglobal.swc
  src_flash/
    FlyingDamageApp.as3proj      — проект для компіляції SWF
    src/com/flyingdamage/*.as    — вихідники SWF
  bin/             — сюди складається скомпільований SWF
python/
  gui/mods/mod_flyingdamage.py            — точка входу
  gui/mods/flyingdamage/                  — контролер, хуки, налаштування
resources/
  in/gui/flash/FlyingDamageApp.swf        — SWF, що потрапляє в мод
build.py           — збірка .wotmod
build.json         — конфіг збірки
.github/workflows/release.yml             — CI (компілює SWF + пакує)
```

## Як зібрати SWF (у тебе, на ПК)

### Варіант 1 — Adobe Animate
Відкрий проєкт як у Masters-Marks (через .fla) і публікуй. `build.py --flash`.

### Варіант 2 — Apache Flex mxmlc (як робить CI)
1. Встанови Apache Flex SDK 4.16.1 + Java.
2. Поклади `as3/libs/playerglobal.swc` у Flex SDK
   (`frameworks/libs/player/32.0/playerglobal.swc`).
3. Компілюй:
```
mxmlc -source-path+=as3/src_flash/src ^
  -library-path+=as3/libs/playerglobal.swc ^
  -external-library-path+=as3/libs/common-1.0-SNAPSHOT.swc ^
  -external-library-path+=as3/libs/common_i18n_library-1.0-SNAPSHOT.swc ^
  -external-library-path+=as3/libs/base_app-1.0-SNAPSHOT.swc ^
  -external-library-path+=as3/libs/gui_base-1.0-SNAPSHOT.swc ^
  -external-library-path+=as3/libs/gui_lobby-1.0-SNAPSHOT.swc ^
  -external-library-path+=as3/libs/gui_battle-1.0-SNAPSHOT.swc ^
  -external-library-path+=as3/libs/lobby.swc ^
  -external-library-path+=as3/libs/battle.swc ^
  -target-player=32.0 -swf-version=39 -optimize=true ^
  -output=as3/bin/FlyingDamageApp.swf ^
  -- as3/src_flash/src/com/flyingdamage/FlyingDamageView.as
```
4. Скопіюй `as3/bin/FlyingDamageApp.swf` → `resources/in/gui/flash/`.

### Варіант 3 — GitHub Actions (найпростіше)
Запуш проєкт у свій GitHub-репозиторій і зроби тег `v3.0.0` (або запусти
workflow вручну). CI сам завантажить Flex SDK, скомпілює SWF і збере .wotmod
у релізі. Нічого локально ставити не треба.

## Зібрати .wotmod
```
pip install psutil
python build.py --distribute
```
Готовий файл — у `build/com.author.flyingdamage_3.0.0.wotmod`.
Скопіюй у `<WoT>/mods/2.3.0.1/`.

## Як це працює
1. Python реєструє Scaleform-View, прив'язаний до `FlyingDamageApp.swf`.
2. На старті бою View вантажиться в бойовий застосунок (`loadView`).
3. Хук `onHealthChanged` рахує урон, проєктує позицію танка на екран,
   і викликає `view.flashObject.as_showDamage(x, y, dmg, ...)`.
4. SWF (AbstractView) малює цифру й анімує підйом + згасання.

## Логи
`<WoT>/python.log`, тег `[FlyingDamage]`. Очікувані рядки:
```
[FlyingDamage] flash view registered
[FlyingDamage] loadView requested
[FlyingDamage] view _populate
[FlyingDamage] [SWF] configUI done
[FlyingDamage] [SWF] recv d=334 x=1152 y=447
```
