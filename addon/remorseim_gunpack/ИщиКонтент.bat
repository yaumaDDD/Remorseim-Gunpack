@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title Remorseim Gunpack - поиск и чистка контента

rem Батник лежит прямо в папке аддона, поэтому корень — его же папка.
cd /d "%~dp0"

echo ==================================================================
echo   Remorseim Gunpack :: контент для НОВЫХ свепов
echo ==================================================================
echo.
echo   Папка аддона: %CD%
echo.
echo   Контент ищется ТОЛЬКО для новых оружий и ближнего боя Remorseim
echo   и раскладывается в три папки рядом с этим батником:
echo.
echo       models\      модели .mdl/.vvd/.vtx/.phy
echo       materials\   материалы .vmt/.vtf + иконки vgui
echo       sound\       звуки .wav/.ogg
echo.
echo   Лишнее (то, что не нужно ни одной модели/текстуре новых свепов)
echo   можно удалить пунктом 8 - оно считается по content_manifest.json.
echo.
echo ==================================================================
echo.

rem --- ищем Python -------------------------------------------------
set PY=
where py >nul 2>nul && set PY=py -3
if "%PY%"=="" ( where python >nul 2>nul && set PY=python )
if "%PY%"=="" (
    echo [ОШИБКА] Python не найден.
    echo Установите Python 3 с https://python.org и запустите снова.
    echo При установке поставьте галочку "Add Python to PATH".
    pause
    exit /b 2
)

set SCRIPT=%~dp0tools\find_content.py
if not exist "%SCRIPT%" (
    echo [ОШИБКА] Не найден tools\find_content.py рядом с батником.
    pause
    exit /b 2
)

echo Python:
%PY% --version
echo.

rem --- путь к Garry's Mod ------------------------------------------
set GMPATH=
if not "%GMOD_PATH%"=="" set GMPATH=%GMOD_PATH%
if "%GMPATH%"=="" (
    set /p GMPATH="Путь к папке garrysmod (Enter - найти автоматически): "
)
if not "%GMPATH%"=="" set GMOD_PATH=%GMPATH%
echo.

:menu
echo ------------------------------------------------------------------
echo   Что делаем?
echo ------------------------------------------------------------------
echo   1 - Все три папки: models + materials + sound
echo   2 - Только models
echo   3 - Только materials
echo   4 - Только sound
echo   5 - Пересобрать список контента (content_manifest.json)
echo   6 - Проверить, чего не хватает
echo   7 - Воркшоп-аддоны с контентом
echo   8 - УДАЛИТЬ лишнее из models/materials/sound
echo   9 - Показать, что будет удалено (без удаления)
echo   0 - Выход
echo ------------------------------------------------------------------
set CHOICE=
set /p CHOICE="Выбор [1]: "
if "%CHOICE%"=="" set CHOICE=1

if "%CHOICE%"=="0" exit /b 0
if "%CHOICE%"=="1" goto all_content
if "%CHOICE%"=="2" goto only_models
if "%CHOICE%"=="3" goto only_materials
if "%CHOICE%"=="4" goto only_sound
if "%CHOICE%"=="5" goto rebuild
if "%CHOICE%"=="6" goto check
if "%CHOICE%"=="7" goto workshop
if "%CHOICE%"=="8" goto prune
if "%CHOICE%"=="9" goto prune_dry
echo Не понял выбор "%CHOICE%".
echo.
goto menu

:all_content
echo.
echo [1/2] Подготовка: список контента...
%PY% "%SCRIPT%" build
if errorlevel 1 goto fail
echo.
echo [2/2] Поиск и раскладка: models + materials + sound...
%PY% "%SCRIPT%" content
set RESULT=%errorlevel%
goto done

:only_models
echo.
%PY% "%SCRIPT%" build
if errorlevel 1 goto fail
echo.
echo Поиск и раскладка: только models...
%PY% "%SCRIPT%" content --only models
set RESULT=%errorlevel%
goto done

:only_materials
echo.
%PY% "%SCRIPT%" build
if errorlevel 1 goto fail
echo.
echo Поиск и раскладка: только materials...
%PY% "%SCRIPT%" content --only materials
set RESULT=%errorlevel%
goto done

:only_sound
echo.
%PY% "%SCRIPT%" build
if errorlevel 1 goto fail
echo.
echo Поиск и раскладка: только sound...
%PY% "%SCRIPT%" content --only sounds
set RESULT=%errorlevel%
goto done

:rebuild
echo.
%PY% "%SCRIPT%" build
set RESULT=%errorlevel%
goto done

:check
echo.
%PY% "%SCRIPT%" scan
set RESULT=%errorlevel%
goto done

:workshop
echo.
%PY% "%SCRIPT%" workshop
set RESULT=0
goto done

:prune_dry
echo.
echo Показываю, что лишнее (ничего не удаляю)...
%PY% "%SCRIPT%" prune --dry-run
set RESULT=0
goto done

:prune
echo.
echo ВНИМАНИЕ: сейчас будут УДАЛЕНЫ файлы из models/materials/sound,
echo которых нет в content_manifest.json.
echo.
set CONFIRM=
set /p CONFIRM="Точно удалить? (yes/no) [no]: "
if /i not "%CONFIRM%"=="yes" (
    echo Отменено.
    goto menu
)
echo.
%PY% "%SCRIPT%" prune
set RESULT=%errorlevel%
goto done

:done
echo.
if "%RESULT%"=="0" (
    echo ==================================================================
    echo   ГОТОВО.
    echo ==================================================================
) else (
    echo ==================================================================
    echo   ГОТОВО, но части контента нет на диске.
    echo   Список выше; ещё раз можно подписаться на воркшоп-аддоны (пункт 7).
    echo ==================================================================
)
echo.
echo Папка аддона: %CD%
echo Список:       content_manifest.json
echo.
pause
exit /b 0

:fail
echo.
echo [ОШИБКА] Не удалось. Смотрите сообщения выше.
pause
exit /b 1
