@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title Remorseim Gunpack - поиск контента

cd /d "%~dp0.."

echo ==================================================================
echo   Remorseim Gunpack :: поиск контента для оружия
echo ==================================================================
echo.
echo   Этот батник собирает аддон и проверяет, каких моделей и звуков
echo   не хватает для оружия Remorseim.
echo.
echo   ВАЖНО: сам контент (модели/звуки) в GitHub не кладётся - он
echo   весит слишком много. Аддон содержит только lua-скрипты, а
echo   контент подтягивается из воркшоп-аддонов.
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

echo [1/4] Python: 
%PY% --version
echo.

echo [2/4] Распаковка zip-архивов и сборка аддона...
%PY% tools\find_content.py build
if errorlevel 1 goto fail
echo.

echo [3/4] Проверка контента в Garry's Mod...
set /p GMPATH="Путь к папке garrysmod (Enter - найти автоматически): "
if not "%GMPATH%"=="" set GMOD_PATH=%GMPATH%
%PY% tools\find_content.py scan
set SCAN_RESULT=%errorlevel%
echo.

echo [4/4] Воркшоп-аддоны с контентом
%PY% tools\find_content.py workshop
echo.

if "%SCAN_RESULT%"=="0" (
    echo ==================================================================
    echo   ГОТОВО: весь контент на месте.
    echo ==================================================================
) else (
    echo ==================================================================
    echo   ГОТОВО, но части контента нет.
    echo   Подпишитесь на воркшоп-аддоны выше - этого достаточно.
    echo ==================================================================
)

echo.
echo Аддон лежит в: addon\remorseim_gunpack
echo Список нужных файлов: content_manifest.json
echo.
pause
exit /b 0

:fail
echo.
echo [ОШИБКА] Сборка не удалась. Смотрите сообщения выше.
pause
exit /b 1
