@echo off
:: ============================================================
::  git_commit.bat — Commit y push rapido con version
::  Uso: doble click, o desde consola con mensaje opcional
::  Ejemplo: git_commit.bat "fix: correccion en scanner"
:: ============================================================

echo.
echo ========================================
echo   ML TRADING — CONTROL DE VERSIONES
echo ========================================
echo.

:: Verificar que es un repo git
if not exist ".git" (
    echo [!] Esta carpeta no es un repositorio Git.
    echo     Ejecuta primero git_setup.bat
    pause
    exit /b
)

:: Mostrar estado actual
echo [INFO] Estado del repositorio:
git status --short
echo.

:: Ver si hay cambios
git diff --quiet --cached
git status --porcelain > tmp_status.txt
for %%A in (tmp_status.txt) do if %%~zA==0 (
    echo [OK] No hay cambios pendientes. Todo esta actualizado.
    del tmp_status.txt
    pause
    exit /b
)
del tmp_status.txt

:: Obtener la version actual del tag
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
echo   [1] fix   — correccion de bug (v0.0.X)
echo   [2] feat  — nueva funcionalidad (v0.X.0)
echo   [3] major — cambio grande / breaking (vX.0.0)
echo   [4] chore — mantenimiento / refactor (sin cambio de version)
echo.
set /p CHANGE_TYPE="Elige tipo [1-4]: "

:: Mensaje del commit
if "%~1"=="" (
    set /p COMMIT_MSG="Mensaje del commit: "
) else (
    set COMMIT_MSG=%~1
)

:: Prefijo segun tipo
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

if "%CHANGE_TYPE%"=="1" (
    set /a NEW_PAT=%PAT%+1
    set NEW_VER=v%MAJ%.%MIN%.%NEW_PAT%
)
if "%CHANGE_TYPE%"=="2" (
    set /a NEW_MIN=%MIN%+1
    set NEW_VER=v%MAJ%.%NEW_MIN%.0
)
if "%CHANGE_TYPE%"=="3" (
    set /a NEW_MAJ=%MAJ%+1
    set NEW_VER=v%NEW_MAJ%.0.0
)
if "%CHANGE_TYPE%"=="4" (
    set NEW_VER=%LAST_TAG%
)

echo.
echo [>>] Haciendo commit: "%PREFIX%: %COMMIT_MSG%"

:: Staging + commit
git add .
git commit -m "%PREFIX%: %COMMIT_MSG%"

if %errorlevel% neq 0 (
    echo [!] Error en el commit. Revisa el estado del repo.
    pause
    exit /b
)

:: Tag de version (solo si no es chore)
if not "%CHANGE_TYPE%"=="4" (
    git tag -a %NEW_VER% -m "%PREFIX%: %COMMIT_MSG%"
    echo [OK] Tag creado: %NEW_VER%
)

:: Push
echo.
echo [>>] Subiendo a GitHub...
git push origin main

if not "%CHANGE_TYPE%"=="4" (
    git push origin %NEW_VER%
)

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    if not "%CHANGE_TYPE%"=="4" (
        echo   [OK] SUBIDO — Version: %NEW_VER%
    ) else (
        echo   [OK] SUBIDO — %LAST_TAG% ^(sin cambio de version^)
    )
    echo ========================================
) else (
    echo.
    echo [!] Error al hacer push. Verifica tu conexion y autenticacion.
)

echo.
pause
