# Remorseim Gunpack — оружие Remorseim для обычного Z-City

Аддон **добавляет** в обычный Z-City (`Z-City.zip` → `z_city`) всё оружие и
melee-swep'ы из архива Remorseim (`remorseim main.zip` → `remorseism-main`),
которых в нём нет.

Ничего не заменяется: файлы Z-City не перезаписываются, базовые классы
(`homigrad_base`, `weapon_melee`, `weapon_m4super`, `weapon_revolver2`,
`weapon_tpik1_base`, `weapon_bandage_sh`) используются как есть. Всё, что
нужно докрутить, докручивается точечно и только если этого ещё нет.

---

## Что внутри

```
addon/remorseim_gunpack/          ← готовый аддон (кидать в garrysmod/addons/)
├── addon.json
└── lua/
    ├── autorun/
    │   ├── sh_remorseim_gunpack.lua      слой совместимости (клиент+сервер)
    │   └── server/
    │       ├── sv_gunpack_boot.lua       список оружия + хелперы
    │       └── sv_gunpack_content.lua    ← генерируется автоматически
    ├── weapons/                          50 стволов и melee-swep'ов
    └── entities/                         rem_bomb_*, ent_enhanced_hook,
                                          zbox_lootbox, граната с зажигательным

tools/
├── ИщиКонтент.bat                        ← БАТНИК: сборка + поиск контента
└── find_content.py                       его логика

build/
├── manifest.json                         список переносимого оружия
└── build_addon.py                        сборщик аддона

content_manifest.json                     что докачать (звуки/модели)
```

### Разница между архивами

| | оружий | что это |
|---|---|---|
| `Z-City.zip` | 192 | обычный Z-City, база |
| `remorseim main.zip` | 240 | форк с новым оружием |
| **новых в Remorseim** | **50** | их и переносит аддон |

Плюс в Remorseim есть более новые версии баз (`weapon_melee`, `homigrad_base`),
но их **нельзя** просто положить в Z-City — это замена, которая сломает весь
остальной арсенал. Поэтому аддон берёт из них только отдельные методы
(см. `sh_remorseim_gunpack.lua`).

---

## Установка

1. Скопируйте папку `addon/remorseim_gunpack` в:
   ```
   ...\Steam\steamapps\common\GarrysMod\garrysmod\addons\
   ```
   Должно получиться `garrysmod/addons/remorseim_gunpack/lua/...`
2. Контент (модели/звуки) — см. раздел «Контент» ниже.
3. Запустите игру, оружие появится в спавн-меню в тех же категориях, что и
   обычное (`Weapons - Assault Rifles`, `Weapons - Melee`, `ZCity Other` …).

---

## Батник поиска контента

```
tools\ИщиКонтент.bat
```

Двойной клик. Что делает:

1. находит Python;
2. распаковывает zip-архивы в `.work/` и собирает аддон;
3. спрашивает путь к `garrysmod` (Enter — поиск автоматически по типовым
   путям Steam), проверяет, каких моделей и звуков не хватает;
4. выводит id воркшоп-аддонов, которые закрывают контент.

Можно и по отдельности:

```bat
python tools\find_content.py prepare    :: распаковать архивы
python tools\find_content.py build      :: собрать аддон
python tools\find_content.py scan       :: проверить контент
python tools\find_content.py workshop   :: показать воркшоп-id
```

Если Garry's Mod стоит нестандартно:

```bat
set GMOD_PATH=D:\Games\GarrysMod\garrysmod
```

---

## Контент (и почему его нет в GitHub)

Модели и звуки оружия весят сотни мегабайт — GitHub такое не принимает
(лимит 100 МБ на файл и ~1 ГБ на репозиторий, плюс это мусор в истории).
Поэтому:

* **в репозитории только скрипты** (аддон ~1.5 МБ);
* точный список нужных файлов лежит в `content_manifest.json`;
* сервер сам раздаёт эти файлы через `resource.AddSingleFile` — список
  компилируется в `lua/autorun/server/sv_gunpack_content.lua`;
* на практике контент закрывается тремя воркшоп-аддонами:

| id | зачем |
|---|---|
| [`3657897364`](https://steamcommunity.com/sharedfiles/filedetails/?id=3657897364) | основной контент Z-City |
| [`3257937532`](https://steamcommunity.com/sharedfiles/filedetails/?id=3257937532) | distac content |
| [`3759394449`](https://steamcommunity.com/sharedfiles/filedetails/?id=3759394449) | релиз Remorseim — контент нового оружия |

Для выделенного сервера — либо коллекция с этими аддонами, либо FastDL:
файлы из `content_manifest.json` выкладываются на http-хост, путь прописывается
в `sv_downloadurl`.

---

## Что перенесено

### Оружие (50)

| класс | название | категория |
|---|---|---|
| `weapon_50beowulf` | Beowulf | Weapons - Sniper Rifles |
| `weapon_ak47` | AK-47 | Weapons - Assault Rifles |
| `weapon_type56` | Type 56-1 | Weapons - Assault Rifles |
| `weapon_m16a1` | M16A1 | Weapons - Assault Rifles |
| `weapon_m16a1_30` | M16A1 (30 mag) | Weapons - Assault Rifles |
| `weapon_nlar15` | Non-lethal AR-15 | Weapons - Carbines |
| `weapon_mp5a5` | HK MP5A5 | Weapons - Machine-Pistols |
| `weapon_mp5k` | HK MP5K | Weapons - Machine-Pistols |
| `weapon_mp5sd6` | HK MP5SD6 | Weapons - Machine-Pistols |
| `weapon_mp5eod` | HK MP5 EOD | Weapons - Machine-Pistols |
| `weapon_mp5_custom` | HK MP5 Custom | Weapons - Machine-Pistols |
| `weapon_mp5sd6_custom` | HK MP5SD6 Custom | Weapons - Machine-Pistols |
| `weapon_mp540` | HK MP5/40 | Weapons - Machine-Pistols |
| `weapon_ro635` | RO-635 | Weapons - Machine-Pistols |
| `weapon_coltlmg` | Colt LMG | Weapons - Machineguns |
| `weapon_m231` | Patriot | Weapons - Machineguns |
| `weapon_m231ad` | Patriot (Admin) | Weapons - Machineguns |
| `weapon_m4short` | XM-1014 Short | Weapons - Shotguns |
| `weapon_m4sport` | M4 Super 90 Sport | Weapons - Shotguns |
| `weapon_m4tac` | M4 Super 90 Tactical | Weapons - Shotguns |
| `weapon_m870` | Remington M870 | Weapons - Shotguns |
| `weapon_m870mcs` | Remington M870 MCS | Weapons - Shotguns |
| `weapon_remington870_long` | Remington 870 long | Weapons - Shotguns |
| `weapon_remington870_sawed_off` | Remington 870 sawed-off | Weapons - Shotguns |
| `weapon_spas12_modern` | Franchi SPAS-12M | Weapons - Shotguns |
| `weapon_spas12_short` | Franchi SPAS-12 Short | Weapons - Shotguns |
| `weapon_spas12_folded` | Franchi SPAS-12 Folded | Weapons - Shotguns |
| `weapon_glock17b` | Glock 17 Burst | Weapons - Pistols |
| `weapon_glock17fd` | Glock 17 FD | Weapons - Pistols |
| `weapon_glock17lb` | Glock 17 LB | Weapons - Pistols |
| `weapon_deagle_c` | Desert Eagle Compensated | Weapons - Pistols |
| `weapon_deagle_annihilator` | Annihilator | Weapons - Pistols |
| `weapon_m1911compact` | M1911 Compact | Weapons - Pistols |
| `weapon_m1911custom` | M1911 Custom | Weapons - Pistols |
| `weapon_nlglock17` | Non-lethal Glock 17 | Weapons - Pistols |
| `weapon_nlglock26` | Non-lethal Glock 26 | Weapons - Pistols |
| `weapon_revolverm500` | S&W M500 | Weapons - Pistols |
| `weapon_combatknife` | M7 Bayonet | Weapons - Melee |
| `weapon_metalbat` | Aluminium Bat | Weapons - Melee |
| `weapon_chainsaw` | Chainsaw | Weapons - Melee |
| `weapon_ammocrate` | Ammo Crate | ZCity Other |
| `weapon_defibrillator` | AED | ZCity Medicine |
| `weapon_midazolam` | Midazolam Autoinjector | ZCity Medicine |
| `weapon_enhanced_hook` | Enhanced Grappling Hook | ZCity Other |
| `weapon_hg_grenade_incendiary_tpik` | AN M14 (зажигательная) | Weapons - Explosive |
| `weapon_spawnmenu_pda` | Tablet | Weapons - Other |
| `weapon_callbomber` | Admin Bomber | ZCity Other |
| `weapon_carpetbomber` | Carpet Bomber | ZCity Other |
| `weapon_airstrike` | Airstrike | ZCity Other |
| `weapon_uav` | UAV | ZCity Other |

### Сущности, без которых оружие не работает

* `rem_bomb_base`, `rem_bomb_500`, `rem_bomb_2000` — бомбы для
  `weapon_callbomber` / `weapon_carpetbomber` / `weapon_airstrike` / `weapon_uav`;
* `ent_enhanced_hook` — крюк для `weapon_enhanced_hook`;
* `zbox_lootbox` — ящик доставки для `weapon_spawnmenu_pda`.

Зажигательная граната (`weapon_hg_grenade_incendiary_tpik`) работает через
штатные Z-City-сущности `ent_hg_spoon` и `prop_physics` — своих сущностей
она не требует.

### Новые калибры

В обычном Z-City этих патронов нет, аддон регистрирует их сам
(`sh_remorseim_gunpack.lua`), вместе с патронными ящиками:

| калибр | для чего |
|---|---|
| `.500 S&W Magnum` | S&W M500 |
| `12.7x43 Beowulf` | Beowulf |
| `9x19 Rubber` | Non-lethal Glock 17 / 26 |
| `5.56x45 Rubber` | Non-lethal AR-15 |
| `.40 SW` | HK MP5/40 (калибр в Z-City есть, но не был прописан в `AmmoTypes2`) |

---

## Технические детали совместимости

Что докидывается в базовый `weapon_melee` (только если метода нет):

| метод | зачем |
|---|---|
| `GetLHIKStateOffset` | позиция левой руки при блоке/самопорезе (M7 Bayonet) |
| `IsSelfHarming` | флаг «режет себя» (в Z-City есть только `owner.suiciding`) |
| `GetSelfHarmShake` | тряска камеры при самопорезе |
| `GetSelfHarmCutLocal` | алиас из Remorseim |
| `ResetCombo` / `GetComboDamageMul` / `ApplyComboDamage` | комбо-система биты и пилы |
| `CancelChargeAttack` | цепная пила зовёт из `Holster`/`OnRemove` |
| `IsHitCooldownTarget` / `ApplyHitCooldown` | кулдаун повторного удара |

Хелперы Z-City, которых не хватало:

* `hg.velocityDamage` — нужен `ent_enhanced_hook` (в Z-City он локальный);
* `hg.organism.StartFibrillation` / `AddCardiacStress` — нужны AED и мидазоламу;
* `hg.DefibReviveIncapacitated` — оживление через AED.

Всё это ставится только при отсутствии — если в вашей версии Z-City они уже
есть, аддон их не трогает.

Отладка:

```
remorseim_gunpack_verbose 1
```

---

## Сборка с нуля

```bat
tools\ИщиКонтент.bat
```

или вручную:

```bat
python tools\find_content.py prepare
python tools\find_content.py build
```

`build_addon.py` читает `build/manifest.json` (список оружия) и копирует
lua-файлы из `.work/remorseism-main/` в `addon/remorseim_gunpack/`.
Добавить ещё один ствол — дописать строку в `manifest.json` и в
`sv_gunpack_boot.lua` (там же категория), затем пересобрать.

---

## Лицензия и авторство

Скрипты оружия взяты из Remorseim (AGPL-3.0, см. `remorseim main.zip` →
`LICENSE`). Аддон их не переписывает, а переносит в Z-City как отдельный
аддон. Уважайте труд авторов: не выдавайте это за своё и оставляйте ссылки
на оригиналы.
