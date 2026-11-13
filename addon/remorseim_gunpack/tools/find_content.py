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
    content    — найти контент новых свep'ов и разложить в models/ materials/ sound/
                 (можно ограничить: content --only models|materials|sounds)
    prune      — удалить из models/ materials/ sound/ всё, что не нужно свep'ам
                 (--dry-run — только показать, что будет удалено)
    scan       — проверить, каких моделей/звуков не хватает на диске
    workshop   — вывести id воркшоп-аддонов, которые нужно подключить
    all        — prepare + build + content + scan

Коды возврата: 0 — всё хорошо, 1 — чего-то не хватает, 2 — ошибка.
"""

import json
import os
import re
import sys
import zipfile

# Скрипт лежит ВНУТРИ аддона: <repo>/addon/remorseim_gunpack/tools/find_content.py
ADDON = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(ADDON))
WORK = os.path.join(REPO, ".work")
CONTENT = os.path.join(ADDON, "content_manifest.json")

# Папки аддона, куда складывается контент: ровно те, что видит Garry's Mod
CONTENT_DIRS = ("models", "materials", "sound")

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
    zips = [f for f in os.listdir(REPO) if f.lower().endswith(".zip")]
    if not zips:
        if os.path.isdir(WORK):
            log("  zip-архивов нет, но .work/ уже распакован — идём дальше.")
            return True
        log("В корне репозитория нет zip-архивов.")
        log("Положите рядом с батником 'Z-City.zip' и 'remorseim main.zip'.")
        return False

    os.makedirs(WORK, exist_ok=True)
    for z in zips:
        log("  распаковка: " + z)
        with zipfile.ZipFile(os.path.join(REPO, z)) as zf:
            zf.extractall(WORK)
    return True


# --------------------------------------------------------------------------
# build (делегируем build_addon.py)
# --------------------------------------------------------------------------

def build():
    sys.path.insert(0, os.path.join(REPO, "build"))
    import build_addon  # noqa: E402

    sys.argv = ["build_addon.py"]
    return build_addon.main() == 0


# --------------------------------------------------------------------------
# content — поиск и раскладка контента по папкам аддона
# --------------------------------------------------------------------------

def content_dst(path):
    """'models/x.mdl' -> addon/remorseim_gunpack/models/x.mdl"""
    return os.path.join(ADDON, path.replace("/", os.sep))


def content_dirs():
    for kind in CONTENT_DIRS:
        os.makedirs(os.path.join(ADDON, kind), exist_ok=True)


def workshop_content_roots(gmod):
    """Папки, где Steam держит распакованный контент воркшопа."""
    roots = []
    if gmod:
        for sub in ("addons", "workshop"):
            d = os.path.join(gmod, sub)
            if os.path.isdir(d):
                roots.append(d)
    # отдельный steamapps/workshop/content/4000 — если есть
    steamapps = os.path.dirname(gmod) if gmod else None
    while steamapps and os.path.basename(steamapps) not in ("steamapps", "") and "steamapps" not in steamapps.lower():
        parent = os.path.dirname(steamapps)
        if parent == steamapps:
            break
        steamapps = parent
    if steamapps:
        for cand in (
            os.path.join(steamapps, "workshop", "content", "4000"),
            os.path.join(os.path.dirname(steamapps), "workshop", "content", "4000"),
        ):
            if os.path.isdir(cand):
                roots.append(cand)
    return roots


_INDEX = {}
AMBIGUOUS = []


def build_index(roots):
    """Один раз обходим garrysmod + воркшоп и запоминаем все файлы по имени.

    Полный обход на каждый файл был бы слишком долгим: манифест содержит
    сотни путей, а воркшоп — десятки тысяч файлов.
    """
    if _INDEX:
        return _INDEX
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fn in filenames:
                _INDEX.setdefault(fn.lower(), []).append(os.path.join(dirpath, fn))
    return _INDEX


def find_source_file(roots, relpath):
    """Ищем файл по относительному пути в garrysmod и в папках воркшопа."""
    rel = relpath.replace("\\", "/")
    # 1) точный путь от корня garrysmod — самый частый случай
    for root in roots:
        direct = os.path.join(root, rel.replace("/", os.sep))
        if os.path.isfile(direct):
            return direct

    # 2) поиск по имени файла среди проиндексированных
    base = os.path.basename(rel).lower()
    candidates = build_index(roots).get(base) or []
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        return None

    # 3) если несколько — предпочитаем тот, у которого совпадает хвост пути
    tail = rel.lower().replace("/", os.sep)
    for full in candidates:
        if full.lower().endswith(tail):
            return full

    # 4) хвост не совпал: имён вроде w.mdl в воркшопе десятки, поэтому берём
    #    файл, у которого совпадает хотя бы папка-родитель, иначе не угадываем
    parent = os.path.basename(os.path.dirname(rel)).lower()
    if parent:
        for full in candidates:
            if parent in full.lower().replace("\\", "/").split("/")[-2:-1]:
                AMBIGUOUS.append(rel)
                return full

    AMBIGUOUS.append(rel)
    return None


def content(only=None):
    """Ищет файлы из content_manifest.json и раскладывает их в папки аддона.

    only — список категорий ('models', 'materials', 'sounds') или None (все).
    """
    data = load_content()
    if not data:
        return 2, 0, 0

    content_dirs()

    gmod = find_garrysmod()
    roots = []
    if gmod:
        roots.append(gmod)
        log("garrysmod: " + gmod)
    ws = workshop_content_roots(gmod)
    if ws:
        log("воркшоп:   %d папк(а/и)" % len(ws))
        roots.extend(ws)
    if not roots:
        hr()
        log("Не нашёл ни garrysmod, ни воркшоп-контент.")
        log("Укажите путь вручную: set GMOD_PATH=...\\garrysmod")
        hr()
        return 1, 0, 0

    copied, found, missing = 0, [], []

    for kind in ("models", "materials", "sounds"):
        if only and kind not in only:
            continue
        items = data.get(kind, [])
        local_missing = []
        for rel in items:
            src = find_source_file(roots, rel)
            if not src:
                local_missing.append(rel)
                continue
            dst = content_dst(rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.isfile(dst) and os.path.getsize(dst) == os.path.getsize(src):
                found.append(rel)
                continue
            import shutil
            shutil.copyfile(src, dst)
            copied += 1
            found.append(rel)
        missing.extend(local_missing)
        log("  %-10s найдено %3d / %3d" % (kind, len(items) - len(local_missing), len(items)))

    hr()
    log("Скопировано в аддон: %d" % copied)
    log("Уже было на месте:   %d" % (len(found) - copied))
    log("Не найдено:          %d" % len(missing))
    if AMBIGUOUS:
        log("Неоднозначное имя:   %d (файл с таким именем есть, но путь не совпал)" % len(AMBIGUOUS))
    hr()

    if AMBIGUOUS:
        log("Проверьте глазами — имя файла встречается у разных моделей:")
        for a in AMBIGUOUS[:15]:
            log("  " + a)
        hr()

    if missing:
        log("Этого нет ни в garrysmod, ни в воркшопе — докачайте:")
        for m in missing[:40]:
            log("  " + m)
        if len(missing) > 40:
            log("  ... и ещё %d, полный список в content_manifest.json" % (len(missing) - 40))
        hr()

    return (0 if not missing else 1), len(found), len(missing)


# --------------------------------------------------------------------------
# prune — удалить из папок контента всё, что не нужно новым свep'ам
# --------------------------------------------------------------------------

def wanted_set(data):
    """Множество путей, которые реально нужны (в нижнем регистре)."""
    wanted = set()
    for kind in ("models", "materials", "sounds"):
        for rel in data.get(kind, []):
            wanted.add(rel.replace("\\", "/").lower())
    return wanted


def is_engine_whitelisted(rel):
    """Служебное, что не относится к оружию, но и удалять не надо."""
    low = rel.lower()
    return os.path.basename(low) in ("readme.txt", ".gitkeep")


def prune(dry_run=False):
    """Проходит по models/, materials/, sound/ и удаляет лишнее.

    «Лишнее» = файл, которого нет в content_manifest.json, то есть он не
    нужен ни одной модели, текстуре или звуку новых свep'ов.
    """
    data = load_content()
    if not data:
        return 2, 0, 0

    wanted = wanted_set(data)
    removed, kept, size_freed = 0, 0, 0

    for kind in CONTENT_DIRS:
        root = os.path.join(ADDON, kind)
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, ADDON).replace(os.sep, "/")

                if rel.lower() not in wanted and not is_engine_whitelisted(rel):
                    try:
                        sz = os.path.getsize(full)
                    except OSError:
                        sz = 0
                    if dry_run:
                        log("  [показать] " + rel)
                    else:
                        try:
                            os.remove(full)
                        except OSError:
                            continue
                        log("  удалён: " + rel)
                    removed += 1
                    size_freed += sz
                else:
                    kept += 1

        # пустые папки после чистки
        if not dry_run:
            for dirpath, dirnames, filenames in os.walk(root, topdown=False):
                if dirpath == root:
                    continue
                if not os.listdir(dirpath):
                    try:
                        os.rmdir(dirpath)
                    except OSError:
                        pass

    hr()
    if dry_run:
        log("Лишнего: %d файл(ов), нужных: %d" % (removed, kept))
        log("Это только показ. Для удаления запустите без --dry-run.")
    else:
        log("Удалено лишнего: %d файл(ов) (%.1f МБ)" % (removed, size_freed / 1048576.0))
        log("Оставлено нужного: %d" % kept)
    hr()
    return 0, removed, kept


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
    """path вида 'sound/xxx/y.wav', 'models/...mdl', 'materials/...vmt'.

    Сначала смотрим в самом аддоне (туда контент складывает режим content),
    потом в garrysmod/ и воркшопе.
    """
    if os.path.isfile(content_dst(path)):
        return True
    p = path.replace("\\", "/")
    if not gmod:
        return False
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
        log("Не нашёл папку garrysmod — проверяю только папки самого аддона.")
        log("Указать путь вручную: set GMOD_PATH=C:\\...\\GarrysMod\\garrysmod")
        hr()

    log("garrysmod: " + gmod)
    missing = {"sounds": [], "models": [], "materials": [], "particles": []}

    for kind in ("sounds", "models", "materials"):
        for path in data.get(kind, []):
            if not exists_in_gmod(gmod, path):
                missing[kind].append(path)

    total = sum(len(data.get(k, [])) for k in ("sounds", "models", "materials", "particles"))
    miss = sum(len(v) for v in missing.values())

    hr()
    log("Проверено файлов: %d" % total)
    log("Не найдено:       %d" % miss)
    hr()

    if missing["models"]:
        log("\nМОДЕЛИ (addon/remorseim_gunpack/models/...):")
        for m in missing["models"]:
            log("  " + m)

    if missing["materials"]:
        log("\nМАТЕРИАЛЫ (addon/remorseim_gunpack/materials/...):")
        for m in missing["materials"]:
            log("  " + m)

    if missing["sounds"]:
        log("\nЗВУКИ (addon/remorseim_gunpack/sound/...):")
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
    if mode == "prune":
        dry = "--dry-run" in argv or "-n" in argv
        return prune(dry)[0]
    if mode == "content":
        only = None
        if "--only" in argv:
            i = argv.index("--only")
            if i + 1 < len(argv):
                only = [x.strip().lower() for x in argv[i + 1].split(",") if x.strip()]
        return content(only)[0]
    if mode == "scan":
        return scan()
    if mode == "workshop":
        return workshop()

    # all
    log("Шаг 1/4 — распаковка архивов")
    if not prepare():
        return 2
    log("Шаг 2/4 — сборка аддона")
    if not build():
        return 2
    log("Шаг 3/4 — поиск и раскладка контента в models/ materials/ sound/")
    rc_content = content()[0]
    log("Шаг 4/4 — проверка контента")
    rc = scan()
    workshop()
    return rc_content if rc_content else rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
