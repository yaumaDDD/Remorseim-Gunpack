#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remorseim Gunpack :: find_content.py
Поиск контента (моделей/звуков) для оружия Remorseim.

Зачем: контент оружия весит много, и заливать его в GitHub нельзя
(лимит на размер файла и на размер репозитория). Поэтому аддон содержит
только lua-скрипты, а контент игроки/сервер докачивают воркшоп-аддоном
или через FastDL. Этот скрипт говорит, ЧТО именно нужно и ЧЕГО не хватает.

Режимы (запускается из ИщиКонтент.bat):
    prepare    — распаковать zip-архивы в .work/
    build      — собрать аддон (копирование lua + content_manifest.json)
    scan       — проверить, каких моделей/звуков не хватает на диске
    workshop   — вывести id воркшоп-аддонов, которые нужно подключить
    all        — prepare + build + scan

Коды возврата: 0 — всё хорошо, 1 — чего-то не хватает, 2 — ошибка.
"""

import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, ".work")
ADDON = os.path.join(ROOT, "addon", "remorseim_gunpack")
CONTENT = os.path.join(ROOT, "content_manifest.json")

# Воркшоп-аддоны, которые Z-City и Remorseim тянут как зависимости.
# 3657897364 — основной контент Z-City (модели/звуки/партиклы)
# 3257937532 — distac content
# 3759394449 — релиз Remorseim (см. README архива Remorseim)
WORKSHOP_IDS = [
    ("3657897364", "Z-City — основной контент (обязателен)"),
    ("3257937532", "Z-City — distac content (обязателен)"),
    ("3759394449", "Remorseim — релиз (контент оружия Remorseim)"),
]


def log(msg=""):
    print(msg)

# В .bat вывод идёт через chcp 65001; на всякий случай не падаем на cp1251
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def hr(ch="=", n=66):
    log(ch * n)


# --------------------------------------------------------------------------
# prepare
# --------------------------------------------------------------------------

def prepare():
    zips = [f for f in os.listdir(ROOT) if f.lower().endswith(".zip")]
    if not zips:
        log("В корне репозитория нет zip-архивов.")
        log("Положите рядом с батником 'Z-City.zip' и 'remorseim main.zip'.")
        return False

    os.makedirs(WORK, exist_ok=True)
    for z in zips:
        log("  распаковка: " + z)
        with zipfile.ZipFile(os.path.join(ROOT, z)) as zf:
            zf.extractall(WORK)
    return True


# --------------------------------------------------------------------------
# build (делегируем build_addon.py)
# --------------------------------------------------------------------------

def build():
    sys.path.insert(0, os.path.join(ROOT, "build"))
    import build_addon  # noqa: E402

    sys.argv = ["build_addon.py"]
    return build_addon.main() == 0


# --------------------------------------------------------------------------
# scan
# --------------------------------------------------------------------------

GARRYS_MOD = [
    r"C:\Program Files (x86)\Steam\steamapps\common\GarrysMod\garrysmod",
    r"C:\Program Files\Steam\steamapps\common\GarrysMod\garrysmod",
    r"D:\Steam\steamapps\common\GarrysMod\garrysmod",
    r"D:\SteamLibrary\steamapps\common\GarrysMod\garrysmod",
    r"E:\SteamLibrary\steamapps\common\GarrysMod\garrysmod",
    os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/GarrysMod/garrysmod"),
    os.path.expanduser("~/.steam/steam/steamapps/common/GarrysMod/garrysmod"),
    os.path.expanduser("~/.local/share/Steam/steamapps/common/GarrysMod/garrysmod"),
]


def find_garrysmod():
    env = os.environ.get("GMOD_PATH")
    if env and os.path.isdir(env):
        return env
    for p in GARRYS_MOD:
        if os.path.isdir(p):
            return p
    return None


def load_content():
    if not os.path.isfile(CONTENT):
        log("Нет content_manifest.json — сначала соберите аддон (пункт 2).")
        return None
    with open(CONTENT, encoding="utf-8") as f:
        return json.load(f)


def exists_in_gmod(gmod, path):
    """path вида 'sound/xxx/y.wav' или 'models/...mdl'."""
    p = path.replace("\\", "/")
    if p.lower().startswith("sound/"):
        return os.path.isfile(os.path.join(gmod, p)) or os.path.isfile(
            os.path.join(gmod, p[len("sound/"):]))
    return os.path.isfile(os.path.join(gmod, p))


def scan():
    data = load_content()
    if not data:
        return 2

    gmod = find_garrysmod()
    if not gmod:
        hr()
        log("Не нашёл папку garrysmod.")
        log("Укажите путь вручную в переменной окружения GMOD_PATH, например:")
        log('    set GMOD_PATH=C:\\Program Files (x86)\\Steam\\steamapps\\common\\GarrysMod\\garrysmod')
        hr()
        log("Список того, что нужно скачать, всё равно доступен:")
        log("    content_manifest.json")
        return 1

    log("garrysmod: " + gmod)
    missing = {"sounds": [], "models": [], "particles": []}

    for kind in ("sounds", "models"):
        for path in data.get(kind, []):
            if not exists_in_gmod(gmod, path):
                missing[kind].append(path)

    total = sum(len(data.get(k, [])) for k in ("sounds", "models", "particles"))
    miss = sum(len(v) for v in missing.values())

    hr()
    log("Проверено файлов: %d" % total)
    log("Не найдено:       %d" % miss)
    hr()

    if missing["models"]:
        log("\nМОДЕЛИ (положите в garrysmod/models/...):")
        for m in missing["models"]:
            log("  " + m)

    if missing["sounds"]:
        log("\nЗВУКИ (положите в garrysmod/sound/...):")
        for s in missing["sounds"]:
            log("  " + s)

    if miss:
        hr()
        log("Проще всего — подписаться на воркшоп-аддоны (пункт 4).")
        return 1

    log("Все модели и звуки на месте.")
    return 0


# --------------------------------------------------------------------------
# workshop
# --------------------------------------------------------------------------

def workshop():
    hr()
    log("КАК ЗАКРЫТЬ КОНТЕНТ (без заливки в GitHub)")
    hr()
    log("В GitHub нельзя положить тяжёлый контент, поэтому аддон везёт только")
    log("скрипты, а модели/звуки берутся из воркшопа. Подпишитесь на:")
    log()
    for wid, desc in WORKSHOP_IDS:
        log("  %s  — %s" % (wid, desc))
        log("     https://steamcommunity.com/sharedfiles/filedetails/?id=" + wid)
    log()
    log("Для ВЫДЕЛЕННОГО сервера контент раздаётся так:")
    log("  1) в collection ставятся эти три аддона;")
    log("  2) либо FastDL: файлы из content_manifest.json кладутся на http-хост,")
    log("     а в server.cfg прописывается sv_downloadurl.")
    log()
    log("Точный список нужных файлов: content_manifest.json")
    return 0


# --------------------------------------------------------------------------

def main(argv):
    mode = (argv[1] if len(argv) > 1 else "all").lower()

    if mode == "prepare":
        return 0 if prepare() else 2
    if mode == "build":
        return 0 if build() else 2
    if mode == "scan":
        return scan()
    if mode == "workshop":
        return workshop()

    # all
    log("Шаг 1/3 — распаковка архивов")
    if not prepare():
        return 2
    log("Шаг 2/3 — сборка аддона")
    if not build():
        return 2
    log("Шаг 3/3 — проверка контента")
    rc = scan()
    workshop()
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
