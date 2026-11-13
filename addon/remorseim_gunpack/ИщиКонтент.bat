@echo off
chcp 65001>nul
setlocal EnableDelayedExpansion
title Remorseim Gunpack - контент
cd /d "%~dp0"

rem ==================================================================
rem  Чистый batch: ни Python, ни Node, ничего доустанавливать не надо.
rem  Списки нужных файлов лежат рядом, в tools\:
rem      models.txt     models\weapons\hammer\w.mdl
rem      materials.txt  materials\vgui\ak47.png
rem      sounds.txt     sound\axe\AxeBigBite-01.wav
rem  По строке на путь. Генерируются при сборке аддона.
rem ==================================================================

set "ADDON=%CD%"
set "TOOLS=%ADDON%\tools"
set "L_MODELS=%TOOLS%\models.txt"
set "L_MATERIALS=%TOOLS%\materials.txt"
set "L_SOUNDS=%TOOLS%\sounds.txt"

echo ==================================================================
echo   Remorseim Gunpack :: контент для НОВЫХ свепов
echo ==================================================================
echo.
echo   Папка аддона: %ADDON%
echo.

if not exist "%L_MODELS%" (
    echo [ОШИБКА] Нет tools\models.txt - нечего искать.
    echo Списки создаются при сборке аддона. Возьмите готовый архив,
    echo там они уже лежат.
    echo.
    pause
    exit /b 2
)

rem ------------------------------------------------------------------
rem  Путь к Garry's Mod
rem ------------------------------------------------------------------
set "GM="
if not "%GMOD_PATH%"=="" if exist "%GMOD_PATH%\" set "GM=%GMOD_PATH%"
if not defined GM call :guess_gmod

if not defined GM (
    echo Garry's Mod автоматически не нашёлся.
    echo.
    set "GM_IN="
    set /p "GM_IN=Путь к папке garrysmod (Enter - пропустить): "
    if defined GM_IN if exist "!GM_IN!\" set "GM=!GM_IN!"
)

rem ------------------------------------------------------------------
rem  Корни поиска: garrysmod, её addons, воркшоп 4000
rem ------------------------------------------------------------------
set "R1=%GM%"
set "R2="
set "R3="
set "R4="
if defined GM (
    set "R2=!GM!\addons"
    set "R3=!GM!\..\..\..\workshop\content\4000"
    set "R4=!GM!\..\..\..\..\workshop\content\4000"
)

if defined GM (
    echo garrysmod: !GM!
) else (
    echo garrysmod: не найден - ищу только в папках самого аддона.
)
echo.

rem ------------------------------------------------------------------
:quit
if defined IDX if exist "%IDX%" del "%IDX%" >nul 2>nul
exit /b 0

:menu
echo ------------------------------------------------------------------
echo   Что делаем?
echo ------------------------------------------------------------------
echo   1 - Найти и разложить: models + materials + sound
echo   2 - Только models
echo   3 - Только materials
echo   4 - Только sound
echo   5 - Проверить, чего не хватает
echo   6 - УДАЛИТЬ лишнее из models/materials/sound
echo   7 - Показать лишнее (без удаления)
echo   0 - Выход
echo ------------------------------------------------------------------
set "CHOICE="
set /p "CHOICE=Выбор [1]: "
if "%CHOICE%"=="" set "CHOICE=1"

if "%CHOICE%"=="0" goto quit
if "%CHOICE%"=="1" goto run_all
if "%CHOICE%"=="2" goto run_models
if "%CHOICE%"=="3" goto run_materials
if "%CHOICE%"=="4" goto run_sound
if "%CHOICE%"=="5" goto scan
if "%CHOICE%"=="6" goto prune_ask
if "%CHOICE%"=="7" goto prune_dry
echo Не понял выбор "%CHOICE%".
echo.
goto menu

rem ==================================================================
rem  Поиск и раскладка
rem ==================================================================
:run_all
set "WANT=all"
goto run_start
:run_models
set "WANT=models"
goto run_start
:run_materials
set "WANT=materials"
goto run_start
:run_sound
set "WANT=sound"
goto run_start

:run_start
echo.
set "COPIED=0"
set "FOUND=0"
set "MISSING=0"
set "AMBIG=0"
del "%TEMP%\rem_missing.txt" >nul 2>nul
del "%TEMP%\rem_ambig.txt" >nul 2>nul

if "%WANT%"=="all"       call :do_list "%L_MODELS%"
if "%WANT%"=="all"       call :do_list "%L_MATERIALS%"
if "%WANT%"=="all"       call :do_list "%L_SOUNDS%"
if "%WANT%"=="models"    call :do_list "%L_MODELS%"
if "%WANT%"=="materials" call :do_list "%L_MATERIALS%"
if "%WANT%"=="sound"     call :do_list "%L_SOUNDS%"

echo.
echo ------------------------------------------------------------------
echo   Найдено: %FOUND%   скопировано новых: %COPIED%   не найдено: %MISSING%
if not "%AMBIG%"=="0" echo   Неоднозначных имён: %AMBIG% (файл есть, но путь не совпал)
echo ------------------------------------------------------------------

if not "%MISSING%"=="0" (
    echo.
    echo Чего нет ни в garrysmod, ни в воркшопе:
    call :show_head "%TEMP%\rem_missing.txt" 40
    echo.
    echo Проще всего подписаться на воркшоп-аддоны Z-City и Remorseim.
)

if not "%AMBIG%"=="0" (
    echo.
    echo Имя файла встречается у нескольких моделей - проверьте руками:
    call :show_head "%TEMP%\rem_ambig.txt" 15
)
goto after

rem ----------------------------------------------------------------
:do_list
rem %1 = файл со списком относительных путей
if not exist "%~1" goto :eof
for /f "usebackq delims=" %%R in ("%~1") do call :one_file "%%R"
goto :eof

rem ----------------------------------------------------------------
:one_file
rem %~1 = models\weapons\hammer\w.mdl
set "REL=%~1"
set "DST=%ADDON%\%REL%"

if exist "%DST%" (
    set /a FOUND+=1
    goto :eof
)

set "SRC="
call :locate "%REL%"

if not defined SRC (
    set /a MISSING+=1
    >>"%TEMP%\rem_missing.txt" echo %REL%
    goto :eof
)

for %%D in ("%DST%") do if not exist "%%~dpD" mkdir "%%~dpD" >nul 2>nul
copy /y "%SRC%" "%DST%" >nul 2>nul
if errorlevel 1 (
    set /a MISSING+=1
    >>"%TEMP%\rem_missing.txt" echo %REL%
) else (
    set /a COPIED+=1
    set /a FOUND+=1
)
goto :eof

rem ----------------------------------------------------------------
:locate
rem %~1 = относительный путь. На выходе SRC (пусто, если не нашли).
set "REL=%~1"
set "SRC="

rem 1) точный путь от каждого корня - это быстро, чаще всего срабатывает
for %%R in ("%R1%" "%R2%" "%R3%" "%R4%") do (
    if not "%%~R"=="" if not defined SRC if exist "%%~fR\%REL%" set "SRC=%%~fR\%REL%"
)
if defined SRC goto :eof

rem 2) структура папок в воркшопе другая, поэтому ищем по имени файла.
rem    Обходить дерево на каждый из сотен путей нельзя - строим индекс
rem    один раз и дальше только читаем его.
call :ensure_index
if not exist "%IDX%" goto :eof

for %%F in ("%REL%") do set "BASE=%%~nxF"
if not defined BASE goto :eof

rem Ищем по имени. Если хвост пути совпал - берём его. Если совпал только
rem имя и таких файлов несколько - НЕ угадываем: это может быть чужая
rem модель с тем же именем, лучше сообщить и оставить место пустым.
set "EXACT="
set "FIRST="
set "COUNT=0"

for /f "usebackq delims=" %%H in (`findstr /i /e /l /c:"\%BASE%" "%IDX%"`) do (
    set /a COUNT+=1
    if not defined FIRST set "FIRST=%%H"
    if not defined EXACT (
        echo %%H| findstr /i /e /l /c:"\%REL%" >nul
        if not errorlevel 1 set "EXACT=%%H"
    )
)

if defined EXACT (
    set "SRC=%EXACT%"
    goto :eof
)

if "%COUNT%"=="1" (
    set "SRC=%FIRST%"
    goto :eof
)

if "%COUNT%"=="0" goto :eof

rem неоднозначно
set /a AMBIG+=1
>>"%TEMP%\rem_ambig.txt" echo %REL%
goto :eof

rem ----------------------------------------------------------------
:ensure_index
rem Один обход garrysmod + addons + воркшопа. Результат кэшируется на запуск.
if defined IDX goto :eof
set "IDX=%TEMP%\rem_index_%RANDOM%.txt"
del "%IDX%" >nul 2>nul

echo   строю индекс файлов garrysmod и воркшопа (один раз, может занять минуту)...
for %%R in ("%R1%" "%R2%" "%R3%" "%R4%") do (
    if not "%%~R"=="" if exist "%%~fR\" (
        dir /b /s /a-d "%%~fR\*" 2>nul >>"%IDX%"
    )
)
if not exist "%IDX%" set "IDX="
goto :eof

rem ==================================================================
rem  Проверка: чего не хватает
rem ==================================================================
:scan
echo.
set "HAVE=0"
set "LACK=0"
del "%TEMP%\rem_lack.txt" >nul 2>nul

for %%L in ("%L_MODELS%" "%L_MATERIALS%" "%L_SOUNDS%") do (
    if exist "%%~L" (
        for /f "usebackq delims=" %%R in ("%%~L") do (
            if exist "%ADDON%\%%R" (
                set /a HAVE+=1
            ) else (
                set /a LACK+=1
                >>"%TEMP%\rem_lack.txt" echo %%R
            )
        )
    )
)

echo ------------------------------------------------------------------
echo   На месте: %HAVE%   не хватает: %LACK%
echo ------------------------------------------------------------------
if not "%LACK%"=="0" (
    echo.
    echo Не хватает:
    call :show_head "%TEMP%\rem_lack.txt" 40
) else (
    echo.
    echo Всё, что нужно новым свep'ам, лежит в папках аддона.
)
goto after

rem ==================================================================
rem  Чистка лишнего
rem ==================================================================
:prune_ask
echo.
echo ВНИМАНИЕ: будут УДАЛЕНЫ файлы из models/materials/sound,
echo которых нет в списках tools\*.txt.
echo.
set "OK="
set /p "OK=Точно удалить? (yes/no) [no]: "
if /i not "%OK%"=="yes" (
    echo Отменено.
    goto menu
)
set "DO_DELETE=1"
goto prune_run

:prune_dry
echo.
set "DO_DELETE=0"

:prune_run
rem Словарь нужных файлов: ключ = имя файла, значение = 1.
rem Сравниваем по имени, а не по полному пути: если такое имя нужно
rem хотя бы одной модели - файл оставляем. Лучше оставить лишнее,
rem чем снести нужное.
set "JUNK=0"
set "KEPT=0"

for %%L in ("%L_MODELS%" "%L_MATERIALS%" "%L_SOUNDS%") do (
    if exist "%%~L" (
        for /f "usebackq delims=" %%R in ("%%~L") do (
            for %%B in ("%%R") do set "NEED_%%~nxB=1"
        )
    )
)

for %%K in (models materials sound) do (
    if exist "%ADDON%\%%K" (
        for /f "usebackq delims=" %%F in (`dir /b /s /a-d "%ADDON%\%%K\*" 2^>nul`) do (
            set "ISNEEDED="
            for %%B in ("%%F") do (
                if defined NEED_%%~nxB set "ISNEEDED=1"
                if /i "%%~nxB"=="README.txt" set "ISNEEDED=1"
            )

            if defined ISNEEDED (
                set /a KEPT+=1
            ) else (
                set /a JUNK+=1
                if "%DO_DELETE%"=="1" (
                    del /f /q "%%~fF" >nul 2>nul
                    echo   удалён: %%~fF
                ) else (
                    echo   лишний: %%~fF
                )
            )
        )
    )
)

rem пустые папки: rd падает на непустых, поэтому три прохода
rem подряд сносят и вложенные, и родительские
if "%DO_DELETE%"=="1" (
    for %%P in (1 2 3) do (
        for %%K in (models materials sound) do (
            if exist "%ADDON%\%%K" (
                for /f "usebackq delims=" %%D in (`dir /b /s /ad "%ADDON%\%%K\*" 2^>nul`) do rd "%%~fD" >nul 2>nul
            )
        )
    )
)

echo.
echo ------------------------------------------------------------------
if "%DO_DELETE%"=="1" (
    echo   Удалено лишнего: %JUNK%   оставлено нужного: %KEPT%
) else (
    echo   Лишнего: %JUNK%   нужного: %KEPT%
    echo   Это только показ. Для удаления - пункт 6.
)
echo ------------------------------------------------------------------
goto after

rem ==================================================================
rem  Вспомогательное
rem ==================================================================
:show_head
rem %1 = файл, %2 = сколько строк показать
if not exist "%~1" goto :eof
set "N=0"
for /f "usebackq delims=" %%M in ("%~1") do (
    set /a N+=1
    if !N! LEQ %~2 echo   %%M
)
if !N! GTR %~2 echo   ... всего %N%, полный список: %~1
goto :eof

rem ----------------------------------------------------------------
:guess_gmod
rem сначала реестр: путь к Steam, потом типовые папки
for /f "tokens=2*" %%A in ('reg query "HKCU\Software\Valve\Steam" /v SteamPath 2^>nul ^| findstr /i "SteamPath"') do (
    if not defined GM if exist "%%~B\steamapps\common\GarrysMod\garrysmod\" set "GM=%%~B\steamapps\common\GarrysMod\garrysmod"
)
for %%P in (
    "C:\Program Files (x86)\Steam\steamapps\common\GarrysMod\garrysmod"
    "C:\Program Files\Steam\steamapps\common\GarrysMod\garrysmod"
    "D:\Steam\steamapps\common\GarrysMod\garrysmod"
    "D:\SteamLibrary\steamapps\common\GarrysMod\garrysmod"
    "E:\SteamLibrary\steamapps\common\GarrysMod\garrysmod"
    "C:\Games\GarrysMod\garrysmod"
) do (
    if not defined GM if exist "%%~P\" set "GM=%%~P"
)
goto :eof

rem ----------------------------------------------------------------
:after
if defined IDX if exist "%IDX%" del "%IDX%" >nul 2>nul
echo.
pause
exit /b 0
