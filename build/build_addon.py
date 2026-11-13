#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remorseim Gunpack :: build_addon.py

Копирует lua-файлы оружия из распакованного архива Remorseim в аддон.

Ближний бой (melee) переносится ОТДЕЛЬНО: см. build/gen_melee.py и
build/melee_manifest.json — там каждый свep получает свой класс
weapon_rem_melee_* и свою базу weapon_rem_melee_base.

Использование (Windows):
    python build\\build_addon.py
или через батник:
    ИщиКонтент.bat  (он же подготовит исходники и соберёт аддон)

Скрипт НЕ трогает оригиналы: только читает .work/remorseism-main и пишет
в addon/remorseim_gunpack.
"""

import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, ".work")
ADDON = os.path.join(ROOT, "addon", "remorseim_gunpack")
MANIFEST = os.path.join(ROOT, "build", "manifest.json")


def log(msg):
    print("[build] " + msg)


def load_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def read(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def weapon_files(src_root, cls):
    """Все lua-файлы класса оружия: weapon_x.lua либо папка weapon_x/."""
    out = []
    flat = os.path.join(src_root, cls + ".lua")
    if os.path.isfile(flat):
        out.append(flat)
    folder = os.path.join(src_root, cls)
    if os.path.isdir(folder):
        for dirpath, _, files in os.walk(folder):
            for fn in files:
                if fn.endswith(".lua"):
                    out.append(os.path.join(dirpath, fn))
    return out


def copy_weapons(man):
    src_root = os.path.join(WORK, man["source_root"], "lua", "weapons")
    dst_root = os.path.join(ADDON, "lua", "weapons")
    os.makedirs(dst_root, exist_ok=True)

    copied = 0
    missing = []

    for entry in man["weapons"]:
        cls = entry["class"]
        files = weapon_files(src_root, cls)
        if not files:
            missing.append(cls)
            continue

        for f in files:
            rel = os.path.relpath(f, src_root)
            dst = os.path.join(dst_root, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(f, dst)
            copied += 1

    log("weapon files copied: %d" % copied)
    if missing:
        log("ВНИМАНИЕ, не найдены в архиве Remorseim: %s" % ", ".join(missing))
    return missing


def copy_entities(man):
    src_root = os.path.join(WORK, man["source_root"], "lua", "entities")
    dst_root = os.path.join(ADDON, "lua", "entities")
    needed = set()
    for ents in man.get("extra_entities", {}).values():
        needed.update(ents)

    copied = 0
    for cls in sorted(needed):
        src = os.path.join(src_root, cls + ".lua")
        if os.path.isfile(src):
            os.makedirs(dst_root, exist_ok=True)
            shutil.copyfile(src, os.path.join(dst_root, cls + ".lua"))
            copied += 1
            continue

        folder = os.path.join(src_root, cls)
        if os.path.isdir(folder):
            for dirpath, _, files in os.walk(folder):
                for fn in files:
                    if not fn.endswith(".lua"):
                        continue
                    full = os.path.join(dirpath, fn)
                    rel = os.path.relpath(full, src_root)
                    dst = os.path.join(dst_root, rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copyfile(full, dst)
                    copied += 1
            continue

        log("ВНИМАНИЕ, сущность не найдена: %s" % cls)

    log("entity files copied: %d" % copied)


# --------------------------------------------------------------------------
# Сбор контента: звуки / модели, которые встречаются в новом оружии
# --------------------------------------------------------------------------

SOUND_FIELDS = """Primary.Sound Primary.SoundEmpty Secondary.Sound ReloadSound ReloadSoundEmpty
DeploySnd HolsterSnd AttackHit Attack2Hit AttackHitFlesh Attack2HitFlesh AttackSwing
SuicideSound hitSound hitSoundFlesh swingsound swingsound2 soundswing chainsaw""".split()

RE_SOUND = re.compile(r'["\']((?:sound/)?[A-Za-z0-9_\-/\.]+\.(?:wav|ogg|mp3))["\']')
RE_MODEL = re.compile(r'["\'](models/[^"\']+\.mdl)["\']')
RE_PARTICLE = re.compile(r'PrecacheParticleSystem\s*\(\s*["\']([^"\']+)["\']')


def z_city_known_refs():
    """Собираем все пути, которые уже упоминает обычный Z-City."""
    zdir = os.path.join(WORK, "z_city")
    sounds, models = set(), set()
    for dirpath, _, files in os.walk(zdir):
        for fn in files:
            if not fn.endswith(".lua"):
                continue
            try:
                text = read(os.path.join(dirpath, fn))
            except OSError:
                continue
            sounds.update(m.lower() for m in RE_SOUND.findall(text))
            models.update(m.lower() for m in RE_MODEL.findall(text))
    return sounds, models


def collect_content(man):
    """Возвращает (sounds, models), которые нужны новому оружию,
    но не упоминаются в обычном Z-City."""
    known_sounds, known_models = z_city_known_refs()

    src_root = os.path.join(WORK, man["source_root"], "lua", "weapons")
    new_sounds, new_models, particles = set(), set(), set()

    for entry in man["weapons"]:
        for f in weapon_files(src_root, entry["class"]):
            text = read(f)
            new_sounds.update(m for m in RE_SOUND.findall(text) if "models/" not in m)
            new_models.update(RE_MODEL.findall(text))
            particles.update(RE_PARTICLE.findall(text))

    # звуки/модели ближнего боя Remorseim
    melee_manifest = os.path.join(ROOT, "build", "melee_manifest.json")
    if os.path.isfile(melee_manifest):
        with open(melee_manifest, encoding="utf-8") as f:
            mm = json.load(f)
        base_src = os.path.join(WORK, mm["source_root"], mm["base"]["source"])
        texts = [read(base_src)] if os.path.isfile(base_src) else []
        for entry in mm["weapons"]:
            for f in weapon_files(src_root, entry["class"]):
                texts.append(read(f))
        for text in texts:
            new_sounds.update(m for m in RE_SOUND.findall(text) if "models/" not in m)
            new_models.update(RE_MODEL.findall(text))
            particles.update(RE_PARTICLE.findall(text))

    # модели и звуки, которые уже используются обычным Z-City, качать не надо
    sounds = sorted(s for s in new_sounds if s.lower() not in known_sounds)
    models = sorted(m for m in new_models if m.lower() not in known_models)
    return sounds, models, sorted(particles)


def normalize_sound_path(s):
    s = s.replace("\\", "/")
    if not s.lower().startswith("sound/"):
        s = "sound/" + s
    return s


def lua_list(name, items):
    lines = ["%s = {" % name]
    for it in items:
        lines.append("\t%r," % it)
    lines.append("}")
    return "\n".join(lines)


def write_content_manifest(man, sounds, models, particles):
    out = {
        "_comment": [
            "Список контента, который нужен оружию Remorseim и которого нет в обычном Z-City.",
            "Его ищет батник tools/ИщиКонтент.bat (и Steam Workshop Downloader / FastDL).",
        ],
        "particles": particles,
        "models": models,
        "sounds": [normalize_sound_path(s) for s in sounds],
    }
    path = os.path.join(ROOT, "content_manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # Lua-копия для сервера: аддон сам зарегистрирует файлы на скачивание
    srv_dir = os.path.join(ADDON, "lua", "autorun", "server")
    os.makedirs(srv_dir, exist_ok=True)
    lua_path = os.path.join(srv_dir, "sv_gunpack_content.lua")
    body = []
    body.append("-- АВТОГЕНЕРАЦИЯ: build/build_addon.py — не редактировать руками.")
    body.append("-- Список контента, которого нет в обычном Z-City.")
    body.append("REMORSEIM_GUNPACK = REMORSEIM_GUNPACK or {}")
    body.append("REMORSEIM_GUNPACK.Content = {")
    body.append("\tsounds = {")
    for s in out["sounds"]:
        body.append('\t\t%r,' % s)
    body.append("\t},")
    body.append("\tmodels = {")
    for m in out["models"]:
        body.append('\t\t%r,' % m)
    body.append("\t},")
    body.append("\tparticles = {")
    for p in out["particles"]:
        body.append('\t\t%r,' % p)
    body.append("\t},")
    body.append("}")
    with open(lua_path, "w", encoding="utf-8") as f:
        f.write("\n".join(body) + "\n")

    log("content manifest: %d sounds, %d models, %d particles"
        % (len(out["sounds"]), len(out["models"]), len(out["particles"])))
    return path


def main():
    if not os.path.isdir(WORK):
        log("Нет папки .work — сначала запустите tools/prepare_sources.bat "
            "(он распакует zip-архивы).")
        return 1

    man = load_manifest()

    if not os.path.isdir(os.path.join(WORK, man["source_root"])):
        log("Нет папки .work/%s — распакуйте 'remorseim main.zip'." % man["source_root"])
        return 1

    copy_weapons(man)
    copy_entities(man)

    # ближний бой — отдельно, со своей базой и своими классами
    import gen_melee  # noqa: E402
    sys.argv = ["gen_melee.py"]
    if gen_melee.main() != 0:
        log("ВНИМАНИЕ: не удалось сгенерировать ближний бой")

    sounds, models, particles = collect_content(man)
    write_content_manifest(man, sounds, models, particles)

    log("готово: addon/remorseim_gunpack")
    return 0


if __name__ == "__main__":
    sys.exit(main())
