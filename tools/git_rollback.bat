@echo off
:: ============================================================
::  git_rollback.bat — Ver historial y revertir versiones
::  Ubicacion: tools\git_rollback.bat
:: ============================================================

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR:~0,-1%"
for %%i in ("%PROJECT_DIR%") do set "PROJECT_DIR=%%~dpi"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

cd /d "%PROJECT_DIR%"
echo [INFO] Directorio: %PROJECT_DIR%

git status >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] No se encontro repositorio Git en: %PROJECT_DIR%
    pause
    exit /b
)

echo.
echo ========================================
echo   ML TRADING — HISTORIAL Y ROLLBACK
echo ========================================
echo.
echo   [1] Ver historial de commits
echo   [2] Ver versiones (tags)
echo   [3] Revertir a una version anterior
echo   [4] Ver diferencias entre versiones
echo   [5] Salir
echo.
set /p OPTION="Elige opcion [1-5]: "

if "%OPTION%"=="1" goto :historial
if "%OPTION%"=="2" goto :tags
if "%OPTION%"=="3" goto :rollback
if "%OPTION%"=="4" goto :diff
if "%OPTION%"=="5" exit /b
goto :eof

:historial
echo.
echo ── ULTIMOS 20 COMMITS ──────────────────
git log --oneline --graph --decorate -20
echo.
pause
goto :eof

:tags
echo.
echo ── VERSIONES DISPONIBLES ───────────────
git tag --sort=-v:refname
echo.
pause
goto :eof

:rollback
echo.
git tag --sort=-v:refname
echo.
set /p TARGET="Version a restaurar (ej: v2.0.0): "
echo.
echo [!] Esto creara una rama temporal. Main no se modifica.
set /p CONFIRM="Confirmar? (S/N): "
if /i not "%CONFIRM%"=="S" ( echo Cancelado. & pause & goto :eof )
git checkout -b rollback/%TARGET% %TARGET%
echo.
echo [OK] Rama: rollback/%TARGET%
echo     Para volver: git checkout Main
echo.
pause
goto :eof

:diff
echo.
git tag --sort=-v:refname
echo.
set /p VER1="Version base (ej: v1.0.0): "
set /p VER2="Version a comparar (ej: v2.0.0 o HEAD): "
echo.
git diff %VER1% %VER2% --stat
echo.
pause
goto :eof
