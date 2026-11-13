# Remorseim Gunpack — оружие Remorseim для обычного Z-City

Аддон **добавляет** в обычный Z-City (`Z-City.zip` → `z_city`) оружие и
melee-swep'ы из архива Remorseim (`remorseim main.zip` → `remorseism-main`).

* **Огнестрел и снаряжение (47 классов)** — то, чего в Z-City нет,
  переносится как есть, на существующих базах.
* **Весь ближний бой Remorseim (33 класса)** — отдельной веткой: своя база
  `weapon_rem_melee_base`, свои классы `weapon_rem_melee_*`, своя категория
  «Weapons - Remorseim Melee». Даже если предмет с таким названием в Z-City
  уже есть, старая версия остаётся нетронутой, а рядом появляется новая.

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
    │   ├── sh_rem_melee_decals.lua       синяки от ударов (свои decal-имена)
    │   ├── sh_rem_hitstop.lua            хитстоп ближнего боя (из Remorseim)
    │   └── server/
    │       ├── sv_gunpack_boot.lua       список оружия + хелперы
    │       └── sv_gunpack_content.lua    ← генерируется автоматически
    ├── weapons/                          47 огнестрела + 33 melee (weapon_rem_melee_*)
    └── entities/                         rem_bomb_*, ent_enhanced_hook,
                                          zbox_lootbox, граната с зажигательным

tools/
├── ИщиКонтент.bat                        ← БАТНИК: сборка + поиск контента
└── find_content.py                       его логика

build/
├── manifest.json                         список переносимого огнестрела/снаряжения
├── melee_manifest.json                   список ближнего боя (отдельная ветка)
├── gen_melee.py                          генератор weapon_rem_melee_*
└── build_addon.py                        сборщик аддона

content_manifest.json                     что докачать (звуки/модели)
```

### Разница между архивами

| | оружий | что это |
|---|---|---|
| `Z-City.zip` | 192 | обычный Z-City, база |
| `remorseim main.zip` | 240 | форк с новым оружием |
| **новых в Remorseim** | **50** | 47 переносятся как есть + 33 melee отдельной веткой |

Плюс в Remorseim есть более новые версии баз (`weapon_melee`, `homigrad_base`).
Положить их в Z-City под теми же именами нельзя — это замена, которая сломает
весь остальной арсенал. Поэтому:

* новая **melee-база** сохранена под своим классом `weapon_rem_melee_base`,
  и на ней живёт вся ветка ближнего боя Remorseim;
* для `homigrad_base` из неё взяты только отдельные методы
  (см. `sh_remorseim_gunpack.lua`).

---

## Скачать

Готовый архив аддона лежит прямо в репозитории:

**https://github.com/yaumaDDD/Remorseim-Gunpack/raw/v1.0.0/build_output/remorseim_gunpack.zip** (~282 КБ)

Если ссылка не открывается — откройте
`build_output/remorseim_gunpack.zip` в репозитории и нажмите «Download».

Внутри уже распакованная папка `remorseim_gunpack` — её и кидать в `garrysmod/addons/`.

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

### Огнестрел и снаряжение (47)

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

### Ближний бой (33) — отдельно от Z-City

Весь melee из Remorseim перенесён **отдельной веткой**, а не подменой старых классов:

* база — форкнутая melee-база Remorseim, живёт как `weapon_rem_melee_base`;
* каждый свep получил свой класс `weapon_rem_melee_<имя>`;
* категория в спавн-меню — **Weapons - Remorseim Melee**;
* `weapon_melee` и всё ближнее оружие Z-City остались ровно такими, как были.

Поэтому, например, `weapon_bat` (Z-City) и `weapon_rem_melee_bat` (Remorseim
версия с комбо-ударами и блоком) спокойно лежат рядом и не конфликтуют.

| класс | название | примечание |
|---|---|---|
| `weapon_rem_melee_ballistic_shield` | Ballistic Shield (Rem) | щит, блокирует пули |
| `weapon_rem_melee_bat` | Bat (Rem) | бейсбольная бита |
| `weapon_rem_melee_brick` | Brick (Rem) | кирпич |
| `weapon_rem_melee_buck200knife` | Buck 120 General (Rem) | нож |
| `weapon_rem_melee_chainsaw` | Chainsaw (Rem) | бензопила, топливо и стамина |
| `weapon_rem_melee_chair_leg` | Chair Leg (Rem) | ножка стула |
| `weapon_rem_melee_combatknife` | M7 Bayonet (Rem) | штык-нож |
| `weapon_rem_melee_hammer` | Hammer (Rem) | молоток |
| `weapon_rem_melee_hatchet` | Hatchet (Rem) | топорик |
| `weapon_rem_melee_hg_axe` | Fire Axe (Rem) | пожарный топор |
| `weapon_rem_melee_hg_bottle` | Bottle (Rem) | бутылка (ломается) |
| `weapon_rem_melee_hg_bottlebroken` | Broken Bottle (Rem) | розочка |
| `weapon_rem_melee_hg_crowbar` | Crowbar (Rem) | монтировка |
| `weapon_rem_melee_hg_crowbar_gordon` | Crowbar Gordon (Rem) | не спавнится, как в оригинале |
| `weapon_rem_melee_hg_extinguisher` | Fire Extinguisher (Rem) | огнетушитель |
| `weapon_rem_melee_hg_glassshard` | Glass Shard (Rem) | осколок стекла |
| `weapon_rem_melee_hg_glassshard_taped` | Taped Glass Shard (Rem) | осколок с изолентой |
| `weapon_rem_melee_hg_machete` | Machete (Rem) | мачете |
| `weapon_rem_melee_hg_mug` | Mug (Rem) | кружка |
| `weapon_rem_melee_hg_shovel` | Shovel (Rem) | лопата |
| `weapon_rem_melee_hg_sledgehammer` | Sledgehammer (Rem) | кувалда |
| `weapon_rem_melee_hg_spear` | Spear (Rem) | копьё |
| `weapon_rem_melee_hg_spear_knife` | Modified Spear (Rem) | копьё с ножом |
| `weapon_rem_melee_hg_spear_pro` | Pro Spear (Rem) | прокачанное копьё |
| `weapon_rem_melee_hg_stunstick` | Stunstick (Rem) | дубинка |
| `weapon_rem_melee_hg_tonfa` | Police Tonfa (Rem) | тонфа |
| `weapon_rem_melee_leadpipe` | Lead Pipe (Rem) | труба |
| `weapon_rem_melee_metalbat` | Aluminium Bat (Rem) | алюминиевая бита |
| `weapon_rem_melee_pan` | Pan (Rem) | сковорода |
| `weapon_rem_melee_pocketknife` | Switchblade (Rem) | выкидной нож |
| `weapon_rem_melee_ram` | Battering Ram (Rem) | таран |
| `weapon_rem_melee_sogknife` | SOG SEAL 2000 (Rem) | нож |
| `weapon_rem_melee_table_leg` | Table Leg (Rem) | ножка стола |

Технические отличия этой ветки:

* база Remorseim умеет то, чего нет в Z-City: направленный блок, парирование,
  clash оружия, комбо-серии, charged-атака, щит, хитстоп;
* одноимённые хуки/команды/сети переименованы с суффиксом `_rem`
  (`hg_tape_shard` → `hg_tape_shard_rem`, `melee_attack` → `melee_attack_rem`
  и т.п.), чтобы не перекрывать такие же в Z-City;
* перекрёстные ссылки внутри ветки ведут на свои классы
  (бутылка ломается в свою розочку, осколок + скотч → свой осколок с изолентой);
* `weapon_hg_crowbar_gordon` намеренно не появляется в меню — как в оригинале.

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

Что докидывается в **свою** базу ближнего боя `weapon_rem_melee_base`
(только если метода ещё нет — базовый `weapon_melee` Z-City не трогается):

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

`build_addon.py` читает `build/manifest.json` (огнестрел и снаряжение) и
копирует lua-файлы из `.work/remorseism-main/` в `addon/remorseim_gunpack/`.
Ближний бой он собирает отдельно, вызывая `build/gen_melee.py` по списку
`build/melee_manifest.json` — тот делает свою базу и свои классы.

Добавить ещё один ствол — дописать строку в `manifest.json` и в
`sv_gunpack_boot.lua` (там же категория). Добавить ещё один melee — строку в
`melee_manifest.json` (и, при желании, в `GP.MeleeWeapons` в
`sv_gunpack_boot.lua`), затем пересобрать.

---

## Лицензия и авторство

Скрипты оружия взяты из Remorseim (AGPL-3.0, см. `remorseim main.zip` →
`LICENSE`). Аддон их не переписывает, а переносит в Z-City как отдельный
аддон. Уважайте труд авторов: не выдавайте это за своё и оставляйте ссылки
на оригиналы.
