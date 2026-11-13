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
RE_MODEL = re.compile(r'["\'](models/[^"\']+\.(?:mdl|vvd|vtx|phy|ani))["\']')
RE_PARTICLE = re.compile(r'PrecacheParticleSystem\s*\(\s*["\']([^"\']+)["\']')
# материалы: Material("vgui/x.png"), Material("zbattle/blood")
RE_MATERIAL = re.compile(r'\b(?:Material|CreateMaterial)\(\s*["\']([^"\']+)["\']')


def z_city_known_refs():
    """Собираем все пути, которые уже упоминает обычный Z-City."""
    zdir = os.path.join(WORK, "z_city")
    sounds, models, materials = set(), set(), set()
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
            materials.update(m.lower() for m in RE_MATERIAL.findall(text))
    return sounds, models, materials


def content_sources(man):
    """Все lua-файлы, которые попадут в аддон: огнестрел + база melee + меlee."""
    src_root = os.path.join(WORK, man["source_root"], "lua", "weapons")
    texts = []

    for entry in man["weapons"]:
        for f in weapon_files(src_root, entry["class"]):
            texts.append(read(f))

    melee_manifest = os.path.join(ROOT, "build", "melee_manifest.json")
    if os.path.isfile(melee_manifest):
        with open(melee_manifest, encoding="utf-8") as f:
            mm = json.load(f)
        base_src = os.path.join(WORK, mm["source_root"], mm["base"]["source"])
        if os.path.isfile(base_src):
            texts.append(read(base_src))
        for entry in mm["weapons"]:
            for f in weapon_files(src_root, entry["class"]):
                texts.append(read(f))

    # скрипты, которые лежат в аддоне рядом с оружием (хитстоп, синяки)
    lua_dir = os.path.join(ADDON, "lua")
    for dirpath, _, files in os.walk(lua_dir):
        if os.sep + "weapons" in dirpath:
            continue
        for fn in files:
            if fn.endswith(".lua"):
                texts.append(read(os.path.join(dirpath, fn)))

    return texts


def material_path(name):
    """'vgui/x.png' -> 'materials/vgui/x.png'; 'zbattle/blood' -> 'materials/zbattle/blood.vmt'."""
    name = name.strip().replace("\\", "/").lstrip("/")
    if name.lower().startswith("materials/"):
        return name
    if not os.path.splitext(name)[1]:
        name += ".vmt"
    return "materials/" + name


def expand_model(path):
    """Для .mdl нужны ещё vvd/vtx/phy — без них модель не загрузится."""
    if not path.lower().endswith(".mdl"):
        return [path]
    base = path[:-4]
    return [path, base + ".vvd", base + ".vtx", base + ".phy"]


def collect_content(man):
    """Возвращает (sounds, models, materials, particles) для новых свep'ов,
    которых нет в обычном Z-City."""
    known_sounds, known_models, known_materials = z_city_known_refs()

    new_sounds, new_models, new_materials, particles = set(), set(), set(), set()

    for text in content_sources(man):
        new_sounds.update(m for m in RE_SOUND.findall(text) if "models/" not in m)
        for mdl in RE_MODEL.findall(text):
            new_models.update(expand_model(mdl))
        for mat in RE_MATERIAL.findall(text):
            # служебные материалы движка не качаем
            if mat.lower() in ("vgui/white", "vgui/black", "cable/cable2",
                               "debugempty", "color", "vgui/white_additive"):
                continue
            new_materials.add(material_path(mat))
        particles.update(RE_PARTICLE.findall(text))

    # модели, которые уже используются обычным Z-City, качать не надо
    known_norm = set()
    for k in known_sounds:
        k = k.replace("\\", "/").lower()
        known_norm.add(k)
        known_norm.add(k[len("sound/"):] if k.startswith("sound/") else k)

    sounds = sorted({
        s for s in (normalize_sound_path(x) for x in new_sounds)
        if s.lower() not in known_norm and s.lower()[len("sound/"):] not in known_norm
    })
    models = sorted(m for m in new_models if m.lower() not in known_models)
    materials = sorted(m for m in new_materials if m.lower() not in known_materials)
    return sounds, models, materials, sorted(particles)


def content_dir_name(path):
    """Куда класть файл: 'models', 'materials' или 'sound' (внутри аддона)."""
    p = path.lower()
    if p.startswith("models/"):
        return "models"
    if p.startswith("materials/"):
        return "materials"
    return "sound"


def write_placeholder_dirs(sounds, models, materials):
    """Создаёт в аддоне пустые (но существующие) папки models/ materials/ sound/
    с README внутри — контент туда кладёт батник."""
    roots = {
        "models": models,
        "materials": materials,
        "sound": sounds,
    }
    texts = {
        "models": "Сюда батник складывает .mdl/.vvd/.vtx/.phy для НОВЫХ свep'ов Remorseim.\n"
                  "Пути внутри повторяют garrysmod/, например models/weapons/...\n"
                  "Файлы отсюда аддон сам раздаёт клиентам (resource.AddSingleFile).\n",
        "materials": "Сюда батник складывает .vmt/.vtf для НОВЫХ свep'ов Remorseim\n"
                     "(иконки в vgui/, материалы моделей и т.п.).\n"
                     "Пути внутри повторяют garrysmod/, например materials/vgui/...\n",
        "sound": "Сюда батник складывает .wav/.ogg для НОВЫХ свep'ов Remorseim.\n"
                 "Пути внутри повторяют garrysmod/, например sound/axe/...\n",
    }
    for kind, items in roots.items():
        d = os.path.join(ADDON, kind)
        os.makedirs(d, exist_ok=True)
        keep = os.path.join(d, "README.txt")
        if not os.path.isfile(keep):
            with open(keep, "w", encoding="utf-8", newline="\r\n") as f:
                f.write(texts[kind])
                f.write("\nВсего по списку: %d файл(ов).\n" % len(items))
                f.write("Лишнее удаляет ИщиКонтент.bat - пункт 8 (или 9, чтобы сначала посмотреть).\n")


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


def write_content_manifest(man, sounds, models, materials, particles):
    """Пишет content_manifest.json + lua-копию для сервера.

    Пути в манифесте — как в garrysmod/ (models/..., materials/..., sound/...),
    чтобы их можно было один-в-один положить в FastDL.
    """
    out = {
        "_comment": [
            "Контент, который нужен НОВЫМ свep'ам Remorseim и которого нет в обычном Z-City.",
            "models/ materials/ sound/ — пути внутри garrysmod/ и внутри аддона.",
            "Ищет и раскладывает: ИщиКонтент.bat в папке аддона (tools/find_content.py content).",
            "Файлы уже лежат в addon/remorseim_gunpack/{models,materials,sound}/ —",
            "если они там есть, качать ничего не нужно.",
        ],
        "howto": {
            "автоматически": "ИщиКонтент.bat в папке аддона -> пункт 1",
            "вручную": "найти по путям в своей папке garrysmod/workshop и скопировать",
            "куда": "models/, materials/, sound/ рядом с батником — структура сохраняется",
            "лишнее": "ИщиКонтент.bat -> пункт 8 удаляет всё, чего нет в этом списке",
        },
        "counts": {
            "models": len(models),
            "materials": len(materials),
            "sounds": len(sounds),
            "particles": len(particles),
        },
        "models": models,
        "materials": materials,
        "sounds": sounds,
        "particles": particles,
    }
    path = os.path.join(ADDON, "content_manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # Lua-копия для сервера: аддон сам зарегистрирует файлы на скачивание
    srv_dir = os.path.join(ADDON, "lua", "autorun", "server")
    os.makedirs(srv_dir, exist_ok=True)
    lua_path = os.path.join(srv_dir, "sv_gunpack_content.lua")

    body = [
        "-- АВТОГЕНЕРАЦИЯ: build/build_addon.py — не редактировать руками.",
        "-- Контент, которого нет в обычном Z-City, только для НОВЫХ свep'ов Remorseim.",
        "-- Физические файлы лежат в addon/remorseim_gunpack/{models,materials,sound}/",
        "REMORSEIM_GUNPACK = REMORSEIM_GUNPACK or {}",
        "REMORSEIM_GUNPACK.Content = {",
    ]
    for key in ("models", "materials", "sounds", "particles"):
        body.append("\t%s = {" % key)
        for item in out[key]:
            body.append("\t\t%r," % item)
        body.append("\t},")
    body.append("}")
    with open(lua_path, "w", encoding="utf-8") as f:
        f.write("\n".join(body) + "\n")

    log("содержимое: %d моделей, %d материалов, %d звуков, %d частиц"
        % (len(models), len(materials), len(sounds), len(particles)))
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

    sounds, models, materials, particles = collect_content(man)
    write_content_manifest(man, sounds, models, materials, particles)
    write_placeholder_dirs(sounds, models, materials)

    log("готово: addon/remorseim_gunpack")
    return 0


if __name__ == "__main__":
    sys.exit(main())
