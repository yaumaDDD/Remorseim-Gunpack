@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title Remorseim Gunpack - поиск контента

cd /d "%~dp0.."

echo ==================================================================
echo   Remorseim Gunpack :: поиск контента для НОВЫХ свепов
echo ==================================================================
echo.
echo   Контент ищется ТОЛЬКО для новых оружий и ближнего боя Remorseim
echo   и раскладывается в три папки аддона:
echo.
echo       addon\remorseim_gunpack\models\      модели .mdl/.vvd/.vtx/.phy
echo       addon\remorseim_gunpack\materials\   материалы .vmt/.vtf + иконки
echo       addon\remorseim_gunpack\sound\       звуки .wav/.ogg
echo.
echo   Старое оружие Z-City не трогается - его контент уже на месте.
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
echo   5 - Пересобрать аддон (структура папок + content_manifest.json)
echo   6 - Проверить, чего не хватает
echo   7 - Воркшоп-аддоны с контентом
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
echo Не понял выбор "%CHOICE%".
echo.
goto menu

:all_content
echo.
echo [1/2] Подготовка: сборка аддона и списка контента...
%PY% tools\find_content.py build
if errorlevel 1 goto fail
echo.
echo [2/2] Поиск и раскладка: models + materials + sound...
%PY% tools\find_content.py content
set RESULT=%errorlevel%
goto done

:only_models
echo.
echo [1/2] Подготовка: сборка аддона и списка контента...
%PY% tools\find_content.py build
if errorlevel 1 goto fail
echo.
echo [2/2] Поиск и раскладка: только models...
%PY% tools\find_content.py content --only models
set RESULT=%errorlevel%
goto done

:only_materials
echo.
echo [1/2] Подготовка: сборка аддона и списка контента...
%PY% tools\find_content.py build
if errorlevel 1 goto fail
echo.
echo [2/2] Поиск и раскладка: только materials...
%PY% tools\find_content.py content --only materials
set RESULT=%errorlevel%
goto done

:only_sound
echo.
echo [1/2] Подготовка: сборка аддона и списка контента...
%PY% tools\find_content.py build
if errorlevel 1 goto fail
echo.
echo [2/2] Поиск и раскладка: только sound...
%PY% tools\find_content.py content --only sounds
set RESULT=%errorlevel%
goto done

:rebuild
echo.
%PY% tools\find_content.py build
set RESULT=%errorlevel%
goto done

:check
echo.
%PY% tools\find_content.py scan
set RESULT=%errorlevel%
goto done

:workshop
echo.
%PY% tools\find_content.py workshop
set RESULT=0
goto done

:done
echo.
if "%RESULT%"=="0" (
    echo ==================================================================
    echo   ГОТОВО: всё, что нужно, найдено и разложено по папкам.
    echo ==================================================================
) else (
    echo ==================================================================
    echo   ГОТОВО, но части контента нет на диске.
    echo   Список выше; ещё раз можно подписаться на воркшоп-аддоны (пункт 7).
    echo ==================================================================
)
echo.
echo Аддон:  addon\remorseim_gunpack
echo Список: content_manifest.json
echo.
pause
exit /b 0

:fail
echo.
echo [ОШИБКА] Сборка не удалась. Смотрите сообщения выше.
pause
exit /b 1
