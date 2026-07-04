@echo off
REM ============================================================
REM  Flying Damage - package .wotmod (SWF already compiled).
REM  Compiles python -> .pyc, packages STORED with SWF included.
REM  Run:  .\build_wotmod.bat
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

set MOD_ID=com.author.flyingdamage
set MOD_VER=3.2.0
set OUT=%MOD_ID%_%MOD_VER%.wotmod

echo.
echo ==== [1/5] Locate Python 2.7 ====
set "PY="
py -2.7 -c "import sys" >nul 2>&1 && set "PY=py -2.7"
if not defined PY if exist "C:\Python27\python.exe" set "PY=C:\Python27\python.exe"
if not defined PY (
    echo   ERROR: Python 2.7 not found (install 2.7.18).
    pause & exit /b 1
)
echo   Using: %PY%

echo.
echo ==== [2/5] Check SWF exists ====
if not exist "resources\in\gui\flash\FlyingDamageApp.swf" (
    echo   ERROR: resources\in\gui\flash\FlyingDamageApp.swf missing.
    echo   Compile the SWF first (see README) or run via GitHub Actions.
    pause & exit /b 1
)
echo   SWF present.

echo.
echo ==== [3/5] Stage files ====
if exist stage rmdir /s /q stage
mkdir stage
mkdir stage\res\gui\flash
mkdir stage\res\scripts\client\gui\mods
copy /y resources\in\gui\flash\FlyingDamageApp.swf stage\res\gui\flash\ >nul
xcopy /e /i /y python\gui\mods stage\res\scripts\client\gui\mods >nul

echo.
echo ==== [4/5] Compile .py -^> .pyc, remove .py ====
%PY% -m compileall -f stage\res\scripts\client\gui\mods
set "PYC_OK=0"
for /r "stage\res\scripts\client\gui\mods" %%f in (*.pyc) do set "PYC_OK=1"
if "%PYC_OK%"=="0" ( echo   ERROR: no .pyc produced. & pause & exit /b 1 )
del /s /q stage\res\scripts\client\gui\mods\*.py >nul 2>&1

> stage\meta.xml echo ^<root^>
>> stage\meta.xml echo     ^<id^>%MOD_ID%^</id^>
>> stage\meta.xml echo     ^<version^>%MOD_VER%^</version^>
>> stage\meta.xml echo     ^<name^>Flying Damage^</name^>
>> stage\meta.xml echo     ^<description^>Floating damage numbers above tanks (SWF view).^</description^>
>> stage\meta.xml echo ^</root^>

echo.
echo ==== [5/5] Package STORED ====
if exist "%OUT%" del /q "%OUT%"
set "SEVENZIP="
if exist "%ProgramFiles%\7-Zip\7z.exe" set "SEVENZIP=%ProgramFiles%\7-Zip\7z.exe"
if exist "%ProgramFiles(x86)%\7-Zip\7z.exe" set "SEVENZIP=%ProgramFiles(x86)%\7-Zip\7z.exe"
pushd stage
if defined SEVENZIP (
    "%SEVENZIP%" a -tzip -mx0 "..\%OUT%" meta.xml res >nul
) else (
    %PY% -c "import zipfile,os; z=zipfile.ZipFile(r'..\%OUT%','w',zipfile.ZIP_STORED); [z.write(os.path.join(r,f), os.path.join(r,f)) for r,_,fs in os.walk('.') for f in fs]; z.close()"
)
popd
rmdir /s /q stage

echo.
if exist "%OUT%" (
    echo ============================================================
    echo   SUCCESS:  %OUT%
    echo   Copy to:  ^<WoT^>\mods\2.3.0.1\
    echo ============================================================
) else (
    echo   ERROR: archive not created.
)
echo.
pause
