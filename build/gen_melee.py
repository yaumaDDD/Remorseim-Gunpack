#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remorseim Gunpack :: gen_melee.py

Ближний бой Remorseim переносится ОТДЕЛЬНО от Z-City:

  * база — форкнутая melee-база Remorseim (weapon_melee.lua из архива),
    сохраняется как СВОЙ класс `weapon_rem_melee_base`;
  * каждый melee-свep получает СВОЙ класс `weapon_rem_melee_<имя>`
    с переставленным SWEP.Base на эту базу;
  * у свep'ов, которые уже есть в Z-City, остаётся нетронутым оригинал —
    наш класс живёт рядом, в категории «Weapons - Remorseim Melee».

Дополнительно правится:
  * PrintName каждого оружия (см. melee_manifest.json) — чтобы в списке было
    видно, что это ближний бой Remorseim;
  * внутриигровые перекрёстные ссылки между нашими классами
    (бутылка -> розочка, осколок -> осколок с изолентой, скотч и т.п.);
  * имена hook.add / concommand / network-строк, которые иначе перекрыли бы
    одноимённые из Z-City.

Скрипт идемпотентный: можно запускать сколько угодно раз.
"""

import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, ".work")
ADDON = os.path.join(ROOT, "addon", "remorseim_gunpack")
MELEE_MANIFEST = os.path.join(ROOT, "build", "melee_manifest.json")

# старый класс -> новый класс (только ближний бой Remorseim)
PREFIX = "weapon_rem_melee_"


def log(msg):
    print("[melee] " + msg)


def read(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# --------------------------------------------------------------------------
# Хуки и команды, которые уже заняты в Z-City теми же именами.
# Если оставить как есть — новые вещи молча не подключатся (или перекроют
# старые). Поэтому добавляем суффикс _rem.
# --------------------------------------------------------------------------
HOOK_RENAMES = {
    ("PostEntityFireBullets", "hg_shield_block"): "hg_shield_block_rem",
    ("PostPlayerDraw", "hg_shield_back"): "hg_shield_back_rem",
    ("PostDrawTranslucentRenderables", "hg_shield_back_fake"): "hg_shield_back_fake_rem",
    ("Should Fake Up", "NailTaped"): "NailTaped_rem",
    ("OnNetVarSet", "AsdGuilt"): "AsdGuilt_rem",
}

CONCOMMAND_RENAMES = {
    "hg_tape_shard": "hg_tape_shard_rem",
    "hg_tape_knife_spear": "hg_tape_knife_spear_rem",
}

# network-строки: у Z-City уже есть bloody_decal_1 и melee_attack.
# bloody_decal_1 НЕ переименовываем: у нас и у Z-City одинаковый формат пакета
# (net.WriteEntity(self)), и обработчик Z-City рисует кровь правильно. Если
# завести своё имя — пришлось бы тащить в аддон весь sh_bloody_decals.lua.
NET_RENAMES = {
    "melee_attack": "melee_attack_rem",
    "bruise_decal": "bruise_decal_rem",
    # имена decal-ов синяков у Z-City не заняты, но префикс надёжнее
}


def rename_hooks(text):
    for (ev, name), new in HOOK_RENAMES.items():
        text = re.sub(
            r'hook\.Add\(\s*"%s"\s*,\s*"%s"' % (re.escape(ev), re.escape(name)),
            'hook.Add("%s", "%s"' % (ev, new),
            text,
        )
    for old, new in CONCOMMAND_RENAMES.items():
        text = re.sub(
            r'concommand\.Add\(\s*"%s"' % re.escape(old),
            'concommand.Add("%s"' % new,
            text,
        )
    for old, new in NET_RENAMES.items():
        text = re.sub(r'(util\.)?AddNetworkString\(\s*"%s"\s*\)' % re.escape(old),
                      lambda m: '%sAddNetworkString("%s")' % (m.group(1) or "", new), text)
        text = re.sub(r'net\.(Start|Receive)\(\s*"%s"' % re.escape(old),
                      lambda m: 'net.%s("%s"' % (m.group(1), new), text)
    return text


def insert_after_header(text, marker_line, extra):
    """Вставляет extra сразу после первой строки с marker_line (если ещё нет)."""
    if extra.strip() in text:
        return text

    m = re.search(re.escape(marker_line), text)
    if not m:
        return extra + "\n" + text

    end = text.find("\n", m.end())
    if end < 0:
        end = len(text)
    return text[: end + 1] + extra + text[end + 1 :]


# --------------------------------------------------------------------------
# 1. База
# --------------------------------------------------------------------------

def build_base(man):
    src = os.path.join(WORK, man["source_root"], man["base"]["source"])
    if not os.path.isfile(src):
        log("НЕТ файла базы: %s" % src)
        return False

    text = read(src)
    base = man["base"]

    # ловим случай, если база внутри архива сама на что-то опирается
    m = re.search(r'^SWEP\.Base\s*=\s*"([^"]+)"', text, re.M)
    if m:
        log("ВНИМАНИЕ: база Remorseim сама наследует '%s'" % m.group(1))

    text = rename_hooks(text)

    # Внутри базы class-ссылки заменяем аккуратно:
    #   GetClass() == "weapon_melee"  — проверка «это сама база», оставляем смысл
    #   Base ~= "weapon_melee"        — проверка наследования, должна смотреть на нашу базу
    text = text.replace('GetClass() == "weapon_melee"',
                        'GetClass() == "%s"' % man["base"]["target_class"])
    text = re.sub(r'"weapon_melee"', '"%s"' % man["base"]["target_class"], text)
    text = re.sub(r'"Bruise\.Add"', '"Bruise.Rem"', text)
    text = text.replace('"bruises/bruise"', '"bruises/bruise"')
    # ...но проверку «кто я» возвращаем на исходный класс (иначе база начнёт
    # считать себя обычным мечом и включать спец-режимы)
    text = text.replace('GetClass() == "%s"' % man["base"]["target_class"],
                        'GetClass() == "weapon_melee"')

    text = insert_after_header(
        text,
        'SWEP.PrintName',
        '-- Автогенерация: build/gen_melee.py (из архива Remorseim, weapon_melee.lua)\n'
        '-- Отдельная база ближнего боя Remorseim: не подменяет Z-City weapon_melee.\n',
    )

    text = re.sub(r'^SWEP\.PrintName\s*=\s*"[^"]*"',
                  'SWEP.PrintName = "%s"' % base["print_name"], text, count=1, flags=re.M)
    text = re.sub(r'^SWEP\.Category\s*=\s*"[^"]*"',
                  'SWEP.Category = "%s"' % base["category"], text, count=1, flags=re.M)

    out = os.path.join(ADDON, "lua", "weapons", base["target_class"] + ".lua")
    write(out, text)
    log("база сохранена: %s" % base["target_class"])
    return True


# --------------------------------------------------------------------------
# 2. Оружие
# --------------------------------------------------------------------------

def build_weapons(man):
    src_root = os.path.join(WORK, man["source_root"], "lua", "weapons")
    dst_root = os.path.join(ADDON, "lua", "weapons")

    # карта переименований для перекрёстных ссылок
    renames = {w["class"]: PREFIX + w["class"][len("weapon_"):] for w in man["weapons"]}

    # старые классы Z-City, которые тоже фигурируют в перекрёстных ссылках
    # (скотч, руки) — их НЕ надо трогать, они остаются как есть.
    keep = {"weapon_ducttape", "weapon_hands_sh", "weapon_melee"}

    made, skipped = 0, []

    for entry in man["weapons"]:
        old = entry["class"]
        new = renames[old]
        src = os.path.join(src_root, old + ".lua")
        folder = os.path.join(src_root, old)
        if os.path.isdir(folder):
            # оружие-папка (cl_init / init / shared) — берём init.lua как основной файл
            for cand in ("init.lua", "shared.lua", "cl_init.lua"):
                if os.path.isfile(os.path.join(folder, cand)):
                    src = os.path.join(folder, cand)
                    break

        if not os.path.isfile(src):
            skipped.append(old)
            continue

        text = read(src)

        # часть файлов в архиве с отступом — ищем Base без привязки к началу строки
        m = re.search(r'\bSWEP\.Base\s*=\s*"([^"]+)"', text)
        if not m:
            skipped.append(old + " (нет SWEP.Base)")
            continue
        if m.group(1) != "weapon_melee":
            skipped.append("%s (Base=%s)" % (old, m.group(1)))
            continue

        # 1) база -> наша
        text = re.sub(r'\bSWEP\.Base\s*=\s*"[^"]+"',
                      'SWEP.Base = "%s"' % man["base"]["target_class"],
                      text, count=1)

        # 2) ссылки на классы ближнего боя Remorseim (включая ссылку на самого
        #    себя — имя класса задаётся именем файла, в тексте его может не быть)
        for o, n in renames.items():
            text = re.sub(r'"%s"' % re.escape(o), '"%s"' % n, text)
            text = re.sub(r"'%s'" % re.escape(o), "'%s'" % n, text)

        # 2.1) старую базу Z-City внутри своих файлов не дёргаем:
        #      weapons.GetStored("weapon_melee") -> наша база
        text = re.sub(r'"weapon_melee"', '"%s"' % man["base"]["target_class"], text)

        # 3) ссылки на руки/скотч Z-City не трогаем (они в keep)

        # 4) PrintName: добавляем пометку, чтобы отличать от версии Z-City
        pn = re.search(r'\bSWEP\.PrintName\s*=\s*"([^"]*)"', text)
        if pn:
            name = entry.get("print_name") or pn.group(1)
            text = re.sub(r'\bSWEP\.PrintName\s*=\s*"[^"]*"',
                          'SWEP.PrintName = "%s"' % name, text, count=1)
        else:
            text = insert_after_header(
                text, 'SWEP.Base', 'SWEP.PrintName = "%s"\n' % (entry.get("print_name") or old))

        # 4.1) принудительно скрываемые из меню (как в оригинале Remorseim)
        if entry.get("spawnable") is not None:
            value = "true" if entry["spawnable"] else "false"
            if re.search(r'\bSWEP\.Spawnable\s*=', text):
                text = re.sub(r'\bSWEP\.Spawnable\s*=\s*\w+',
                              'SWEP.Spawnable = %s' % value, text, count=1)
            else:
                text = insert_after_header(text, 'SWEP.Base', 'SWEP.Spawnable = %s\n' % value)

        # 5) категория
        if re.search(r'\bSWEP\.Category\s*=\s*"', text):
            text = re.sub(r'\bSWEP\.Category\s*=\s*"[^"]*"',
                          'SWEP.Category = "%s"' % man["category"], text, count=1)
        else:
            text = insert_after_header(
                text, 'SWEP.Base', 'SWEP.Category = "%s"\n' % man["category"])

        # 6) хуки/команды/сети
        text = rename_hooks(text)

        # 7) заголовок
        text = insert_after_header(
            text,
            'SWEP.Base',
            '-- Автогенерация: build/gen_melee.py — из %s.lua архива Remorseim\n' % old,
        )

        write(os.path.join(dst_root, new + ".lua"), text)
        made += 1

    log("создано классов: %d" % made)
    if skipped:
        log("пропущено: %s" % ", ".join(skipped))
    return True


def main():
    if not os.path.isdir(WORK):
        log("Нет папки .work — сначала распакуйте архивы (tools/ИщиКонтент.bat).")
        return 1

    with open(MELEE_MANIFEST, encoding="utf-8") as f:
        man = json.load(f)

    if not os.path.isdir(os.path.join(WORK, man["source_root"])):
        log("Нет папки .work/%s" % man["source_root"])
        return 1

    ok = build_base(man) and build_weapons(man)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
