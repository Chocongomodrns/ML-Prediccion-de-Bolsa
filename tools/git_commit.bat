@echo off
:: ============================================================
::  git_commit.bat — Commit y push rapido con version
::  Ubicacion: tools\git_commit.bat
::  Uso: doble click desde cualquier lugar
:: ============================================================

:: Obtener la carpeta donde esta este .bat y subir un nivel
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR:~0,-1%"
for %%i in ("%PROJECT_DIR%") do set "PROJECT_DIR=%%~dpi"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

:: Moverse a la raiz del proyecto
cd /d "%PROJECT_DIR%"
echo [INFO] Directorio del proyecto: %PROJECT_DIR%

:: Verificar que hay un repo Git
git status >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] No se encontro repositorio Git en: %PROJECT_DIR%
    pause
    exit /b
)

echo.
echo ========================================
echo   ML TRADING — CONTROL DE VERSIONES
echo ========================================
echo.

:: Mostrar estado
echo [INFO] Estado del repositorio:
git status --short
echo.

:: Ver si hay cambios
git status --porcelain > "%TEMP%\gitstatus.txt" 2>&1
for %%A in ("%TEMP%\gitstatus.txt") do if %%~zA==0 (
    echo [OK] No hay cambios pendientes.
    del "%TEMP%\gitstatus.txt"
    pause
    exit /b
)
del "%TEMP%\gitstatus.txt"

:: Obtener la rama actual
for /f %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set CURRENT_BRANCH=%%i
echo [INFO] Rama actual: %CURRENT_BRANCH%
echo.

:: Obtener ultima version
for /f %%i in ('git tag --sort=-v:refname 2^>nul') do (
    set LAST_TAG=%%i
    goto :got_tag
)
set LAST_TAG=v0.0.0
:got_tag
echo [INFO] Ultima version: %LAST_TAG%
echo.

:: Tipo de cambio
echo Tipo de cambio:
echo   [1] fix   — correccion de bug        (v0.0.X)
echo   [2] feat  — nueva funcionalidad      (v0.X.0)
echo   [3] major — cambio grande / breaking (vX.0.0)
echo   [4] chore — mantenimiento / refactor (sin cambio de version)
echo.
set /p CHANGE_TYPE="Elige tipo [1-4]: "

:: Mensaje del commit
set /p COMMIT_MSG="Mensaje del commit: "

:: Prefijo
if "%CHANGE_TYPE%"=="1" set PREFIX=fix
if "%CHANGE_TYPE%"=="2" set PREFIX=feat
if "%CHANGE_TYPE%"=="3" set PREFIX=BREAKING
if "%CHANGE_TYPE%"=="4" set PREFIX=chore
if "%PREFIX%"=="" set PREFIX=chore

:: Calcular nueva version
for /f "tokens=1,2,3 delims=." %%a in ("%LAST_TAG:v=%") do (
    set MAJ=%%a
    set MIN=%%b
    set PAT=%%c
)
if "%MAJ%"=="" set MAJ=0
if "%MIN%"=="" set MIN=0
if "%PAT%"=="" set PAT=0

if "%CHANGE_TYPE%"=="1" ( set /a NEW_PAT=%PAT%+1 & set NEW_VER=v%MAJ%.%MIN%.%NEW_PAT% )
if "%CHANGE_TYPE%"=="2" ( set /a NEW_MIN=%MIN%+1 & set NEW_VER=v%MAJ%.%NEW_MIN%.0 )
if "%CHANGE_TYPE%"=="3" ( set /a NEW_MAJ=%MAJ%+1 & set NEW_VER=v%NEW_MAJ%.0.0 )
if "%CHANGE_TYPE%"=="4" ( set NEW_VER=%LAST_TAG% )

echo.
echo [>>] Commit: "%PREFIX%: %COMMIT_MSG%"

git add .
git commit -m "%PREFIX%: %COMMIT_MSG%"

if %errorlevel% neq 0 (
    echo [!] Error en el commit.
    pause
    exit /b
)

if not "%CHANGE_TYPE%"=="4" (
    git tag -a %NEW_VER% -m "%PREFIX%: %COMMIT_MSG%"
    echo [OK] Tag: %NEW_VER%
)

echo.
echo [>>] Subiendo a GitHub rama: %CURRENT_BRANCH%
git push origin %CURRENT_BRANCH%

if not "%CHANGE_TYPE%"=="4" (
    git push origin %NEW_VER%
)

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    if not "%CHANGE_TYPE%"=="4" (
        echo   [OK] SUBIDO — Version: %NEW_VER%
    ) else (
        echo   [OK] SUBIDO — %LAST_TAG%
    )
    echo ========================================
) else (
    echo [!] Error al hacer push.
)

echo.
pause
