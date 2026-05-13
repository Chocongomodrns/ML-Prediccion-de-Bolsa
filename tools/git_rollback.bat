@echo off
:: ============================================================
::  git_rollback.bat — Ver historial y revertir versiones
:: ============================================================

echo.
echo ========================================
echo   ML TRADING — HISTORIAL Y ROLLBACK
echo ========================================
echo.

if not exist ".git" (
    echo [!] Esta carpeta no es un repositorio Git.
    pause
    exit /b
)

echo Que quieres hacer?
echo.
echo   [1] Ver historial de commits
echo   [2] Ver versiones ^(tags^)
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
set /p TARGET="Version a restaurar (ej: v1.2.0) o hash de commit: "
echo.
echo [!] ATENCION: Esto creara una rama temporal con esa version.
echo     Tu rama main NO se modifica hasta que confirmes.
echo.
set /p CONFIRM="Confirmar? (S/N): "
if /i not "%CONFIRM%"=="S" (
    echo Cancelado.
    pause
    goto :eof
)
git checkout -b rollback/%TARGET% %TARGET%
echo.
echo [OK] Ahora estas en la rama rollback/%TARGET%
echo     Para volver a main: git checkout main
echo     Para hacer este rollback permanente en main:
echo       git checkout main
echo       git merge rollback/%TARGET%
echo       git push origin main
echo.
pause
goto :eof

:diff
echo.
git tag --sort=-v:refname
echo.
set /p VER1="Version base (ej: v1.0.0): "
set /p VER2="Version a comparar (ej: v1.1.0 o HEAD): "
echo.
git diff %VER1% %VER2% --stat
echo.
pause
goto :eof
