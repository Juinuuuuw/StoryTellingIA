@echo off
echo ============================================================
echo  INSTALANDO / VERIFICANDO rembg
echo ============================================================
cd /d %~dp0
call venv\Scripts\activate.bat

echo.
echo Verificando dependencias...
pip show rembg >nul 2>&1
if %errorlevel% neq 0 (
    echo rembg nao encontrado. Instalando...
    pip install rembg onnxruntime pillow
) else (
    echo rembg ja instalado. OK!
)

echo.
echo ============================================================
echo  INICIANDO rembg_server.py na porta 5001
echo ============================================================
python servidor\rembg_server.py
pause
