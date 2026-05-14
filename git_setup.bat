@echo off
:: ============================================================
::  git_setup.bat — Configuracion inicial de Git + GitHub
::  Ejecutar UNA SOLA VEZ desde la carpeta del proyecto
:: ============================================================

echo.
echo ========================================
echo   SETUP INICIAL GIT + GITHUB
echo ========================================
echo.

:: 1. Verificar si Git esta instalado
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Git no encontrado. Descargando instalador...
    echo.
    echo Abre este enlace y descarga Git para Windows:
    echo https://git-scm.com/download/win
    echo.
    echo Despues de instalar, vuelve a ejecutar este script.
    pause
    start https://git-scm.com/download/win
    exit /b
)

echo [OK] Git detectado:
git --version
echo.

:: 2. Configurar identidad (solo si no esta configurada)
git config --global user.name >nul 2>&1
if "%errorlevel%"=="1" (
    set /p GIT_NAME="Tu nombre para Git (ej: Juan Lopez): "
    git config --global user.name "%GIT_NAME%"
)

git config --global user.email >nul 2>&1
if "%errorlevel%"=="1" (
    set /p GIT_EMAIL="Tu email de GitHub: "
    git config --global user.email "%GIT_EMAIL%"
)

:: 3. Inicializar repo local (si no existe)
if not exist ".git" (
    echo [>>] Inicializando repositorio local...
    git init
    git branch -M main
    echo [OK] Repo inicializado
) else (
    echo [OK] Repo local ya existe
)
echo.

:: 4. Crear .gitignore
if not exist ".gitignore" (
    echo [>>] Creando .gitignore...
    (
        echo # Python
        echo __pycache__/
        echo *.pyc
        echo *.pyo
        echo *.pyd
        echo .Python
        echo *.egg-info/
        echo dist/
        echo build/
        echo.
        echo # Modelos entrenados ^(pueden ser grandes^)
        echo models/
        echo.
        echo # Entornos virtuales
        echo venv/
        echo .venv/
        echo env/
        echo.
        echo # IDEs
        echo .vscode/
        echo .idea/
        echo *.suo
        echo.
        echo # Datos sensibles
        echo .env
        echo secrets.py
        echo config_local.py
        echo.
        echo # Logs
        echo *.log
    ) > .gitignore
    echo [OK] .gitignore creado
) else (
    echo [OK] .gitignore ya existe
)
echo.

:: 5. Primer commit
echo [>>] Preparando primer commit...
git add .
git commit -m "feat: version inicial del proyecto"
echo.

:: 6. Conectar con GitHub
echo ========================================
echo   CONECTAR CON GITHUB
echo ========================================
echo.
echo 1. Ve a https://github.com/new
echo 2. Crea un repositorio nuevo (SIN inicializar con README)
echo 3. Copia la URL del repo (ej: https://github.com/tu-usuario/trading-ml.git)
echo.
set /p REPO_URL="Pega aqui la URL de tu repositorio GitHub: "
echo.

git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%

echo [>>] Subiendo codigo a GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   [OK] PROYECTO SUBIDO A GITHUB
    echo ========================================
    echo.
    echo Para futuras actualizaciones usa: git_commit.bat
) else (
    echo.
    echo [!] Error al hacer push. Posibles causas:
    echo     - No iniciaste sesion en GitHub
    echo     - La URL del repo es incorrecta
    echo.
    echo Autenticate con GitHub CLI o con token:
    echo https://docs.github.com/es/authentication
)

echo.
pause
